import os, glob
from pathlib import Path

import h5py
import nibabel as nib
from nilearn.masking import unmask, apply_mask
import numpy as np
import pandas as pd
from scipy.io import loadmat, savemat
from scipy.stats import zscore
import argparse


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Estimates voxelwise noise ceilings from GLMsingle betas"
    )
    parser.add_argument(
        '--things_dir',
        required=True,
        type=str,
        help='path to THINGS data directory',
    )
    parser.add_argument(
        '--sub_num',
        required=True,
        type=str,
        help='two-digit subject number',
    )
    return parser.parse_args()


def get_sess_vector(things_dir, sub_num):
    '''
    Create vector that labels each trial by its session
    '''
    session_file_path = f"{things_dir}/things.glmsingle/task-things_runlist.h5"
    sess_file = h5py.File(session_file_path, 'r')
    sessions = [f'{x}' for x in list(sess_file[sub_num]['sessions'])]

    sess_vector = []
    for ses in sessions:
        sess_vector += [ses] * (60*len(sess_file[sub_num][ses]))

    return sessions, sess_vector, sess_file


def normalize_betas(betas, sessions, sess_vector):
    '''
    Normalize (z-score) voxel values across trial, within session
    '''
    ses_blist = []
    for ses in sessions:
        mask_vect = np.array(sess_vector) == ses
        # Note: by default, z-scores computed along axis = 0, WITHIN voxel (across trials)
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.zscore.html
        ses_betas = zscore(betas[mask_vect], axis=0, nan_policy='propagate') # Oli's
        #ses_betas = np.nan_to_num(zscore(betas[mask_vect], axis=0, nan_policy='omit'))
        ses_blist.append(ses_betas)

    z_betas = np.concatenate(ses_blist, axis=0)

    return z_betas


def get_img_vector(things_dir, sub_num, sess_file, sessions, n=3, rm_blanks=False):
    '''
    Create vector that labels each trial by its image
    '''
    img_vector = []
    des_path = Path(
        f"{things_dir}/things.glmsingle/sub-{sub_num}/glmsingle/"
        f"input/sub-{sub_num}_task-things_model-glmsingle_desc-sparse_design.h5"
    )
    des_file = h5py.File(des_path, 'r')

    if rm_blanks:
        df_path = Path(
            f"{things_dir}/things.behaviour/sub-{sub_num}/beh/"
            f"sub-{sub_num}_task-things_desc-perTrial_annotation.tsv"
        )
        sub_df = pd.read_csv(df_path, sep = '\t')

    for ses in sessions:
        runs = [f'{x:02}' for x in list(sess_file[sub_num][ses])]
        ses_num = f'{int(ses):02}'
        if rm_blanks:
            ses_df = sub_df[sub_df['session']==f'ses-0{ses_num}']

        for run in runs:
            run_imgNum = np.array(des_file[ses_num][run]['design_coord'])[:, 1]
            if rm_blanks:
                run_df = ses_df[ses_df['run']==int(run)]
                nan_vec = pd.isna(run_df['response_type'])
                # replace image number with -1 when no button press recorded
                run_imgNum[nan_vec] = -1

            run_imgNum = run_imgNum.tolist()
            img_vector += run_imgNum

    des_file.close()

    # only include labels shown n times (default n=3)
    labels, counts = np.unique(img_vector, return_counts=True)
    rep_labels = labels[counts==n] # n = 3
    rep_labels = rep_labels[rep_labels >= 0] # remove -1 placeholder

    return img_vector, rep_labels


def get_noise_variance(z_betas, img_vector, rep_labels):
    '''
    Calculate standard deviation across the 3 image repetitions, for each image
    '''
    std_noise_per_img = []

    for label in rep_labels:
        mask_vect = np.array(img_vector) == label
        img_betas = z_betas[mask_vect]
        #std_img = np.nanstd(img_betas, axis=0, ddof=1)
        std_img = np.std(img_betas, axis=0, ddof=1)
        std_noise_per_img.append(std_img)

    img_noise_arr = np.stack(std_noise_per_img, axis=0)
    #noise_var = np.nanmean(img_noise_arr**2, axis=0)
    noise_var = np.mean(img_noise_arr**2, axis=0)

    return noise_var


def reshape_beta(betas, img_vector, rep_labels):
    '''
    Reshape betas into (voxels, rep, img) data cube
    '''
    betas_per_img = []

    for label in rep_labels:
        mask_vect = np.array(img_vector) == label
        img_betas = betas[mask_vect].T
        betas_per_img.append(img_betas)

    beta_cube = np.stack(betas_per_img, axis=2)

    return beta_cube


def compute_noise_ceiling(things_dir, mat_file, sub_num, n=3, rm_blanks=False):
    '''
    Calculates stdev across all images (within repetition number 1, 2 or 3);
    Approach adpoted in THINGS-data paper (Oli's approach)
    Leads to fewer NaN z-scores than normalizing within session (like NSD).
    '''

    '''
    Step 0: load betas
    '''
    matfile = h5py.File(mat_file, 'r')
    betas = np.squeeze(np.array(matfile['modelmd']))
    matfile.close()
    '''
    Step 1: create vector that labels each trial by its image
    '''
    sessions, _, sess_file = get_sess_vector(things_dir, sub_num)
    img_vector, rep_labels = get_img_vector(
        things_dir, sub_num, sess_file, sessions, n, rm_blanks=rm_blanks,
    )
    sess_file.close()
    '''
    Step 2: reshape data into cube, dim = (voxels, repetitions, images)
    '''
    beta_cube = reshape_beta(betas, img_vector, rep_labels)
    assert(beta_cube.shape[-2] == n)
    '''
    Step 3: normalize betas per image & calculate noise stdev
    '''
    #normalized = np.nan_to_num(zscore(beta_cube, axis=-1, nan_policy='omit'))
    #noisesd = np.sqrt(np.nanmean(np.nanvar(normalized, axis=-2, ddof=1), axis=-1))
    normalized = zscore(beta_cube, axis=-1, nan_policy='propagate')
    noisesd = np.sqrt(np.mean(np.var(normalized, axis=-2, ddof=1), axis=-1))
    '''
    Step 4: calculate signal stdev
    '''
    sigsd = np.sqrt(np.clip(1 - noisesd ** 2, 0., None))
    '''
    Step 5: compute the noise ceiling signal-to-noise ratio
    '''
    ncsnr = sigsd / noisesd
    '''
    Step 6: compute the noise ceiling per voxel
    '''
    nc = np.nan_to_num(100 * ((ncsnr ** 2) / ((ncsnr ** 2) + (1 / n))))

    return nc


def compute_noise_ceiling_nsd(things_dir, mat_file, sub_num, n=3, rm_blanks=False):
    '''
    Normalizes betas within session (across runs from that session), as
    recommended by NSD data paper. Leads to more nan vals than normalizing per image.
    Step 0: load betas
    '''
    matfile = h5py.File(mat_file, 'r')
    betas = np.squeeze(np.array(matfile['modelmd']))
    matfile.close()

    '''
    Step 1: z-score the betas per SESSION (not per run)
    '''
    sessions, sess_vector, sess_file = get_sess_vector(things_dir, sub_num)
    z_betas = normalize_betas(betas, sessions, sess_vector)
    '''
    Step 2: compute the average noise variance
    '''
    img_vector, rep_labels = get_img_vector(
        things_dir, sub_num, sess_file, sessions, n, rm_blanks=rm_blanks,
    )
    noise_var = get_noise_variance(z_betas, img_vector, rep_labels)
    noise_std = noise_var**(0.5)
    '''
    Step 3: compute the average signal variance
    '''
    signal_var = np.maximum(0, 1 - noise_var)
    signal_std = signal_var**(0.5)
    '''
    Step 4: compute the noise ceiling signal-to-noise ratio
    '''
    ncsnr = signal_std / noise_std
    '''
    Step 5: compute the noise ceiling per voxel
    '''
    nc = np.nan_to_num(100*((ncsnr**2) / ((ncsnr**2) + (1/n)))) # n = 3

    return nc


if __name__ == '__main__':
    '''
    Derive voxelwise noise ceilings from beta scores estimated with GLMsingle.

    The noise ceiling estimation is adapted from the Natural Scene Dataset's
    datapaper methodology. source: https://www.nature.com/articles/s41593-021-00962-x
    '''
    args = get_arguments()

    things_dir = args.things_dir
    sub_num = args.sub_num

    data_path = f"{things_dir}/things.glmsingle/sub-{sub_num}/glmsingle"
    in_file = f"{data_path}/output/T1w/TYPED_FITHRF_GLMDENOISE_RR.mat"

    nc_arr = compute_noise_ceiling(
        things_dir,
        in_file,
        sub_num,
        n=3,
        rm_blanks=True,
    )

    # unmask array with union functional mask, and remask with no-NaN mask
    union_mask = nib.load(
        f"{data_path}/input/sub-{sub_num}_task-things_"
        "space-T1w_label-brain_desc-union_mask.nii"
    )
    clean_mask = nib.load(
        f"{data_path}/input/sub-{sub_num}_task-things_"
        "space-T1w_label-brain_desc-unionNonNaN_mask.nii"
    )

    nc_arr = apply_mask(unmask(nc_arr, union_mask), clean_mask)
    outpath_mat = Path(
        f"{data_path}/output/sub-{sub_num}_task-things_"
        "space-T1w_model-fitHrfGLMdenoiseRR_stat-noiseCeilings_statmap.mat"
    )
    savemat(outpath_mat, {'NC': nc_arr})

    nc_nii = unmask(nc_arr, clean_mask)  # remove NaN voxels
    outpath_nii = Path(
        f"{data_path}/output/sub-{sub_num}_task-things_"
        "space-T1w_model-fitHrfGLMdenoiseRR_stat-noiseCeilings_statmap.nii.gz"
    )
    nib.save(nc_nii, outpath_nii)
