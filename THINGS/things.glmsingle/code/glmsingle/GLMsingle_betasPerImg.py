import os, glob, json
import argparse
from pathlib import Path

import h5py
import nibabel as nib
from nilearn.masking import unmask, apply_mask
import numpy as np
import pandas as pd
from scipy.stats import zscore
import tqdm


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Average betas per stimulus image from single-trial GLMsingle betas",
    )
    parser.add_argument(
        '--things_dir',
        required=True,
        type=str,
        help='path to THINGS data directory',
    )
    parser.add_argument(
        '--zbetas',
        action='store_true',
        default=False,
        help='if true, z-score single-trial betas before averaging',
    )
    parser.add_argument(
        '--sub_num',
        required=True,
        type=str,
        help='two-digit subject number',
    )

    return parser.parse_args()


# Removed:
# categ_recognizability, img_recognizability; not in updated THINGSplus version
# img_memorability; permission needed to share
col_names = [
                'image_name', 'image_category',
                'things_image_nr', 'things_category_nr',
                'highercat27_names', 'highercat53_names', 'highercat53_num',
                'categ_concreteness', 'categ_wordfreq_COCA',
                'categ_nameability', 'img_nameability',
                #'categ_recognizability', 'img_recognizability',
                'categ_consistency', 'img_consistency',
                #'img_memorability',
                'categ_size', 'categ_arousal', 'categ_manmade',
                'categ_precious', 'categ_living',
                'categ_heavy', 'categ_natural',
                'categ_moves', 'categ_grasp', 'categ_hold',
                'categ_be_moved', 'categ_pleasant'
            ]


def get_sess_vector(data_dir, sub_num):
    '''
    Create vector that labels each trial by its session number
    '''
    session_file_path = Path(
        f"{data_dir}/things.glmsingle/task-things_runlist.h5"
    )
    sess_file = h5py.File(session_file_path, 'r')
    sessions = [f'{x}' for x in list(sess_file[sub_num]['sessions'])]

    sess_vector = []
    for ses in tqdm.tqdm(sessions, desc = 'creating session vector'):
        sess_vector += [ses] * (60*len(sess_file[sub_num][ses]))

    return sessions, sess_vector, sess_file


def normalize_betas(betas, sessions, sess_vector):
    '''
    Normalize (z-score) voxel values across trial, within session
    '''
    ses_blist = []
    for ses in sessions:
        mask_vect = np.array(sess_vector) == ses
        """
        By default, z-scores computed along axis = 0, WITHIN voxel (across trials)
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.zscore.html
        """
        ses_betas = zscore(betas[mask_vect], axis=0, nan_policy='propagate')
        #ses_betas = np.nan_to_num(zscore(betas[mask_vect], axis=0, nan_policy='omit'))
        ses_blist.append(ses_betas)

    return np.concatenate(ses_blist, axis=0)


def update_checkedimgs(df, run_imgNum, ref_img, checked_imgs):
    """
    Validate number-to-image correspondance as sanity check for
    *events.tsv data and GLMsingle & noise-ceiling analyses

    Also adds image-specific metrics and annotations to checked_imgs dict
    for content & representation analyses
    """
    img_names = df['image_name'].to_numpy()
    for i in range(df.shape[0]):
        assert ref_img[img_names[i]+'.jpg'] == run_imgNum[i]

    # Add image-specific metrics to dictionary
    add_mask = [x not in checked_imgs for x in img_names]
    df_2add = df[add_mask]
    for i in range(df_2add.shape[0]):
        iname = df_2add['image_name'].iloc[i]
        checked_imgs[iname] = {}
        checked_imgs[iname]['blanks'] = 0
        for feat in col_names:
            checked_imgs[iname][feat] = df_2add[feat].iloc[i]


def avg_beta(
    subj_h5file, betas, img_vector, rep_labels, img_info, u_mask, c_mask,
):
    '''
    Reshape betas into (voxels, rep, img) data cube
    '''
    betas_per_img = []

    for label in tqdm.tqdm(rep_labels, desc = 'averaging and saving betas'):
        mask_vect = np.array(img_vector) == label
        img_betas = betas[mask_vect]#.T
        n = img_betas.shape[0]
        # remove NaN voxels from final array w clean mask
        clean_betas = apply_mask(unmask(img_betas, u_mask), c_mask)

        label_grp = subj_h5file.create_group(label)
        label_grp.create_dataset('betas', data=np.mean(clean_betas, axis=0))
        label_grp.create_dataset('num_reps', data=[n])

        for k in img_info[label].keys():
            label_grp.create_dataset(k, data=[img_info[label][k]])

    return subj_h5file


def get_img_vector(data_dir, sub_num, sess_file, sessions, rm_blanks=False):
    '''
    Script creates a vector to label each trial with its image name

    It also validates the trial labelling from GLMsingle, and from
    the cleaned up event files
    '''
    img_vector = []

    des_path = Path(
        f"{data_dir}/things.glmsingle/sub-{sub_num}/glmsingle/input/"
        f"sub-{sub_num}_task-things_sparsedesign.h5"
    )
    des_file = h5py.File(des_path, 'r')

    """
    This step is not needed, but it's a sanity check to validate the trial
    labelling of the GLMsingle analysis.
    """
    json_path = Path(
        f"{data_dir}/things.glmsingle/sub-{sub_num}/glmsingle/input/"
        f"sub-{sub_num}_task-things_imgDesignNumbers.json"
    )
    with open(json_path, 'r') as f:
        ref_img = json.load(f)

    checked_imgs = {}
    df_path = Path(
        f"{data_dir}/things.behaviour/sub-{sub_num}/beh/"
        f"sub-{sub_num}_task-things_desc-perTrial_annotation.tsv"
    )
    sub_df = pd.read_csv(df_path, sep = '\t')

    # recreate order of bold & design matrices for GLMsingle
    for ses in tqdm.tqdm(sessions, desc = 'creating image vector'):
        runs = [f'{x:02}' for x in list(sess_file[sub_num][ses])]
        ses_num = f'{int(ses):02}'
        ses_df = sub_df[sub_df['session']==f'ses-0{ses_num}']

        for run in runs:
            run_imgNum = np.array(des_file[ses_num][run]['design_coord'])[:, 1]
            run_df = ses_df[ses_df['run']==int(run)]

            """
            validation step: add image-specific netrics to dict,
            and validate trial labels for GLMsingle & noise ceiling analyses
            """
            update_checkedimgs(run_df, run_imgNum, ref_img, checked_imgs)

            run_imgs = run_df['image_name'].to_numpy()
            nan_vec = pd.isna(run_df['response_type'])
            if np.sum(nan_vec) > 0:
                """
                Document number of trials without responses for that image.
                The option 'rm_blanks' allows to exclude those trials from
                the beta averaging
                """
                blank_imgNum = run_imgs[nan_vec]
                for im_name in blank_imgNum:
                    checked_imgs[im_name]['blanks'] += 1
            if rm_blanks:
                # replace image number with 'NoResponse' when no button press recorded
                run_imgs[nan_vec] = 'NoResponse'

            img_vector += run_imgs.tolist()

    des_file.close()

    labels, counts = np.unique(img_vector, return_counts=True)
    # only include labels without blanks if rm_blanks is True
    labels = labels[labels != 'NoResponse'] # remove placeholder

    return img_vector, labels, checked_imgs


def average_betas_perImg(data_dir, sub_num, rm_blanks=False, zbetas=False):
    '''
    Step 1: create vector that labels each trial by its image
    Validate image number/name correspondance for that subject
    '''
    sessions, sess_vector, sess_file = get_sess_vector(data_dir, sub_num)
    img_vector, rep_labels, img_info = get_img_vector(
        data_dir, sub_num, sess_file, sessions, rm_blanks=rm_blanks,
    )

    '''
    Step 2: load betas from GLMsingle output file (model D)
    '''
    matfile = h5py.File(
        f"{data_dir}/things.glmsingle/sub-{sub_num}/glmsingle/output/T1w/"
        "TYPED_FITHRF_GLMDENOISE_RR.mat", 'r',
    )
    betas = np.squeeze(np.array(matfile['modelmd']))
    matfile.close()
    if zbetas:
        # normalize betas separately per voxel, across trials within session
        betas = normalize_betas(betas, sessions, sess_vector)

    '''
    Step 3: average betas and save arrays in hdf5 file
    '''
    union_mask = nib.load(
        f"{data_dir}/things.glmsingle/sub-{sub_num}/glmsingle/input/"
        f"sub-{sub_num}_task-things_space-T1w_label-brain_desc-union_mask.nii"
    )
    clean_mask = nib.load(
        f"{data_dir}/things.glmsingle/sub-{sub_num}/glmsingle/input/"
        f"sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii"
    )
    zname = 'desc-zscore_' if zbetas else ''
    subj_h5file = h5py.File(
        f"{data_dir}/things.glmsingle/sub-{sub_num}/glmsingle/output/sub-{sub_num}_"
        f"task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-imageBetas_{zname}statseries.h5",
        'w',
    )
    subj_h5file = avg_beta(
        subj_h5file, betas, img_vector, rep_labels, img_info, union_mask, clean_mask,
    )

    '''
    Step 4: add mask data to reconstruct masked & flattened betas in nibabel
    '''
    subj_h5file.create_dataset('mask_array', data=clean_mask.get_fdata())
    subj_h5file.create_dataset('mask_affine', data=clean_mask.affine)

    subj_h5file.close()


if __name__ == '__main__':
    """
    Script averages GLMsingle betas per image across repetitions for each
    subject.

    Betas are saved into a 1D array of flattened masked voxels for each image.

    The following image-specific annotations from the THINGS and THINGSplus database are
    also saved for each image: 'image_category', 'things_category_nr',
    'things_image_nr', 'categ_arousal',  'categ_concreteness',
    'categ_consistency', 'categ_nameability', 'categ_size', 'categ_wordfreq_COCA',
    'highercat27_names', 'highercat53_names', 'highercat53_num', 'img_consistency',
    'img_nameability', 'categ_manmade', 'categ_precious', 'categ_living', 'categ_heavy',
    'categ_natural', 'categ_moves', 'categ_grasp', 'categ_hold', 'categ_be_moved',
    and 'categ_pleasant'.
    """
    args = get_arguments()

    average_betas_perImg(
        args.things_dir, args.sub_num, rm_blanks=True, zbetas=args.zbetas,
    )
