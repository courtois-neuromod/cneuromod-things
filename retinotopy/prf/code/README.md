Retinotopy Pipeline
==============================

Uses an adaptation of [Kay et al. (2013)](https://doi.org/10.1152/jn.00105.2013)'s retinotopy task to estimate population receptive fields from fMRI data with the [analyzePRF toolbox](https://github.com/cvnlab/analyzePRF), and delineates early visual cortex ROIs from the pRF maps using [the Neuropythy toolbox](https://github.com/noahbenson/neuropythy).

**Links and documentation**
- Kay et al. (2013)'s [retinotopy task](https://doi.org/10.1152/jn.00105.2013)
- CNeuroMod [retinotopy task](https://github.com/courtois-neuromod/task_stimuli/blob/master/src/tasks/retinotopy.py)
- The Human Connectome Project 7 Tesla retinotopy dataset [description and pRF analysis](https://doi.org/10.1167/18.13.23)
- The HCP [retinotopy stimuli](http://kendrickkay.net/analyzePRF)
- analyzePRF toolbox [repository](https://github.com/cvnlab/analyzePRF)
- Neuropythy [repository](https://github.com/noahbenson/neuropythy)


------------
## Step 1. Create TR-by-TR aperture masks of the retinotopy task

In preparation for analyzePRF, build TR-by-TR aperture masks using ``retinotopy/stimuli``, based on the retinotopy task implemented in Psychopy.

Launch the following script:
```bash
DATADIR="path/to/cneuromod-things/retinotopy"

python make_apertureMasks.py --data_dir="${DATADIR}"
```

**Input**:
- ``retinotopy/stimuli``'s  ``apertures_bars.npz``, ``apertures_ring.npz`` and ``apertures_wedge_newtr.npz`` files, the binary aperture masks used by the Psychopy script to create apertures within which patterns of visual stimuli become visible during the task. [1 = pixel where visual patterns are displayed at time t, 0 = voxel where no pattern is visible]

**Output**:
- ``task-retinotopy_condition-{bars, rings, wedges}_desc-perTR_apertures.mat``, a sequence of aperture frames aranged in the order in which they appeared in a run of a given task, at a temporal frequency downsampled  (from task's 15 fps) to match the temporal frequency of the BOLD signal acquisition (fMRI TR = 1.49s). Note that the aperture sequence was the same for every run of the same task (e.g., all ``task-rings`` runs used the same aperture sequence). Frames were averaged within a TR so that mask values (floats) reflect the proportion of a TR during which patterns were visible in each pixel (value range = [0, 1]). Frames were resized from 768x768 to 192x192 pixels to speed up pRF processing time. The first three TRs were dropped to match the duration of the BOLD data (3 TRs dropped for signal equilibrium).

------------
# Step 2. Pre-process and chunk the BOLD data for analyzePRF

Prepare the BOLD data to process with the analyzepRF toolbox: vectorize, denoise,
standardize, average across runs of the same task, and chunk into small brain segments.

Launch the following script for each subject:
```bash
DATADIR="path/to/cneuromod-things"

python prepare_BOLD.py --dir_path="${DATADIR}" --sub="01"
```

**Input**:
- All of a subject's ``*_bold.nii.gz`` and ``*mask.nii.gz`` files, for all sessions (~6) and runs (3 per session)
(e.g., ``sub-03_ses-003_task-rings_space-T1w_desc-preproc_part-mag_bold.nii.gz``).
- All of a subject's confound ``*sub-01_ses-002_task-bars_desc-confounds_part-mag_timeseries.tsv`` files, for all sessions (~6) and runs (2 per session) (e.g., ``sub-01_ses-002_task-bars_desc-confounds_part-mag_timeseries.tsv``)
- ``anatomical/smriprep/sub-{sub_num}/anat/sub-{sub_num}_label-GM_probseg.nii.gz``, a subject's grey matter mask outputed by fmriprep .

**Output**:
- Two brain masks generated from the union of the run ``*_mask.nii.gz`` files and ``*_label-GM_probseg.nii.gz``: ``sub-{sub_num}_task-retinotopy_space-T1w_label-brain_desc-unionNonNaN_mask.nii`` includes the voxels with signal across all functional runs, and ``sub-{sub_num}_task-retinotopy_space-T1w_label-brain_desc-unionNaN_mask.nii`` includes voxels that lack signal in at least one run (to be excluded).  
- ``sub-{sub_num}_task-retinotopy_condition-{task}_space-T1w_desc-chunk{chunk_num}_bold.mat``, chunks of vectorized, detrended bold signal averaged across sessions for runs of the same task, to load in matlab (~850 .mat files of >200k voxels each), dim = (voxels, TR)

------------

## Step 3. Estimage population receptive fields with AnalyzePRF toolbox

Process chunks of data with the [analyzePRF](https://github.com/cvnlab/analyzePRF) retinotopy toolbox (in matlab).
Note that the code requires the MATLAB Optimization Toolbox and Matlab Parallel Computing Toolbox (``parfor``) to run.

For the script to run, the [analyzePRF repository](https://github.com/cvnlab/analyzePRF)
needs to be installed as a [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
under ``cneuromod-things/retinotopy/prf/code`` (commit ``a3ac908``).

See [here](http://kendrickkay.net/analyzePRF/) for documentation and examples. \
Note: the script processes a single participant at a time, VERY slowly.

E.g., to process sub-01's chunks 0 to 10 (inclusively)
```bash
SUB_NUM="01" # 01, 02, 03, 05
STARTCHUNK="0"
ENDCHUNK="10"
NWORKERS="36"

DATADIR="path/to/cneuromod-things/retinotopy/prf"
CODEDIR="${DATADIR}/code"
cd ${CODEDIR}

matlab -nodisplay -nosplash -nodesktop -r "sub_num='${SUB_NUM}';code_dir='${CODEDIR}';data_dir='${DATADIR}';first_chunk='${STARTCHUNK}';last_chunk='${ENDCHUNK}';nwork='${NWORKERS}';run('run_analyzePRF.m'); exit;"
```
Note 1: NWORKERS, the number of parpool workers, should be set to match the number of available CPUs (matlab default is set to max 12, but can be overriden in the script). \
Note2: load ``StdEnv/2020`` and ``matlab/2021a.5`` modules to run on
Alliance Canada (36h job per subject, 36 CPUs per task, 5000M memory/CPU). Both the Optimization and the Parallel Computing toolboxes are available on the Beluga cluster.

**Input**:
- ``task-retinotopy_condition-{bars, rings, wedges}_desc-perTR_apertures.mat``, the apertures per TR for each run type generated in Step 1.
- ``sub-{sub_num}_task-retinotopy_condition-{task}_space-T1w_desc-chunk{chunk_num}_bold.mat``, the chunks of normalized bold data averaged across runs generated in Step 2.

**Output**:
- ``sub-{sub_num}_task-retinotopy_space-T1w_model-analyzepRF_desc-chunk{chunk_num}_*.mat``, population receptive field metrics (``ang``, ``ecc``, ``expt``, ``rfsize``, ``R2`` and ``gain``) estimated for each voxel, saved per chunk.

------------
**Step 5. Reconstruct chunked output files into brain volumes and pre-process metrics for Neuropythy toolbox**

Copy the chunked results files from elm/ginkgo:/ /home/mariestl/cneuromod/retinotopy/analyzePRF/results/sub-0*/fullbrain
into beluga:/home/mstlaure/projects/rrg-pbellec/mstlaure/retino_analysis/results/analyzePRF/chunked/s0*

Then, reassemble the chunked output files into brain volumes and adapt them for Neuropythy. \
Neuropythy repo [here](https://github.com/noahbenson/neuropythy); Neuropythy user manual [here](https://osf.io/knb5g/wiki/Usage/).\
Note: processes a single participant's data at a time.

Script: src/features/reassamble_voxels.py
```bash
python -m src.features.reassamble_voxels.py --sub_num=”sub-03”
```

**Input**: Chunks of retinotopy metrics saved as 1D arrays in .mat file \
**Output**: Brain volumes of retinotopy metrics in T1w space

------------
**Step 6. Convert retinotopy output maps from T1w volumes into surfaces with freesurfer**

Notes:
- this step requires access to fmriprep freesurfer output
- I installed freesurfer locally in my home directory, following Compute Canada [guidelines](https://docs.computecanada.ca/wiki/FreeSurfer)
- The $SUBJECTS_DIR variable must be set to the path to the directory where cneuromod subjects' freesurfer output is saved

Script: src/features/run_FS.sh
To run (where "01" is the subject number):
```bash
./src/features/run_FS.sh 01  
```

**Input**: Brain volumes of retinotopy metrics in T1w space \
**Output**: freesurfer surface maps (one per hemisphere per metric). e.g., lh.s01_prf_ang.mgz & rh.s01_prf_ang.mgz


------------
**Step 7. Process surface maps with neuropythy toolbox**

The Neuropythy toolbox estimates regions of interest based on a single subject's retinotopy results, plus a prior of ROIs estimated from the HCP project.
Neuropythy [repo](https://github.com/noahbenson/neuropythy) and [command line arguments](https://github.com/noahbenson/neuropythy/blob/master/neuropythy/commands/register_retinotopy.py); Neuropythy [user manual](https://osf.io/knb5g/wiki/Usage/).

Notes:
- this step requires to load java and freesurfer modules; $SUBJECTS_DIR needs to be specified just like in step 6.
- There is a Visible Deprecation Warning that appears with newer versions of numpy that do not affect the output. [Filed repo issue here.](https://github.com/noahbenson/neuropythy/issues/24)

Script: src/features/run_neuropythy.sh
To run (where "01" is the subject number):
```bash
./src/features/run_neuropythy.sh 01
```

**Input**: freesurfer surface maps of retinotopy metrics \
**Output**: Inferred retinotopy surface maps (based on atlas prior and subject's own retinotopy data) and region of interest labels (e.g., lh.inferred_varea.mgz)

------------
**Step 8. Reorient and resample neuropythy output maps and project the results back into T1w volume space**

**First**: re-orient the neuropythy output with mri_convert and fsl
Script: src/features/reorient_npythy.sh
```bash
./src/features/reorient_npythy.sh 01
```
Notes:
- this script needs to run from within the subject’s freesurfer "MRI" directory (hence the "cd") so it knows where to find freesurfer files.
- on Compute Canada, the script prompts to specify which module versions to use; chose option 2 : fsl/6.0.3 StdEnv/2020 gcc/9.3.0

**Second**: Resample binary visual ROIs to T1w functional space
Script: src/features/resample_npythy_ROIs.py
Before running, load project's virtual env with **workon retino_analysis** (on beluga)
```bash
python -m src.features.resample_npythy_ROIs --sub_num=”sub-01”
```

**Input**: Inferred retinotopy surface maps \
**Output**: NIfTI volumes of retinotopy results adjusted from atlas prior, and inferred regions of interest (binary mask for V1, V2, V3, hV4, V01, V02, L01, L02, T01, T02, V3b and V3a) in T1w space

--------

**Step 8. Clean up operation**

When z-scoring (per run) the BOLD data given to the AnalyzePRF toolbox, some voxels within
the WholeBrain functional mask (used to mask data across all runs) have nan scores (due to low/no signal on some runs).

Step 1: identify voxels to exclude from final volumes

This script identifies voxels with nan scores, and creates masks to exclude them from final result volumes.

Server: beluga \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/retino_analysis/data/temp_bold \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/retino_analysis \
Script: quick_mask_QC_retino.py

Call script in interactive session on beluga (small dumb script, input and output paths hard-coded)
```bash
workon retino_analysis
python -m quick_mask_QC_retino
```

**Input**:
- All subject's *bold.nii.gz files, for all sessions (~6) and runs (3 per session) \
(e.g., sub-03_ses-10_task-things_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz)
- The functional mask used to mask all run data (e.g., sub-02_WholeBrain.nii.gz)

**Output**:
- One mask that includes all voxels with at least one normalized BOLD value equal to nan within the broader functional brain mask (e.g., 01_nanmask_T1w_retino.nii)
- One mask that includes all voxels with no normalized BOLD value equal to nan within the broader functional brain mask (e.g., 01_goodvoxmask_T1w_retino.nii)


Step 2: This script uses the good voxel mask created in step one to clean up output volumes of AnalyzePRF and Neuropythy analyses

Server: beluga \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/retino_analysis/results \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/retino_analysis \
Script: clean_volumes.py

Call script in interactive session on beluga (small dumb script, input and output paths hard-coded)
```bash
workon retino_analysis
python -m clean_volumes --sub_num=sub-01
```

**Input**:
- The functional mask used to mask all run data (e.g., sub-02_WholeBrain.nii.gz) and the clean mask created in step 1 (e.g., 01_goodvoxmask_T1w_retino.nii)
- The .mat files of AnalyzePRF results per masked voxels outputed at step 5
- The resampled volumes of Neuropythy data (sub-01/resampled*.nii.gz) outputed at step 7

**Output**:
- Clean volumes of Neuropythy and AnalyzePRF results in functional T1w space. All files are relabelled *goodvox.nii.gz
