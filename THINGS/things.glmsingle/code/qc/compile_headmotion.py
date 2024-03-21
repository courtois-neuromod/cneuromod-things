import glob, os, json
import argparse

import numpy as np
import pandas as pd
from tqdm import tqdm


def get_arguments():

    parser = argparse.ArgumentParser(
        description=
        "Export metrics of head motion from fmri.prep confound files"
        " and export as single .tsv per subject",
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to root dataset directory that contains '
        'desc-confounds_part-mag_timeseries.tsv files',
    )
    parser.add_argument(
        '--out_dir',
        required=True,
        type=str,
        help='absolute path to directory where output .tsv files are saved',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number',
    )
    return parser.parse_args()


def extract_motion(
    data_path: str,
    out_path: str,
    sub_num: str,
) -> None:
    '''
    Load every confound file outputed from fmriprep,
    extract head motion metrics and concatenate in dataframe.
    Export as .tsv
    '''
    suffix = '_desc-confounds_part-mag_timeseries.tsv'
    confound_files = sorted(glob.glob(
        f"{data_path}/sub-{sub_num}/ses-*/func/*{suffix}"))

    ids = ['session', 'run']
    col_names = [
        'framewise_displacement',
        'trans_x', 'trans_y', 'trans_z',
        'rot_x', 'rot_y', 'rot_z'
        ]

    sub_df = pd.DataFrame(columns=ids + col_names)

    for conf_path in tqdm(
        confound_files,
        desc='extracting motion parameters from confound files',
    ):
        chunks = os.path.basename(conf_path).split('_')
        ses_num = chunks[1][-2:]
        run_num = chunks[3][-1]

        df_run = pd.read_csv(conf_path, sep = '\t')[col_names]
        df_run.insert(
            loc=0, column='session', value=ses_num, allow_duplicates=True,
        )
        df_run.insert(
            loc=1, column='run', value=run_num, allow_duplicates=True,
        )
        sub_df = pd.concat((sub_df, df_run), ignore_index=True)

    sub_df.to_csv(
        f'{out_path}/sub-{sub_num}/qc/sub-{sub_num}_'
        'task-things_headmotion.tsv',
        sep='\t', header=True, index=False,
    )


if __name__ == '__main__':
    '''
    Compile dataframe of head motion metrics for each subject
    and export as .tsv
    '''
    args = get_arguments()

    extract_motion(args.data_dir, args.out_dir, args.sub)
