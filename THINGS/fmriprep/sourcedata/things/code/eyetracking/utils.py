import json
import copy

import numpy as np
import pandas as pd
import scipy
from scipy import interpolate


def get_list(
    out_path: str,
    is_final: bool,
) -> pd.DataFrame:
    '''
    get clean list of runs to process
    '''
    fname = 'QCed_finalbids_list' if is_final else 'QCed_file_list'
    file_list = pd.read_csv(
        f'{out_path}/QC_gaze/{fname}.tsv',
        sep='\t',
        header=0,
    )

    clean_list = file_list[file_list['DO_NOT_USE']!=1.0]
    if is_final:
        return clean_list[clean_list['Fails_DriftCorr']!=1.0]
    else:
        return clean_list


def create_gaze_path(row, file_path):
    '''
    for each run, create path to deserialized gaze file
    '''
    s = row['subject']
    ses = row['session']
    task = row["task"]

    task_root = file_path.split('/')[-1]
    if task_root == 'mario3':
        task = 'task-mario3'

    return f'{file_path}/{s}/{ses}/{s}_{ses}_{row["run"]}_{row["file_number"]}_{task}_gaze2D.npz'


def create_event_path(row, file_path, log=False):
    '''
    for each run, create path to events.tsv file
    '''
    s = row['subject']
    ses = row['session']
    if log:
        return f'{file_path}/{s}/{ses}/{s}_{ses}_{row["file_number"]}.log'
    else:
        if row['task'] in ['task-bar', 'task-rings', 'task-wedges', 'task-flocdef', 'task-flocalt']:
            return f'{file_path}/{s}/{ses}/{s}_{ses}_{row["file_number"]}_{row["task"]}_events.tsv'
        else:
            return f'{file_path}/{s}/{ses}/{s}_{ses}_{row["file_number"]}_{row["task"]}_{row["run"]}_events.tsv'


def create_ip_path(row, file_path):
    '''
    for each run, create path to info.player.json file
    '''
    s = row['subject']
    ses = row['session']
    r = row['run']
    t = row['task']
    fnum = row['file_number']

    if row['task'] in ['task-bar', 'task-rings', 'task-wedges', 'task-flocdef', 'task-flocalt']:
        return f'{file_path}/{s}/{ses}/{s}_{ses}_{fnum}.pupil/{t}/000/info.player.json'
    else:
        return f'{file_path}/{s}/{ses}/{s}_{ses}_{fnum}.pupil/{t}_{r}/000/info.player.json'


def create_dg_path(row, file_path):
    '''
    for each run, create path to deepgaze predictions file (friends task)
    '''
    s, epi = row['run'].split('e')
    ep = (epi[:-1]).zfill(2) + epi[-1]
    task = row['task']

    return f'{file_path}/deepgaze_coord/friends_s0{s[-1]}e{ep}_locmax_normalized_xy.npz'


def create_mkv_path(row, file_path):
    '''
    for each run, create path to .mkv stimulus file (friends task)
    '''
    s, epi = row['run'].split('e')
    ep = (epi[:-1]).zfill(2) + epi[-1]
    task = row['task']

    return f'{file_path}/s{s[-1]}/friends_s0{s[-1]}e{ep}.mkv'


def add_file_paths(
    clean_list: pd.DataFrame,
    in_path: str,
    out_path: str,
    mkv_path: str,
    task: str,
) -> pd.DataFrame:
    '''
    add file paths to list of runs
    '''
    clean_list['gaze_path'] = clean_list.apply(lambda row: create_gaze_path(row, out_path), axis=1)
    if task == 'friends':
        clean_list['dg_path'] = clean_list.apply(lambda row: create_dg_path(row, out_path), axis=1)
        clean_list['mkv_path'] = clean_list.apply(lambda row: create_mkv_path(row, mkv_path), axis=1)
    else:
        clean_list['events_path'] = clean_list.apply(lambda row: create_event_path(row, in_path), axis=1)
        clean_list['log_path'] = clean_list.apply(lambda row: create_event_path(row, in_path, log=True), axis=1)
        clean_list['infoplayer_path'] = clean_list.apply(lambda row: create_ip_path(row, in_path), axis=1)

    return clean_list


def get_onset_time(
    log_path: str,
    run_num: str,
    ip_path: str,
    gz_ts: float,
) -> float:
    onset_time_dict = {}
    TTL_0 = -1
    has_lines = True

    with open(log_path) as f:
        lines = f.readlines()
        if len(lines) == 0:
            has_lines = False
        for line in lines:
            if "fMRI TTL 0" in line:
                TTL_0 = line.split('\t')[0]
            elif "saved wide-format data to /scratch/neuromod/data" in line:
                rnum = line.split('\t')[-1].split('_')[-2]
                onset_time_dict[rnum] = float(TTL_0)
            elif "class 'src.tasks.videogame.VideoGameMultiLevel'" in line:
                rnum = line.split(': ')[-2].split('_')[-1]
                onset_time_dict[rnum] = float(TTL_0)
            elif "class 'src.tasks.localizers.FLoc'" in line:
                rnum = run2task_mapping['floc'][line.split(': ')[-2]]
                onset_time_dict[rnum] = float(TTL_0)
            elif "class 'src.tasks.retinotopy.Retinotopy'" in line:
                rnum = run2task_mapping['retino'][line.split(': ')[-2]]
                onset_time_dict[rnum] = float(TTL_0)

    if has_lines:
        o_time = onset_time_dict[run_num]

        with open(ip_path, 'r') as f:
            iplayer = json.load(f)
        sync_ts = iplayer['start_time_synced_s']
        syst_ts = iplayer['start_time_system_s']

        is_sync_gz = (gz_ts-sync_ts)**2 < (gz_ts-syst_ts)**2
        is_sync_ot = (o_time-sync_ts)**2 < (o_time-syst_ts)**2
        if is_sync_gz != is_sync_ot:
            if is_sync_ot:
                o_time += (syst_ts - sync_ts)
            else:
                o_time += (sync_ts - syst_ts)
    else:
        print('empty log file, onset time estimated from gaze timestamp')
        o_time = gz_ts

    return o_time


def reset_gaze_time(
    gaze: np.array,
    onset_time: float,
    conf_thresh: float=0.9,
    distance: bool=True,
) -> tuple:
    '''
    Realign gaze timestamps based on the task & eyetracker onset/offset.
    Export new list of gaze dictionaries
    (w task-aligned time stamps) and other metrics needed to perform
    drift correction
    '''
    # all gaze values (unfiltered)
    reset_gaze_list = []
    all_x = []
    all_y = []
    all_times = []
    all_conf = []

    """
    Normalized (proportion of screen) distance between above-threshold gaze
    and fixation point(if distance=True) or normalized position
    (if distance=False).
    """
    (x_diff, y_diff) = [0.5, 0.5] if distance else [0.0, 0.0]

    clean_x = []
    clean_y = []
    clean_times = []
    clean_conf = []

    for gz_pt in gaze:
        timestp = gz_pt['timestamp'] - onset_time
        # exclude gaze & pupil gathered before task onset
        if timestp > 0.0:
            x_norm, y_norm = gz_pt['norm_pos']
            cfd = gz_pt['confidence']

            all_x.append(x_norm)
            all_y.append(y_norm)
            all_times.append(timestp)
            all_conf.append(cfd)

            gz_pt['reset_time'] = timestp
            reset_gaze_list.append(gz_pt)

            if cfd > conf_thresh:
                clean_x.append(x_norm - x_diff)
                clean_y.append(y_norm - y_diff)
                clean_conf.append(cfd)
                clean_times.append(timestp)

    return reset_gaze_list, (all_x, all_y, all_times, all_conf), (clean_x, clean_y, clean_times, clean_conf)


def apply_poly(
    ref_times: list,
    distances: list,
    degree: int,
    all_times: np.array,
    anchors: list = [150, 150],
) -> np.array:
    '''
    Fit polynomial to a distribution, then export points along that polynomial curve
    that correspond to specific gaze time stamps

    The very begining and end of distribution are excluded for stability
    e.g., participants sometimes look off screen at movie onset & offset,
    while deepgaze is biased to the center when shown a black screen.
    This really throws off polynomials
    '''
    if degree == 1:
        p1, p0 = np.polyfit(ref_times[anchors[0]:-anchors[1]], distances[anchors[0]:-anchors[1]], 1)
        p_of_all = p1*(all_times) + p0

    elif degree == 2:
        p2, p1, p0 = np.polyfit(ref_times[anchors[0]:-anchors[1]], distances[anchors[0]:-anchors[1]], 2)
        p_of_all = p2*(all_times**2) + p1*(all_times) + p0

    elif degree == 3:
        p3, p2, p1, p0 = np.polyfit(ref_times[anchors[0]:-anchors[1]], distances[anchors[0]:-anchors[1]], 3)
        p_of_all = p3*(all_times**3) + p2*(all_times**2) + p1*(all_times) + p0

    elif degree == 4:
        p4, p3, p2, p1, p0 = np.polyfit(ref_times[anchors[0]:-anchors[1]], distances[anchors[0]:-anchors[1]], 4)
        p_of_all = p4*(all_times**4) + p3*(all_times**3) + p2*(all_times**2) + p1*(all_times) + p0

    return p_of_all


def apply_gaussian(
    ref_times: list,
    distances: list,
    all_times: np.array,
    rollwin_dur: float = 15.0,
    fps: float = 250.0,
    anchors: list = [150, 150],
) -> np.array:

    roll_win = int(fps*rollwin_dur)

    dist = distances[anchors[0]:-anchors[1]]
    median_line = pd.Series(dist).rolling(roll_win).median()
    under_line = pd.Series(dist).rolling(roll_win).quantile(0.25)
    over_line = pd.Series(dist).rolling(roll_win).quantile(0.75)

    median_line[:roll_win-1] = np.median(dist[:roll_win])
    under_line[:roll_win-1] = np.quantile(dist[:roll_win], 0.25)
    over_line[:roll_win-1] = np.quantile(dist[:roll_win], 0.75)

    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html
    sig_val = int(fps*20)
    median_gauss = scipy.ndimage.gaussian_filter(copy.deepcopy(median_line), sigma=sig_val, mode='nearest', truncate=1.0)
    under_gauss = scipy.ndimage.gaussian_filter(copy.deepcopy(under_line), sigma=sig_val, mode='nearest', truncate=1.0)
    over_gauss = scipy.ndimage.gaussian_filter(copy.deepcopy(over_line), sigma=sig_val, mode='nearest', truncate=1.0)
    avg_smooth = (median_gauss + under_gauss + over_gauss)/3

    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html
    f = interpolate.interp1d(ref_times[anchors[0]:-anchors[1]], avg_smooth, bounds_error=False, fill_value="extrapolate", assume_sorted=True)
    f_of_all = f(all_times)

    return f_of_all


def driftcorr_fromlast(
    fd_x: list,
    fd_y: list,
    f_times: list,
    all_x: list,
    all_y: list,
    all_times: list,
    previous_image: bool=False,
) -> tuple:
    i = 0
    j = 0
    all_x_aligned = []
    all_y_aligned = []

    '''
    THINGS task
    gap = 1: re-align from previous isi, current image or current image + isi median position
    gap = 2: re-align from previous image or previous image + isi median position
    OTHER tasks: gap = 1
    '''
    gap = 2 if previous_image else 1

    for i in range(len(all_times)):
        while j < len(f_times)-gap and all_times[i] > f_times[j+gap]:
            j += 1
        all_x_aligned.append(all_x[i] - fd_x[j])
        all_y_aligned.append(all_y[i] - fd_y[j])

    return all_x_aligned, all_y_aligned


def format_gaze(
    x_vals: list,
    y_vals: list,
    time_vals: list,
    gaze_list: list
) -> pd.DataFrame:
    """
    Export drift-corrected gaze, realigned timestamps,
    and all other metrics (pupils, etc) to bids-compliant .tsv file.

    guidelines: https://bids-specification--1128.org.readthedocs.build/en/1128/modality-specific-files/eye-tracking.html#sidecar-json-document-_eyetrackjson
    """
    col_names = [
        'eye_timestamp',
        'eye1_x_coordinate', 'eye1_y_coordinate',
        'eye1_confidence',
        'eye1_x_coordinate_driftCorr', 'eye1_y_coordinate_driftCorr',
        'eye1_pupil_x_coordinate', 'eye1_pupil_y_coordinate',
        'eye1_pupil_diameter',
        'eye1_pupil_ellipse_axes',
        'eye1_pupil_ellipse_angle',
        'eye1_pupil_ellipse_center'
    ]

    final_gaze_list = []

    assert len(gaze_list) == len(x_vals)
    for i in range(len(gaze_list)):
        gaze_pt = gaze_list[i]
        assert gaze_pt['reset_time'] == time_vals[i]

        gaze_pt_data = [
            gaze_pt['reset_time'], # in s
            #round(gaze_pt['reset_time']*1000, 0), # int, in ms
            gaze_pt['norm_pos'][0], gaze_pt['norm_pos'][1],
            gaze_pt['confidence'],
            x_vals[i], y_vals[i],
            gaze_pt['base_data']['norm_pos'][0], gaze_pt['base_data']['norm_pos'][1],
            gaze_pt['base_data']['diameter'],
            gaze_pt['base_data']['ellipse']['axes'],
            gaze_pt['base_data']['ellipse']['angle'],
            gaze_pt['base_data']['ellipse']['center'],
        ]

        final_gaze_list.append(gaze_pt_data)

    return pd.DataFrame(np.array(final_gaze_list, dtype=object), columns=col_names)
