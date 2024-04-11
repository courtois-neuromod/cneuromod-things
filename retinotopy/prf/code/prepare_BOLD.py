import os, glob, json
import argparse

from load_confounds import Minimal
import nibabel as nib
from nilearn.signal import clean
from nilearn.masking import apply_mask, intersect_masks, unmask
from nilearn.image import resample_to_img
from nilearn.image.image import smooth_img
import numpy as np
from scipy.io import savemat
from scipy.stats import zscore
from tqdm import tqdm


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
        '--chunk_size',
        default=240,
        type=int,
        help='number of voxels per chunk',
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


def flatten_epi(dir_path, sub, chunk_size, sub_mask):

    out_dir = f"{dir_path}/retinotopy/prf/{sub}/prf/input/"
    task_list = ['wedges', 'rings', 'bars']

    sub_affine = None
    for task in task_list:
        scan_list = sorted(
            glob.glob(
                f"{dir_path}/retinotopy/fmriprep/{sub}/ses-0*/func/"
                f"{sub}_ses-0*_task-{task}_space-T1w_desc-preproc_part-mag_bold.nii.gz",
            )
        )

        flatbold_list = []
        for scan in scan_list:

            epi = nib.load(scan)
            assert epi.shape[-1] == 202
            if sub_affine is None:
                sub_affine = epi.affine
            else:
                assert np.sum(epi.affine == sub_affine) == 16

            # dim = (time, vox)
            flat_bold = apply_mask(imgs=epi, mask_img=sub_mask)

            # extract epi's confounds
            temp_bold = f"{out_dir}/{os.path.basename(scan).replace('_part-mag', '')}"
            conf_path = scan.replace(
                "_space-T1w_desc-preproc_part-mag_bold.nii.gz",
                "_desc-confounds_part-mag_timeseries.tsv",
            )
            temp_conf = f"{out_dir}/{os.path.basename(conf_path).replace('_part-mag', '')}"
            subprocess.run(
                f"cp {conf_path} {temp_conf}", shell = True,
                executable="/bin/bash",
            )
            confounds = Minimal(
                global_signal='basic').load(temp_bold)
            subprocess.run(
                f"rm -f {temp_conf}", shell = True,
                executable="/bin/bash",
            )

            """
            Detrend and normalize flattened data
            Note: signal.clean takes (time, vox) shaped input
            """
            flat_bold_dt = clean(
                flat_bold,
                detrend=True,
                standardize='zscore',
                standardize_confounds=True,
                t_r=None,
                confounds=confounds,
                ensure_finite=True,
            ).T # dim = (vox, time)

            # Remove first 3 volumes of each run
            flatbold_list.append(flat_bold_dt[:, 3:])

        '''
        Save the data as a cell vector of voxels x time.
        For K.Kay's toolbox, it can also be X x Y x Z x time

        Number of voxels within "clean" brain mask, per participant
        sub-01: 205455 voxels (w inclusive full brain mask, no NaN)
        sub-02: 221489 voxels (w inclusive full brain mask, no NaN)
        sub-03: 197945 voxels (w inclusive full brain mask, no NaN)
        sub-05: ? voxels (w inclusive full brain mask, no NaN)
        '''

        mean_bold = np.mean(np.array(flatbold_list), axis=0)  # dim= (vox, time)
        #savemat(
        #    f"{dir_path}/retinotopy/prf/{sub}/prf/input/"
        #    f"{sub}_task-retinotopy_condition-{task}_space-T1w_label-brain_bold.mat",
        #    {f"{sub}_"task" : mean_bold},
        #)

        num_vox = mean_bold.shape[0]
        chunk_path = f"{dir_path}/retinotopy/prf/{sub}/prf/input/chunks"
        Path(chunk_path).mkdir(parents=True, exist_ok=True)
        file_path = f"{chunk_path}/{sub}_task-retinotopy_condition-{task}_space-T1w_desc-chunk%04d_bold.mat"

        for i in range(int(np.ceil(num_vox/chunk_size))):
            savemat(
                file_path % i,
                {f"sub{sub[-2:]}_{task}": mean_bold[i*chunk_size:(i+1)*chunk_size, :]}
            )


if __name__ == '__main__':
    '''
    Script takes runs of bold.nii.gz files, flattens them, detrends them,
    averages them per task across sessions, chunks them into vectorized segments
    of lenght = chunk_size, and exports them into .mat files
    '''
    args = get_arguments()

    epi_mask = make_mask(args.dir_path, f"sub-{args.sub}")
    flatten_epi(args.dir_path, f"sub-{args.sub}", args.chunk_size, epi_mask)
