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
TODO: remove, since step already described under things.behaviour
TODO: adjust downstream scripts that rely on this step's output... (removed memorability metrics, file name change...)

## Step 1b. Generate a single .tsv file with trial-specific metrics from *events.tsv files

Assign image-wise annotations and performance metrics to a concatenation of
each trial for each subject. See ``cneuromod-things/THINGS/things.behaviour/README.md``
under **Image Recognition Performance Metrics**  for more details.

This step is not required to run GLMsingle to extract trialwise betas from the
data, but its output is needed for downstream analyses. It uses annotations from
the THINGS and THINGSplus databases, which can be downloaded [here](https://osf.io/jum2f/)
and saved directly under ``cneuromod-things/THINGS/things.fmriprep/sourcedata/things/annotations/THINGS+``.

Launch the following script to process a subject's sessions
```bash
EVDIR="cneuromod-things/THINGS/things.fmriprep/sourcedata/things"
ANDIR="cneuromod-things/THINGS/things.fmriprep/sourcedata/things/things.stimuli/annotations"
OUTDIR="cneuromod-things/THINGS/things.behaviour"

python code/behav_data_annotate.py --events_dir="${EVDIR}" --annot_dir="${ANDIR}" --out_dir="${OUTDIR}" --sub="01"
```
## TODO: remove step 1b: refer to doc and script and output under things.behaviour

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

------------
## Step 3. Generate lists of valid runs per session for all subjects

Generate list of valid runs nested per session for each subject to import
in matlab and loop over while running GLMsingle.

Run script for all subjects
```bash
python GLMsingle_makerunlist.py
```

**Input**:
- All 4 subject's ``sub-{sub_num}_task-things_space-T1w_maskedBOLD.h5``
files produced in step 2.

**Output**:
- ``task-things_desc-runlist.h5``, a single file of nested lists of valid runs
per session for each subject

------------
## Step 4. Run GLMsingle on _maskedBOLD.h5 and _sparsedesign.h5 files from Steps 1 and 2

Run GLMsingle in matlab to compute trialwise beta scores for each voxel within the
functional brain mask.

Launch the following script for each subject, specifying the subject number,
bold volume space (``T1w``) & number of voxels per chunk as arguments
(recommended: reduce to ``35000`` from ``50000`` default to avoid OOM) \
```bash
cd cneuromod-things/THINGS/things.glmsingle/code/glmsingle
matlab -nodisplay -nosplash -nodesktop -r "sub_num='01';bold_type='T1w';chunk_size='35000';run('GLMsingle_run.m'); exit;"
```
Note: load StdEnv/2020, nixpkgs/16.09 and matlab/2020a modules to run on
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
**Step 4. Compute noise ceilings on trial-unique betas**
Code is adapted from NSD's datapaper methodology

Server: beluga (Compute Canada) \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results \
Script: GLMs_noiseCeiling.py

Update and launch the following script for each output file (either one per subject per model, or one per subject per model per chunk of voxels
```bash
./launch_GLMs_noiseCeil.sh 01
```

**Input**:
- A single .mat file created in Step 3 (GLMsingle output), which contains trial-unique betas per voxel for a specific subject \
and model (B, C or D), e.g., TYPED_FITHRF_GLMDENOISE_RR.mat
- runlist_THINGS.h5 created in Step 2b, a single file with lists of valid runs per session for all subjects \
(saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/bold_files)
- A subject's sub-(sub_num)_things_sparsedesign.h5 files created in Step 1 \
(saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/design_files)
- OPTION to discard trials with no answer: \
requires sub-{sub_num}_things_SVM_y.tsv, a single .tsv file per subject with trial-specific \
performance and stimulus-related metrics from events.tsv files created in Step 1b. \
(saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/SVM_design_files)

**Output**:
- A single .mat file with a noise ceiling estimation per voxel (masked and flattened 1D matrix of lengh = num voxels)

**Visualization**
To convert vectorized noise ceiling data into volume:
from scipy.io import loadmat, savemat
import nibabel as nib
import numpy as np
from nilearn.masking import unmask

mask = nib.load(f'{sub_num}_umask_T1w.nii')
nc = np.squeeze(loadmat(f'sub{sub_num}_T1w_modelD_NoiseCeil.mat')['NC'])
nc_vol = unmask(nc, mask)
nib.save(nc_vol, f'sub{sub_num}_T1w_modelD_NoiseCeil.nii')

To convert .nii volume into freesurfer surface:
SUB_NUM="01"
VOLFILE="sub${SUB_NUM}_T1w_modelD_NoiseCeil.nii"
L_OUTFILE="lh.s${SUB_NUM}_T1w_modelD_noiseCeiling.mgz"
R_OUTFILE="sub-${SUB_NUM}/rh.s${SUB_NUM}_T1w_modelD_noiseCeiling.mgz"
mri_vol2surf --src ${VOLFILE} --out ${L_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi lh
mri_vol2surf --src ${VOLFILE} --out ${R_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi rh

To overlay surface data on inflated brain infreesurfer's freeview
freeview -f $SUBJECTS_DIR/sub-${SUB_NUM}/surf/lh.inflated:overlay=lh.s${SUB_NUM}_T1w_modelD_noiseCeiling.mgz:overlay_threshold=5,0 -viewport 3d

freeview -f $SUBJECTS_DIR/sub-03/surf/rh.inflated:overlay=sub-03/rh.s03_T1w_R2_modelD.mgz:overlay_threshold=4,0 -viewport 3d

------------
**Step 5. Export betas per trial in HDF5 file (organized per session and run; 1 file per subject)**

Server: beluga (Compute Canada) \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results \
Script: GLMs_sortBetas.py

Launch the following script for each subject
```bash
./launch_GLMs_sortBetas.sh 01
```

**Input**:
- A single .mat file created in Step 3, which contains trial-unique betas per voxel for a specific subject \
and model (B, C or D), e.g., TYPED_FITHRF_GLMDENOISE_RR.mat
- runlist_THINGS.h5 created in Step 2b, a single file with lists of valid runs per session for all subjects \
 (saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/bold_files)
- the mask file (.nii) used/generated in Step 2 (saved under /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/masks/{sub_num}_umask_T1w.nii)

**Output**:
- A single .h5 file that contains data organized in groups whose key is the session number, and sub-key is the run number \
- the .h5 file also includes a functional mask array with dims corresponding to the input bold volumes, and its 4x4 affine matrix. Those two arrays can be used to rebuild brain volumes (in native space) from the 1D masked beta arrays. \
e.g.,
```python
import nibabel as nib
from nilearn.masking import unmask
mask = nib.nifti1.Nifti1Image(np.array(h5file['mask_array']), affine=np.array(h5file['mask_affine'])) \
velcro_04s_unmasked_betas = unmask(np.array(h5file['velcro_04s']['betas']), mask)
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

------------

**Step 7. Clean-up operation**

When z-scoring (per run) the BOLD data given to GLMsingle toolbox, some voxels within
the functional mask (union of all run functional masks) contained nan scores (due to low/no signal on some runs).

This script identifies voxels with nan scores, and creates masks to exclude them from analyses.
It also applies those masks to the following analyses:
- betas exported per trial and per image
- noise ceiling computations

TODO
- top image per beta within functional ROIs
- TSNE plots
- classification analyses (e.g., SVM)
- retinotopy? (seems ok)
- fLoc: seems ok, but exclude from ROI masks?


Server: beluga \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/data/things.fmriprep \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results \
Script: GLMsingle_create_nanMask.py

Call script in interactive session on beluga (small dumb script, input and output paths hard-coded)
```bash
module load python/3.7
source /project/rrg-pbellec/mstlaure/.virtualenvs/things_memory_results/bin/activate
python -m GLMs_create_nanMask
```

**Input**:
- All 6 subject's *bold.nii.gz files, for all sessions (~36) and runs (6 per session) \
(e.g., sub-03_ses-10_task-things_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz)
- The functional mask averaged from each run's functional run (e.g., 01_umask_T1w.nii)
- Output files from the noiseceiling and beta sorting (per trial and per image) scripts

**Output**:
- One mask that includes all voxels with at least one normalized BOLD value equal to nan within the broader functional brain mask (e.g., 01_nanmask_T1w.nii)
- One mask that includes all voxels with no normalized BOLD value equal to nan within the broader functional brain mask (e.g., 01_goodvoxmask_T1w.nii)
- noise ceiling maps (e.g., sub01_T1w_modelD_NoiseCeil_Final_noBlanks_goodvoxMask.mat)
- betas per trial (e.g., results/betas/betas_per_trial/01_things_T1w_betas_goodvoxMask.h5)
- betas per image (e.g., results/betas/betas_per_img/01_things_T1w_betas_goodvoxMask.h5)


NOTE: sub-06 session 8, run 6 was corrupted (brain voxels misaligned with other fmriprepped runs). All final analyses were redone without that run.
