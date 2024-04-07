
Descriptive analyses
================================

## Step 1. Organize image annotations in a .json for easy access

Script compiles THINGS, THINGSplus and manual annotations in a dictionary
for each image in the dataset to facilitate access during descriptive analyses.

Launch the script to compile all annotations for all subjects
```bash
DATADIR="cneuromod-things/THINGS"

python extract_annotations.py --things_dir="${DATADIR}"
```

*Input*:

- All subjects' ``things.behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-perTrial_annotation.tsv`` files.

*Output*:

- ``things.glm/task-things_imgAnnotations.json``, a dictionary with THINGS, THINGSplus and manual annotations for each image in the dataset, with image names as key.

------------------

## Step 2. Rank images per beta score within each voxel

Within each voxel, rank each dataset image according to its averaged beta score.

Launch the following script, specifying the subject number. E.g.,
```bash
DATADIR="path/to/cneuromod-things"

python rank_img_perVox.py --data_dir="${DATADIR}" --sub="01"
```

**Input**:
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-imageBetas_desc-zscore_statseries.h5``, the beta scores organized in groups whose key is the image name (e.g., 'camel_02s').
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-trialBetas_desc-zscore_statseries.h5``, the beta scores organized in nested groups whose key is the session number and sub-key is the run number.
- ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii``, the functional mask used to vectorize the brain beta scores.
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz``, the subject's noise ceiling map.
- ``fLoc/floc.rois/sub-{sub_num}/rois/task-derived/f"sub-{sub_num}_task-floc_space-T1w_stats-tscores_contrast-*_roi-*cutoff-*_nvox-*_fwhm-5_ratio-0.3_desc-unsmooth_mask.nii.gz``, ROI masks derived from the fLoc task (``sub-06_task-floc_space-T1w_stats-noiseCeil_contrast-*_roi-*_cutoff-*_nvox-100_fwhm-3_mask.nii.gz`` for ``sub-06`` who did not complete floc).


**Output**:
- ``sub-{sub_num}_task-things_desc-{perImage, perTrial}_labels.npy``, an array of image labels.
- ``sub-{sub_num}_task-things_space-T1w_stats-betas_desc-{perImage, perTrial}_statseries.npy``, an array for (image-wise or trial-wise) betas concatenated for the entire dataset.
- ``sub-{sub_num}_task-things_space-T1w_stats-ranks_desc-{perImage, perTrial}_statseries.npy``, an array for ranks to index image labels and beta scores. Within each column (voxel), indices are ordered according to the magnitude of their (trial-wise or image-wise) beta score, from smallest to largest. These ranks can be used to index image labels and beta scores in the ``*labels.npy`` and the ``*stats-betas_desc-{perImage, perTrial}_statseries.npy`` arrays. E.g., the last 10 ranks of the 3rd column (voxel) index the image labels with the highest beta scores within the 3rd voxel inside the brain mask.
- For each functional ROI identified with the fLoc task: ``sub-{sub_num}_task-things_space-T1w_{roi_name}_cutoff-{noiseceil_thresh}_nvox-{voxel_count}_stats-{ranks, betas, noiceCeilings}_desc-{perTrial, perImage}_statseries.npy``, the betas, beta rankings and noise ceilings from the 50 voxels with the highest noise ceilings within each ROI mask.


------------------

# Step 3. Ccompute metrics to generate t-SNE plots
