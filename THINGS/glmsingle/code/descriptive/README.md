
Descriptive analyses
================================

## Step 1. Organize image annotations in a .json for easy access

This script compiles THINGS, THINGSplus and manual annotations in a dictionary
for each image in the dataset to facilitate access during descriptive analyses.

Launch the script to compile all annotations for all subjects
```bash
DATADIR="cneuromod-things/THINGS"

python extract_annotations.py --things_dir="${DATADIR}"
```

*Input*:

- All subjects' ``THINGS/behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-perTrial_annotation.tsv`` files.

*Output*:

- ``THINGS/glmsingle/task-things_imgAnnotations.json``, a dictionary with THINGS, THINGSplus and manual annotations for each image in the dataset, with image names as key.

------------------

## Step 2. Rank images per beta score within each voxel

Within each voxel, this script ranks each dataset image according to its beta score, either per trial or per image (averaged across multiple repetitions; betas were estimated using GLM single).

Launch the following script, specifying the subject number. E.g.,
```bash
DATADIR="path/to/cneuromod-things"

python rank_img_perVox.py --data_dir="${DATADIR}" --sub="01"
```

**Input**:
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-imageBetas_desc-zscore_statseries.h5``, the GLM single beta scores organized in groups whose key is the image name (e.g., 'camel_02s').
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-trialBetas_desc-zscore_statseries.h5``, the GLM single beta scores organized in nested groups whose key is the session number and sub-key is the run number.
- ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii``, the functional mask used to vectorize the brain beta scores.
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz``, the subject's noise ceiling map derived from the THINGS task.
- ``fLoc/floc.rois/sub-{sub_num}/rois/task-derived/f"sub-{sub_num}_task-floc_space-T1w_stats-tscores_contrast-*_roi-*cutoff-*_nvox-*_fwhm-5_ratio-0.3_desc-unsmooth_mask.nii.gz``, ROI masks derived from the fLoc task (``sub-06_task-floc_space-T1w_stats-noiseCeil_contrast-*_roi-*_cutoff-*_nvox-100_fwhm-3_mask.nii.gz`` for ``sub-06`` who did not complete fLoc).


**Output**:
- ``sub-{sub_num}_task-things_space-T1w_stats-betas_desc-{perImage, perTrial}_statseries.npy``, an array of (image-wise or trial-wise) betas concatenated for the entire dataset.
- ``sub-{sub_num}_task-things_desc-{perImage, perTrial}_labels.npy``, an array of corresponding image labels for the beta scores.
- ``sub-{sub_num}_task-things_space-T1w_stats-ranks_desc-{perImage, perTrial}_statseries.npy``, an array of ranked indices that index image labels and beta scores. Within each column (voxel), indices are ordered according to the magnitude of their (trial-wise or image-wise) beta score, from smallest to largest. These ranks can be used to index image labels and beta scores in the ``*labels.npy`` and the ``*stats-betas_desc-{perImage, perTrial}_statseries.npy`` arrays. E.g., the last 10 ranks of the 3rd column (voxel) index the image labels with the highest beta scores within the 3rd voxel inside the brain mask.
- For each functional ROI identified with the fLoc task: ``sub-{sub_num}_task-things_space-T1w_{roi_name}_cutoff-{noiseceil_thresh}_nvox-{voxel_count}_stats-{ranks, betas, noiseCeilings}_desc-{perTrial, perImage}_statseries.npy``, the betas, ranked indices and noise ceilings of the 50 voxels with the highest noise ceilings within each ROI mask.


------------------

## Step 3. Perform data reduction on beta scores per ROI

This script performs scaling on beta scores from low- and high-level visual ROIs identified with fLoc and retinotopy. This step is required to project trials and image stimuli into a lower dimensional space, e.g., to generate t-SNE plots that reflect the structure of stimulus representation within ROIs.

Launch the following script, specifying the subject number. Run the script with and without the ``--perImg`` flag to perform data reduction per trial and then per stimulus image. \
E.g.,
```bash
DATADIR="path/to/cneuromod-things"

python beta_scaling.py --data_dir="${DATADIR}" --sub="01"
python beta_scaling.py --data_dir="${DATADIR}" --perImg --sub="01"
```

**Input**:
- ``sub-{sub_num}_task-things_space-T1w_stats-betas_desc-{perImage, perTrial}_statseries.npy``, an array of (image-wise or trial-wise) betas concatenated for the entire dataset (generated in Step 2 above).
- ``sub-{sub_num}_task-things_desc-{perImage, perTrial}_labels.npy``, the betas' corresponding image labels (generated in Step 2 above).
- ``THINGS/glmsingle/sub-{sub_num}/glmsingle/input/sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii``, the functional brain mask used to generate the beta arrays.
- ``fLoc/rois/sub-{sub_num}/rois/task-derived/sub-{sub_num}_task-floc_space-T1w_stats-tscores_contrast-{face_roi-FFA, face_roi-OFA, scene_roi-MPA, scene_roi-OPA, scene_roi-PPA}_cutoff-*_desc-unsmooth_mask.nii.gz``, masks of above-threshold voxels (based on fLoc contrasts) contained within ROI masks from the Kanwisher group.
- ``fLoc/rois/sub-{sub_num}/rois/task-derived/sub-{sub_num}_task-floc_space-T1w_stats-tscores_contrast-{faces, bodies, places}_cutoff-3.72_desc-unsmooth_mask.nii.g``, masks of above-threshold voxels (t > 3.72) on fLoc contrasts (faces, bodies and places) contained within their respective set of Kanwisher parcels (face, body or scene).
- ``fLoc/rois/sub-{sub_num}/glm/sub-{sub_num}_task-floc_space-T1w_model-GLM_stats-tscores_contrast-{faces, bodies, places}_desc-unsmooth_statseries.nii.gz``, t-scores for the faces, bodies and places contrasts derived from the fLoc task (NSD-style contrasts).
- ``fLoc/rois/sub-{sub_num}/rois/from_atlas/sub-{sub_num}_parcel-kanwisher_space-T1w_contrast-{c[0]}_mask.nii``, group-derived parcels from the Kanwisher group warped to single-subject space.
- ``retinotopy/prf/sub-{sub_num}/rois/sub-{sub_num}_task-retinotopy_space-T1w_res-func_model-npythy_label-{V1, V2, V3}_desc-nn_mask.nii.gz``, masks of visual areas V1, V2 and V3 derived from retinotopy data and group priors with NeuroPythy.
- ``THINGS/glmsingle/sub-{sub_num}/glmsingle/output/sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz``, maps of voxelwise noise ceilings derived from the THINGS task.


**Output**:
``sub-{sub_num}_task-things_space-T1w_stats-tSNE_label-visualROIs_desc-{perImage, perTrial}_statseries.npz``, a collection of numpy arrays that contain t-SNE components (and their corresponding labels) derived from voxel beta scores (per trial or per image) contained within the following visual ROIs:
- face-sensitive regions FFA and OFA
- scene-sensitive regions PPA, MPA and OPA
- low-level visual areas V1, V2 and V3
- the union of face, body and scene-sensitive voxels (selected at two different thresholds: t > 2.5 and t > 3.72) contained within their corresponding set of Kanwisher parcels.
- a collection of brain voxels with the highest noise ceilings derived from the THINGS task (no spatial contiguity requirement)
The output file also contains the number of voxels in each ROI mask, as a reference.
