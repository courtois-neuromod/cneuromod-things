import os, sys, glob
from io import TextIOWrapper

import numpy as np
from numpy import nan as NaN
import pandas as pd
from pathlib import Path

import argparse
import datetime
import tqdm


def get_log_times(log_list):
    '''
    Function takes list of log files from a session and extracts the logged
    computer time of image presentation for each trial
    '''
    log_dict = {}
    for log_file in log_list:
        log_num = os.path.basename(log_file).split('_')[2].split('.')[0]
        log_dict[log_num] = {}

        with open(log_file) as f:
            lines = f.readlines()
            count = -1
            for line in lines:
                if 'ThingsMemory: task starting at' in line:
                    count += 1
                    log_dict[log_num][count] = []
                elif 'image: ' in line:
                    split_line = line.split('\t')
                    img_time = split_line[0].split(' ')[0]
                    img_name = split_line[-1].split(':')[-1][:-1]
                    log_dict[log_num][count].append((img_time, img_name))

    return log_dict


def get_sess_times(
    time_path: str,
    sub_num: str,
) -> dict:
    """
    Create a dictionary of session dates from subject's text file with saved
    scan dates.
    Note: subjects' scan dates are identifiers.
    For confidentiality, they cannot be shared in a public repository.
    """
    months = {
              'Jan': 1,
              'Feb': 2,
              'Mar': 3,
              'Apr': 4,
              'May': 5,
              'Jun': 6,
              'Jul': 7,
              'Aug': 8,
              'Sep': 9,
              'Oct': 10,
              'Nov': 11,
              'Dec': 12,
    }

    session_times = {}
    scantime_path = f'{time_path}/sub-{sub_num}_scandates.txt'
    with open(scantime_path) as f:
        lines = f.readlines()
        for line in lines:
            chunks = line.split(' ')
            y = chunks[-2]
            d = chunks[-4]
            m = chunks[-5] if chunks[-5] is not '' else chunks[-6]
            sub, sess = chunks[-1].split('/')[-3:-1]

            if not sess in session_times.keys():
                session_times[sess] = datetime.datetime(int(y), months[m], int(d))

    # Manual updates for fluke session for which there are no events files.
    # (I just copied events files from another subject as approximation)
    if sub_num == '03':
        session_times['ses-013b'] = datetime.datetime(2021, 7, 28)

    return session_times


def get_ses_list(
    in_path: str,
    sub_num: str,
    session_times: dict,
) -> list:
    """
    Return list of subject's sessions
    """
    # Sanity check: sessions found match those in session_times dict
    ses_list = []
    list_all_runs = sorted(
        glob.glob(os.path.join(in_path, f'sub-{sub_num}', 'ses*', '*events.tsv'))
    )
    for run_path in list_all_runs:
        ses_num = run_path.split('/')[-1].split('_')[1]
        ses_list.append(ses_num)
        assert ses_num in session_times.keys()

    return sorted(list(np.unique(ses_list)))


def get_timing(
    in_path: str,
    et_path: str,
    ses_list: list,
    sub_num: str,
    session_times: dict,
    out_path: str,
) -> tuple:
    """
    Concatenate all the subject's *events.tsv files (even the excluded
    & repeated sessions) in chronological order into a single large DataFrame.

    Processing session by session, access within-session trial times
    from .log files (concatenated).
    Add three identifier columns: subject, session, flag to exclude bad sessions
    Add two timing columns: session date, and within-session trial timing (from log files)
    """
    # DataFrame of raw datapoints per trial concatenated across sessions and runs
    df_trials = None
    cols_to_keep = []
    run_error_report = open(f'{out_path}/sub-{sub_num}_error_run_report.txt', 'w+')

    # process files per session
    for ses_num in tqdm.tqdm(ses_list, desc='concatenating event files per session'):
        ses_time = session_times[ses_num]
        flag_to_exclude = 'b' in ses_num
        run_list = sorted(
            glob.glob(f"{in_path}/sub-{sub_num}/{ses_num}/*events.tsv")
        )

        # Extract times from session's log files, returns dictionary
        log_list = sorted(
            glob.glob(f"{in_path}/sub-{sub_num}/{ses_num}/*log")
        )
        if not flag_to_exclude:
            log_dict = get_log_times(log_list)
            count = 0
            seen_fids = []

        for run_event in run_list:
            run_df = pd.read_csv(run_event, sep = '\t')
            if df_trials is None:
                cols_to_keep = list(run_df.columns)

            # sanity check: is this the correct file?
            ids = os.path.basename(run_event).split('_')
            sub = ids[0]
            sess = ids[1]
            run_num = ids[-2].split('-')[-1]
            assert f'sub-{sub_num}' == sub
            assert sess == ses_num
            assert int(run_num) == run_df['run'][0]

            # insert additional columns
            # subject, session, flag to exclude, time (date), time (computer time for session's trial)
            run_df.insert(loc=0, column='subject', value=sub_num, allow_duplicates=True)
            run_df.insert(loc=1, column='session', value=ses_num, allow_duplicates=True)
            run_df.insert(loc=2, column='exclude_session', value=flag_to_exclude, allow_duplicates=True)
            run_df.insert(loc=3, column='date_time', value=ses_time, allow_duplicates=True)

            if flag_to_exclude:
                # within-session timing not important for discarded sessions, use placeholder
                run_df.insert(loc=18, column='session_trial_time', value=NaN, allow_duplicates=True)
            else:
                file_id = ids[2]
                if file_id in seen_fids:
                    count += 1
                else:
                    seen_fids.append(file_id)
                    count = 0

                try:
                    """
                    Extract image timestamps from psychopy log files
                    """
                    img_info = np.array(log_dict[file_id][count])
                    img_time = img_info[:, 0]
                    img_name = img_info[:, 1]

                    assert np.sum(img_name == run_df['image_path'].to_numpy()) == img_name.shape[0]
                    assert np.array_equal(img_name, run_df['image_path'].to_numpy())
                    run_df.insert(loc=18, column='session_trial_time', value=img_time, allow_duplicates=True)
                except:
                    """
                    If no task log file, derive image timestamps from raw eyetracking
                    timestamps
                    """
                    print(sub_num, ses_num, run_num, file_id, count)
                    run_error_report.write(f'empty log file for sub-{sub_num}, {ses_num}, run {run_num[-1]}\n')
                    et_file = f'{et_path}/sub-{sub_num}/{ses_num}/sub-{sub_num}_{ses_num}_{file_id}.pupil/task-thingsmemory_run-{run_num[-1]}/000/eye0_timestamps.npy'
                    if os.path.exists(et_file):
                        r_time = np.load(et_file)[0]
                        img_time = (run_df['onset'].to_numpy() + r_time).tolist()
                        run_df.insert(loc=18, column='session_trial_time', value=img_time, allow_duplicates=True)
                    else:
                        print('no eyetracking timestamps')
                        run_df.insert(loc=18, column='session_trial_time', value=NaN, allow_duplicates=True)

                ## Note: sub-01 ses-14 has an extra 18 trials shown ("run-0");
                # I manually removed the other trials (19+) listed in the events file that were not shown
                # verified: the number of trials will match those in the log file (18 trials listed)
            if df_trials is None:
                df_trials = run_df
            else:
                df_trials = pd.concat((df_trials, run_df), ignore_index=True)

    return df_trials, run_error_report, cols_to_keep


def fix_entries(
    df_trials: pd.DataFrame,
    out_path: str,
    sub_num: str,
) -> pd.DataFrame:
    """
    Validate the DataFrame's following columns,
    whose value depends on previous / subsequent trials
    - condition: seen/unseen
    - subcondition: seen-within-between, etc
    - repetition : 1-3 (normally)
    - error: True/False (determined based on response_txt and condition)

    Flag trials that require updating in a text file.
    Add three columns:
    - time since previous rep (in days and in seconds),
    - number of stimuli shown since previous rep
    At the end, delete session date column (identifier/confidential)
    """
    shown_images = {}
    # text file that documents trials with erroneous labels
    error_report = open(f'{out_path}/sub-{sub_num}_error_trial_report.txt', 'w+')

    df_trials.insert(loc=2, column='atypical', value=False, allow_duplicates=True)
    df_trials.insert(loc=3, column='atypical_log', value='', allow_duplicates=True)
    df_trials.insert(loc=22, column='delay_days', value=NaN, allow_duplicates=True)
    df_trials.insert(loc=23, column='delay_seconds', value=NaN, allow_duplicates=True)
    df_trials.insert(loc=24, column='trials_since_lastrep', value=NaN, allow_duplicates=True)

    # slow, tedious, clunky for loop bruteforcing its way through the DataFrame
    for i in tqdm.tqdm(range(df_trials.shape[0]), desc='validating all trial entries'):
        img_name = os.path.basename(df_trials['image_path'][i])
        ses = df_trials['session'][i]
        run = df_trials['run'][i]
        trial_num = df_trials['order'][i]

        # the image is UNSEEN
        if not img_name in shown_images.keys():
            # add entry to dict of seen images
            shown_images[img_name] = {
                                      'idx': i,
                                      'rep_num': 1,
                                      'previous_reps': '' #'-between' '-within'
            }
            # validate condition
            if not df_trials['condition'][i] == 'unseen':
                error_report.write(f'condition changed from seen to unseen for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                df_trials['condition'][i] = 'unseen'
                df_trials['atypical'][i] = True
                df_trials['atypical_log'][i] += '_condition:unseen'
            # validate subcondition
            df_ses = df_trials[df_trials['session']==ses]
            df_img = df_ses[df_ses['image_path']==df_trials['image_path'][i]]
            subcon_val = 'unseen-within' if df_img.shape[0] > 1 else 'unseen-between'
            if not df_trials['subcondition'][i] == subcon_val:
                error_report.write(f'subcondition changed to {subcon_val} for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                df_trials['subcondition'][i] = subcon_val
                df_trials['atypical'][i] = True
                df_trials['atypical_log'][i] += f'_subcondition:{subcon_val}'
            # validate repetition
            if not df_trials['repetition'][i] == 1:
                error_report.write(f'repetition set to 1 for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                df_trials['repetition'][i] = 1
                df_trials['atypical'][i] = True
                df_trials['atypical_log'][i] += '_repetition:1'
            # validate error
            error_val = df_trials['error'][i]
            resp_given = df_trials['response_txt'][i]
            if resp_given in ['unseen', 'seen']: #TODO: check, is it NaN?
                if resp_given == 'unseen' and error_val == True:
                    error_report.write(f'error set to False for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                    df_trials['error'][i] = False
                    df_trials['atypical'][i] = True
                    df_trials['atypical_log'][i] += '_error:False'
                elif resp_given == 'seen' and error_val == False:
                    error_report.write(f'error set to True for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                    df_trials['error'][i] = True
                    df_trials['atypical'][i] = True
                    df_trials['atypical_log'][i] += '_error:True'

        # the image is SEEN
        elif img_name in shown_images.keys():
            # fill up delay columns (days and seconds) and trials_since_lastrep column
            # update entry to dict of seen images
            old_i = shown_images[img_name]['idx']
            df_trials['trials_since_lastrep'][i] = i - old_i
            if df_trials['session'][old_i] == ses:
                df_trials['delay_days'][i] = 0
                df_trials['delay_seconds'][i] = float(df_trials['session_trial_time'][i]) - float(df_trials['session_trial_time'][old_i])
                shown_images[img_name]['previous_reps'] += '-within'
            else:
                df_trials['delay_days'][i] = (df_trials['date_time'][i] - df_trials['date_time'][old_i]).days
                df_trials['delay_seconds'][i] = 0.0
                shown_images[img_name]['previous_reps'] += '-between'

            shown_images[img_name]['idx'] = i
            shown_images[img_name]['rep_num'] += 1

            rep_num = shown_images[img_name]['rep_num']
            previous_reps = shown_images[img_name]['previous_reps']

            # validate condition
            if not df_trials['condition'][i] == 'seen':
                error_report.write(f'condition changed from unseen to seen for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                df_trials['condition'][i] = 'seen'
                df_trials['atypical'][i] = True
                df_trials['atypical_log'][i] += '_condition:seen'
            # validate subcondition
            if not df_trials['subcondition'][i] == f'seen{previous_reps}':
                error_report.write(f'subcondition changed to seen{previous_reps} for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                df_trials['subcondition'][i] = f'seen{previous_reps}'
                df_trials['atypical'][i] = True
                df_trials['atypical_log'][i] += f'_subcondition:seen{previous_reps}'
            # validate repetition
            if not df_trials['repetition'][i] == rep_num:
                error_report.write(f'repetition set to {str(rep_num)} for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                df_trials['repetition'][i] = rep_num
                df_trials['atypical'][i] = True
                df_trials['atypical_log'][i] += f'_repetition:{str(rep_num)}'
            # validate error
            error_val = df_trials['error'][i]
            resp_given = df_trials['response_txt'][i]
            if resp_given in ['unseen', 'seen']: #TODO: check, is it NaN?
                if resp_given == 'unseen' and error_val==False:
                    error_report.write(f'error set to True for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                    df_trials['error'][i] = True
                    df_trials['atypical'][i] = True
                    df_trials['atypical_log'][i] += '_error:True'
                elif resp_given == 'seen' and error_val==True:
                    error_report.write(f'error set to False for sub-{sub_num}, {ses}, run {str(int(run))}, trial {str(int(trial_num))}\n')
                    df_trials['error'][i] = False
                    df_trials['atypical'][i] = True
                    df_trials['atypical_log'][i] += '_error:False'

    # scanning dates should not be included in saved files as they are identifiers; comment out line below to debug
    df_trials.drop(columns=['date_time'])
    df_trials.to_csv(f'{out_path}/sub-{sub_num}_things_concattrials.tsv', sep='\t', header=True, index=False)
    error_report.close()

    return df_trials


def export_events_files(
    df_trials: pd.DataFrame,
    cols_to_keep: list,
    ses_list: list,
    out_path: str,
    sub_num: str,
    run_error_report: TextIOWrapper,
) -> None:
    """
    Export newly updated/corrected *events.tsv files with
    additional timing columns, for valid sessions only
    """
    id_cols = ['subject', 'session']
    added_cols = ['session_trial_time', 'atypical', 'atypical_log', 'exclude_session',
                  'delay_days', 'delay_seconds', 'trials_since_lastrep']
    cols_to_keep = id_cols + cols_to_keep + added_cols

    for ses_num in tqdm.tqdm(ses_list, desc='exporting updated event files'):
        if 'b' not in ses_num:
            df_ses = df_trials[df_trials['session']==ses_num]
            run_list = sorted(list(np.unique(df_ses['run'])))

            for run in run_list:
                # exclude run 0, run 40, etc
                if int(run) in [1, 2, 3, 4, 5, 6]:
                    out_dir = os.path.join(out_path, f'sub-{sub_num}', ses_num)
                    Path(out_dir).mkdir(parents=True, exist_ok=True)

                    out_name = os.path.join(
                        out_dir,
                        f'sub-{sub_num}_{ses_num}_task-things_run-{str(int(run))}_events.tsv',
                    )
                    df_run = df_ses[df_ses['run']==run]

                    if True in list(np.unique(df_run['atypical'])):
                        run_error_report.write(
                            f'atypical entries detected in sub-{sub_num}, '
                            f'{ses_num}, run {str(int(run))}\n'
                        )

                    df_run = df_run[cols_to_keep]
                    df_run.to_csv(out_name, sep='\t', header=True, index=False)

    run_error_report.close()


def validate_behav_data(
    in_path: str,
    time_path: str,
    et_path: str,
    sub_num: str,
    out_path: str,
) -> None:
    '''
    Input:
        in_path:  path to bids directory that contains *events.tsv files
        time_path:  path to directory with temp scan dates text files
        et_path:  path to raw directory with psychopy log files
            (with trial timestamps) and raw eye-tracking data
        sub_num :  two-digit subject number
        out_path:  path to output directory
    Output:
        None : exports updated *events.tsv files in specified output directory
    '''

    '''
    STEP 1: Create a dictionary of session dates
    '''
    session_times = get_sess_times(time_path, sub_num)


    '''
    STEP 2: Concatenate subject's *events.files into one DataFrame.
    Insert identifier and timing columns.
    '''
    ses_list = get_ses_list(in_path, sub_num, session_times)

    df_trials, run_error_report, cols_to_keep = get_timing(
        in_path,
        et_path,
        ses_list,
        sub_num,
        session_times,
        out_path,
    )


    '''
    STEP 3: validate condition, subcontition and accuracy.
    Compute delays between repetitions.
    Delete session date column (identifier/confidential)
    '''
    df_trials = fix_entries(
        df_trials,
        out_path,
        sub_num,
    )


    '''
    STEP 4: Export updated/corrected *events.tsv files
    '''
    export_events_files(
        df_trials, cols_to_keep, ses_list, out_path, sub_num, run_error_report,
    )


def main():
    """
    This script is rather rough and relies on brute force to validate each trial's data.

    It validates and corrects the conditions, sub-conditions
    and responses included in the raw *events.tsv files
    outputed for the THINGS dataset, based on the order in which sessions were
    administered and stimuli were shown to the participants.

    Specifically, the script
    - adds timing information to *events.tsv file: for repeated
    images (2nd or 3rd showing), it computes the delay (in days or seconds)
    since the last presentation, and the number of stimuli shown since the
    previous repetition (to estimate stimulus interference with recognition).
    - corrects trial labels (e.g., seen/unseen) in the few cases
    when sessions were not ran in the pre-planned order.
    - corrects accuracy accordingly (e.g., if a participant answered "seen" to
    an image accidentally shown in a previous session when it was supposed to
    be novel, the "error" value is changed from True to False to reflect the
    fact that the image was correctly recognized).

    ***NOTE: a few cleaned up *events.tsv files were edited manually after
    being outputed by this script***
    The 'exclude_session' column flags sessions that should be excluded from
    analyses of memory recognition (due to deviations from pre-planned patterns
    of repetition).
    Those sessions are fine to assess concept representation and perception.
    The 'exclude_session' column was changed MANUALLY from FALSE to TRUE
    for all rows in the following files:
    - sub-03: sessions 24, 25 and 26 (all 6 runs)
    - sub-06: sessions 19, 20, 21, 22, 23, 24, 25 and 26 (all 6 runs)

    A few more sessions include "atypical trials", that is, trials whose
    pattern of repetition deviates from the pre-planned protocole.
    e.g. a run was interrupted mid-scan and then redone, or runs were
    ran out of order within a session.
    Those trials are flagged with the 'atypical' (boolean flag) and
    'atypical_log' (text) columns, and they (or the runs / sessions that
    contain them) can be excluded at the experimenter's discretion.

    Additional notes about the QCing of the CNeuroMod-THINGS dataset are included
    in qc_notes.md.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data_dir',
        type=str,
        required=True,
        help='path to bids directory with *events.tsv files',
    )
    parser.add_argument(
        '--time_dir',
        type=str,
        default='/home/mariestl/cneuromod/THINGS',
        help='path to directory with temp scan dates text files',
    )
    parser.add_argument(
        '--log_dir',
        type=str,
        default='/unf/eyetracker/neuromod/things/sourcedata',
        help='path to directory with raw psychopy log files (trials timestamps)',
    )
    parser.add_argument(
        '--out_dir',
        type=str,
        required=True,
        help='path to output directory',
    )
    parser.add_argument(
        '--sub',
        type=str,
        required=True,
        help='two-digit subject number',
    )
    args = parser.parse_args()

    out_path = args.out_dir
    Path(out_path).mkdir(parents=True, exist_ok=True)

    validate_behav_data(
        args.data_dir, args.time_dir, args.log_dir, args.sub, out_path,
    )


if __name__ == '__main__':
    sys.exit(main())
