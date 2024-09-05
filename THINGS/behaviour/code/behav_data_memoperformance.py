import sys, glob

import argparse
from pathlib import Path

import numpy as np
from numpy import nan as NaN
import pandas as pd
from scipy.stats import norm
import tqdm


SUBCONDITIONS = [
    'unseen-within',
    'unseen-between',
    'seen-within',
    'seen-between',
    'seen-within-between',
    'seen-between-within',
]

COL_NAMES = [
    'hit', 'miss', 'false_alarm', 'correct_rej',
    'old', 'new', 'rate_hit_minus_FA','dprime',
    'rt_hit', 'rt_miss', 'rt_FA', 'rt_CR',
    'diff_rt_hit_minus_FA',

    'hit_within', 'hit_between', 'hit_within_between', 'hit_between_within',
    'miss_within', 'miss_between', 'miss_within_between', 'miss_between_within',
    'old_within', 'old_between', 'old_within_between', 'old_between_within',
    'rate_Hwith_min_FA', 'rate_Hbetw_min_FA',
    'rate_Hwith_betw_min_FA', 'rate_Hbetw_with_min_FA',

    'rt_hit_within', 'rt_hit_between',
    'rt_hit_within_between', 'rt_hit_between_within',
    'diff_rt_Hwith_min_Hbetw',
    'rt_miss_within', 'rt_miss_between',
    'rt_miss_within_between', 'rt_miss_between_within',

    'hit_loConf', 'hit_hiConf', 'miss_loConf', 'miss_hiConf',
    'FA_loConf', 'FA_hiConf', 'CR_loConf', 'CR_hiConf', 'dprime_hiConf',
    'rt_hit_loConf', 'rt_hit_hiConf', 'rt_miss_loConf', 'rt_miss_hiConf',
    'diff_rt_hitHC_minus_hitLC',
    'rt_FA_loConf', 'rt_FA_hiConf', 'rt_CR_loConf', 'rt_CR_hiConf',

    'hit_within_loConf', 'hit_between_loConf',
    'hit_within_hiConf', 'hit_between_hiConf',
    'hit_within_between_loConf', 'hit_between_within_loConf',
    'hit_within_between_hiConf', 'hit_between_within_hiConf',
    'miss_within_loConf', 'miss_between_loConf',
    'miss_within_hiConf', 'miss_between_hiConf',
    'miss_within_between_loConf', 'miss_between_within_loConf',
    'miss_within_between_hiConf', 'miss_between_within_hiConf',

    'rt_hit_within_loConf', 'rt_hit_between_loConf',
    'rt_hit_within_hiConf', 'rt_hit_between_hiConf',
    'rt_hit_within_between_loConf', 'rt_hit_between_within_loConf',
    'rt_hit_within_between_hiConf', 'rt_hit_between_within_hiConf',
    'rt_miss_within_loConf', 'rt_miss_between_loConf',
    'rt_miss_within_hiConf', 'rt_miss_between_hiConf',
    'rt_miss_within_between_loConf', 'rt_miss_between_within_loConf',
    'rt_miss_within_between_hiConf', 'rt_miss_between_within_hiConf'
]

def get_dprime(miss, hit, FA, CR):
    """
    Calculate d' based on https://lindeloev.net/calculating-d-in-python-and-php/
    """
    old = miss + hit
    new = FA + CR

    H_min_FA = (hit / old) - (FA / new)

    # Calculate hit_rate and avoid d' infinity
    hit_rate = hit / old
    if hit_rate == 1:
        hit_rate = 1 - (0.5 / old)
    elif hit_rate == 0:
        hit_rate = 0.5 / old

    # Calculate false alarm rate and avoid d' infinity
    FA_rate = FA / new
    if FA_rate == 1:
        FA_rate = 1 - (0.5 / new)
    elif FA_rate == 0:
        FA_rate = 0.5 / new

    dprime = norm.ppf(hit_rate) - norm.ppf(FA_rate)

    return old, new, H_min_FA, dprime


def get_counts_and_rts(dframe, col_label = 'error'):
    '''
    Returns the tally of correct ('error' == False) and incorrect
    ('error' == True) trials, and the mean reaction time (s) for those trials
    '''
    df_counts = dframe[col_label].value_counts()
    count_false = df_counts[False] if False in df_counts.index else 0
    count_true = df_counts[True] if True in df_counts.index else 0

    df_rts = dframe.groupby(col_label).mean().response_time
    rt_false = df_rts[False] if False in df_rts.index else NaN
    rt_true = df_rts[True] if True in df_rts.index else NaN

    return count_false, count_true, rt_false, rt_true


def extract_data_from_trials(df):
    '''
    Extracts performance metrics from a single dataframe of individual trials
    Input:
        df(pandas DataFrame) created from behavioural .tsv file(s)
    Output:
        run_data(list) performance metrics
    '''

    df_unseen, df_seen = [x for _, x in df.groupby(df['condition']=='seen')]

    hits, misses, rt_hit, rt_miss = get_counts_and_rts(df_seen)
    corRej, falseA, rt_CR, rt_FA = get_counts_and_rts(df_unseen)

    old, new, rate_H_min_FA, dprime = get_dprime(misses, hits, falseA, corRej)

    diff_rt_hit_minus_FA = rt_hit - rt_FA

    run_data = [hits, misses, falseA, corRej, old, new, rate_H_min_FA, dprime,
                rt_hit, rt_miss, rt_FA, rt_CR, diff_rt_hit_minus_FA]

    """
    Get scores per subconditions
    """
    # if first session, there are only "old_within" trials
    first_sess = len(df_seen['subcondition'].value_counts()) < 2
    if first_sess:
        old_within = old
        old_between = old_within_between = old_between_within = 0
        df_seen_within = df_seen
    else:
        df_seen_within = df_seen[df_seen['subcondition']=='seen-within']
        df_seen_between = df_seen[df_seen['subcondition']=='seen-between']
        df_seen_within_between = df_seen[df_seen['subcondition']=='seen-within-between']
        df_seen_between_within = df_seen[df_seen['subcondition']=='seen-between-within']

        old_within = df_seen_within.shape[0]
        old_between = df_seen_between.shape[0]
        old_within_between = df_seen_within_between.shape[0]
        old_between_within = df_seen_between_within.shape[0]

    # Hit and miss rates and reaction times per subconditions
    (
        hit_within, miss_within, rt_hit_within, rt_miss_within,
    ) = get_counts_and_rts(df_seen_within)

    no_trials = 0, 0, NaN, NaN
    (
        hit_between, miss_between, rt_hit_between, rt_miss_between
    ) = no_trials if first_sess else get_counts_and_rts(df_seen_between)
    (
        hit_within_between, miss_within_between,
        rt_hit_within_between, rt_miss_within_between
    ) = no_trials if first_sess else get_counts_and_rts(df_seen_within_between)
    (
        hit_between_within, miss_between_within,
        rt_hit_between_within, rt_miss_between_within
    ) = no_trials if first_sess else get_counts_and_rts(df_seen_between_within)

    """
    Hit - FA rate per subcondition
    Hit rate minus false alarm rate = (hit / old) - (FA / new)
    From a signal detection theory perspective, this isn't the greatest metric since
    FA rate reflects all four conditions (within/between/within-between/between-within)
    but probably ok *as long as* the false alarm rate is low...
    """
    rate_Hwith_min_FA = (hit_within / old_within) - (falseA / new)
    rate_Hbetw_min_FA = NaN if first_sess else (hit_between / old_between) - (falseA / new)
    rate_Hwith_betw_min_FA = NaN if first_sess else (hit_within_between / old_within_between) - (falseA / new)
    rate_Hbetw_with_min_FA = NaN if first_sess else (hit_between_within / old_between_within) - (falseA / new)

    # Difference between mean reaction times for hits-within and hits-between
    diff_rt_Hwith_min_Hbetw = rt_hit_within - rt_hit_between

    # Admittedly very ugly code. Sorry.
    run_data = run_data + [
                            hit_within, hit_between,
                            hit_within_between, hit_between_within,
                            miss_within, miss_between,
                            miss_within_between, miss_between_within,
                            old_within, old_between,
                            old_within_between, old_between_within,
                            rate_Hwith_min_FA, rate_Hbetw_min_FA,
                            rate_Hwith_betw_min_FA, rate_Hbetw_with_min_FA,
                            rt_hit_within, rt_hit_between,
                            rt_hit_within_between, rt_hit_between_within,
                            diff_rt_Hwith_min_Hbetw, rt_miss_within,
                            rt_miss_between,  rt_miss_within_between,
                            rt_miss_between_within
                          ]

    # Hit, miss, FA and CR rates and reaction times per confidence rating
    hit_loConf, hit_hiConf, rt_hit_loConf, rt_hit_hiConf = get_counts_and_rts(
        df_seen[df_seen['error']==False], 'response_confidence'
    ) if hits > 0 else no_trials

    miss_loConf, miss_hiConf, rt_miss_loConf, rt_miss_hiConf = get_counts_and_rts(
        df_seen[df_seen['error']==True], 'response_confidence'
    ) if misses > 0 else no_trials

    FA_loConf, FA_hiConf, rt_FA_loConf, rt_FA_hiConf = get_counts_and_rts(
        df_unseen[df_unseen['error']==True], 'response_confidence'
    ) if falseA > 0 else no_trials

    CR_loConf, CR_hiConf, rt_CR_loConf, rt_CR_hiConf = get_counts_and_rts(
        df_unseen[df_unseen['error']==False], 'response_confidence'
    ) if corRej > 0 else no_trials

    """
    "high confidence" dprime considers only high confidence hits as true hits,
    and the rest as missed no_trials.
    Low confidence false alarms are also counted as correct rejections
    """
    _, _, _, dprime_hiConf = get_dprime(
        misses + hit_loConf, hit_hiConf, FA_hiConf, corRej+FA_loConf
    )
    diff_rt_hitHC_minus_hitLC = rt_hit_hiConf - rt_hit_loConf

    run_data = run_data + [
                            hit_loConf, hit_hiConf,
                            miss_loConf, miss_hiConf,
                            FA_loConf, FA_hiConf,
                            CR_loConf, CR_hiConf, dprime_hiConf,
                            rt_hit_loConf, rt_hit_hiConf,
                            rt_miss_loConf, rt_miss_hiConf,
                            diff_rt_hitHC_minus_hitLC,
                            rt_FA_loConf, rt_FA_hiConf,
                            rt_CR_loConf, rt_CR_hiConf
                          ]

    # Hit and miss rates and reaction times per subcondition per confidence rating
    (
        hit_within_loConf, hit_within_hiConf,
        rt_hit_within_loConf, rt_hit_within_hiConf,
    ) = get_counts_and_rts(
        df_seen_within[df_seen_within['error']==False], 'response_confidence'
    ) if hit_within > 0 else no_trials

    (
        miss_within_loConf, miss_within_hiConf,
        rt_miss_within_loConf, rt_miss_within_hiConf,
    ) = get_counts_and_rts(
        df_seen_within[df_seen_within['error']==True], 'response_confidence'
    ) if miss_within > 0 else no_trials

    (
        hit_between_loConf, hit_between_hiConf,
        rt_hit_between_loConf, rt_hit_between_hiConf,
    ) = get_counts_and_rts(
        df_seen_between[df_seen_between['error']==False], 'response_confidence'
    ) if hit_between > 0 else no_trials

    (
        miss_between_loConf, miss_between_hiConf,
        rt_miss_between_loConf, rt_miss_between_hiConf,
    ) = get_counts_and_rts(
        df_seen_between[df_seen_between['error']==True],
        'response_confidence',
    ) if miss_between > 0 else no_trials

    (
        hit_within_between_loConf, hit_within_between_hiConf,
        rt_hit_within_between_loConf, rt_hit_within_between_hiConf,
    ) = get_counts_and_rts(
        df_seen_within_between[df_seen_within_between['error']==False],
        'response_confidence',
    ) if hit_within_between > 0 else no_trials

    (
        miss_within_between_loConf, miss_within_between_hiConf,
        rt_miss_within_between_loConf, rt_miss_within_between_hiConf,
    ) = get_counts_and_rts(
        df_seen_within_between[df_seen_within_between['error']==True],
        'response_confidence',
    ) if miss_within_between > 0 else no_trials

    (
        hit_between_within_loConf, hit_between_within_hiConf,
        rt_hit_between_within_loConf, rt_hit_between_within_hiConf,
    ) = get_counts_and_rts(
        df_seen_between_within[df_seen_between_within['error']==False],
        'response_confidence',
    ) if hit_between_within > 0 else no_trials

    (
        miss_between_within_loConf, miss_between_within_hiConf,
        rt_miss_between_within_loConf, rt_miss_between_within_hiConf,
    ) = get_counts_and_rts(
        df_seen_between_within[df_seen_between_within['error']==True],
        'response_confidence',
    ) if miss_between_within > 0 else no_trials

    return run_data + [
                        hit_within_loConf, hit_between_loConf,
                        hit_within_hiConf, hit_between_hiConf,
                        hit_within_between_loConf, hit_between_within_loConf,
                        hit_within_between_hiConf, hit_between_within_hiConf,
                        miss_within_loConf, miss_between_loConf,
                        miss_within_hiConf, miss_between_hiConf,
                        miss_within_between_loConf, miss_between_within_loConf,
                        miss_within_between_hiConf, miss_between_within_hiConf,
                        rt_hit_within_loConf, rt_hit_between_loConf,
                        rt_hit_within_hiConf, rt_hit_between_hiConf,
                        rt_hit_within_between_loConf, rt_hit_between_within_loConf,
                        rt_hit_within_between_hiConf, rt_hit_between_within_hiConf,
                        rt_miss_within_loConf, rt_miss_between_loConf,
                        rt_miss_within_hiConf, rt_miss_between_hiConf,
                        rt_miss_within_between_loConf, rt_miss_between_within_loConf,
                        rt_miss_within_between_hiConf, rt_miss_between_within_hiConf
                    ]


def process_runs(
    in_path: str,
    out_path: str,
    clean_mode: bool=False,
) -> None:
    '''
    For each subject, performance metrics are extracted per trial, per run,
    per session and overall (excluding session 1, which differs from the
    subsequent sessions because it excludes between-session repetitions).
    Scores are exported as .tsv files.

    Input:
        in_path: path to bids folder that contains *events.tsv files
        out_path: path to output directory
        clean_mode: if True, trials for which the flag exclude_session == True
        are excluded from the score calculations.
    Output:
        None
    '''
    f_ids = ['subject', 'session', 'run']

    # text file documents # of trials with no response, per run
    na_report = open(f"{out_path}/na_report.txt", 'w+')

    for sub_num in ["sub-01", "sub-02", "sub-03", "sub-06"]:

        Path(f"{out_path}/{sub_num}/beh").mkdir(parents=True, exist_ok=True)

        """
        DataFrames of performance metrics
        """
        df_runs = pd.DataFrame(columns=f_ids + COL_NAMES) # per run
        df_sessions = pd.DataFrame(columns=f_ids[:2] + COL_NAMES) # per session
        # per subject; excludes session 1
        df_subjects = pd.DataFrame(columns=[f_ids[0]] + COL_NAMES)

        """
        DataFrame of raw data points per trial concatenated across
        subjects, sessions and runs
        """
        df_trials = None

        run_list = sorted(glob.glob(f"{in_path}/{sub_num}/ses*/func/*events.tsv"))
        for run_path in tqdm.tqdm(run_list, desc=f'processing {sub_num} run files'):
            '''
            Calculate performance metrics per run for each session
            '''
            ids = run_path.split('/')[-1].split('_')
            assert sub_num == ids[0]
            sess_num = ids[1]
            run_num = ids[-2]
            ids_vals = [sub_num, sess_num, run_num]

            df = pd.read_csv(run_path, sep = '\t')

            """
            if clean_mode == True, exclude runs flagged during clean-up process
            """
            exclude_file = df['exclude_session'][0] == True if clean_mode else False
            na_count = np.sum(df['response'].isna())
            if (na_count > 0) and not exclude_file:
                na_report.write(
                    f"{na_count} missing responses for {sub_num}, {sess_num},"
                    f" {run_num}\n"
                )
                df = df[~df['response'].isna()]

            if (na_count < 60) and not exclude_file:
                # exclude runs from session 1
                # also sub-03 ses-025 which was repeated (all conditions are "seen")
                num_subcond = np.sum(
                    [x in SUBCONDITIONS for x in df['subcondition'].unique()]
                )
                if num_subcond == 6:
                    run_data = ids_vals + extract_data_from_trials(df)
                    df_runs = df_runs.append(
                        pd.Series(run_data, index=df_runs.columns),
                        ignore_index=True,
                    )

                """
                Initialize concatenated dataframe of all trials across all subjects & sessions
                """
                # Add identifier column(s) if needed
                for i in range(len(f_ids)):
                    if not f_ids[i] in df.columns.tolist():
                        df.insert(
                            loc=i, column=f_ids[i],
                            value=ids_vals[i], allow_duplicates=True,
                        )

                # concatenate all subject's trials
                if df_trials is None:
                    df_trials = pd.DataFrame(columns=df.columns.tolist())
                df_trials = pd.concat((df_trials, df), ignore_index=True)

        '''
        Calculate and export scores per subject, and per session for each subject
        '''
        # Exclude session 1 from subject's global score
        sub_data = [sub_num] + extract_data_from_trials(
            df_trials[df_trials['session']!='ses-001']
        )
        df_subjects = df_subjects.append(
            pd.Series(sub_data, index=df_subjects.columns), ignore_index=True,
        )

        for sess in df_trials['session'].unique():
            sub_ses_df = df_trials[df_trials['session']==sess]
            if len(sub_ses_df['condition'].value_counts()) == 2:
                sub_session_data = [sub_num, sess] + extract_data_from_trials(
                    sub_ses_df
                )
                df_sessions = df_sessions.append(
                    pd.Series(sub_session_data, index=df_sessions.columns),
                    ignore_index=True,
                )

        '''
        Export subject's dataframes
        '''
        o_path = f"{out_path}/{sub_num}/beh/{sub_num}_task-things_desc-"
        df_trials.to_csv(
            f"{o_path}perTrial_beh.tsv",
            sep='\t', header=True, index=False,
        )
        df_runs.to_csv(
            f"{o_path}perRun_beh.tsv",
            sep='\t', header=True, index=False,
        )
        df_sessions.to_csv(
            f"{o_path}perSession_beh.tsv",
            sep='\t', header=True, index=False,
        )
        df_subjects.to_csv(
            f"{o_path}global_beh.tsv",
            sep='\t', header=True, index=False,
        )

    na_report.close()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--idir',
        type=str,
        required=True,
        help='path to things.raw bids folder with *events.tsv output files',
    )
    parser.add_argument(
        '--odir',
        type=str,
        default='../',
        help='path to output directory',
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        default=False,
        help='if true, exclude trials flagged w exclude_session == True',
    )
    args = parser.parse_args()

    process_runs(args.idir, args.odir, args.clean)


if __name__ == '__main__':
    sys.exit(main())
