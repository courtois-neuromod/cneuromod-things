import glob, os, json
import argparse

import h5py
import numpy as np
import pandas as pd
from tqdm import tqdm


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Compiles all events.tsv files into a single HDF5 file for the entire fLoc dataset"
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to dataset directory that contains events.tsv files',
    )
    parser.add_argument(
        '--out_dir',
        required=True,
        type=str,
        help='absolute path to output directory',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number',
    )

    return parser.parse_args()


def build_nilearn_matrix(df, c_dict):
    '''
    Model events file for block design analysis (each block is 4TR, or 5.96s,
    with 12 stimuli shown from the same category)
    '''
    condi_names = list(c_dict.keys())

    df = df[df['category'].apply(lambda x: x in condi_names)]
    df.block_trial.loc[df.category=='baseline'] = 0
    df = df[df['block_trial'] == 0]

    df.subcategory.loc[df.category=='baseline'] = 'baseline'
    trial_type = df['subcategory'].to_list()
    duration = np.repeat(5.96, len(trial_type)).tolist()

    # onset time (in s) after removing the first three fMRI volumes (1.49*3 = 4.47s)
    onset = df['onset'].apply(lambda x: x - 4.47).to_list()

    return onset, duration, trial_type


def compile_floc_design(data_path, out_path, sub_num):
    '''
    Script generates a time x conditions design matrix for each run
    (event file), where 1 = a condition's onset TR.

    To save space, all design matrices are saved as sparse matrices (rather than
    full matrices filled with zeroes) within a single HDF5 file per participant.
    That is, each matrix is saved as a list of coordinates, and each trial
    (a set of coordinates) is saved as a tuple : (onset TR x condition number).
    These coordinates are used to generate sparse design matrices in matlab:
    https://www.mathworks.com/help/matlab/math/constructing-sparse-matrices.html

    Time is in TR, conditions is the total number of conditions
    (faces, corridors, etc) across all runs & sessions.
    Note that, in the CNeuromod adapation of the fLoc paradigm,
    bloc onset is aligned to the TR (1.49s).
    '''
    event_files = sorted(
        glob.glob(
            f"{data_path}/sub-{sub_num}/ses-*/func/sub-0*_ses-00*_task-fLoc_run-0*events.tsv"
        )
    )

    '''
    There are two runs per session. Each run uses slightly different stimulus
    categories (with some overlap for faces and words).

    Typically, run 1 uses the task's default stimuli ('def'), and run 2 uses the
    task's alternative stimuli ('alt')
    The def run uses the "default" stimuli:
        bodies = body (0), characters = word (1), faces = adult (2),
        objects = car (3), places = house (4), scrambled = scrambled
    The alt run uses the "alternate" stimuli:
        bodies = limb (5), characters = word (1), faces = adult (2),
        objects = instrument (6), places = corridor (7), scrambled = scrambled
    # see https://github.com/courtois-neuromod/floc.stimuli/blob/4415763fc728918c856a174be27fe4ea69abdb6c/config.json
    '''
    condi_dict = {
                  "def": {
                             'bodies': 0,
                             'characters': 1,
                             'faces': 2,
                             'objects': 3,
                             'places': 4,
                             'baseline': 8
                  },
                  "alt": {
                             'bodies': 5,
                             'characters': 1,
                             'faces': 2,
                             'objects': 6,
                             'places': 7,
                             'baseline': 8
                  }
    }

    subj_h5file = h5py.File(
        f"{out_path}/sub-{sub_num}/glm/sub-{sub_num}_task-floc_model-GLM_design.h5",'w'
    )

    for ev_path in tqdm(event_files, desc='exporting design matrices to HDF5 file'):
        sub, ses, _, run, _ = os.path.basename(ev_path).split('_')
        ses_num = ses[-2:]
        run_num = run[-2:]

        # TODO: exclude sub-02's session 02 from the dataset...
        if not ses_num in subj_h5file.keys():
            subj_h5file.create_group(ses_num)

        run_group = subj_h5file[ses_num].create_group(run_num)

        design_df = pd.read_csv(ev_path, sep='\t')
        task_version = design_df['task_version'][0]

        onset, duration, trial_type = build_nilearn_matrix(
            design_df,
            condi_dict[task_version],
        )
        run_group.create_dataset('onset', data=onset)
        run_group.create_dataset('duration', data=duration)
        run_group.create_dataset('trial_type', data=trial_type)

    subj_h5file.close()


if __name__ == '__main__':
    '''
    Step 1 to running a first-level GLM contrast in nilearn on fLoc CNeuromod dataset

    For each run, the script exports each run as a group saved into a HDF5 file (one per subject)
    Each run (.h5 group) has a list of onsets, of durations, and of conditions (the subcategory, e.g., 'faces')
    for each bloc in the run (blocs are treated as trials)
    These values will be loaded in nilearn to create design matrices to model each bloc's HRF
    '''
    args = get_arguments()

    compile_floc_design(args.data_dir, args.out_dir, args.sub)
