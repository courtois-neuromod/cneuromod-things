import glob, os
import argparse
from pathlib import Path

import h5py
import nibabel as nib
from nilearn.masking import unmask, apply_mask
import numpy as np
from scipy.stats import zscore
from tqdm import tqdm


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Organizes trialwise GLMsingle betas into .h5 file"
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='path to things.glmsingle data directory',
    )
    parser.add_argument(
        '--zbetas',
        action='store_true',
        default=False,
        help='if true, z-score single-trial betas before saving',
    )
    parser.add_argument(
        '--sub_num',
        required=True,
        type=str,
        help='two-digit subject number',
    )

    return parser.parse_args()


def compile_betas_hdf5(data_dir, sub_num, zbetas=False):
    '''
    load list of sessions and their runs for that subject
    '''
    sub_run_list = h5py.File(
        f"{data_dir}/task-things_desc-runlist.h5", 'r')[sub_num]

    '''
    Load union and clean (no NaN voxels) functional masks
    '''
    union_mask = nib.load(
        f"{data_dir}/sub-{sub_num}/GLMsingle/input/"
        f"sub-{sub_num}_task-things_space-T1w_desc-func-union_mask.nii"
    )
    clean_mask = nib.load(
        f"{data_dir}/sub-{sub_num}/GLMsingle/input/"
        f"sub-{sub_num}_task-things_space-T1w_desc-func-clean_mask.nii"
    )
    num_vox = int(np.sum(union_mask.get_fdata()))

    '''
    Get subject's GLMs output file
    '''
    mat_file = Path(
        f"{data_dir}/sub-{sub_num}/GLMsingle/output/T1w/"
        "TYPED_FITHRF_GLMDENOISE_RR.mat"
    )
    gfile = h5py.File(mat_file, 'r')
    all_betas = np.squeeze(np.array(gfile['modelmd']))
    gfile.close()
    assert(all_betas.shape[1]==num_vox)

    if zbetas:
        all_betas = zscore(all_betas, axis=0, nan_policy='propagate')


    '''
    prepare final output file (beta arrays sorted per session and run)
    '''
    zname = '-zscored' if zbetas else ''
    subj_h5file = h5py.File(
        f"{data_dir}/sub-{sub_num}/GLMsingle/output/sub-{sub_num}_"
        f"task-things_space-T1w_res-func_desc{zname}-betas-per-trial.h5",
        'w',
    )

    '''
    For each run, save betas in .h5 file
    '''
    count = 0
    for i in range(len(sub_run_list['sessions'])):
        ses_num = str(sub_run_list['sessions'][i])
        ses_grp = subj_h5file.create_group(ses_num)

        for j in range(len(sub_run_list[ses_num])):
            run_num = str(sub_run_list[ses_num][j])
            ses_grp.create_group(run_num)

            run_betas = all_betas[count:count+60]
            clean_betas = apply_mask(unmask(run_betas, union_mask), clean_mask)

            subj_h5file[ses_num][run_num].create_dataset('betas', data=clean_betas)
            count += 60

    subj_h5file.create_dataset('mask_array', data=clean_mask.get_fdata())
    subj_h5file.create_dataset('mask_affine', data=clean_mask.affine)

    subj_h5file.close()
    sub_run_list.close()


if __name__ == '__main__':
    """
    Script organizes betas outputed by GLMsingle into one .h5 file per subject,
    with betas sorted per session and run.

    Betas are saved into arrays (trials, voxels) whose rows correspond to
    1D arrays of flattened voxels masked with a functional mask.
    """
    args = get_arguments()

    compile_betas_hdf5(args.data_dir, args.sub_num, args.zbetas)
