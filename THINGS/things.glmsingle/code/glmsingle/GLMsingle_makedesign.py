import glob, os, json
import argparse
from pathlib import Path

import h5py
import nibabel as nib
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from tqdm import tqdm


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Compiles all *events.tsv files into a single HDF5 file for the entire THINGS dataset"
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to root dataset directory that contains *events.tsv files'
    )
    parser.add_argument(
        '--out_dir',
        required=True,
        type=str,
        help='absolute path to directory where output .h5 file is saved',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number',
    )
    args = parser.parse_args()

    return args


def get_imgname(event_file):

    df = pd.read_csv(event_file, sep='\t')[['image_path', 'response']]
    df['image_path'] = df['image_path'].apply(lambda x: os.path.basename(x))
    cond_names = df['image_path'].to_numpy()

    return cond_names


def compile_design_hdf5(data_path, out_path, sub_num, sparse=True):

    event_files = sorted(glob.glob(f'{data_path}/sub-{sub_num}/ses-*/func/*events.tsv'))

    '''
    Compile list of all image names seen by a participant across all runs and sessions
    '''
    image_names = [
        get_imgname(ef) for ef in tqdm(
            event_files, desc='extracting image names from event files'
        )
    ]
    image_names = np.unique(np.hstack(image_names))

    '''
    Create a dictionary that assigns a unique number to each image
    The image-number mapping is unique to each participant, and is used to
    build design matrices
    '''
    image_refnums = {}
    total_image_count = 0

    for img in tqdm(image_names, desc='building dict of image reference numbers'):
        if not img in image_refnums:
            image_refnums[img] = total_image_count
            total_image_count += 1

    with open(f'{out_path}/sub-{sub_num}_task-things_desc-image-design-refnumbers.json', 'w') as outfile:
        json.dump(image_refnums, outfile)

    '''
    Generate a time x conditions design matrix for each run (event file),
    where 1 = a condition's onset TR.
    Save all design matrices in a single HDF5 file per participant

    Time is in TR, conditions is the total number of conditions (unique images)
    across all runs & sessions. Note that, in the THINGS memory CNeuromod
    paradigm, trial onset is aligned to the TR (1.49s).

    If "sparse" == True, rather than saving full matrices mostly filled with zeros,
    design matrices are saved as a list of coordinates in the final design matrix.
    Each trial is saved as a tuple : (onset TR x image number)

    These coordinates are used to generate sparse design matrices in matlab:
    https://www.mathworks.com/help/matlab/math/constructing-sparse-matrices.html
    '''
    if sparse:
        subj_h5file = h5py.File(f'{out_path}/sub-{sub_num}_task-things_sparsedesign.h5','w')
    else:
        subj_h5file = h5py.File(f'{out_path}/sub-{sub_num}_task-things_fulldesign.h5','w')

    TRs_per_run = 188 # 190 - 2 after removing first two volumes
    tr_count = subj_h5file.create_dataset('TR_count', data=[TRs_per_run])
    tr_val = subj_h5file.create_dataset('TR', data=[1.49])
    num_condition = subj_h5file.create_dataset('total_conditions', data=[total_image_count])

    for ev_path in tqdm(event_files, desc='exporting design matrices to HDF5 file'):
        sub, ses, _, run, _ = os.path.basename(ev_path).split('_')
        ses_num = ses[-2:]
        run_num = f'0{str(run[-1])}'

        if not ses_num in subj_h5file.keys():
            subj_h5file.create_group(ses_num)

        run_group = subj_h5file[ses_num].create_group(run_num)

        design_df = pd.read_csv(ev_path, sep='\t')[['duration', 'onset', 'image_path']]
        # replace image name by its condition number in the dataframe
        design_df['image_path'] = design_df['image_path'].apply(lambda x: image_refnums[os.path.basename(x)])
        # convert onset time (in s) into TRs, after removing the first two fMRI volumes (1.49*2 = 2.98, rounded up to 3s)
        design_df['onset'] = design_df['onset'].apply(lambda x: int((x - 3.0)/1.49))

        if sparse:
            coord = np.array(list(zip(
                design_df['onset'].to_numpy().tolist(),
                design_df['image_path'].to_numpy().tolist()
            )))
            design_coord = run_group.create_dataset('design_coord', data=coord)

        else:
            # final matrix dim must be (time in TR, num conditions across all runs & sessions)
            row_coord  = design_df['onset'].to_numpy()
            col_coord  = design_df['image_path'].to_numpy()
            data = np.repeat(1, len(row_coord))
            design_mat = coo_matrix(
                (data, (row_coord, col_coord)),
                shape=(TRs_per_run, total_image_count)
            ).toarray()
            design_file = run_group.create_dataset('design', data=design_mat)

    subj_h5file.close()


if __name__ == '__main__':
    '''
    Step 1 to running GLMsingle in matlab on THINGS CNeuromod dataset

    First, the script parses through a subject's events.tsv files (across sessions and runs),
    and assigns a unique number to each stimulus image which it saves into a dictionary.
    E.g., results/design_files/sub-03_image_design_refnumbers.json

    Then, for each run, the script exports each trial as a pair of coordinates
    (onset time in TRs, image number). Each list of coordinates (60 per run,
    one set of coordinates per trial) is saved into a HDF5 file (one per subject).
    E.g., path/to/out_dir/sub-0*_things_sparsedesign.h5
    These coordinates will be loaded in matlab to create sparse design matrices
    to model each trial's HRF.
    '''
    args = get_arguments()

    out_dir = f"{args.out_dir}/sub-{args.sub}/GLMsingle/input"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    compile_design_hdf5(args.data_dir, out_dir, args.sub, sparse=True)
