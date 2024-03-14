import glob, os, json
import argparse
from pathlib import Path

import h5py
import nibabel as nib
from nilearn.masking import unmask, apply_mask, intersect_masks
import numpy as np
import pandas as pd
from scipy.stats import zscore
from tqdm import tqdm


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Normalizes and flattens all bold.nii files into a single HDF5 file for the entire THINGS dataset"
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to root dataset directory that contains events.tsv files',
    )
    parser.add_argument(
        '--out_dir',
        required=True,
        type=str,
        help='absolute path to directory where output .h5 file is saved',
    )
    parser.add_argument(
        '--mni',
        action='store_true',
        default=False,
        help='if true, analyse bold files in MNI space, else native T1w space',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number',
    )

    return parser.parse_args()


def compile_maskedBOLD_hdf5(data_path, out_path, sub_num, mni=False):
    '''
    Generate a mask from the union of brain voxels across sessions and runs
    '''
    if mni:
        mask_suffix = '_space-MNI152NLin2009cAsym_desc-brain_part-mag_mask.nii.gz'
        mspace = 'T1w'
    else:
        mask_suffix = '_space-T1w_desc-brain_part-mag_mask.nii.gz'
        mspace = 'MNI'

    mask_list = sorted(
        glob.glob(f'{data_path}/sub-{sub_num}/ses-*/func/*{mask_suffix}')
    )
    mask = intersect_masks(mask_list, threshold=0)

    sub_out_path = f"{out_path}/sub-{sub_num}/GLMsingle/input"
    Path(sub_out_path).mkdir(parents=True, exist_ok=True)
    nib.save(
        mask,
        f"{sub_out_path}/sub-{sub_num}_task-things_space-{mspace}_desc-func-union_mask.nii"
    )

    '''
    Generate a masked (flattened) voxels x time (TRs per run) matrix for each run
    Save all bold matrices in a single HDF5 file per participant
    Time is in TR (1.49s)
    '''
    if mni:
        suffix = '_space-MNI152NLin2009cAsym_desc-preproc_part-mag_bold.nii.gz'
    else:
        suffix = '_space-T1w_desc-preproc_part-mag_bold.nii.gz'

    bold_files = sorted(
        glob.glob(f'{data_path}/sub-{sub_num}/ses-*/func/*{suffix}')
    )


    if mni:
        subj_h5file = h5py.File(f'{sub_out_path}/sub-{sub_num}_task-things_space-MNI_maskedBOLD.h5','w')
    else:
        subj_h5file = h5py.File(f'{sub_out_path}/sub-{sub_num}_task-things_space-T1w_maskedBOLD.h5','w')

    TRs_per_run = 188 # 190 - 2 after removing first two volumes
    tr_val = subj_h5file.create_dataset('TR', data=[1.49])

    for bold_path in tqdm(bold_files, desc='exporting masked BOLD to HDF5 file'):
        chunks = os.path.basename(bold_path).split('_')
        ses_num = chunks[1][-2:]
        run_num = chunks[3][-1]

        try:
            masked_bold = np.nan_to_num(zscore(apply_mask(nib.load(bold_path), mask, dtype=np.single))).T
            # Remove first 2 volumes of each run
            masked_bold = masked_bold[:, 2:]
            assert(masked_bold.shape[1] == TRs_per_run)

            # Note: only save if it doesn't crash
            if not ses_num in subj_h5file.keys():
                subj_h5file.create_group(ses_num)

            run_group = subj_h5file[ses_num].create_group(run_num)
            bold_file = run_group.create_dataset('bold', data=masked_bold)

        except:
            print('something went wrong loading session ' + str(ses_num) + ', run ' + run_num)

    subj_h5file.close()


if __name__ == '__main__':
    '''
    Step 2 to running GLMsingle in matlab on THINGS CNeuromod dataset

    The script normalizes (z-score) and masks (flattens) bold data from each run of
    the THINGS dataset, and saves each flattened data matrix into one
    HDF5 file per participant.

    These data are used as input for GLMsingle
    '''
    args = get_arguments()

    compile_maskedBOLD_hdf5(args.data_dir, args.out_dir, args.sub, args.mni)
