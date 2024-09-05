import os, glob, re
import argparse

import h5py
import nibabel as nib
from nilearn.masking import apply_mask
import numpy as np
import pandas as pd
import tqdm


def get_arguments():
    parser = argparse.ArgumentParser(
        description="ranks images by their mean GLMsingle beta score within selected voxels",
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to cneuromod-things project repo',
    )
    parser.add_argument(
        '--nc_cutoff',
        default=50,
        type=int,
        help='maximal number of voxels with highest noise ceilings to include'
        ' within each ROI',
    )
    parser.add_argument(
        '--sub_num',
        required=True,
        type=str,
        help='two-digit subject number',
    )

    return parser.parse_args()


def rank_roi_betas(
    data_dir: str,
    nc_cutoff: int,
    sub_num: str,
    beta_idx: np.array,
    beta_block: np.array,
    per_trial: bool,
) -> None:
    """
    Load fLoc ROI masks, and vectorize them with the THINGS unionNonNan mask,
    so that voxels are aligned in 1D voxel arrays. Also load the masked
    (1D) noise ceiling map.

    For each ROI (face_FFA, face_OFA, face_pSTS, scene_PPA, scene_MPA,
    scene_OPA, body_EBA), select up to 50 voxels with the highest noise ceilings
    within the ROI mask, and export their beta values and ranked image/beta indices.
    """
    # load things functional mask (no NaN)
    things_mask = nib.load(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/glmsingle/input/"
        f"sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_"
        "mask.nii",
    )

    # load and mask noise ceiling map to be in same space as betas
    flat_noiseceil = apply_mask(nib.load(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/glmsingle/output/"
        f"sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_"
        "stats-noiseCeilings_statmap.nii.gz",
    ), things_mask)

    # list ROI masks from fLoc
    roi_mask_list = sorted(
        glob.glob(
            f"{data_dir}/fLoc/rois/sub-{sub_num}/rois/task-derived/"
            f"sub-{sub_num}_task-floc_space-T1w_stats-tscores_contrast-*_roi-*_"
            "cutoff-*_nvox-*_fwhm-5_ratio-0.3_desc-unsmooth_mask.nii.gz",
        )
    )
    if len(roi_mask_list) == 0:
        # sub-06 did not complete fLoc task: use noise-ceiling derived masks
        roi_mask_list = sorted(
            glob.glob(
                f"{data_dir}/fLoc/rois/sub-{sub_num}/rois/task-derived/"
                f"sub-{sub_num}_task-floc_space-T1w_stats-noiseCeil_contrast-*"
                f"_roi-*_cutoff-*_nvox-100_fwhm-3_mask.nii.gz",
            )
        )

    assert len(roi_mask_list) in range(1, 8)
    for rpath in roi_mask_list:
        flat_floc = apply_mask(nib.load(rpath), things_mask).astype(bool)
        roi_nvox = np.sum(flat_floc)

        roi_noiseCeil = flat_noiseceil * flat_floc
        roi_cutoff = int(min(roi_nvox, nc_cutoff))
        nc_thresh = np.sort(roi_noiseCeil)[-roi_cutoff]

        top_noiseceil = flat_noiseceil >= nc_thresh
        roi_voxmask = flat_floc * top_noiseceil

        roi_idx = beta_idx.T[roi_voxmask].T
        roi_bloc = beta_block.T[roi_voxmask].T
        roi_NCs = flat_noiseceil[roi_voxmask]

        c = os.path.basename(rpath).split('_')[4:6]
        roi_name = f'{c[0]}_{c[1]}'

        desc = "desc-perTrial" if per_trial else "desc-perImage"
        tval = ("%.2f" % nc_thresh)
        np.save(
            f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
            f"sub-{sub_num}_task-things_space-T1w_{roi_name}_cutoff-{tval}_"
            f"nvox-{roi_cutoff}_stats-ranks_{desc}_statseries.npy",
            roi_idx,
        )
        np.save(
            f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
            f"sub-{sub_num}_task-things_space-T1w_{roi_name}_cutoff-{tval}_"
            f"nvox-{roi_cutoff}_stats-betas_{desc}_statseries.npy",
            roi_bloc,
        )
        np.save(
            f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
            f"sub-{sub_num}_task-things_space-T1w_{roi_name}_cutoff-{tval}_"
            f"nvox-{roi_cutoff}_stats-noiseCeilings_{desc}_statseries.npy",
            roi_NCs,
        )


def rank_imgs_per_vox(
    data_dir: str,
    nc_cutoff: int,
    sub_num: str,
) -> None:
    '''
    Step 1:
    Build matching arrays of normalized beta values [dim = (images, voxels)]
    and image indices [dim = (images,)]

    For cleaner signal, only consider images with 3 repetitions for which a
    button press was recorded (no blank trials)
    '''
    subj_h5file = h5py.File(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/glmsingle/output/"
        f"sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_"
        "stats-imageBetas_desc-zscore_statseries.h5",
        "r",
    )

    all_keys =  [x for x in subj_h5file.keys() if x not in  ['mask_array', 'mask_affine']]
    noblank_keys = [x for x in all_keys if int(np.array(subj_h5file[x]['blanks'])[0])==0]
    img_keys =  [x for x in noblank_keys if int(np.array(subj_h5file[x]['num_reps'])[0])==3]

    num_vox = subj_h5file[img_keys[0]]['betas'].shape[0]

    beta_block = np.empty((len(img_keys), num_vox))
    img_indices = []

    for i in range(len(img_keys)):

        img_label = img_keys[i]
        beta_block[i, :] = np.array(subj_h5file[img_label]['betas'])
        img_indices.append(img_label)
        assert img_indices[i] == img_label

    subj_h5file.close

    img_indices = np.array(img_indices)
    beta_block = np.nan_to_num(beta_block)
    np.save(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
        f"sub-{sub_num}_task-things_desc-perImage_labels.npy",
        img_indices,
    )
    np.save(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
        f"sub-{sub_num}_task-things_space-T1w_stats-betas_desc-perImage_"
        "statseries.npy",
        beta_block,
    )

    '''
    Step 2:
    Sort beta indices according to beta values, in increasing order, per voxel.

    Within each column (voxel), values index a row in the image label and
    beta score arrays, ranked according to their beta score (smallest to largest).

    E.g., beta_idx[-10, 3] is the row index of the image with the 10th largest
    beta score in the 4th voxel within the vectorized brain mask.

    Its image label is:
        img_indices[beta_idx[-10, 3]]
    This image's beta scores are:
        beta_block[beta_idx[-10, 3]] (for all brain voxels)
        beta_block[beta_idx[-10, 3], 3] (for the 4th voxel only)
    '''
    beta_idx = np.argsort(beta_block, axis=0)

    np.save(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
        f"sub-{sub_num}_task-things_space-T1w_stats-ranks_desc-perImage_"
        "statseries.npy",
        beta_idx,
    )

    '''
    Step 3:
    Rank betas within functional ROIs
    '''
    rank_roi_betas(
        data_dir, nc_cutoff, sub_num, beta_idx, beta_block, per_trial=False,
    )


def get_sess_vector(data_dir, sub_num):
    '''
    Create vector that labels each trial by its session
    '''
    sess_file = h5py.File(
        f"{data_dir}/THINGS/glmsingle/task-things_runlist.h5",
        "r",
    )
    sessions = [f'{x}' for x in list(sess_file[sub_num]['sessions'])]

    sess_vector = []
    for ses in tqdm.tqdm(sessions, desc = 'creating session vector'):
        sess_vector += [ses] * (60*len(sess_file[sub_num][ses]))

    return sessions, sess_vector, sess_file


def build_matrices(data_dir, sub_num, s_h5file, sess_file, sessions, rm_blanks=True):
    '''
    Script concatenates all trialwise betas, and creates a vector to
    label each trial with its image name
    '''
    img_vector = []
    betas_per_trial = []
    sub_df = pd.read_csv(
        f"{data_dir}/THINGS/behaviour/sub-{sub_num}/beh/"
        f"sub-{sub_num}_task-things_desc-perTrial_annotation.tsv",
        sep = '\t',
    )

    # create list of images in order shown and processed with GLMsingle
    for ses in tqdm.tqdm(sessions, desc = 'creating image and beta matrices'):
        runs = [f'{x:02}' for x in list(sess_file[sub_num][ses])]
        ses_num = f'{int(ses):02}'
        ses_df = sub_df[sub_df['session']==f'ses-0{ses_num}']

        for run in runs:
            run_df = ses_df[ses_df['run']==int(run)]

            run_imgs = run_df['image_name'].to_numpy()
            nan_vec = pd.isna(run_df['response_type'])

            run_betas = np.array(s_h5file[ses][run[-1]]['betas']) # dim = (trials, voxels)

            if rm_blanks:
                # remove trials without behav response (button press)
                run_imgs = run_imgs[~nan_vec]
                run_betas = run_betas[~nan_vec]

            betas_per_trial.append(run_betas)
            img_vector.append(run_imgs)

    all_betas = np.concatenate(betas_per_trial, axis=0)
    all_imgs = np.concatenate(img_vector, axis=0)

    return all_imgs, all_betas


def rank_imgs_per_vox_perTrial(
    data_dir: str,
    nc_cutoff: int,
    sub_num: str,
) -> None:
    '''
    Step 1:
    Build matching arrays of beta values [dim = (trials, voxels)]
    and image indices [dim = (trials,)]
    '''
    subj_h5file = h5py.File(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/glmsingle/output/"
        f"sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_"
        "stats-trialBetas_desc-zscore_statseries.h5",
        "r",
    )

    sessions, sess_vector, sess_file = get_sess_vector(data_dir, sub_num)
    img_indices, beta_block = build_matrices(
        data_dir, sub_num, subj_h5file, sess_file, sessions, rm_blanks=True,
    )

    subj_h5file.close()

    np.save(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
        f"sub-{sub_num}_task-things_desc-perTrial_labels.npy",
        img_indices,
    )
    np.save(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
        f"sub-{sub_num}_task-things_space-T1w_stats-betas_desc-perTrial_"
        "statseries.npy",
        beta_block,
    )

    '''
    Step 2:
    Sort beta indices according to beta values, in increasing order,
    within each voxel. Save output.
    '''
    beta_idx = np.argsort(beta_block, axis=0)

    np.save(
        f"{data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
        f"sub-{sub_num}_task-things_space-T1w_stats-ranks_desc-perTrial_"
        "statseries.npy",
        beta_idx,
    )

    '''
    Step 3:
    Rank betas within functional ROIs
    '''
    rank_roi_betas(
        data_dir, nc_cutoff, sub_num, beta_idx, beta_block, per_trial=True,
    )


if __name__ == '__main__':
    """
    Script concatenates voxelwise normalized beta scores (from GLMsingle) into
    single array.

    Within each voxel, it ranks beta scores from low to high (for single trials,
    and averaged per image), to identify which images lead to higher
    activation within each voxel.

    For a set of ROIs with categorical preferences for faces, images or bodies
    identified with the fLoc task, it also identifies the 50 voxels with the
    highest noise ceilings, and it ranks their beta scores (per trial, and
    averaged per image) to identify their favorite image in the stimulus set.
    """
    args = get_arguments()

    """
    rank images within voxel using signal averaged over 3 repetitions
    for each image
    """
    rank_imgs_per_vox(args.data_dir, args.nc_cutoff, args.sub_num)

    """
    rank images within voxel using trialwise signal
    """
    rank_imgs_per_vox_perTrial(args.data_dir, args.nc_cutoff, args.sub_num)
