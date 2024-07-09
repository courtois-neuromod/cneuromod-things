import os, glob, sys, json
from pathlib import Path

import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt

import argparse

from utils import get_list, add_file_paths, driftcorr_fromlast, get_onset_time
from utils import reset_gaze_time, format_gaze


def get_arguments():
    parser = argparse.ArgumentParser(
        description='clean up, label, QC and bids-formats the THINGS'
        'eye-tracking dataset'
    )
    parser.add_argument(
        '--in_path',
        type=str,
        required=True,
        help='absolute path to directory that contains all data (sourcedata)',
    )
    parser.add_argument(
        '--is_final',
        action='store_true',
        default=False,
        help='if true, export drift-corrected gaze into bids format',
    )
    parser.add_argument(
        '--out_path',
        type=str,
        required=True,
        help='absolute path to analysis directory',
    )

    return parser.parse_args()


def get_single_distance(x1, y1, x2, y2, is_distance=False):
    """
    Function calculates the distance in degrees of visual angle between
    a pair of points.

    If is_distance is True, coordinates are relative distances from the center,
    otherwise they are normalized coordinates as outputed by Pupil Labs
    (as proportion of viewing screen dim = (1024, 1280)).
    """
    norm_center = (0, 0) if is_distance else (0.5, 0.5)

    pre_x = (x1 - norm_center[0])*1280
    pre_y = (y1 - norm_center[1])*1024
    post_x = (x2 - norm_center[0])*1280
    post_y = (y2 - norm_center[1])*1024

    dist_in_pix = 4164 # estimated distance to viewing screen in pixels

    vectors = np.array([[pre_x, pre_y, dist_in_pix], [post_x, post_y, dist_in_pix]])
    distance = np.rad2deg(np.arccos(1.0 - pdist(vectors, metric='cosine')))[0]

    return distance


def get_distances_from_center(x, y, is_distance=False):
    """
    Function calculates the distance to the center of the screen (central
    fixation) in degrees of visual angle for a series of points.

    if is_distance == True:
        x and y are relative distances from the center, else they are
        normalized coordinates as outputed by Pupil Labs (as proportion of
        viewing screen dim = (1024, 1280))
    """
    assert len(x) == len(y)

    dist_in_pix = 4164 # estimated distance to viewing screen in pixels
    m_vecpos = np.array([0., 0., dist_in_pix])

    all_pos = np.stack((x, y), axis=1)
    if is_distance:
        gaze = (all_pos - 0.0)*(1280, 1024)
    else:
        gaze = (all_pos - 0.5)*(1280, 1024)
    gaze_vecpos = np.concatenate(
        (gaze, np.repeat(dist_in_pix, len(gaze)).reshape((-1, 1))),
        axis=1,
    )

    all_distances = []
    for gz_vec in gaze_vecpos:
        vectors = np.stack((m_vecpos, gz_vec), axis=0)
        distance = np.rad2deg(
            np.arccos(1.0 - pdist(vectors, metric='cosine'))
        )[0]
        all_distances.append(distance)

    return all_distances


def get_dist2prev(
    metrics_dict, trial_num, num_back, conf_thresh, use_trial=False,
):
    """
    Function calculates the distance in degrees of visual angle between
    a pair of points:
        - a trial's median gaze position
        - the median gaze position of the preceeding trial (use_trial=True)
        or fixation period (use_trial=False)
    """
    fix_name = 'trial' if use_trial else 'fix'

    x1 = metrics_dict[trial_num-num_back][f'{fix_name}_median_x_{conf_thresh}']
    y1 = metrics_dict[trial_num-num_back][f'{fix_name}_median_y_{conf_thresh}']
    x2 = metrics_dict[trial_num][f'trial_median_x_{conf_thresh}']
    y2 = metrics_dict[trial_num][f'trial_median_y_{conf_thresh}']

    return get_single_distance(x1, y1, x2, y2, is_distance=False)


def get_fixation_gaze_things(
    df_ev, clean_dist_x, clean_dist_y, clean_times, fix_period="image+isi",
):
    """
    Identify gaze points that correspond to reference periods of fixation,
    to use as a reference to perform drift correction.

    For each period of fixation, export the median gaze position,
    its time stamp, and fixation QC metrics (for plotting)
    """
    fix_dist_x = []
    fix_dist_y = []
    fix_times = []

    fix_metrics = {
        'gz_count': [],
        'gz_idx': [],
        'gz_dist_2_prev': [],
    }

    j = 0

    for i in range(df_ev.shape[0]):

        if fix_period == 'image':
            """
            Use image-viewing portion of a trial as reference for drift corr
            """
            fixation_onset = df_ev['onset'][i]
            fixation_offset = fixation_onset + df_ev['duration'][i]
            onset_buffer = 0.0

        elif fix_period == 'isi':
            """
            Use ISI periods as reference for drift corr
            """
            fixation_onset = df_ev['onset'][i] + df_ev['duration'][i]
            fixation_offset = fixation_onset + 1.49
            onset_buffer = 0.6

        elif fix_period == 'image+isi':
            """
            Use image-viewing + ISI as reference for drift corr
            Default for THINGS dataset.
            """
            fixation_onset = df_ev['onset'][i]
            fixation_offset = fixation_onset + df_ev['duration'][i] + 1.49
            onset_buffer = 0.0


        # append gaze from trial fixation period
        trial_fd_x = []
        trial_fd_y = []
        trial_ftimes = []
        while j < len(clean_times) and clean_times[j] < fixation_offset:
            if clean_times[j] > (fixation_onset + onset_buffer) and clean_times[j] < (fixation_offset - 0.1):
                trial_fd_x.append(clean_dist_x[j])
                trial_fd_y.append(clean_dist_y[j])
                trial_ftimes.append(clean_times[j])

            j += 1

        """
        Only includes periods of fixation that have >20 gaze points derived
        from pupils detected above confidence threshold (used during gaze clean)
        """
        if len(trial_fd_x) > 20:
            med_x = np.median(trial_fd_x)
            med_y = np.median(trial_fd_y)

            """
            Compute distance in degrees of visual angle between two
            consecutive fixation points, as QC metric.

            If this is the first fixation period, assume the previous point is
            centered at (0, 0), meaning no drift.
            """
            prev_x, prev_y = (0.0, 0.0) if len(fix_dist_x) < 1 else (fix_dist_x[-1], fix_dist_y[-1])
            fix_metrics['gz_dist_2_prev'].append(
                get_single_distance(med_x, med_y, prev_x, prev_y, is_distance=True)
            )

            # use its first gaze's timestamp to mark fixation period onset
            fix_dist_x.append(med_x)
            fix_dist_y.append(med_y)
            fix_times.append(trial_ftimes[0])

            # QC metric: number of above-threshold gaze points sampled per fix period
            # reflects accuracy of median position estimation
            fix_metrics['gz_count'].append(len(trial_fd_x))
            fix_metrics['gz_idx'].append(i)

    return fix_dist_x, fix_dist_y, fix_times, fix_metrics


def add_metrics_2events(df_ev,
                        all_times,
                        all_conf,
                        all_x,
                        all_y,
                        all_x_aligned,
                        all_y_aligned,
                        conf_thresh=0.9,
                        strategy_name='previous_image+isi',
                        ):

    """
    Calculate distance to central fixation for ALL drift corrected and
    uncorrected gaze points (no filtering based on confidence)
    """
    all_distances = get_distances_from_center(all_x_aligned, all_y_aligned)
    all_distances_raw = get_distances_from_center(all_x, all_y)

    metrics_per_trials = {}
    all_idx = 0

    first_fix_trialnum = None

    """
    Compute trial-wise fixation compliance metrics one trial at at time
    """
    for i in range(df_ev.shape[0]):
        trial_number = df_ev['TrialNumber'][i]

        trial_onset = df_ev['onset'][i]
        trial_offset = trial_onset + df_ev['duration'][i]

        # skip first 0.6s of ISI during which subjects tend to blink
        isi_buffer = 0.0 if 'image+isi' in strategy_name else 0.6
        isi_onset = trial_offset + isi_buffer
        isi_offset = trial_offset + 1.49

        """
        Gather trial's gaze, conf and distance; assign metrics to trial or isi
            - trial = image-viewing period
            - isi = subsequent inter-stimulus interval period
        """
        trial_confs = []
        trial_x = []
        trial_y = []
        trial_distance = []
        isi_confs = []
        isi_x = []
        isi_y = []
        isi_distances = []

        while all_idx < len(all_times) and all_times[all_idx] < isi_offset:
            if all_times[all_idx] > trial_onset:
                if all_times[all_idx] < trial_offset:
                    trial_confs.append(all_conf[all_idx])
                    trial_x.append(all_x[all_idx])
                    trial_y.append(all_y[all_idx])
                    trial_distance.append(all_distances[all_idx])

                elif all_times[all_idx] > isi_onset:
                    isi_confs.append(all_conf[all_idx])
                    isi_x.append(all_x[all_idx])
                    isi_y.append(all_y[all_idx])
                    isi_distances.append(all_distances[all_idx])

            all_idx += 1

        """
        Define reference fixation period used for drift correction,
        depending on strategy (image-viewing period, ISI period, or
        both combined).
        For THINGS, default is image+ISI
        """
        if 'image+isi' in strategy_name:
            fix_confs = trial_confs + isi_confs
            fix_x = trial_x + isi_x
            fix_y = trial_y + isi_y
            fix_distances = trial_distance + isi_distances
        elif 'image' in strategy_name:
            fix_confs = trial_confs
            fix_x = trial_x
            fix_y = trial_y
            fix_distances = trial_distance
        else:
            fix_confs = isi_confs
            fix_x = isi_x
            fix_y = isi_y
            fix_distances = isi_distances

        """
        Process main trial gaze:
            - Filter out gaze estimated from pupils detected w low confidence
            - calculate median
            - calculate distance to trial's own median for all gaze (estimate
            within-trial variability in gaze position)
        """
        t_conf_filter = np.array(trial_confs) > conf_thresh
        t_sum = np.sum(t_conf_filter)
        if t_sum:
            trial_x_arr = np.array(trial_x)[t_conf_filter]
            trial_y_arr = np.array(trial_y)[t_conf_filter]
            trial_dist_arr = np.array(trial_distance)[t_conf_filter]
            t_med_x = np.median(trial_x_arr)
            t_med_y = np.median(trial_y_arr)
            t_dist_to_med = np.array(get_distances_from_center(
                trial_x_arr-t_med_x, trial_y_arr-t_med_y, is_distance=True
            ))

        """
        Process fixation period trial gaze:
            - Filter out gaze estimated from pupils detected w low confidence
            - calculate median
            - calculate distance to fixation's own median for all gaze (estimate
            within-fixation variability in gaze position)
        """
        f_conf_filter = np.array(fix_confs) > conf_thresh
        f_sum = np.sum(f_conf_filter)
        if f_sum:
            if first_fix_trialnum is None:
                first_fix_trialnum = trial_number
            fix_x_arr = np.array(fix_x)[f_conf_filter]
            fix_y_arr = np.array(fix_y)[f_conf_filter]
            fix_dist_arr = np.array(fix_distances)[f_conf_filter]
            f_med_x = np.median(fix_x_arr)
            f_med_y = np.median(fix_y_arr)
            f_dist_to_med = np.array(get_distances_from_center(
                fix_x_arr-f_med_x, fix_y_arr-f_med_y, is_distance=True
            ))

        """
        Build a dictionary of metrics for each trial.
        Metrics include:
            - gaze counts
            - proportion of gaze above confidence thresholds (trial and fixation)
            - trial fixation compliance ratio: the proportion of trial gaze within a
            certain distance (in deg of visual angle) from the fixation point.
            Low scores could reflect a shift in head position, or high variability
            in gaze position (low fixation compliance).
            - trial dist2med ratio: the proportion of trial gaze within a certain
            distance (in deg) from the trial's median position (reflects variability)
            - fix dist2med ratio: the proportion of fixation gaze within a certain
            distance (in deg) from the fixation period's median position (reflects variability).
            Fixation positions estimated from periods with high variability may
            lead to poor drift correction.
        """
        metrics_per_trials[trial_number] = {
            'trial_gaze_count': len(trial_confs),
            'trial_gaze_conf_90': np.sum(np.array(trial_confs) > 0.9)/len(trial_confs) if len(trial_confs) > 0 else np.nan,
            'trial_gaze_conf_75': np.sum(np.array(trial_confs) > 0.75)/len(trial_confs) if len(trial_confs) > 0 else np.nan,
            'fix_gaze_count': len(fix_confs),
            'fix_gaze_conf_90': np.sum(np.array(fix_confs) > 0.9)/len(fix_confs) if len(fix_confs) > 0 else np.nan,
            'fix_gaze_conf_75': np.sum(np.array(fix_confs) > 0.75)/len(fix_confs) if len(fix_confs) > 0 else np.nan,

            f'trial_median_x_{conf_thresh}': t_med_x if t_sum else np.nan,
            f'trial_median_y_{conf_thresh}': t_med_y if t_sum else np.nan,
            'trial_fix_compliance_ratio_deg0.5': np.sum(trial_dist_arr < 0.5)/t_sum if t_sum else np.nan,
            'trial_fix_compliance_ratio_deg1': np.sum(trial_dist_arr < 1.0)/t_sum if t_sum else np.nan,
            'trial_fix_compliance_ratio_deg2': np.sum(trial_dist_arr < 2.0)/t_sum if t_sum else np.nan,
            'trial_fix_compliance_ratio_deg3': np.sum(trial_dist_arr < 3.0)/t_sum if t_sum else np.nan,

            'trial_dist2med_ratio_deg0.5': np.sum(t_dist_to_med < 0.5)/t_sum if t_sum else np.nan,
            'trial_dist2med_ratio_deg1': np.sum(t_dist_to_med < 1.0)/t_sum if t_sum else np.nan,
            'trial_dist2med_ratio_deg2': np.sum(t_dist_to_med < 2.0)/t_sum if t_sum else np.nan,
            'trial_dist2med_ratio_deg3': np.sum(t_dist_to_med < 3.0)/t_sum if t_sum else np.nan,

            f'fix_median_x_{conf_thresh}': f_med_x if f_sum else np.nan,
            f'fix_median_y_{conf_thresh}': f_med_y if f_sum else np.nan,
            'fix_dist2med_ratio_deg0.5': np.sum(f_dist_to_med < 0.5)/f_sum if f_sum else np.nan,
            'fix_dist2med_ratio_deg1': np.sum(f_dist_to_med < 1.0)/f_sum if f_sum else np.nan,
            'fix_dist2med_ratio_deg2': np.sum(f_dist_to_med < 2.0)/f_sum if f_sum else np.nan,
            'fix_dist2med_ratio_deg3': np.sum(f_dist_to_med < 3.0)/f_sum if f_sum else np.nan,
            }

    metrics_per_trials[0] = metrics_per_trials[first_fix_trialnum]

    """
    Add trial-wise fixation compliance metrics into DataFrame (to be
    exported as enhanced events.tsv file for each run).
    """

    """
    Insert the drift correction strategy name and pupil detection confidence
    threshold used to drift correct (as a reference)
    """
    df_ev['drift_correction_strategy'] = df_ev.apply(lambda row: strategy_name, axis=1)
    df_ev['confidence_threshold'] = df_ev.apply(lambda row: conf_thresh, axis=1)

    """
    Insert detected gaze counts for the trial's fixation and image-viewing
    periods
    """
    if 'image+isi' in strategy_name:
        fix_dur = 1.49 + 2.98
    elif 'image' in strategy_name:
        fix_dur = 2.98
    else:
        fix_dur = 1.49 - isi_buffer
    num_back = 0 if 'current' in strategy_name else 1

    df_ev['fix_gaze_count_ratio'] = df_ev.apply(lambda row: (metrics_per_trials[row['TrialNumber']-num_back]['fix_gaze_count'])/(250*fix_dur), axis=1)
    df_ev['trial_gaze_count_ratio'] = df_ev.apply(lambda row: (metrics_per_trials[row['TrialNumber']]['trial_gaze_count'])/(250*2.98), axis=1)

    """
    Insert gaze confidence ratios for the image-viewing and fixation period.

    This ratio is the proportion of gaze detected above a given threshold
    (0.9 or 0.75), out of all collected gaze
    """
    df_ev['fix_gaze_confidence_ratio_0.9'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']-num_back]['fix_gaze_conf_90'], axis=1)
    df_ev['fix_gaze_confidence_ratio_0.75'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']-num_back]['fix_gaze_conf_75'], axis=1)
    df_ev['trial_gaze_confidence_ratio_0.9'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_gaze_conf_90'], axis=1)
    df_ev['trial_gaze_confidence_ratio_0.75'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_gaze_conf_75'], axis=1)

    """
    Insert distance (in deg of visual angle) between the median gaze position
    for the trial's image-viewing period, and:
        - the previous fixation period's median gaze (median_dist_to_fixation)
        - the previous image-viewing period's median gaze (median_dist_to_previous_trial)
    Large distances between median positions can indicate a shift in head position
    or excessive head motion.
    """
    df_ev['median_dist_to_fixation_in_deg'] = df_ev.apply(lambda row: get_dist2prev(metrics_per_trials, row['TrialNumber'], num_back, conf_thresh), axis=1)
    df_ev['median_dist_to_previous_trial_in_deg'] = df_ev.apply(lambda row: get_dist2prev(metrics_per_trials, row['TrialNumber'], 1, conf_thresh, use_trial=True), axis=1)

    """
    Insert fixation compliance ratios: ratios indicate the proportion of
    trial gaze within a certain distance (0.5, 1.0, 2.0 or 3.0 degrees of
    visual angle) from the fixation point.

    Low scores could reflect a shift in head position, and/or high variability
    in gaze position during the trial (low fixation compliance).
    """
    df_ev['trial_fixation_compliance_ratio_0.5'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_fix_compliance_ratio_deg0.5'], axis=1)
    df_ev['trial_fixation_compliance_ratio_1.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_fix_compliance_ratio_deg1'], axis=1)
    df_ev['trial_fixation_compliance_ratio_2.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_fix_compliance_ratio_deg2'], axis=1)
    df_ev['trial_fixation_compliance_ratio_3.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_fix_compliance_ratio_deg3'], axis=1)

    """
    Insert ratios of distance to median.
    - trial_dist2med_ratio: the proportion of trial gaze within a certain
    distance (0.5, 1.0, 2.0 or 3.0 degrees of visual angle) from the trial's
    own median position. Low ratios may indicate poor fixation compliance.
    - fix_dist2med_ratio: the proportion of fixation gaze within a certain
    distance (0.5, 1.0, 2.0 or 3.0 degrees of visual angle) from the fixation
    period's own median position. Fixation positions estimated from periods
    of high variability in gaze position may lead to poor drift correction.
    """
    df_ev['trial_dist2med_ratio_0.5'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_dist2med_ratio_deg0.5'], axis=1)
    df_ev['trial_dist2med_ratio_1.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_dist2med_ratio_deg1'], axis=1)
    df_ev['trial_dist2med_ratio_2.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_dist2med_ratio_deg2'], axis=1)
    df_ev['trial_dist2med_ratio_3.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['trial_dist2med_ratio_deg3'], axis=1)

    df_ev['fix_dist2med_ratio_0.5'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['fix_dist2med_ratio_deg0.5'], axis=1)
    df_ev['fix_dist2med_ratio_1.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['fix_dist2med_ratio_deg1'], axis=1)
    df_ev['fix_dist2med_ratio_2.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['fix_dist2med_ratio_deg2'], axis=1)
    df_ev['fix_dist2med_ratio_3.0'] = df_ev.apply(lambda row: metrics_per_trials[row['TrialNumber']]['fix_dist2med_ratio_deg3'], axis=1)

    return df_ev, all_distances_raw, all_distances



def make_THINGS_QC_figure(
    sub: str,
    ses: str,
    run_num: str,
    fix_metrics: dict,
    gaze_threshold: float,
    run_event: pd.DataFrame,
    clean_times: list,
    clean_dist_x: list,
    clean_dist_y: list,
    fix_times: list,
    fix_dist_x: list,
    fix_dist_y: list,
    all_conf: list,
    all_times: list,
    all_x: list,
    all_x_aligned: list,
    all_y: list,
    all_y_aligned: list,
    all_distInDeg: list,
    all_distInDeg_aligned: list,
    out_fig_path: str,
) -> None:
    """
    Export figures to assess drift correction per run
    """

    fix_metrics['gz_trial_fixCom'] = []
    fix_metrics['gz_dist2prev'] = []
    fix_metrics['fix_gz_conf'] = []

    cutoff = '0.9' if gaze_threshold == 0.9 else '0.75'

    for i in fix_metrics['gz_idx']:
        fix_metrics['gz_trial_fixCom'].append(run_event['trial_fixation_compliance_ratio_1.0'][i])
        fix_metrics['fix_gz_conf'].append(run_event[f'fix_gaze_confidence_ratio_{cutoff}'][i])
        fix_metrics['gz_dist2prev'].append(run_event['median_dist_to_previous_trial_in_deg'][i])

    vals2plot = {
        'col=fix_confidence': {
            'values': fix_metrics['fix_gz_conf'],
            'refs': ['G', 'H', 'I'],
            'cmap': 'plasma_r',
        },
        'col=dist2previous': {
            'values': fix_metrics['gz_dist2prev'],
            'refs': ['J', 'K', 'L'],
            'cmap': 'plasma',
        },
        'col=trial_fix_compliance': {
            'values': fix_metrics['gz_trial_fixCom'],
            'refs': ['M', 'N', 'O'],
            'cmap': 'plasma_r',
        },
    }

    clean_distInDeg = get_distances_from_center(clean_dist_x, clean_dist_y, is_distance=True)
    fix_distInDeg = get_distances_from_center(fix_dist_x, fix_dist_y, is_distance=True)

    color_metric = np.array(all_conf)
    s = color_metric.argsort()
    time_vals = np.array(all_times)[s]
    x_vals = np.array(all_x)[s]
    x_vals_align = np.array(all_x_aligned)[s]
    y_vals = np.array(all_y)[s]
    y_vals_align = np.array(all_y_aligned)[s]
    dist_vals = np.array(all_distInDeg)[s]
    dist_vals_align = np.array(all_distInDeg_aligned)[s]
    cm = color_metric[s]

    mosaic = """
        ABC
        DEF
        GHI
        JKL
        MNO
    """
    fs = (20, 24.0)

    fig = plt.figure(constrained_layout=True, figsize=fs)
    ax_dict = fig.subplot_mosaic(mosaic)
    run_dur = int(run_event.iloc[-1]['onset'] + 20)

    ax_dict["A"].scatter(run_event['onset'].to_numpy(), run_event[f'trial_gaze_confidence_ratio_0.9'].to_numpy(), color='xkcd:dark blue', label='> 0.9')
    ax_dict["A"].scatter(run_event['onset'].to_numpy(), run_event[f'trial_gaze_confidence_ratio_0.75'].to_numpy(), color='xkcd:light green', label='> 0.75')
    ax_dict["A"].set_ylim(-0.1, 1.1)
    ax_dict["A"].set_xlim(0, run_dur)
    ax_dict["A"].legend()
    ax_dict["A"].set_title(f'{sub} {ses} {run_num} trialwise_confidence')

    ax_dict["B"].scatter(run_event['onset'].to_numpy(), run_event['trial_fixation_compliance_ratio_0.5'].to_numpy(), color='xkcd:navy blue', label='< 0.5 deg')
    ax_dict["B"].scatter(run_event['onset'].to_numpy(), run_event['trial_fixation_compliance_ratio_1.0'].to_numpy(), color='xkcd:bright green', label='< 1.0 deg')
    ax_dict["B"].scatter(run_event['onset'].to_numpy(), run_event['trial_fixation_compliance_ratio_2.0'].to_numpy(), color='xkcd:orange', label='< 2.0 deg')
    ax_dict["B"].set_ylim(-0.1, 1.1)
    ax_dict["B"].set_xlim(-0.1, run_dur)
    ax_dict["B"].legend()
    ax_dict["B"].set_title(f'{sub} {ses} {run_num} trialwise_fixCompliance')

    ax_dict["D"].scatter(time_vals, x_vals, s=10, color='xkcd:light grey', alpha=cm)
    ax_dict["D"].scatter(time_vals, x_vals_align, c=cm, s=10, cmap='terrain_r', alpha=0.2)#'xkcd:orange', alpha=all_conf)
    ax_dict["D"].set_ylim(-1.5, 2)
    ax_dict["D"].set_xlim(0, run_dur)
    ax_dict["D"].set_title(f'{sub} {ses} {run_num} gaze_x')

    ax_dict["E"].scatter(time_vals, y_vals, color='xkcd:light grey', alpha=cm)
    ax_dict["E"].scatter(time_vals, y_vals_align, c=cm, s=10, cmap='terrain_r', alpha=0.2)#'xkcd:orange', alpha=all_conf)
    ax_dict["E"].set_ylim(-1.5, 2)
    ax_dict["E"].set_xlim(0, run_dur)
    ax_dict["E"].set_title(f'{sub} {ses} {run_num} gaze_y')

    ax_dict["F"].scatter(time_vals, dist_vals, color='xkcd:light grey', alpha=cm)
    ax_dict["F"].scatter(time_vals, dist_vals_align, c=cm, s=10, cmap='terrain_r', alpha=0.2)#'xkcd:orange', alpha=all_conf)
    ax_dict["F"].set_ylim(-0.1, 20)
    ax_dict["F"].set_xlim(0, run_dur)
    ax_dict["F"].set_title(f'{sub} {ses} {run_num} dist2center_deg')

    for key in vals2plot:
        refs = vals2plot[key]['refs']
        color_metric = vals2plot[key]['values']
        cmap = vals2plot[key]['cmap']

        ax_dict[refs[0]].scatter(clean_times, clean_dist_x, color='xkcd:light blue', s=20, alpha=0.2)
        ax_dict[refs[0]].scatter(fix_times, fix_dist_x, c=color_metric, cmap=cmap, s=20, alpha=1.0)
        ax_dict[refs[0]].set_ylim(-2, 2)
        ax_dict[refs[0]].set_xlim(0, run_dur)
        ax_dict[refs[0]].set_title(f'{sub} {ses} {run_num} fix_distance_x {key}')

        ax_dict[refs[1]].scatter(clean_times, clean_dist_y, color='xkcd:light blue', s=20, alpha=0.2)
        ax_dict[refs[1]].scatter(fix_times, fix_dist_y, c=color_metric, cmap=cmap, s=20, alpha=1.0)
        lb = np.min(fix_dist_y)-0.1 if np.min(fix_dist_y) < -2 else -2
        hb = np.max(fix_dist_y)+0.1 if np.max(fix_dist_y) > 2 else 2
        ax_dict[refs[1]].set_ylim(lb, hb)
        ax_dict[refs[1]].set_xlim(0, run_dur)
        ax_dict[refs[1]].set_title(f'{sub} {ses} {run_num} fix_distance_y {key}')

        ax_dict[refs[2]].scatter(clean_times, clean_distInDeg, color='xkcd:light blue', s=20, alpha=0.2)
        ax_dict[refs[2]].scatter(fix_times, fix_distInDeg, c=color_metric, cmap=cmap, s=20, alpha=1.0)
        ax_dict[refs[2]].set_ylim(-0.1, 15)
        ax_dict[refs[2]].set_xlim(0, run_dur)
        ax_dict[refs[2]].set_title(f'{sub} {ses} {run_num} dist2center_deg {key}')

    fig.savefig(out_fig_path)
    plt.close()


def driftCorr_ETthings(
    row,
    out_path,
    is_final=False,
) -> None:

    [sub, ses, fnum, task_type, run_num, appendix] = os.path.basename(row['events_path']).split('_')
    print(sub, ses, fnum, task_type, run_num)

    if is_final:
        """
        Exports enhanced events files with fixation compliance metrics
        """
        outpath_events = f'{out_path}/Events_files_enhanced'
        Path(outpath_events).mkdir(parents=True, exist_ok=True)
        out_file = f'{outpath_events}/{sub}_{ses}_{fnum}_{task_type}_{run_num}_events.tsv'
    else:
        """
        Exports graphs to manually QC drift correction per run
        """
        outpath_fig = os.path.join(out_path, 'DC_gaze')
        Path(outpath_fig).mkdir(parents=True, exist_ok=True)
        out_file = f'{out_path}/DC_gaze/{sub}_{ses}_{run_num}_{fnum}_{task_type}_DCplot.png'

    if not os.path.exists(out_file):
        #if True:
        try:
            """
            Load run's events.tsv file and raw gaze data (exported as numpy)
            in Step 1
            """
            run_event = pd.read_csv(row['events_path'], sep = '\t', header=0)
            run_gaze = np.load(row['gaze_path'], allow_pickle=True)['gaze2d']

            """
            Identify logged run start time (mri TTL 0) on clock that matches
            the gaze timsestamps using the info.player.json file
            """
            onset_time = get_onset_time(
                row['log_path'],
                row['run'],
                row['infoplayer_path'],
                run_gaze[10]['timestamp'],
            )

            """
            Realign gaze timestamps with run onset, and filter out
            below-threshold gaze ("clean")
            """
            gaze_threshold = row['pupilConf_thresh'] if not pd.isna(
                row['pupilConf_thresh']) else 0.9
            reset_gaze_list, all_vals, clean_vals  = reset_gaze_time(
                run_gaze, onset_time, gaze_threshold,
            )
            # normalized position (x and y), time (s) from onset and confidence for all gaze
            all_x, all_y, all_times, all_conf = all_vals
            # distance from central fixation point for all gaze above confidence threshold
            clean_dist_x, clean_dist_y, clean_times, clean_conf = clean_vals

            """
            Perform drift correction

            Strategy defines the reference period of fixation used to realign
            a trial's gaze.

            The THINGS task required ongoing central fixation. Each trial's gaze
            position is realigned (drift corrected) in relation to the median
            gaze position during the trial (image-viewing period) and ISI that
            precedes the target trial's onset.

            The only exception is the first trial's gaze, which is realigned in
            relation to the median of its own image-viewing and subsequent ISI
            period, as there is no preceding trial.
            """
            strategies = {
                'current_image': ('image', False),
                'previous_image': ('image', True),
                'previous_isi': ('isi', False),
                'current_image+isi': ('image+isi', False),
                'previous_image+isi': ('image+isi', True),
                }
            strategy_name = 'previous_image+isi'
            strategy = strategies[strategy_name]

            fix_dist_x, fix_dist_y, fix_times, fix_metrics = get_fixation_gaze_things(
                run_event,
                clean_dist_x,
                clean_dist_y,
                clean_times,
                fix_period=strategy[0],
            )
            all_x_aligned, all_y_aligned = driftcorr_fromlast(
                fix_dist_x,
                fix_dist_y,
                fix_times,
                all_x,
                all_y,
                all_times,
                previous_image=strategy[1],
            )

            """
            Add trial-wise fixation compliance metrics to run's events.tsv file
            """
            (
                run_event, all_distInDeg, all_distInDeg_aligned,
            ) = add_metrics_2events(
                run_event,
                all_times,
                all_conf,
                all_x,
                all_y,
                all_x_aligned,
                all_y_aligned,
                conf_thresh=gaze_threshold,
                strategy_name=strategy_name,
            )

            if is_final:
                """
                export final events files w metrics on eyetracking &
                fixation quality per trial
                """
                run_event.to_csv(out_file, sep='\t', header=True, index=False)

                """
                Export raw and drift-corrected gaze, realigned timestamps,
                and other metrics (pupils, confidence, etc) as bids-compliant .tsv file.
                Guidelines: https://bids-specification--1128.org.readthedocs.build/en/1128/modality-specific-files/eye-tracking.html#sidecar-json-document-_eyetrackjson
                """
                df_gaze = format_gaze(
                    all_x_aligned,
                    all_y_aligned,
                    all_times,
                    reset_gaze_list,
                )

                bids_out_path = f'{out_path}/final_bids_DriftCor/{sub}/{ses}'
                Path(bids_out_path).mkdir(parents=True, exist_ok=True)
                gfile_path = Path(
                    f'{bids_out_path}/{sub}_{ses}_{task_type}_{run_num}_'
                    'eyetrack.tsv.gz',
                )
                if os.path.exists(gfile_path):
                    # just in case session's run is done twice... note: not bids...
                    gfile_path = Path(
                        f'{bids_out_path}/{sub}_{ses}_{task_type}_{fnum}_'
                        f'{run_num}_eyetrack.tsv.gz',
                        )
                df_gaze.to_csv(
                    gfile_path,
                    sep='\t',
                    header=True,
                    index=False,
                    compression='gzip',
                )

            else:
                """
                plot QC figures (one per run) to assess drift correction
                """
                make_THINGS_QC_figure(
                    sub,
                    ses,
                    run_num,
                    fix_metrics,
                    gaze_threshold,
                    run_event,
                    clean_times,
                    clean_dist_x,
                    clean_dist_y,
                    fix_times,
                    fix_dist_x,
                    fix_dist_y,
                    all_conf,
                    all_times,
                    all_x,
                    all_x_aligned,
                    all_y,
                    all_y_aligned,
                    all_distInDeg,
                    all_distInDeg_aligned,
                    out_file,
                )

        except:
            print('could not process')


def main():
    """
    This script performs drift-correction on the THINGS eyetracking data.

    If the argument "is_final" is false, it exports:
    - charts plotting the drift corrected gaze over time to QC
    the gaze realignment

    If "is_final" is true, it exports:
    - drift-corrected gaze data in a bids-compliant format
    - enhanced *events.tsv files that included trial-wise fixation compliance
    metrics.

    Note: the *events.tsv files are based on the RAW events files, not the
    ones with corrected behavioural metrics (processed with cleanup/clean_events.py).
    To reconcile these files, you will need to run the
    things_add_etQC_2cleanEvents.py script, which imports fixation
    compliance metrics into the corrected events files (to be released with
    the final dataset).

    IMPORTANT: sub-06's ses-020 was ran under sub-01, is saved under sub-01's
    ses-020 (sep 15th is sub-06, sep 22nd is sub-01).
    Those output files (events, gaze and figures) needs to be RELABELLED
    MANUALLY to match the rest of the dataset (corrected events files, bold files).
    """
    args = get_arguments()
    # e.g., (elm): /unf/eyetracker/neuromod/triplets/sourcedata
    in_path = args.in_path
    out_path = args.out_path
    is_final = args.is_final

    # load list of valid files (those deserialized and exported as npz in step 2 that passed QC)
    clean_list = get_list(out_path, is_final)
    clean_list = add_file_paths(clean_list, in_path, out_path, None, 'things')

    # implement drift correction on each run
    clean_list.apply(lambda row: driftCorr_ETthings(row, out_path, is_final), axis=1)


if __name__ == '__main__':
    sys.exit(main())
