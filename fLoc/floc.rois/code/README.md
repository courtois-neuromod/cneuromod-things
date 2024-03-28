fLoc Pipeline
==============================
This pipeline derives subject-specific functional ROIs from the fLoc CNeuromod dataset

**Links and documentation**
- CNeuromod [fLoc task](https://github.com/courtois-neuromod/task_stimuli/blob/main/src/tasks/localizers.py) and [stimuli](https://github.com/courtois-neuromod/floc.stimuli)
- The CNeuromod fLoc task is based on [pyfLoc](https://github.com/NBCLab/pyfLoc),
which was adapted from [VPNL/fLoc](https://github.com/VPNL/fLoc) as published in [Stigliani et al., 2015](https://www.jneurosci.org/content/35/36/12412)
- ROI parcels (improve normalization in CVS space, n=40) were downloaded from the [Kanwisher group](https://web.mit.edu/bcs/nklab/GSS.shtml#download)

------------
## Step 1. Generate design matrices from events.tsv files

Build design matrices from a subject's ``*events.tsv`` files in preparation for a GLM analysis on the BOLD data.

Launch the following script, specifying the subject number.
```bash
DATADIR="cneuromod-things/fLoc/floc.fmriprep/sourcedata/floc"
OUTDIR="cneuromod-things/fLoc/floc.rois"

python fLoc_makedesign.py --data_dir="${DATADIR}" --out_dir="${OUTDIR}" --sub="01"
```

**Input**:
- All of a subject's ``*events.tsv`` files across sessions (~6) and runs (2 per session)\
(e.g., ``sub-03_ses-001_task-fLoc_run-01_events.tsv``)

**Output**:
- ``sub-{sub_num}_task-floc_model-GLM_design.h5``, a HDF5 file with one dataset group per run per session; each group (run) includes three datasets (arrays): 'onset', 'duration' and 'trial_type'

------------
## Step 2. Run first-level GLM in nilearn on fLoc BOLD data

Derive GLM contrasts from multiple sessions and runs of fLoc task with a first-level GLM with nilearn.

Launch the following script, specifying the subject number.
```bash
BOLDDIR="cneuromod-things/fLoc/floc.fmriprep"
OUTDIR="cneuromod-things/fLoc/floc.rois"

python fLoc_firstLevel_nilearn.py --fLoc_dir="${BOLDDIR}" --out_dir="${OUTDIR}" --smooth --sub="01"
python fLoc_firstLevel_nilearn.py --fLoc_dir="${BOLDDIR}" --out_dir="${OUTDIR}" --sub="01"
```

**Input**:
- A subject's ``sub-{sub_num}_task-floc_model-GLM_design.h5`` file created in Step 1.
- All of a subject's ``*bold.nii.gz`` files, for all sessions (~6) and runs (2 per session) (e.g., ``sub-02_ses-005_task-fLoc_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz``)
- All of a subject's confound ``*desc-confounds_timeseries.tsv files``, for all sessions (~6) and runs (2 per session) (e.g., ``sub-02_ses-005_task-fLoc_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz``) \
Note that the script can process scans in MNI or subject (T1w) space (default is T1w)

**Output**:
- Two mask files generated from the union of the run ``_mask.nii.gz`` files save with the _bold.nii.gz files. ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii`` includes the voxels with signal across all functional runs, and ``sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNaN_mask.nii`` includes voxels that lack signal in at least one run (to be excluded).  
- One volume of t-scores and one of beta values (``sub-{sub_num}_task-floc_space-T1w_model-GLM_stats-{tscores, betas}_contrast-{contrast}_desc-{smooth, unsmooth}_statseries.nii.gz``) for each of the 9 GLM contrasts listed below.
- The following four contrasts are as specified in the work of the Kanwisher group:
> * ``faceMinObject``: face > object
> * ``sceneMinObject``: scene > object
> * ``bodyMinObject``: body > object
> * ``objectMinRest``: object > rest
- The following contrasts are as specified in the NSD data paper, who used a localizer task paradigm similar to ours:
> * ``faces``: face > (object, scene, body, character)
> * ``places``: scene > (object, face, body, character)
> * ``bodies``: body > (object, scene, face, character)
> * ``characters``: character > (object, scene, body, face)
> * ``objects``: object > (face, scene, body, character)

------------

## Step 3. Warp Kanwisher group parcels and ROI masks from normalized CVS space into subject (T1w) space

To obtain ROI masks in subject space, we started from normalized (CVS space) parcels of voxels with face, body, scene and object preferences in derived from n=40 individuals by the Kanwisher group.

The following command lines derive ROI masks from those group parcels, and warp the parcels and ROI masks from CVS to MNI to subject (T1w) space.

### 3.0 Download the Kanwisher parcels

Download CVS parcels (``cvs_avg35`` template) in ``.nii`` format from the Kanwisher group [here](https://web.mit.edu/bcs/nklab/GSS.shtml#download) \

Save parcel files under ``floc/floc.rois/standard_masks/kanwisher_parcels/cvs``

### 3.1 Extract normalized (CVS) ROI masks from group parcels (e.g., FFA, PPA)

The CVS parcels each contain many ROIs per contrast. Create a separate mask (in cvs_avg35 space) for the following 7 regions of interest: FFA, OFA, pSTS, PPA, OPA, MPA and EBA.
> * ``FFA``: fusiform face area
> * ``OFA``: occipital face area
> * ``pSTS``: posterior superior temporal sulcus
> * ``PPA``: parahippocampal place area
> * ``OPA``: occipital place area
> * ``MPA``: medial place area
> * ``EBA``: extrastriate body area

Launch the following script
```bash
DATADIR="cneuromod-things/fLoc/floc.rois"

python fLoc_split_CVSparcels_perROI.py --data_dir="${DATADIR}"
```

**Input**:
- the Kanwisher ROI files for each contrast (face, scene, object, body; e.g., ``cvs_scene_parcels/cvs_scene_parcels/fROIs-fwhm_5-0.0001.nii``)
**Output**:
- For each contrast (face, scene, body, object), a series of binary ROI masks in ``cvs_avg35`` space (e.g., ``parcel-kanwisher_space-CVSavg35_contrast-face_roi-{FFA, OFA, pSTS}_desc-{L, R, bilat}_mask.nii``). Note that, for each ROI label, the script produces a left, a right and a bilateral mask.


### 3.2 Warp parcels and ROI masks from CVS to MNI space

Use Freesurfer and FSL to convert CVS parcels and masks from CVS to MNI space as a intermediate step to deriving masks in subject space. Instructions to convert parcels from CVS (cvs_avg35) to MNI space are found [here](https://neurostars.org/t/freesurfer-cvs-avg35-to-mni-registration/17581).

First, you'll need FLS and Freesurfer installed, and your ``$FSLDIR`` and ``$SUBJECTS_DIR`` variables defined.
You can check by making sure that typing ``$SUBJECTS_DIR`` in your terminal returns a directory path.
Something like ``/home/my_username/.local/easybuild/software/2020/Core/freesurfer/7.1.1/subjects``. \
*Note: load ``StdEnv/2020``, ``gcc/9.3.0``, ``fsl/6.0.3``, and ``freesurfer/7.1.1`` modules to run the following commands on Alliance Canada.*

Second, you may need to register the ``cvs_avg35`` template to ``MNI125`` space. **This step only needs to be performed once.** It saves the transformation file ``reg.mni152.2mm.dat`` under ``${SUBJECTS_DIR}/cvs_avg35/mri/transforms/``

Type, from anywhere:
```bash
mni152reg --s cvs_avg35
```

Third, warp the Kanwisher parcels from CVS to MNI152 space for each contrast (face, scene, body, scene).
```bash
PARCELDIR="cneuromod-things/fLoc/floc.rois/standard_masks/kanwisher_parcels"

for PARAM in body face object scene
do
  mri_vol2vol --targ ${PARCELDIR}/cvs/cvs_${PARAM}_parcels/cvs_${PARAM}_parcels/fROIs-fwhm_5-0.0001.nii \
  --mov ${FSLDIR}/data/standard/MNI152_T1_2mm.nii.gz \
  --o ${PARCELDIR}/mni/parcel-kanwisher_space-MNI152T1_res-2mm_contrast-${PARAM}_mask.nii \
  --inv --reg ${SUBJECTS_DIR}/cvs_avg35/mri/transforms/reg.mni152.2mm.dat
done
```

Fourth, warp the Kanwisher ROI masks from CVS to MNI152 space for each ROI
```bash
ROIDIR="cneuromod-things/fLoc/floc.rois/standard_masks/standard_rois"

for PARAM in body_roi-EBA face_roi-FFA face_roi-OFA face_roi-pSTS scene_roi-MPA scene_roi-OPA scene_roi-PPA
do
  mri_vol2vol --targ ${ROIDIR}/parcel-kanwisher_space-CVSavg35_contrast-${PARAM}_desc-bilat_mask.nii \
  --mov $FSLDIR/data/standard/MNI152_T1_2mm.nii.gz \
  --o ${ROIDIR}/parcel-kanwisher_space-MNI152T1_contrast-${PARAM}_desc-bilat_mask.nii \
  --inv --reg ${SUBJECTS_DIR}/cvs_avg35/mri/transforms/reg.mni152.2mm.dat

  mri_vol2vol --targ ${ROIDIR}/parcel-kanwisher_space-CVSavg35_contrast-${PARAM}_desc-L_mask.nii \
  --mov $FSLDIR/data/standard/MNI152_T1_2mm.nii.gz \
  --o ${ROIDIR}/parcel-kanwisher_space-MNI152T1_contrast-${PARAM}_desc-L_mask.nii \
  --inv --reg ${SUBJECTS_DIR}/cvs_avg35/mri/transforms/reg.mni152.2mm.dat

  mri_vol2vol --targ ${ROIDIR}/parcel-kanwisher_space-CVSavg35_contrast-${PARAM}_desc-R_mask.nii \
  --mov $FSLDIR/data/standard/MNI152_T1_2mm.nii.gz \
  --o ${ROIDIR}/parcel-kanwisher_space-MNI152T1_contrast-${PARAM}_desc-R_mask.nii \
  --inv --reg ${SUBJECTS_DIR}/cvs_avg35/mri/transforms/reg.mni152.2mm.dat
done
```

### 3.3 Warp parcels and ROI masks from MNI to subject (T1w)) space

Use ANTs to warp parcels and ROI masks from MNI152 to subject space. Instructions to convert parcels from MNI to T1w space using output from fmriprep can be found [here](https://neurostars.org/t/how-to-transform-mask-from-mni-to-native-space-using-fmriprep-outputs/2880/8). \
*Note: load ``StdEnv/2020``, ``gcc/9.3.0`` and ``ants/2.3.5`` modules to run the following commands on Alliance Canada.*

You will need a reference anatomical image and transformation matrices outputted by fmriprep to warp the masks to each subject's space.

First, warp the Kanwisher parcels from MNI152 to T1w.
```bash
PARCELDIR="cneuromod-things/fLoc/floc.rois/standard_masks/kanwisher_parcels/mni"
OUTDIR="cneuromod-things/fLoc/floc.rois"
SPREPDIR="cneuromod-things/anatomical/anat.smriprep"

for PARAM in body face object scene
do
  for SUBNUM in 01 02 03 06
  do
    OUTSUB="${OUTDIR}/sub-${SUBNUM}/rois/from_atlas"

    antsApplyTransforms --default-value 0 --dimensionality 3 --float 0 \
    --input ${PARCELDIR}/parcel-kanwisher_space-MNI152T1_res-2mm_contrast-${PARAM}_mask.nii \
    --interpolation Linear \
    --output ${OUTSUB}/sub-${SUBNUM}_parcel-kanwisher_space-T1w_contrast-${PARAM}_mask.nii \
    --reference-image ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_desc-preproc_T1w.nii.gz \
    --transform ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5
  done
done
```

Second, warp the Kanwisher ROI masks from MNI152 to T1w.
```bash
ROIDIR="cneuromod-things/fLoc/floc.rois/standard_masks/standard_rois"
OUTDIR="cneuromod-things/fLoc/floc.rois"
SPREPDIR="cneuromod-things/anatomical/anat.smriprep"

for PARAM in body_roi-EBA face_roi-FFA face_roi-OFA face_roi-pSTS scene_roi-MPA scene_roi-OPA scene_roi-PPA
do
  for SUBNUM in 01 02 03 06
  do
    OUTSUB="${OUTDIR}/sub-${SUBNUM}/rois/from_atlas"

    antsApplyTransforms --default-value 0 --dimensionality 3 --float 0 \
    --input ${ROIDIR}/parcel-kanwisher_space-MNI152T1_contrast-${PARAM}_desc-bilat_mask.nii \
    --interpolation Linear \
    --output ${OUTSUB}/sub-${SUBNUM}_parcel-kanwisher_space-T1w_contrast-${PARAM}_desc-bilat_mask.nii \
    --reference-image ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_desc-preproc_T1w.nii.gz \
    --transform ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5

    antsApplyTransforms --default-value 0 --dimensionality 3 --float 0 \
    --input ${ROIDIR}/parcel-kanwisher_space-MNI152T1_contrast-${PARAM}_desc-L_mask.nii \
    --interpolation Linear \
    --output ${OUTSUB}/sub-${SUBNUM}_parcel-kanwisher_space-T1w_contrast-${PARAM}_desc-L_mask.nii \
    --reference-image ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_desc-preproc_T1w.nii.gz \
    --transform ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5

    antsApplyTransforms --default-value 0 --dimensionality 3 --float 0 \
    --input ${ROIDIR}/parcel-kanwisher_space-MNI152T1_contrast-${PARAM}_desc-R_mask.nii \
    --interpolation Linear \
    --output ${OUTSUB}/sub-${SUBNUM}_parcel-kanwisher_space-T1w_contrast-${PARAM}_desc-R_mask.nii \
    --reference-image ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_desc-preproc_T1w.nii.gz \
    --transform ${SPREPDIR}/sub-${SUBNUM}/anat/sub-${SUBNUM}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5
  done
done
```

------------
**Step 4. Create union masks between T1w-warped group ROIs and subjects' t-score maps from the fLoc dataset**

Script: create_subject_rois.py \
Server: beluga \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/floc \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results

Call script within interactive session on beluga (quick), with subject number given as argument
```bash
./launch_createROIs.sh 01
```

**Input**:
- subjects' t-score maps from each series of contrast (kanwisher and nsd) generated in Step 2 (e.g., sub-02_floc_objects_tscore_T1w.nii.gz)
- ROI parcels warped to subjects' native T1w space for each contrast (e.g., sub-03_face_parcels_mni2t1w.nii) computed in Step 3
- subjects' functional union mask used to process the THINGS (not the fLoc union mask!) dataset with GLMsingle (e.g., 01_umask_T1w.nii), so the masked (flattened) voxels are aligned between beta maps and roi maps

**Output**:
- For each subject, for each contrast (face, scene, body, object), an ROI mask (volume) in T1w space that corresponds to the union between the warped group mask and the voxels who's t values are above the specified threshold (e.g., s01_T1w_fLoc_faces_tscore_t5.0.nii.gz). An ROI is calculated for both the Kanwisher (e.g. face > object) and the NSD (face > [object, body. scene, character]) contrast.
- The same contrasts as above, but masked and flattened with the THINGS functional mask used to process the THINGS dataset with GLMsingle, so that matching voxels align between THINGS betas and the fLoc ROIs when both are flattened into 1D vectors (e.g., s03_fLoc_faces_tscore_t5.0_thingsmaskT1w_flat.npy).


------------
**Step 7. Create union masks between T1w-warped binary ROI masks derived from groups and the subjects' own t-score maps derived from the fLoc dataset**

Script: create_subject_rois_perParcel.py \
Server: beluga \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/floc \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results

Call script within interactive session on beluga (quick), with subject number given as argument
```bash
./launch_createROIs_perParcel.sh 01
```

**Input**:
- subjects' t-score maps from each series of contrast (kanwisher, NOT nsd) generated in Step 2 (e.g., sub-02_floc_body-min-object_tscore_T1w.nii.gz)
- ROI parcels warped to subjects' native T1w space for each contrast's parcels of interest (e.g., sub-03_face_FFA_mni2t1w.nii) computed in Step 6
- subjects' functional union mask used to process the THINGS (not the fLoc union mask!) dataset with GLMsingle (e.g., 01_umask_T1w.nii), so the masked (flattened) voxels are aligned between beta maps and roi maps

**Output**:
- For each subject, for each ROI (e.g., face_FFA_L), an ROI binary mask (volume) in T1w space that corresponds to the union between the warped group mask for that parcel and the voxels who's t values are above the specified threshold (e.g., sub-01_fLoc_T1w_face_FFA_t2.5.nii.gz). ROIs are delineated for the Kanwisher (e.g. face > object) contrast (not NSD), bilaterally and per hemisphere.
- The same contrasts as above, but masked and flattened with the THINGS functional mask used to process the THINGS dataset with GLMsingle, so that matching voxels align between THINGS betas and the fLoc ROIs when both are flattened into 1D vectors (e.g., sub-03_fLoc_face_FFA_t2.5_thingsmaskT1w_flat.npy), for bilateral ROIs only.


------------
**Step ??. Visualize ROIs in Pycortex, and draw on flat maps in inkscape...**
