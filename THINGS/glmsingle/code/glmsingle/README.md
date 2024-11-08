GLMsingle Pipeline
==============================
Uses the GLMsingle library to compute trial-wise, voxel-wise beta scores for
the THINGS memory dataset

Denoising is performed with GLMdenoise, while the HRF is modelled with a
function optimized to each voxel from a library of HRF functions. Fractional
Ridge Regression is applied to regularize model parameters in a voxel-specific manner.

**Links and documentation**
- GLMsingle [repository](https://github.com/cvnlab/GLMsingle)
- GLMsingle matlab [source code](https://github.com/cvnlab/GLMsingle/blob/main/matlab/GLMestimatesingletrial.m)
- GLMsingle matlab [documentation](https://glmsingle.readthedocs.io/en/latest/matlab.html)
- GLMsingle example of an [event-related design modelling in matlab](https://github.com/cvnlab/GLMsingle/blob/main/matlab/examples/example1preview/example1.html)

------------
## Step 1. Generate task design matrices from *events.tsv files

In preparation for GLMsingle, build design matrices that identify object images
shown per trial (as task condition) from a subject's ``*events.tsv`` files.

Launch the following script, specifying the subject number. E.g.,
```bash
DATADIR="cneuromod-things/THINGS/fmriprep/sourcedata/things"
OUTDIR="cneuromod-things/THINGS/glmsingle"

python GLMsingle_makedesign.py --data_dir="${DATADIR}" --out_dir="${OUTDIR}" --sub="01"
```

**Input**:
- All of a subject's ``*_events.tsv`` files, across sessions (~36) and runs (6 per session)\
(e.g., ``sub-03_ses-17_task-things_run-02_events.tsv``)

**Output**:
- A ``sub-{sub_num}_task-things_imgDesignNumbers.json`` file that assigns
a unique number to each stimulus image seen by the participant (>4000). The number-image mapping is unique to each participant
- ``sub-{sub_num}_task-things_model-glmsingle_desc-sparse_design.h5``, a HDF5 file with one design matrix per session & run. \
Matrices are saved as lists of coordinates (onset TR, condition number) per trial
that will be used to generate sparse design matrices (TRs per run, total number of conditions) in matlab.

------------
## Step 2. Generate matrices of masked bold data from *_bold.nii.gz files

Vectorize and normalize (z-score) BOLD volumes in subject space (T1w) into masked
1D arrays to process with GLMsingle. Note that denoising is performed later
with GLMsingle.

Launch the following script for each subject
```bash
DATADIR="cneuromod-things/THINGS/fmriprep"
OUTDIR="cneuromod-things/THINGS/glmsingle"

python GLMsingle_preprocBOLD.py --data_dir="${DATADIR}" --out_dir="${OUTDIR}" --sub="01"
```

**Input**:
- All of a subject's ``*_bold.nii.gz`` files, for all sessions (~36) and runs (6 per session)
(e.g., ``sub-03_ses-10_task-things_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz``).
Note that the script can process scans in MNI or T1w space (default is T1w; use default).

**Output**:
- ``sub-{sub_num}_task-things_space-{MNI, T1w}_maskedBOLD.h5``, a HDF5 file with
one flattened matrix of dim = (voxels x time points in TRs) per session & run.
Note that the first two volumes of bold data are dropped for signal equilibrium.
- ``sub-{sub_num}_task-things_space-{MNI, T1w}_label-brain_desc-union_mask.nii``, a mask file
generated from the union of functional ``*_mask.nii.gz`` files saved along the ``*_bold.nii.gz`` files. \
Note: by default, the script processes BOLD data in subject (``T1w``) space, but
it can process data in ``MNI`` space by passing the ``--mni`` argument.

NOTE: sub-06 session 8, run 6 was corrupted (brain voxels misaligned with other
fmriprepped runs). All final analyses were redone without that run.

------------
## Step 3. Generate lists of valid runs per session for all subjects

Generate list of valid runs nested per session for each subject to import
in matlab and loop over while running GLMsingle.

Run script for all subjects
```bash
DATADIR="cneuromod-things/THINGS/glmsingle"
python GLMsingle_makerunlist.py --data_dir="${DATADIR}"
```

**Input**:
- All 4 subject's ``sub-{sub_num}_task-things_space-T1w_maskedBOLD.h5``
files produced in step 2.

**Output**:
- ``task-things_runlist.h5``, a single file of nested lists of valid runs
per session for each subject

------------
## Step 4. Run GLMsingle on _maskedBOLD.h5 and _desc-sparse_design.h5 files

Run GLMsingle in matlab to compute trialwise beta scores for each voxel within the
functional brain mask.

For the script to run, the [GLMsingle repository](https://github.com/courtois-neuromod/GLMsingle)
needs to be installed as a [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
under ``cneuromod-things/THINGS/glmsingle/code/glmsingle`` (commit ``c4e298e``).

Launch the following script for each subject, specifying the subject number,
bold volume space (``T1w``) & number of voxels per chunk as arguments
```bash
SUB_NUM="01" # 01, 02, 03, 06
BD_TYPE="T1w" # MNI, T1w
CHUNK_SZ="35000" # 35000 recommended to avoid OOM; 50000 is default

DATADIR="cneuromod-things/THINGS/glmsingle"
CODEDIR="${DATADIR}/code/glmsingle"
cd ${CODEDIR}

matlab -nodisplay -nosplash -nodesktop -r "sub_num='${SUB_NUM}';bold_type='${BD_TYPE}';chunk_size='${CHUNK_SZ}';code_dir='${CODEDIR}';data_dir='${DATADIR}';run('GLMsingle_run.m'); exit;"
```
Note: load ``StdEnv/2020``, ``nixpkgs/16.09`` and ``matlab/2020a`` modules to run on
Alliance Canada (168h job per subject, 36 CPUs per task, 5000M memory/CPU)

**Input**:
- Subject's ``sub-{sub_num}_things_model-glmsingle_desc-sparse_design.h5`` file created in Step 1.
- Subject's ``sub-{sub_num}_task-things_space-{MNI, T1w}_maskedBOLD.h5`` file created in Step 2.
- ``task-things_runlist.h5``, the file with embedded lists of valid runs per session
for all subjects created in Step 3. \
Note: the script can process scans in MNI or T1w space, to specify as an argument

**Output**:
- All the GLMsingle output files (``*.mat``) saved under ``cneuromod-things/THINGS/glmsingle/sub_{sub_num}/glmsingle/output/{T1w, MNI}``

------------

## Step 5. remove no-signal voxels from functional mask for voxelwise output

When z-scoring (per run) the BOLD data including in the functional mask used to
run the GLMsingle toolbox (union of all run functional masks), some voxels within
the mask contain NaN scores (due to low/no signal on some runs).

This script identifies the voxels with NaN z-scores and creates masks to exclude
them from downstream analyses and voxelwise derivatives.

Launch this script once to process all subjects
```bash
DATADIR="cneuromod-things/THINGS"
python GLMsingle_cleanmask.py --things_dir="${DATADIR}"
```

**Input**:
- All 4 subject's ``*bold.nii.gz`` files, for all sessions (~36) and runs (6 per session) \
(e.g., ``sub-03_ses-10_task-things_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz``)
- ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-union_mask.nii``, the
functional mask generated from the union of the functional masks of every run in Step 2.

**Output**:
- ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNaN_mask.nii``, a mask that
includes any voxel from the functional union mask with at least one normalized NaN score.
- ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii``, a functional
mask excludes any voxel with normalized NaN scores from the functional union mask.

NOTE: sub-06 session 8, run 6 was corrupted (brain voxels misaligned with other fmriprepped runs). All final analyses were redone without that run.

------------

## Step 6. Compute noise ceilings on trial-unique betas

Derive voxelwise noise ceilings from beta scores estimated with GLMsingle (model D:
FITHRF_GLMDENOISE_RR, which  identifies an optimal HRF at each voxel, derives
nuisance regressors via "GLMdenoise", and applies a custom amount of ridge
regularization at each voxel with fracridge).

The noise ceiling estimation is adapted from the [Natural Scene Dataset's datapaper methodology](https://www.nature.com/articles/s41593-021-00962-x).

**Preliminary step**:\
To leave out "blank" trials (trials with no recorded subject
response) from noise ceiling computations, trialwise performance needs to be
extracted. Run the ``behav_data_annotate.py`` script, as described under
**Trial-Wise Image Ratings and Annotations** in the ``cneuromod-things/THINGS/behaviour`` README. Output is saved as ``cneuromod-things/THINGS/behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-perTrial_annotation.tsv``.

To compute noise ceilings, launch the following script for each subject:
```bash
DATADIR="cneuromod-things/THINGS"
python GLMsingle_noiseceilings.py --things_dir="${DATADIR}" --sub_num="01"
```

**Input**:
- A subject's ``TYPED_FITHRF_GLMDENOISE_RR.mat``, a single .mat file outputted by GLMsingle (model D) in Step 4, which contains trial-unique betas per voxel
- ``task-things_runlist.h5``, a single file with nested lists of valid runs per session for each subject created in Step 3.
- A subject's ``sub-{sub_num}_task-things_model-glmsingle_desc-sparse_design.h5`` file created in Step 1.
- A subject's ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-union_mask.nii`` and
``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii`` masks created in Steps 2 and 5, respectively.
- A subject's ``cneuromod-things/THINGS/behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-perTrial_annotations.tsv``, a single .tsv file per subject with trial-wise performance metrics and image annotations created with the ``cneuromod-things/THINGS/behaviour/code/behav_data_annotate.py`` script in the above preliminary step.

**Output**:
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz``, a brain volume
of voxelwise noise ceilings estimation per voxel masked with Step 5's no-NaN mask, in subject's (T1w) EPI space.


To convert ``.nii.gz`` volume into freesurfer surface:
```bash
SUB_NUM="01"
VOLFILE="sub-${SUB_NUM}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz"
L_OUTFILE="lh.sub-${SUB_NUM}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.mgz"
R_OUTFILE="rh.sub-${SUB_NUM}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.mgz"
mri_vol2surf --src ${VOLFILE} --out ${L_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi lh
mri_vol2surf --src ${VOLFILE} --out ${R_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi rh
```

To overlay surface data onto inflated brain infreesurfer's freeview:
```bash
freeview -f $SUBJECTS_DIR/sub-${SUB_NUM}/surf/lh.inflated:overlay=lh.sub-${SUB_NUM}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.mgz:overlay_threshold=5,0 -viewport 3d
freeview -f $SUBJECTS_DIR/sub-${SUB_NUM}/surf/rh.inflated:overlay=rh.sub-${SUB_NUM}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.mgz:overlay_threshold=5,0 -viewport 3d
```

------------

## Step 7. Export betas per trial in HDF5 file

Export trialwise normalized (z-scored) beta scores estimated with GLMsingle modelD
(FITHRF_GLMDENOISE_RR) into a nested .h5 file per subject, in which betas are
organized per run within session.

Betas are saved into arrays of dim=(trials, voxels) where each row is a 1D array of
flattened voxel scores masked with the ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii`` functional mask.

Run the following script for each subject:
```bash
DATADIR="cneuromod-things/THINGS/glmsingle"
python GLMsingle_betasPerTrial.py --data_dir="${DATADIR}" --zbetas --sub_num="01"
```
Note: omit the ``--zbetas`` flag to extract raw GLMsingle betas (not z-scored)

**Input**:
- A subject's ``TYPED_FITHRF_GLMDENOISE_RR.mat``, a single .mat file outputted by GLMsingle (model D) in Step 4, which contains trial-unique betas per voxel
- ``task-things_runlist.h5``, a single file with nested lists of valid runs per session for each subject created in Step 3.
- A subject's ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-union_mask.nii`` and
``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii`` masks created in Steps 2 and 5, respectively.

**Output**:
- ``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-trialBetas_desc-zscore_statseries.h5``, a single ``.h5`` file
that contains beta scores organized in nested groups whose key is the session number and sub-key is the run number.
Betas are saved into arrays of dim=(trials, voxels) where each row is a 1D array of flattened voxel scores masked with the no-NaN functional mask. All trials are included, and rows correspond with those of the ``cneuromod-things/THINGS/fmriprep/sourcedata/things/sub-{sub_num}/ses-*/func/sub-{sub_num}_ses-*_task-things_run-*_events.tsv`` files.
- Beside the betas, the ``.h5`` file also contains the raw 3D array and 4x4 affine matrix of the no-NaN functional mask, whose dims match the input bold volumes. These two arrays (``mask_array`` and ``mask_affine``) can be used to unmask 1D beta arrays to convert them back into brain volumes (in native space).

E.g., to convert the 5th trial of the 2nd run from session 10 into a brain volume:
```python
import h5py
import nibabel as nib
from nilearn.masking import unmask

sub_num = '01'
h5file = h5py.File(f'path/to/sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-trialBetas_desc-zscore_statseries.h5', 'r')
mask = nib.nifti1.Nifti1Image(np.array(h5file['mask_array']), affine=np.array(h5file['mask_affine']))
s10_r2_t5_unmasked_betas = unmask(np.array(h5file['10']['2']['betas'])[4, :], mask)  # trials indexed from 0
```

------------
## Step 8. Export betas averaged per image in HDF5 file

Average trial-wise beta scores estimated with GLMsingle modelD (FITHRF_GLMDENOISE_RR)
per stimulus image, and save scores as one 1D arrays of flattened voxels per image in one .h5 file per subject.

The number of repetitions, and the number of blank trials (no recorded button press), are also saved with each image's mean voxel-wise betas. Note that blank trials are excluded from the image-wise signal averaging.

The script also performs validations on trial-wise metrics from ``*events.tsv`` files, subject-specific image-to-number mappings, and the design matrices given to GLMsingle.

Launch the following script for each subject
```bash
DATADIR="cneuromod-things/THINGS"
python GLMsingle_betasPerImg.py --things_dir="${DATADIR}" --zbetas --sub_num="01"
```

**Input**:
- A subject's ``TYPED_FITHRF_GLMDENOISE_RR.mat``, a single .mat file outputted by GLMsingle (model D) in Step 4, which contains trial-unique betas per voxel
- ``task-things_runlist.h5``, a single file with nested lists of valid runs per session for each subject created in Step 3.
- ``sub-{sub_num}_task-things_imgDesignNumbers.json``, a file created in Step 1 that assigns a unique number to each stimulus image seen by the participant (>4000)
- A subject's ``sub-{sub_num}_task-things_model-glmsingle_desc-sparse_design.h5`` file created in Step 1
- A subject's ``cneuromod-things/THINGS/behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-perTrial_annotation.tsv``, a single .tsv file per subject with trial-wise performance metrics and image annotations created with the ``cneuromod-things/THINGS/behaviour/code/behav_data_annotate.py`` (see Step 6).
- A subject's ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-union_mask.nii`` and
``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii`` masks created in Steps 2 and 5, respectively.

**Output**: \
``sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-imageBetas_desc-zscore_statseries.h5``, a file that contains beta scores organized in groups whose key is the image name (e.g., 'camel_02s'). Under each image, each group includes:
- 'betas': the betas averaged per image (up to 3 repetitions, excluding trials with no answer), saved as a 1D array of flattened voxels masked with the no-NaN functional mask.
- ``num_reps``: the number of image repetitions included in the averaging.
- ``blank``: the number of trials with no recorded answers (no button press)
Note that, because blank trials were excluded, an image shown three times for which no answer was captured on one of those trials will have ``rep_num = 2``, and ``blank = 1`` (the sum of ``blank`` and ``rep_num`` should equal the total number of times an image was shown.

The .h5 file also includes:
- the raw 3D array and 4x4 affine matrix of the no-NaN functional mask, whose dims match the input bold volumes. These two arrays (``mask_array`` and ``mask_affine``) can be used to unmask 1D beta arrays to convert them back into brain volumes (in native space). \
E.g.,
```python
import h5py
import nibabel as nib
from nilearn.masking import unmask

sub_num = '01'
h5file = h5py.File(f'path/to/sub-{sub_num}_model-fitHrfGLMdenoiseRR_stats-imageBetas_desc-zscore_statseries.h5', 'r')
mask = nib.nifti1.Nifti1Image(np.array(h5file['mask_array']), affine=np.array(h5file['mask_affine']))
velcro_04s_unmasked_betas = unmask(np.array(h5file['velcro_04s']['betas']), mask)
```
