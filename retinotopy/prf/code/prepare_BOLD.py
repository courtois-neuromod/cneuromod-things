import os, glob, json
import numpy as np
import nibabel as nib
import nilearn
from nilearn.signal import clean
from nilearn.masking import apply_mask, intersect_masks, unmask
from nilearn.image import resample_to_img
from nilearn.image.image import mean_img, smooth_img
from nilearn.plotting import view_img
from load_confounds import Minimal
from skimage.transform import resize

from scipy.io import loadmat, savemat
import argparse


def get_arguments():

    parser = argparse.ArgumentParser(
        description='Denoise, flatten, average and chunk bold response across retino sessions'
    )
    parser.add_argument(
        '--dir_path',
        required=True,
        type=str,
        help='absolute path to cneuromod-things repo)'
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number',
    )
    args = parser.parse_args()

    return args


def make_mask(dir_path, sub):
    '''
    Build a single-subject whole-brain mask with a conjunction of each run's
    epi mask and of the (smoothed) grey matter mask outputed with fmriprep
    based on freesurfer.

    Within this mask, exclude voxels that lack signal (their normalized signal is NaN).
    To use the analyzepRF toolbox, the number of voxels must be the same across
    all tasks and sessions
    '''
    # mean epi mask
    mask_list = sorted(
        glob.glob(
            f"{dir_path}/retinotopy/fmriprep/{sub}/ses-0*/func/"
            f"{sub}_ses-0*_task-*_space-T1w_desc-brain_part-mag_mask.nii.gz",
        )
    )
    # 0 threshold = union, 1 threshold = intersection; accept any voxel included in either mask
    mean_epi_mask = intersect_masks(mask_list, threshold=0.3)

    # grey matter (anat) segmentation mask
    gm_mask = nib.load(
        f"{dir_path}/anatomical/smriprep/{sub}/anat/{sub}_label-GM_probseg.nii.gz"
    )
    gm_mask_rs = smooth_img(imgs=resample_to_img(
        gm_mask,
        mean_epi_mask,
        interpolation='linear',
    ), fwhm=3)
    gm_mask = nib.nifti1.Nifti1Image(
        (gm_mask_rs.get_fdata() > 0.15).astype('float'),
        affine=gm_mask_rs.affine,
    )
    subject_mask = intersect_masks([gm_mask, mean_epi_mask], threshold=0.0)

    #nib.save(
    #    subject_mask,
    #    f"{dir_path}/retinotopy/prf/{sub}/prf/input/"
    #    f"{sub}_task-retinotopy_space-T1w_label-brain_desc-union_mask.nii",
    #)

    """
    Remove voxels with no signal from subject's brain mask
    """
    bold_files = sorted(
        glob.glob(
            f"{dir_path}/retinotopy/fmriprep/{sub}/ses-0*/func/"
            f"{sub}_ses-0*_task-*_space-T1w_desc-preproc_part-mag_bold.nii.gz",
        )
    )

    nan_masks = []
    notnan_masks = []

    for i in tqdm(range(len(bold_files)), desc='QCing bold files'):
        meanz_vals = np.mean(
            zscore(apply_mask(nib.load(bold_files[i]), subject_mask, dtype=np.single)),
            axis=0,
        )
        nan_masks.append(unmask(np.isnan(meanz_vals), subject_mask))
        notnan_masks.append(unmask(~np.isnan(meanz_vals), subject_mask))

    nan_mask = intersect_masks(nan_masks, threshold=0, connected=False)
    clean_mask = intersect_masks(notnan_masks, threshold=1, connected=False)

    # check that all voxels are within functional mask
    assert np.sum(subject_mask.get_fdata() * clean_mask.get_fdata()) == np.sum(clean_mask.get_fdata())
    assert np.sum(subject_mask.get_fdata() * nan_mask.get_fdata()) == np.sum(nan_mask.get_fdata())

    # check that all mask voxels are assigned
    mask_size = np.sum(subject_mask.get_fdata())
    assert np.sum(nan_mask.get_fdata() + clean_mask.get_fdata()) == mask_size

    nib.save(
        nan_mask,
        f"{dir_path}/retinotopy/prf/{sub}/prf/input/"
        f"{sub}_task-retinotopy_space-T1w_label-brain_desc-unionNaN_mask.nii",
    )
    nib.save(
        clean_mask,
        f"{dir_path}/retinotopy/prf/{sub}/prf/input/"
        f"{sub}_task-retinotopy_space-T1w_label-brain_desc-unionNonNaN_mask.nii",
    )

    return clean_mask


def flatten_epi(dir_path, sub, epi_mask):

    task_list = ['wedges', 'rings', 'bars']

    epilist_per_task = []
    confounds_per_task = []
    sub_affine = None

    for task in task_list:
        scan_list = sorted(glob.glob(os.path.join(dir_path, 'data', 'temp_bold', sub + '*' + task + '_space-T1w_desc-preproc_part-mag_bold.nii.gz')))
        flatbold_list = []

        sess_num = 1

        for scan in scan_list:

            if sub_affine is None:
                sub_affine = nib.load(scan).affine

            epi = nib.load(scan)
            assert np.sum(epi.affine == sub_affine) == 16
            print(epi.shape) # (76, 90, 71, 202) = x, y, z, time (TR)
            assert epi.shape[-1] == 202

            flat_bold = apply_mask(imgs=epi, mask_img=sub_mask) # shape: (time, vox)

            # extract epi's confounds
            confounds = Minimal(global_signal='basic').load(scan[:-20] + 'bold.nii.gz')

            # Detrend and normalize flattened data
            # note: signal.clean takes (time, vox) shaped input
            flat_bold_dt = clean(flat_bold, detrend=True, standardize='zscore',
                                 standardize_confounds=True, t_r=None, confounds=confounds, ensure_finite=True).T # shape: vox per time

            # Remove first 3 volumes of each run
            flat_bold_dt = flat_bold_dt[:, 3:]

            if per_session:
                savemat(os.path.join(dir_path, 'output', 'detrend', sub + '_epi_FULLbrain_' + task + '_sess' + str(sess_num) +'.mat'), {sub + '_' + task : flat_bold_dt})
            else:
                flatbold_list.append(flat_bold_dt)

            sess_num += 1

        if not per_session:
            mean_bold = np.mean(np.array(flatbold_list), axis=0) # shape: voxel per time

            # provides the data as a cell vector of voxels x time. For K.Kay's toolbox, it can also be X x Y x Z x time
            print(mean_bold.shape)
            savemat(os.path.join(dir_path, 'output', 'detrend', sub + '_epi_FULLbrain_' + task + '.mat'), {sub + '_' + task : mean_bold})


if __name__ == '__main__':
    '''
    Script takes runs of bold.nii.gz files, detrends them,
    averages them per task across session, masks and flattens them and exports
    them into .mat files

    It also resizes visual stimuli (apertures) to reduce processing time with analyzePRF
    (by reducing the number of pixels to explore)
    '''
    args = get_arguments()

    epi_mask = make_mask(args.dir_path, f"sub-{args.sub}")
    flatten_epi(args.dir_path, f"sub-{args.sub}", epi_mask)
