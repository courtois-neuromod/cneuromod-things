import os, glob, sys
import numpy as np
import pandas as pd
from pathlib import Path

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt

import argparse


parser = argparse.ArgumentParser(
    description=(
        "lists eye-tracking files and outputs figures to QC gaze"
    ),
)
parser.add_argument(
    '--in_path',
    type=str,
    required=True,
    help="absolute path to dataset's data directory",
)
parser.add_argument(
    '--run_dir',
    default='',
    type=str,
    help='absolute path to main code directory that contains '
    'git@github.com:courtois-neuromod/pupil.git (commit dd26b6a) as a submodule'
)
parser.add_argument(
    '--out_path',
    type=str,
    default='./results',
    help='absolute path to output directory'
)
args = parser.parse_args()

sys.path.append(
    os.path.join(
        args.run_dir,
        "pupil",
        "pupil_src",
        "shared_modules",
    )
)

from file_methods import PLData_Writer, load_pldata_file, load_object, save_object


def process_dset(
    df_files: pd.DataFrame,
    task_root: str,
    ses_list: list,
) -> tuple:

    sub_list = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    pupil_file_paths = []

    for ses_path in ses_list:
        [sub_num, ses_num] = ses_path.split('/')[-2:]

        events_list = sorted(glob.glob(f'{ses_path}/*task*events.tsv'))
        for event in events_list:
            ev_file = os.path.basename(event)

            try:
                skip_run_num = False
                [
                    sub,
                    ses,
                    fnum,
                    task_type,
                    run_num,
                    appendix,
                ] = ev_file.split('_')

                if sub in sub_list:
                    assert sub == sub_num
                    assert ses_num == ses

                    log_list = glob.glob(
                        f'{ses_path}/{sub_num}_{ses_num}_{fnum}.log'
                    )
                    has_log = len(log_list) == 1
                    if has_log:
                        with open(log_list[0]) as f:
                            lines = f.readlines()
                            empty_log = len(lines) == 0
                    else:
                        empty_log = True

                    pupil_path = f'{ses_path}/{sub_num}_{ses_num}_{fnum}.pupil/{task_type}_{run_num}/000'

                    list_pupil = glob.glob(f'{pupil_path}/pupil.pldata')
                    has_pupil = len(list_pupil) == 1
                    if has_pupil:
                        pupil_file_paths.append(
                            (
                                os.path.dirname(list_pupil[0]),
                                (sub, ses, run_num, task_type, fnum),
                            )
                        )

                    has_eyemv = len(glob.glob(f'{pupil_path}/eye0.mp4')) == 1
                    has_gaze = len(glob.glob(f'{pupil_path}/gaze.pldata')) == 1

                    run_data = [
                        sub_num,
                        ses_num,
                        run_num,
                        task_type,
                        fnum,
                        has_pupil,
                        has_gaze,
                        has_eyemv,
                        has_log,
                        empty_log,
                    ]
                    df_files = pd.concat(
                        [
                            df_files,
                            pd.DataFrame(
                                np.array(run_data).reshape(1, -1),
                                columns=df_files.columns,
                            ),
                        ],
                        ignore_index=True,
                    )

            except:
                print(f'cannot process {ev_file}')

    return df_files, pupil_file_paths


def compile_file_list(
    in_path: str,
) -> tuple:

    col_names = [
        'subject',
        'session',
        'run',
        'task',
        'file_number',
        'has_pupil',
        'has_gaze',
        'has_eyemovie',
        'has_log',
        'empty_log',
    ]
    df_files = pd.DataFrame(columns=col_names)

    task_root = in_path.split('/')[-2]
    # on elm, for triplets : in_path = '/unf/eyetracker/neuromod/triplets/sourcedata'
    ses_list = [
        x for x in sorted(glob.glob(
            f'{in_path}/sub-*/ses-*')
        ) if x.split('-')[-1].isnumeric()
    ]

    return process_dset(df_files, task_root, ses_list)


def export_and_plot(
    pupil_path: str,
    in_path: str,
    out_path: str,
) -> None:
    '''
    Function accomplishes two things:
    1. exports gaze and pupil metrics from .pldata (pupil's) format
       to .npz format
    2. compiles list of gaze and pupil positions (with timestamps and
       confidence), and exports plots for visual QCing
    '''
    sub, ses, run, task, fnum = pupil_path[1]

    task_root = out_path.split('/')[-1]

    outpath_gaze = os.path.join(out_path, sub, ses)
    gfile_path = f'{outpath_gaze}/{sub}_{ses}_{run}_{fnum}_{task}_gaze2D.npz'

    if not os.path.exists(gfile_path):
        # gaze data includes pupil metrics from which each gaze was derived
        seri_gaze = load_pldata_file(pupil_path[0], 'gaze')[0]
        print(sub, ses, run, task, len(seri_gaze))

        # Convert serialized file to list of dictionaries
        gaze_2plot_list = []
        deserialized_gaze = []

        for gaze in seri_gaze:
            gaze_data = {}
            # [gaze_x, gaze_y, pupil_x, pupil_y, timestamp, confidence]
            gaze_2plot = np.empty(6)
            for key in gaze.keys():
                if key != 'base_data': # gaze data
                    if key == 'norm_pos':
                        gaze_2plot[0: 2] = [gaze[key][0], gaze[key][1]]
                    elif key == 'timestamp':
                        gaze_2plot[4] = gaze[key]
                    elif key == 'confidence':
                        gaze_2plot[5] = gaze[key]
                    gaze_data[key] = gaze[key]
                else: # pupil data from which gaze was derived
                    gaze_pupil_data = {}
                    gaze_pupil = gaze[key][0]
                    for k in gaze_pupil.keys():
                        if k != 'ellipse':
                            if k == 'norm_pos':
                                gaze_2plot[2: 4] = [
                                    gaze_pupil[k][0],
                                    gaze_pupil[k][1],
                                ]
                            gaze_pupil_data[k] = gaze_pupil[k]
                        else:
                            gaze_pupil_ellipse_data = {}
                            for sk in gaze_pupil[k].keys():
                                gaze_pupil_ellipse_data[sk] = gaze_pupil[k][sk]
                            gaze_pupil_data[k] = gaze_pupil_ellipse_data
                    gaze_data[key] = gaze_pupil_data

            deserialized_gaze.append(gaze_data)
            gaze_2plot_list.append(gaze_2plot)

        print(len(deserialized_gaze))

        try:
            ev_path = f'{in_path}/{sub}/{ses}/{sub}_{ses}_{fnum}_{task}_{run}_events.tsv'
            ev_lasttrial = pd.read_csv(ev_path, sep='\t', header=0).iloc[-1]
            run_dur = int(ev_lasttrial['onset'] + 20)
        except:
            print('event file did not load, using default run duration')
            run_dur = 700

        if len(deserialized_gaze) > 0:
            Path(outpath_gaze).mkdir(parents=True, exist_ok=True)
            np.savez(gfile_path, gaze2d = deserialized_gaze)

            # create and export QC plots per run
            array_2plot = np.stack(gaze_2plot_list, axis=0)

            fig, axes = plt.subplots(4, 1, figsize=(7, 14))
            plot_labels = ['gaze_x', 'gaze_y', 'pupil_x', 'pupil_x']

            for i in range(4):
                axes[i].scatter(
                    array_2plot[:, 4]-array_2plot[:, 4][0],
                    array_2plot[:, i],
                    c=array_2plot[:, 5],
                    s=10,
                    cmap='terrain_r',
                    alpha=0.2,
                )  # alpha=array_2plot[:, 5]*0.4)
                axes[i].set_ylim(-2, 2)
                axes[i].set_xlim(0, run_dur)
                axes[i].set_title(
                    f'{sub} {task} {ses} {run} {plot_labels[i]}'
                )

            outpath_fig = os.path.join(out_path, 'QC_gaze')
            Path(outpath_fig).mkdir(parents=True, exist_ok=True)

            fig.savefig(
                f'{outpath_fig}/{sub}_{ses}_{run}_{fnum}_{task}_QCplot.png'
            )
            plt.close()


def main() -> None:
    """
    This script
    - compiles an overview of all available files (pupils.pldata, gaze.pldata
      and eye0.mp4 exported by pupil, psychopy log file) and exports a
      file list (file_list.tsv).
    - converts gaze.pldata files to .npz format (to process in numpy
      independently of pupil lab classes).
    - exports plots of gaze and pupil positions over time (per run) to
      QC each run (flag camera freezes, missing pupils, excessive drift, etc)
    """
    # in_path e.g., (on elm): /unf/eyetracker/neuromod/triplets/sourcedata
    in_path = args.in_path
    out_path = args.out_path

    '''
    Step 1.1: compile overview of available files
    Export file list as .tsv
    '''
    file_report, pupil_paths = compile_file_list(in_path)

    outpath_report = f"{out_path}/QC_gaze"
    Path(outpath_report).mkdir(parents=True, exist_ok=True)
    file_report.to_csv(
        f"{outpath_report}/file_list.tsv",
        sep='\t',
        header=True,
        index=False,
    )

    '''
    Step 1.2: For each run:
    - export gaze files from pupil .pldata format to numpy .npz format
    - plot the raw gaze & pupil data and export chart for QCing
    '''
    for pupil_path in pupil_paths:
        export_and_plot(pupil_path, in_path, out_path)

    '''
    Step 2: offline manual QCing
    Flag bad runs (missing/corrupt data) based on graphs from step 1.2.
    Compile a clean list of runs to drift-correct and bids-format.
    Save run list as "QCed_file_list.tsv" in the "out_path" directory

    Load this list to identify valid runs to perform drift correction (Step 3).
    '''

if __name__ == '__main__':
    sys.exit(main())
