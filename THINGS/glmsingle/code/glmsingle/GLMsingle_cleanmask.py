import glob
import argparse
from pathlib import Path

import nibabel as nib
from nilearn.masking import unmask, apply_mask, intersect_masks
import numpy as np
from scipy.stats import zscore
from tqdm import tqdm


if __name__ == '__main__':
    '''
    When z-scoring BOLD data given to GLMsingle toolbox,
    a few voxels within the functional mask (union of all run
    functional masks) used to preprocess BOLD data for GLMsingle
    contain NaN scores.

    The following script z-scores BOLD data and identifies
    voxels with NaN scores to be excluded from downstream analyses.
    FOr each subject, it produces one mask of voxels with 1+ NaN scores
    (to be excluded) and one mask of vxels with no NaN scores within the
    functional union mask.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--things_dir',
        required=True,
        type=str,
        help='path to THINGS data directory',
    )
    args = parser.parse_args()

    in_path = f"{args.things_dir}/things.fmriprep"
    out_path = f"{args.things_dir}/things.glmsingle"

    sub_list = ['01', '02', '03', '06']
    suffix = '_space-T1w_desc-preproc_part-mag_bold.nii.gz'

    for sub_num in sub_list:
        mask_path = f'{out_path}/sub-{sub_num}/glmsingle/input'
        mask = nib.load(
            f'{mask_path}/sub-{sub_num}_task-things_space-T1w_label-brain_desc-union_mask.nii'
        )

        bold_files = sorted(
            glob.glob(
                f"{in_path}/sub-{sub_num}/ses-*/func/*{suffix}"
            )
        )

        nan_masks = []
        notnan_masks = []

        for i in tqdm(range(len(bold_files)), desc='processing bold files'):
            meanz_vals = np.mean(zscore(apply_mask(nib.load(bold_files[i]), mask, dtype=np.single)), axis=0)
            nan_masks.append(unmask(np.isnan(meanz_vals), mask))
            notnan_masks.append(unmask(~np.isnan(meanz_vals), mask))

        global_nan_mask = intersect_masks(nan_masks, threshold=0, connected=False)
        global_goodvox_mask = intersect_masks(notnan_masks, threshold=1, connected=False)

        # check that all voxels are within functional mask
        assert np.sum(mask.get_fdata() * global_goodvox_mask.get_fdata()) == np.sum(global_goodvox_mask.get_fdata())
        assert np.sum(mask.get_fdata() * global_nan_mask.get_fdata()) == np.sum(global_nan_mask.get_fdata())

        print(np.sum(global_nan_mask.get_fdata()))
        print(np.sum(global_goodvox_mask.get_fdata()))

        mask_size = np.sum(mask.get_fdata())
        for i in range(len(nan_masks)):
            assert np.sum(nan_masks[i].get_fdata() + notnan_masks[i].get_fdata()) == mask_size
            print(np.sum(nan_masks[i].get_fdata()))

        nib.save(
            global_nan_mask,
            f'{mask_path}/sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNaN_mask.nii'
        )
        nib.save(
            global_goodvox_mask,
            f'{mask_path}/sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii',
        )
