import glob, os, json
import argparse, subprocess

import h5py
import nibabel as nib
import numpy as np
import pandas as pd
from scipy.stats import zscore
from tqdm import tqdm

from nilearn.masking import unmask, apply_mask, intersect_masks
from nilearn.signal import clean
from nilearn.image import smooth_img
from nilearn.interfaces.fmriprep import load_confounds
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix


def get_arguments():
    parser = argparse.ArgumentParser(
        description="First-level analysis of fLoc data with nilearn",
    )
    parser.add_argument(
        '--fLoc_dir',
        required=True,
        type=str,
        help='absolute path to dataset directory that contains bold.nii.gz files'
    )
    parser.add_argument(
        '--out_dir',
        required=True,
        type=str,
        help='absolute path to directory where output .h5 file is saved',
    )
    parser.add_argument(
        '--smooth',
        action='store_true',
        default=False,
        help='if true, apply smoothing to BOLD data',
    )
    parser.add_argument(
        '--mni',
        action='store_true',
        default=False,
        help='if true, analyse BOLD files in MNI space; default is T1w space'
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number',
    )
    return parser.parse_args()


def qc_mask_voxels(bold_files, umask, data_space, out_dir, sub_num, mni):
    nan_masks = []
    notnan_masks = []

    for i in tqdm(range(len(bold_files)), desc='QCing bold files'):
        meanz_vals = np.mean(zscore(apply_mask(nib.load(bold_files[i]), umask, dtype=np.single)), axis=0)
        nan_masks.append(unmask(np.isnan(meanz_vals), umask))
        notnan_masks.append(unmask(~np.isnan(meanz_vals), umask))

    global_nan_mask = intersect_masks(nan_masks, threshold=0, connected=False)
    global_goodval_mask = intersect_masks(notnan_masks, threshold=1, connected=False)

    # check that all voxels are within functional mask
    assert np.sum(umask.get_fdata() * global_goodval_mask.get_fdata()) == np.sum(global_goodval_mask.get_fdata())
    assert np.sum(umask.get_fdata() * global_nan_mask.get_fdata()) == np.sum(global_nan_mask.get_fdata())

    # check that all mask voxels are assigned
    mask_size = np.sum(umask.get_fdata())
    assert np.sum(global_nan_mask.get_fdata() + global_goodval_mask.get_fdata()) == mask_size

    nib.save(
        global_nan_mask,
        f"{out_dir}/sub-{sub_num}/glm/sub-{sub_num}_task-things_space-{data_space}_label-brain_desc-unionNaN_mask.nii",
    )
    nib.save(
        global_goodval_mask,
        f"{out_dir}/sub-{sub_num}/glm/sub-{sub_num}_task-things_space-{data_space}_label-brain_desc-unionNonNaN_mask.nii",
    )

    return global_goodval_mask


def prepare_data(args):
    '''
    Generate a mask from the union of brain voxels across sessions and runs.
    Exclude voxels with no signal variability.
    '''
    sub_num = args.sub_num
    out_dir = args.out_dir
    if args.mni:
        mask_suffix = '_space-MNI152NLin2009cAsym_desc-brain_part-mag_mask.nii.gz'
        bold_suffix = '_space-MNI152NLin2009cAsym_desc-preproc_part-mag_bold.nii.gz'
        data_space = "MNI152NLin2009cAsym"
    else:
        mask_suffix = '_space-T1w_desc-brain_part-mag_mask.nii.gz'
        bold_suffix = '_space-T1w_desc-preproc_part-mag_bold.nii.gz'
        data_space = "T1w"

    mask_list = sorted(
        glob.glob(
            f"{args.fLoc_dir}/sub-{sub_num}/ses-*/func/*{mask_suffix}"
        )
    )
    umask = intersect_masks(mask_list, threshold=0)

    bold_files = sorted(
        glob.glob(
            f"{args.fLoc_dir}/sub-{sub_num}/ses-*/func/*{bold_suffix}"
        )
    )

    clean_mask = qc_mask_voxels(
        bold_files, umask, data_space, out_dir, sub_num, args.mni,
    )

    TRs_per_run = 152 # 155 - 3 after removing first three volumes
    tr = 1.49
    frame_times = np.arange(TRs_per_run) * tr
    cat_labels = [
        'adult', 'body', 'car',
        'corridor', 'house', 'instrument',
        'limb', 'word', 'baseline',
    ]

    subj_design = h5py.File(
        f"{out_dir}/sub-{sub_num}/glm/sub-{sub_num}_task-floc_model-GLM_design.h5",
        'r',
    )

    bold_list = []
    design_list = []
    for bold_path in tqdm(bold_files, desc='building data and design matrices'):
        chunks = os.path.basename(bold_path).split('_')
        ses_num = chunks[1][-2:]
        run_num = f'{int(chunks[3][-1]):02}'

        try:
            temp_bold = f"{out_dir}/sub-{sub_num}/glm/{os.path.basename(bold_path).replace('_part-mag', '')}"
            conf_path = bold_path.replace(
                "_space-T1w_desc-preproc_part-mag_bold.nii.gz",
                "_desc-confounds_part-mag_timeseries.tsv",
            )
            temp_conf = f"{out_dir}/sub-{sub_num}/glm/{os.path.basename(conf_path).replace('_part-mag', '')}"
            subprocess.run(
                f"cp {conf_path} {temp_conf}", shell = True,
                executable="/bin/bash",
            )
            confounds, sample_mask = load_confounds(
                [temp_bold],
                strategy=["high_pass", "motion", "wm_csf", "global_signal"],
                motion="basic", wm_csf="basic", global_signal="basic",
            )
            subprocess.run(
                f"rm -f {temp_conf}", shell = True,
                executable="/bin/bash",
            )
            niifile = nib.load(bold_path)

            # Remove first 3 volumes of each run
            niifile = unmask(
                apply_mask(niifile, clean_mask, dtype=np.single)[3:155, :],
                clean_mask,
            )
            bold_list.append(niifile)

            events_df = pd.DataFrame(
                np.array(subj_design[ses_num][run_num]['onset']),
                columns = ['onset'],
            )
            events_df.insert(
                loc=1,
                column='duration',
                value=np.array(subj_design[ses_num][run_num]['duration']),
                allow_duplicates=True,
            )
            events_df.insert(
                loc=2,
                column='trial_type',
                value=np.array(subj_design[ses_num][run_num]['trial_type']).astype(str),
                allow_duplicates=True,
            )
            design_matrix = make_first_level_design_matrix(
                frame_times,
                events_df,
                add_regs=confounds.iloc[3:155, :],
                drift_model='cosine',
                hrf_model = 'spm',
                high_pass = .01,
            )
            '''
            No run includes all 8 subconditions;
            this process makes sure all design matrices have the
            same columns across runs
            '''
            dm_labels = list(design_matrix.columns)
            for cat_label in cat_labels:
                if cat_label not in dm_labels:
                    design_matrix.insert(loc=0, column=cat_label, value=0.0, allow_duplicates=True)
            design_matrix = design_matrix[cat_labels + dm_labels[6:]]

            design_list.append(design_matrix)

        except:
            print('something went wrong loading session ' + str(ses_num) + ', run ' + run_num)

    subj_design.close()

    return bold_list, design_list, clean_mask


# Function from: https://nilearn.github.io/stable/auto_examples/04_glm_first_level/plot_fiac_analysis.html#sphx-glr-auto-examples-04-glm-first-level-plot-fiac-analysis-py
def pad_vector(contrast_, n_columns):
    """A small routine to append zeros in contrast vectors"""
    return np.hstack((contrast_, np.zeros(n_columns - len(contrast_))))


def run_glm(fmri_img, design_matrices, mask, args):
    sub_num = args.sub_num
    out_dir = args.out_dir

    hrf_model = 'spm' #'spm + derivative'  # The hemodynamic response function is the SPM canonical one.
    smoothing_fwhm = 5 if args.smooth else None

    fmri_glm = FirstLevelModel(
        t_r=1.49, slice_time_ref=0., noise_model='ar1',
        standardize=True, mask_img=mask, drift_model='cosine',
        high_pass=.01, smoothing_fwhm=smoothing_fwhm, hrf_model=hrf_model,
    )
    fmri_glm = fmri_glm.fit(fmri_img, design_matrices=design_matrices)

    n_columns = design_matrices[0].shape[1]
    """
    cat_labels = ['adult', 'body', 'car', 'corridor', 'house',
                  'instrument', 'limb', 'word', 'baseline']
    """
    contrasts = {'faces': pad_vector([7, -1, -1, -1, -1, -1, -1, -1], n_columns),
                 'bodies': pad_vector([-1, 3, -1, -1, -1, -1, 3, -1], n_columns),
                 'characters': pad_vector([-1, -1, -1, -1, -1, -1, -1, 7], n_columns),
                 'objects': pad_vector([-1, -1, 3, -1, -1, 3, -1, -1], n_columns),
                 'places': pad_vector([-1, -1, -1, 3, 3, -1, -1, -1], n_columns),
                 'faceMinObject': pad_vector([2, 0, -1, 0, 0, -1, 0, 0, 0], n_columns),
                 'sceneMinObject': pad_vector([0, 0, -1, 1, 1, -1, 0, 0, 0], n_columns),
                 'bodyMinObject': pad_vector([0, 1, -1, 0, 0, -1, 1, 0, 0], n_columns),
                 'objectMinRest': pad_vector([0, 0, 1, 0, 0, 1, 0, 0, -2], n_columns)
                 }

    data_space = 'MNI152NLin2009cAsym' if args.mni else 'T1w'
    if args.smooth:
        out_space += '_sm'

    for index, (c_id, contrast_val) in tqdm(enumerate(contrasts.items()), desc='computing and exporting contrasts'):
        t_map = fmri_glm.compute_contrast(
            contrast_val, output_type='stat', stat_type='t'
        )
        t_map.to_filename(
            f"{out_dir}/sub-{sub_num}/glm/sub-{sub_num}_task-floc_"
            f"space-{data_space}_model-GLM_stats-tscores_desc-{c_id}_statseries.nii.gz",
        )
        effect_size = fmri_glm.compute_contrast(
            contrast_val, output_type='effect_size',
        )
        effect_size.to_filename(
            f"{out_dir}/sub-{sub_num}/glm/sub-{sub_num}_task-floc_"
            f"space-{data_space}_model-GLM_stats-betas_desc-{c_id}_statseries.nii.gz",
        )


if __name__ == '__main__':
    '''
    Performs first-level analysis to obtain category specific t-scores &
    betas for fLoc task. Requires design matrices created with
    fLOC_makedesign.py script
    '''
    args = get_arguments()

    bold, design, mask = prepare_data(args)
    run_glm(bold, design, mask, args)
