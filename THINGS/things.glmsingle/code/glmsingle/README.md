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
DATADIR="cneuromod-things/THINGS/things.fmriprep/sourcedata/things"
OUTDIR="cneuromod-things/THINGS/things.glmsingle"

python GLMsingle_makedesign.py --data_dir="${DATADIR}" --out_dir="${OUTDIR}" --sub="01"
```

**Input**:
- All of a subject's ``*_events.tsv`` files, across sessions (~36) and runs (6 per session)\
(e.g., ``sub-03_ses-17_task-things_run-02_events.tsv``)

**Output**:
- A ``sub-{sub_num}_task-things_desc-image-design-refnumbers.json`` file that assigns
a unique number to each stimulus image seen by the participant (>4000). The number-image mapping is unique to each participant
- ``sub-{sub_num}_task-things_sparsedesign.h5``, a HDF5 file with one design matrix per session & run. \
Matrices are saved as lists of coordinates (onset TR, condition number) per trial
that will be used to generate sparse design matrices (TRs per run, total number of conditions) in matlab.

------------
## Step 2. Generate matrices of masked bold data from *_bold.nii.gz files

Vectorize and normalize (z-score) BOLD volumes in subject space (T1w) into masked
1D arrays to process with GLMsingle. Note that denoising is performed later
with GLMsingle.

Launch the following script for each subject
```bash
DATADIR="cneuromod-things/THINGS/things.fmriprep"
OUTDIR="cneuromod-things/THINGS/things.glmsingle"

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
- ``sub-{sub_num}_task-things_space-{MNI, T1w}_desc-func-union_mask.nii``, a mask file
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
DATADIR="cneuromod-things/THINGS/things.glmsingle"
python GLMsingle_makerunlist.py --data_dir="${DATADIR}"
```

**Input**:
- All 4 subject's ``sub-{sub_num}_task-things_space-T1w_maskedBOLD.h5``
files produced in step 2.

**Output**:
- ``task-things_desc-runlist.h5``, a single file of nested lists of valid runs
per session for each subject

------------
## Step 4. Run GLMsingle on _maskedBOLD.h5 and _sparsedesign.h5 files

Run GLMsingle in matlab to compute trialwise beta scores for each voxel within the
functional brain mask.

For the script to run, the [GLMsingle repository](https://github.com/courtois-neuromod/GLMsingle)
needs to be installed as a [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
under ``cneuromod-things/THINGS/things.glmsingle/code/glmsingle`` (commit ``c4e298e``).

Launch the following script for each subject, specifying the subject number,
bold volume space (``T1w``) & number of voxels per chunk as arguments
```bash
SUB_NUM="01" # 01, 02, 03, 06
BD_TYPE="T1w" # MNI, T1w
CHUNK_SZ="35000" # 35000 recommended to avoid OOM; 50000 is default

DATADIR="cneuromod-things/THINGS/things.glmsingle"
CODEDIR="${DATADIR}/code/glmsingle"
cd ${CODEDIR}

matlab -nodisplay -nosplash -nodesktop -r "sub_num='${SUB_NUM}';bold_type='${BD_TYPE}';chunk_size='${CHUNK_SZ}';code_dir='${CODEDIR}';data_dir='${DATADIR}';run('GLMsingle_run.m'); exit;"
```
Note: load ``StdEnv/2020``, ``nixpkgs/16.09`` and ``matlab/2020a`` modules to run on
Alliance Canada (168h job per subject, 36 CPUs per task, 5000M memory/CPU)

**Input**:
- Subject's ``sub-{sub_num}_things_sparsedesign.h5`` file created in Step 1.
- Subject's ``sub-{sub_num}_task-things_space-{MNI, T1w}_maskedBOLD.h5`` file created in Step 2.
- ``task-things_desc-runlist.h5``, the file with embedded lists of valid runs per session
for all subjects created in Step 3. \
Note: the script can process scans in MNI or T1w space, to specify as an argument

**Output**:
- All the GLMsingle output files (``*.mat``) saved under ``cneuromod-things/THINGS/things.glmsingle/sub_{sub_num}/GLMsingle/output/{T1w, MNI}``

------------

## Step 5. Create clean functional mask for voxelwise output

When z-scoring (per run) the BOLD data including in the functional mask used to
run the GLMsingle toolbox (union of all run functional masks), some voxels within
the mask contain NaN scores (due to low/no signal on some runs).

This script identifies the voxels with NaN scores and creates masks to exclude
them from downstream analyses and voxelwise derivatives.

Launch this script once to process all subjects
```bash
DATADIR="cneuromod-things/THINGS"
python GLMsingle_cleanmask.py --things_dir="${DATADIR}"
```

**Input**:
- All 4 subject's ``*bold.nii.gz`` files, for all sessions (~36) and runs (6 per session) \
(e.g., ``sub-03_ses-10_task-things_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz``)
- ``sub-{sub_num}_task-things_space-T1w_desc-func-union_mask.nii``, the
functional mask generated from the union of the functional masks of every run in Step 2.

**Output**:
- ``sub-{sub_num}_task-things_space-T1w_desc-NaNvals_mask.nii``, a mask that
includes any voxel from the functional union mask with at least one normalized NaN score.
- ``sub-{sub_num}_task-things_space-T1w_desc-func-clean_mask.nii``, a functional
mask excludes any voxel with normalized NaN scores from the functional union mask.

NOTE: sub-06 session 8, run 6 was corrupted (brain voxels misaligned with other fmriprepped runs). All final analyses were redone without that run.

------------

## Step 6. Compute noise ceilings on trial-unique betas

Derive voxelwise noise ceilings from beta scores estimated with GLMsingle.

The noise ceiling estimation is adapted from the [Natural Scene Dataset's datapaper methodology](https://www.nature.com/articles/s41593-021-00962-x).

**Preliminary step**:\
To leave out "blank" trials (trials with no recorded subject
response) from noise ceiling computations, trialwise performance needs to be
extracted. Run the ``behav_data_annotate.py`` script, as described under
**Trial-Wise Image Ratings and Annotations** in the ``cneuromod-things/THINGS/things.behaviour`` README. Output is saved as ``cneuromod-things/THINGS/things.behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-annotation-per-trial_beh.tsv``.

To compute noise ceilings, launch the following script for each subject:
```bash
DATADIR="cneuromod-things/THINGS"
python GLMsingle_noiseceilings.py --things_dir="${DATADIR}" --sub_num="01"
```

**Input**:
- A subject's ``TYPED_FITHRF_GLMDENOISE_RR.mat``, a single .mat file outputed by GLMsingle (model D) in Step 4, which contains trial-unique betas per voxel
- ``task-things_desc-runlist.h5``, a single file with nested lists of valid runs per session for each subject created in Step 3.
- A subject's ``sub-{sub_num}_task-things_sparsedesign.h5`` file created in Step 1.
- A subject's ``sub-{sub_num}_task-things_space-T1w_desc-func-union_mask.nii`` and
``sub-{sub_num}_task-things_space-T1w_desc-func-clean_mask.nii`` masks created in Steps 2 and 5, respectively.
- A subject's ``cneuromod-things/THINGS/things.behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-annotation-per-trial_beh.tsv``, a single .tsv file per subject with trialwise performance metrics and image annotations created with the ``cneuromod-things/THINGS/things.behaviour/code/behav_data_annotate.py`` script in the above preliminary step.

**Output**:
- ``sub-{sub_num}_task-things_space-T1w_res-func_modelD_noise-ceilings.mat``,
a single .mat file with a noise ceiling estimation per voxel saved as a
flattened 1D array whose lengh corresponds to the number of voxels within the ``sub-{sub_num}_task-things_space-T1w_desc-func-clean_mask.nii`` functional mask.
- ``sub-{sub_num}_task-things_space-T1w_res-func_modelD_noise-ceilings.nii.gz``, a brain volume
of voxelwise noise ceilings masked with Step 5's clean mask, in subject's (T1w) EPI space.


To convert ``.nii.gz`` volume into freesurfer surface:
```bash
SUB_NUM="01"
VOLFILE="sub-${SUB_NUM}_task-things_space-T1w_res-func_modelD_noise-ceilings.nii.gz"
L_OUTFILE="lh.sub-${SUB_NUM}_task-things_space-T1w_modelD_noise-ceilings.mgz"
R_OUTFILE="rh.sub-${SUB_NUM}_task-things_space-T1w_modelD_noise-ceilings.mgz"
mri_vol2surf --src ${VOLFILE} --out ${L_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi lh
mri_vol2surf --src ${VOLFILE} --out ${R_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi rh
```

To overlay surface data onto inflated brain infreesurfer's freeview:
```bash
freeview -f $SUBJECTS_DIR/sub-${SUB_NUM}/surf/lh.inflated:overlay=lh.sub-${SUB_NUM}_task-things_space-T1w_modelD_noise-ceilings.mgz:overlay_threshold=5,0 -viewport 3d

freeview -f $SUBJECTS_DIR/sub-${SUB_NUM}/surf/rh.inflated:overlay=rh.sub-${SUB_NUM}_task-things_space-T1w_modelD_noise-ceilings.mgz:overlay_threshold=5,0 -viewport 3d
```

------------

## Step 7. Export betas per trial in HDF5 file

Export trialwise normalized (z-scored) beta scores into a nested .h5 file per subject,
in which betas are organized per run within session.

Betas are saved into arrays (trials, voxels) where each row is a 1D array of
flattened voxel scores masked with the ``sub-{sub_num}_task-things_space-T1w_desc-func-clean_mask.nii`` functional mask.

Launch the following script for each subject
```bash
DATADIR="cneuromod-things/THINGS/things.glmsingle"
python GLMsingle_betas_per_trial.py --data_dir="${DATADIR}" --zbetas --sub_num="01"
```
Note: omit the ``--zbetas`` flag to extract raw GLMsingle betas

**Input**:
- A subject's ``TYPED_FITHRF_GLMDENOISE_RR.mat``, a single .mat file outputed by GLMsingle (model D) in Step 4, which contains trial-unique betas per voxel
- ``task-things_desc-runlist.h5``, a single file with nested lists of valid runs per session for each subject created in Step 3.
- A subject's ``sub-{sub_num}_task-things_space-T1w_desc-func-union_mask.nii`` and
``sub-{sub_num}_task-things_space-T1w_desc-func-clean_mask.nii`` masks created in Steps 2 and 5, respectively.

**Output**:
- ``sub-{sub_num}_task-things_space-T1w_res-func_desc-zscored-betas-per-trial.h5``, a single ``.h5`` file that contains beta scores organized in nested groups whose key is the session number and sub-key is the run number. Betas are saved into arrays (trials, voxels) where each row is a 1D array of flattened voxel scores masked with the clean functional mask.
- beside betas, the ``.h5`` file also contains the raw 3D array and 4x4 affine matrix of the clean functional mask, whose dims match the input bold volumes. These two arrays (``mask_array`` and ``mask_affine``) can be used to unmask 1D beta arrays to convert them back into brain volumes (in native space).

E.g., to convert the 5th trial of the 2nd run from session 10 into a brain volume:
```python
import nibabel as nib
from nilearn.masking import unmask

mask = nib.nifti1.Nifti1Image(np.array(h5file['mask_array']), affine=np.array(h5file['mask_affine']))
s10_r2_t5_unmasked_betas = unmask(np.array(h5file['10']['2']['betas'])[4, :], mask)
```

------------
**Step 6. Export betas averaged per image in HDF5 file (1 file per subject)**

Note: the script is overly complicated at the moment because it performs validations on:
- the trial-specific metrics from the input .tsv file (step 1b)
- the subject-specific image-to-number mapping (step 1)
- the design matrices used for glm_single (step 1)
It could be simplified to rely strictly on the .tsv file rather than on the .h5 design matrix

Server: beluga (Compute Canada) \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results \
Script: GLMs_betas_per_image.py

Launch the following script for each subject
```bash
./launch_GLMs_betasPerImg.sh 01
```

**Input**:
- A single .mat file created in Step 3, which contains trial-unique betas per voxel for a specific subject \
and model (B, C or D), e.g., TYPED_FITHRF_GLMDENOISE_RR.mat
- runlist_THINGS.h5 created in Step 2b, a single file with lists of valid runs per session for all subjects \
 (saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/bold_files)
- The .json file that assigns a unique number to each stimulus image seen by the participant (>4000) generated at Step 1 \
(saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/design_files/sub-{sub_num}_image_design_refnumbers.json)
- A subject's sub-(sub_num)_things_sparsedesign.h5 file (saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/design_files) created in Step 1
- The sub-{sub_num}_things_SVM_y.tsv file (saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/SVM_design_files) created in Step 1b
- the mask file (.nii) used/generated in Step 2 (saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/masks/{sub_num}_umask_T1w.nii)

**Output**:
A single .h5 file that contains data organized in groups whose key is the image name (e.g., 'camel_02s'). \
Under each image, each group includes:
- 'betas': the mean masked betas, a flattened series of betas from GLMsingle's model D averaged per image (up to 3 repetitions)
- 'num_reps': the number of times the image was repeated
- 'blank': the number of trials with no recorded answers (no button press)
- image-specific metrics from the THINGS database : 'image_category', 'things_category_nr', \
'things_image_nr', 'categ_arousal',  'categ_concreteness', 'categ_consistency', 'categ_nameability', \ 'categ_recognizability', 'categ_size', 'categ_wordfreq_COCA', 'highercat27_names', 'highercat53_names', \
'highercat53_num', 'img_consistency', 'img_memorability', 'img_nameability', 'img_recognizability', \
'categ_manmade', 'categ_precious', 'categ_living', 'categ_heavy', 'categ_natural', 'categ_moves', \
'categ_grasp', 'categ_hold', 'categ_be_moved', and 'categ_pleasant').\
The .h5 file also includes:
- a functional mask array with dims corresponding to the input bold volumes, and its 4x4 affine matrix. \
Those two arrays can be used to rebuild brain volumes (in native space) from the 1D masked beta arrays. \
e.g.,
```python
import nibabel as nib
from nilearn.masking import unmask
mask = nib.nifti1.Nifti1Image(np.array(h5file['mask_array']), affine=np.array(h5file['mask_affine'])) \
velcro_04s_unmasked_betas = unmask(np.array(h5file['velcro_04s']['betas']), mask)
```
