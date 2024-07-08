import os, glob, sys
from pathlib import Path

import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist

import argparse


def get_arguments():
    parser = argparse.ArgumentParser(
        description='concatenates drift-corrected gaze and trial-wise fixation'
        'metrics across all runs'
    )
    parser.add_argument(
        '--sub_num',
        type=str,
        required=True,
        help='two-digit subject number, e.g., "01"',
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to data directory',
    )

    return parser.parse_args()


def get_degrees(x, y):
    '''
    converts normalized coordinates x and y into degrees of visual angle, and
    calculate gaze distance from central fixation point
    '''
    assert len(x) == len(y)

    dist_in_pix = 4164 # in pixels
    m_vecpos = np.array([0., 0., dist_in_pix])

    all_pos = np.stack((x, y), axis=1)
    gaze_in_deg = (all_pos - 0.5)*(17.5, 14.0)

    gaze = (all_pos - 0.5)*(1280, 1024)
    gaze_vecpos = np.concatenate((gaze, np.repeat(dist_in_pix, len(gaze)).reshape((-1, 1))), axis=1)

    all_distances = []
    for gz_vec in gaze_vecpos:
        vectors = np.stack((m_vecpos, gz_vec), axis=0)
        distance = np.rad2deg(np.arccos(1.0 - pdist(vectors, metric='cosine')))[0]
        all_distances.append(distance)

    return gaze_in_deg[:, 0].tolist(), gaze_in_deg[:, 1].tolist(), all_distances


def main():
    '''
    TODO: list eye-tracking files
    make concat events metrics
    for each file:
        load corresponding events.tsv file
        add columns to subject's large concatenated file, w subject and episode col

        parse through event file:
        for each trial:
            sample corresponding gaze (0.1s after onset, until offset)
            downsample trial's gaze  to 25Hz (from 250hz...)
            filter above conf threshold
            calculate distance to fix center

            concat x, y and dist

    '''

    args = get_arguments()

    in_path = Path(
        f"{args.data_dir}/THINGS/fmriprep/sourcedata/things"
    )
    out_path = Path(
        f"{args.data_dir}/THINGS/behaviour/sub-{args.sub_num}/fix"
    )
    out_path.mkdir(parents=True, exist_ok=True)

    conf_thresh = 0.75 if args.sub_num == "01" else 0.9

    cols2keep = [
                    'subject',
                    'session',
                    'run',
                    'TrialNumber',
                    'image_path',
                    'image_nr',
                    'condition',
                    'subcondition',
                    'repetition',
                    'onset',
                    'duration',
                    'response',
                    'error',
                    'drift_correction_strategy',
                    'fix_gaze_count_ratio',
                    'trial_gaze_count_ratio',
                    'fix_gaze_confidence_ratio_0.9',
                    'fix_gaze_confidence_ratio_0.75',
                    'trial_gaze_confidence_ratio_0.9',
                    'trial_gaze_confidence_ratio_0.75',
                    'median_dist_to_fixation_in_deg',
                    'median_dist_to_previous_trial_in_deg',
                    'trial_fixation_compliance_ratio_0.5',
                    'trial_fixation_compliance_ratio_1.0',
                    'trial_fixation_compliance_ratio_2.0',
                    'trial_fixation_compliance_ratio_3.0',
                    'trial_dist2med_ratio_0.5',
                    'trial_dist2med_ratio_1.0',
                    'trial_dist2med_ratio_2.0',
                    'trial_dist2med_ratio_3.0',
                    'fix_dist2med_ratio_0.5',
                    'fix_dist2med_ratio_1.0',
                    'fix_dist2med_ratio_2.0',
                    'fix_dist2med_ratio_3.0',
                    ]

    df_alltrials = pd.DataFrame(columns=cols2keep) # per trial
    df_allgaze = pd.DataFrame(
        columns=['subject','session', 'run', 'trial', 'x', 'y', 'dist']
    ) # per gaze point

    et_file_list = sorted(glob.glob(
        f'{in_path}/sub-{args.sub_num}/ses-0*/func/sub-{args.sub_num}*_eyetrack.tsv.gz'
    ))
    for et_file in et_file_list:
        sub, ses, task, run, _ = os.path.basename(et_file).split('_')
        #print(sub, ses, run)

        behav_file_path = glob.glob(
            f'{in_path}/{sub}/{ses}/func/*{run}*_events.tsv'
        )
        assert len(behav_file_path) == 1
        df_b = pd.read_csv(behav_file_path[0], sep= '\t')
        df_alltrials = pd.concat((df_alltrials, df_b[cols2keep]), ignore_index=True)

        df_et = pd.read_csv(et_file, sep= '\t')

        for i in range(df_b.shape[0]):
            # skip trials  with no behav response (button press)
            trial_num = df_b.iloc[i]["TrialNumber"]
            if not np.isnan(df_b.iloc[i]["response"]):
                onset = df_b.iloc[i]["onset"] + 0.1
                offset = df_b.iloc[i]["onset"] + df_b.iloc[i]["duration"]

                # filter time stamps and downsample (one every five gaze points)
                df_trial = df_et[np.logical_and(
                    df_et["eye_timestamp"].to_numpy() > onset,
                    df_et["eye_timestamp"].to_numpy() < offset
                )][::5]
                # filter out gaze below confidence threshold
                df_trial = df_trial[df_trial["eye1_confidence"].to_numpy() > conf_thresh]

                x_norm = df_trial["eye1_x_coordinate_driftCorr"].tolist()
                y_norm = df_trial["eye1_y_coordinate_driftCorr"].tolist()

                x_deg, y_deg, dist_deg = get_degrees(x_norm, y_norm)

                df_deg = pd.DataFrame(
                    {
                        "x": x_deg,
                        "y": y_deg,
                        "dist": dist_deg,
                    }
                )
                df_deg.insert(loc=0, column="subject", value=sub, allow_duplicates=True)
                df_deg.insert(loc=1, column="session", value=ses, allow_duplicates=True)
                df_deg.insert(loc=2, column="run", value=run, allow_duplicates=True)
                df_deg.insert(loc=3, column="trial", value=trial_num, allow_duplicates=True)

                df_allgaze = pd.concat((df_allgaze, df_deg), ignore_index=True)

    df_alltrials.to_csv(
        f"{out_path}/sub-{sub_num}_task-things_desc-perTrial_fixCompliance.tsv",
        sep='\t', header=True, index=False,
    )
    df_allgaze.to_csv(
        f"{out_path}/sub-{sub_num}_task-things_desc-driftCor_gaze.tsv",
        sep='\t', header=True, index=False,
    )


if __name__ == '__main__':
    sys.exit(main())
