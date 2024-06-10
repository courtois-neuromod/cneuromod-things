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

python retino_make_apertureMasks.py --data_dir="${DATADIR}"
```

**Input**:
- ``retinotopy/stimuli``'s  ``apertures_bars.npz``, ``apertures_ring.npz`` and ``apertures_wedge_newtr.npz`` files, the binary aperture masks used by the Psychopy script to create apertures within which patterns of visual stimuli become visible during the task. [1 = pixel where visual patterns are displayed at time t, 0 = voxel where no pattern is visible]

**Output**:
- ``task-retinotopy_condition-{bars, rings, wedges}_desc-perTR_apertures.mat``, a sequence of aperture frames aranged in the order in which they appeared in a run of a given task, at a temporal frequency downsampled  (from task's 15 fps) to match the temporal frequency of the BOLD signal acquisition (fMRI TR = 1.49s). Note that the aperture sequence was the same for every run of the same task (e.g., all ``task-rings`` runs used the same aperture sequence). Frames were averaged within a TR so that mask values (floats) reflect the proportion of a TR during which patterns were visible in each pixel (value range = [0, 1]). Frames were resized from 768x768 to 192x192 pixels to speed up pRF processing time. The first three TRs were dropped to match the duration of the BOLD data (3 TRs dropped for signal equilibrium).

------------
## Step 2. Pre-process and chunk the BOLD data for analyzePRF

Prepare the BOLD data to process with the analyzepRF toolbox: vectorize, denoise,
standardize, average across runs of the same task, and chunk into small brain segments.

Launch the following script for each subject:
```bash
DATADIR="path/to/cneuromod-things"

python retino_prepare_BOLD.py --dir_path="${DATADIR}" --sub="01"
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

matlab -nodisplay -nosplash -nodesktop -r "sub_num='${SUB_NUM}';code_dir='${CODEDIR}';data_dir='${DATADIR}';first_chunk='${STARTCHUNK}';last_chunk='${ENDCHUNK}';nwork='${NWORKERS}';run('retino_run_analyzePRF.m'); exit;"
```
Note 1: NWORKERS, the number of parpool workers, should be set to match the number of available CPUs (matlab default is set to max 12, but can be overriden in the script). \
Note2: load ``StdEnv/2020`` and ``matlab/2021a.5`` modules to run on
Alliance Canada (36h job per subject, 36 CPUs per task, 5000M memory/CPU). Both the Optimization and the Parallel Computing toolboxes are available on the Beluga cluster.

**Input**:
- ``task-retinotopy_condition-{bars, rings, wedges}_desc-perTR_apertures.mat``, the apertures per TR for each run type generated in Step 1.
- ``sub-{sub_num}_task-retinotopy_condition-{task}_space-T1w_desc-chunk{chunk_num}_bold.mat``, the chunks of normalized bold data averaged across runs generated in Step 2.

**Output**:
- ``sub-{sub_num}_task-retinotopy_space-T1w_model-analyzePRF_stats-{stat}_desc-chunk{chunk_num}_statseries.mat``, population receptive field metrics (``ang``, ``ecc``, ``expt``, ``rfsize``, ``R2`` and ``gain``) estimated for each voxel, saved per chunk.

------------

## Step 4. Reconstruct analyzePRF chunked output into brain volumes and adapt metrics for Neuropythy

Re-assemble the chunked files outputed by analyzePRF into brain volumes, and convert their metrics to be compatible with the Neuropythy toolbox.

**Links and documentation**
- Neuropythy [repo](https://github.com/noahbenson/neuropythy)
- Neuropythy [user manual](https://osf.io/knb5g/wiki/Usage/)

Run this script for each subject
```bash
DATADIR="path/to/cneuromod-things/retinotopy/prf"

python retino_reassamble_voxels.py --data_dir="${DATADIR}" --sub="01"
```

**Input**:
- ``sub-{sub_num}_task-retinotopy_space-T1w_model-analyzePRF_stats-{stat}_desc-chunk{chunk_num}_statseries.mat``, chunks of retinotopy metrics generated in Step 3 (saved as 1D arrays in .mat file)
- ``sub-{sub_num}_task-retinotopy_space-T1w_label-brain_desc-unionNonNaN_mask.nii``, the functional brain mask generated in Step 2.
**Output**:
- ``sub-{sub}_task-retinotopy_space-T1w_model-analyzepRF_label-brain_stats-{stat}_statseries.nii.gz``, analyzePRF metrics reassambled into brain volumes (T1w space)
- ``sub-{sub}_task-retinotopy_space-T1w_model-analyzepRF_label-brain_stats-{stat}_desc-npythy_statseries.nii.gz``, analyzePRF metrics processed to be compatible with the Neuropythy toolbox and exported as brain volumes (T1w space)

------------

## Step 5. Convert retinotopy outputs from brain volumes to surfaces

Use Freesurfer to convert retinotopy output metrics from brain volumes (T1w space) to surfaces to be analyzed with the Neuropythy toolbox.

Note:
- The Freesurfer ``SUBJECTS_DIR`` variable must be overwritten to match the ``cneuromod-things/anatomical/smriprep/sourcedata/freesurfer`` directory, which contains the CNeuroMod subjects' Freesurfer data

Run the following command lines
```bash
DATADIR="/path/to/cneuromod-thing"

# overwrite Freesurfer SUBJECTS_DIR
SUBJECTS_DIR="${DATADIR}/anatomical/smriprep/sourcedata/freesurfer"

SUB_NUM="01" # 01, 02, 03
VOLDIR="${DATADIR}/retinotopy/prf/sub-${SUB_NUM}/prf/output"
SURFDIR="${DATADIR}/retinotopy/prf/sub-${SUB_NUM}/rois/input"

for RES_TYPE in ang ecc x y R2 rfsize
do
  VOLFILE="${VOLDIR}/sub-${SUB_NUM}_task-retinotopy_space-T1w_model-analyzePRF_label-brain_stats-${RES_TYPE}_desc-npythy_statseries.nii.gz"
  L_OUTFILE="${SURFDIR}/lh.s${SUB_NUM}_prf_${RES_TYPE}.mgz"
  R_OUTFILE="${SURFDIR}/rh.s${SUB_NUM}_prf_${RES_TYPE}.mgz"

  mri_vol2surf --src ${VOLFILE} --out ${L_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi lh
  mri_vol2surf --src ${VOLFILE} --out ${R_OUTFILE} --regheader "sub-${SUB_NUM}" --hemi rh
done
```
*Note: load the ``StdEnv/2020`` and ``freesurfer/7.1.1`` modules to run the commands above on Alliance Canada.*


**Input**:
- ``sub-{sub_num}_task-retinotopy_space-T1w_model-analyzePRF_label-brain_stats-{stat}_desc-npythy_statseries.nii.gz``, brain volumes in T1w space of analyzePRF metrics processed for Neuropythy generated in Step 4.
**Output**:
- ``s{sub_num}_prf_{ang, ecc, x, y, R2, rfsize}.mgz``, retinotopy output metrics in surface maps (one per hemisphere per metric). e.g., ``lh.s01_prf_ang.mgz``, ``rh.s01_prf_ang.mgz``, etc.


------------

## Step 6. Process surface maps with Neuropythy

The Neuropythy toolbox estimates regions of interest based on a single subject's
retinotopy results, plus a prior of ROIs estimated from the HCP project.

**Links and documentation**
- Neuropythy [repo](https://github.com/noahbenson/neuropythy)
- Neuropythy [user manual](https://osf.io/knb5g/wiki/Usage/).
- [command line arguments](https://github.com/noahbenson/neuropythy/blob/master/neuropythy/commands/register_retinotopy.py)

Notes:
- The Freesurfer ``SUBJECTS_DIR`` variable must be overwritten to match the ``cneuromod-things/anatomical/smriprep/sourcedata/freesurfer`` directory, which contains the CNeuroMod subjects' Freesurfer data
- A Visible Deprecation Warning appears with newer versions of numpy that do not affect the output. [Filed repo issue here.](https://github.com/noahbenson/neuropythy/issues/24)
- the ``scale`` argument specifies the strength of the functional forces (subject's retinotopy) relative to anatomical forces (atlas prior) during the registration. Higher scale values will generally result in more warping while lower values will result in less warping. The default value is ``20``.


Run the following command lines
```bash
DATADIR="/path/to/cneuromod-thing"

# overwrite Freesurfer SUBJECTS_DIR
SUBJECTS_DIR="${DATADIR}/anatomical/smriprep/sourcedata/freesurfer"

SUB_NUM="01" # 01, 02, 03
INDIR="${DATADIR}/retinotopy/prf/sub-${SUB_NUM}/rois/input"
OUTDIR="${DATADIR}/retinotopy/prf/sub-${SUB_NUM}/rois/output"

python -m neuropythy \
      register_retinotopy "sub-${SUB_NUM}" \
      --verbose \
      --surf-outdir="${OUTDIR}" \
      --surf-format="mgz" \
      --vol-outdir="${OUTDIR}" \
      --vol-format="mgz" \
      --lh-angle="${INDIR}/lh.s${SUB_NUM}_prf_ang.mgz" \
      --lh-eccen="${INDIR}/lh.s${SUB_NUM}_prf_ecc.mgz" \
      --lh-radius="${INDIR}/lh.s${SUB_NUM}_prf_rfsize.mgz" \
      --lh-weight="${INDIR}/lh.s${SUB_NUM}_prf_R2.mgz" \
      --rh-angle="${INDIR}/rh.s${SUB_NUM}_prf_ang.mgz" \
      --rh-eccen="${INDIR}/rh.s${SUB_NUM}_prf_ecc.mgz" \
      --rh-radius="${INDIR}/rh.s${SUB_NUM}_prf_rfsize.mgz" \
      --rh-weight="${INDIR}/rh.s${SUB_NUM}_prf_R2.mgz" \
      --scale=20.0

echo "Job finished"
```
*Note: load the ``StdEnv/2020``, ``java/11.0.2`` and ``freesurfer/7.1.1`` modules to run the commands above on Alliance Canada.*

**Input**:
- Retinotopy output metrics in surface maps (one per hemisphere per metric). e.g., ``lh.s01_prf_ang.mgz``, ``rh.s01_prf_ang.mgz``, etc.
**Output**:
- Inferred retinotopy surface maps (based on atlas prior and subject's own retinotopy data) and region of interest labels (e.g., lh.inferred_varea.mgz)

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
