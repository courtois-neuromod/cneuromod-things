fLoc Pipeline
==============================
This pipeline derives subject-specific functional ROIs from the fLoc CNeuromod dataset

**Links and documentation**
- CNeuromod [fLoc task](https://github.com/courtois-neuromod/task_stimuli/blob/main/src/tasks/localizers.py) and [stimuli](https://github.com/courtois-neuromod/floc.stimuli)
- The CNeuromod fLoc task is based on [pyfLoc](https://github.com/NBCLab/pyfLoc),
which was adapted from [VPNL/fLoc](https://github.com/VPNL/fLoc) as published in [Stigliani et al., 2015](https://www.jneurosci.org/content/35/36/12412)
- ROI parcels (improve normalization in CVS space, n=40) were downloaded from the [Kanwisher group](https://web.mit.edu/bcs/nklab/GSS.shtml#download)
- Instructions to convert parcels from CSV (cvs_avg35) to MNI space [here](https://neurostars.org/t/freesurfer-cvs-avg35-to-mni-registration/17581)
- Instructions to convert parcels from MNI to T1w space with fmriprep output [here](https://neurostars.org/t/how-to-transform-mask-from-mni-to-native-space-using-fmriprep-outputs/2880/8)

------------
## Step 1. Generate design matrices from events.tsv files

Build design matrices from a subject's ``*events.tsv`` files in preparation for a GLM analysis on the BOLD data.

Launch the following script, specifying the subject number.
```bash
DATADIR="cneuromod-things/fLoc/floc.fmriprep/sourcedata/floc"
OUTDIR="cneuromod-things/fLoc/floc.rois"

python floc_makedesign.py --data_dir="${DATADIR}" --out_dir="${OUTDIR}" --sub="01"
```

**Input**:
- All of a subject's ``*events.tsv`` files across sessions (~6) and runs (2 per session)\
(e.g., ``sub-03_ses-001_task-fLoc_run-01_events.tsv``)

**Output**:
- ``sub-{sub_num}_task-floc_model-GLM_design.h5``, a HDF5 file with one dataset group per run per session; each group (run) includes three datasets (arrays): 'onset', 'duration' and 'trial_type'

------------
## Step 2. Run first-level GLM in nilearn on fLoc BOLD data using design .h5 files from Step 1

Derive GLM contrasts from multiple sessions and runs of fLoc task with a first-level GLM with nilearn.

Launch the following script, specifying the subject number.
```bash
BOLDDIR="cneuromod-things/fLoc/floc.fmriprep"
OUTDIR="cneuromod-things/fLoc/floc.rois"

python floc_firstLevel_nilearn.py --fLoc_dir="${BOLDDIR}" --out_dir="${OUTDIR}" --smooth --sub="01"
python floc_firstLevel_nilearn.py --fLoc_dir="${BOLDDIR}" --out_dir="${OUTDIR}" --sub="01"
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
> * face > object  
> * scene > object  
> * body > object  
> * object > rest
- The following contrasts are as specified in the NSD data paper, who used a localizer task paradigm similar to ours:
> * face > (object, scene, body, character)
> * scene > (object, face, body, character)
> * body > (object, scene, face, character)
> * character > (object, scene, body, face)
> * object > (face, scene, body, character)

------------
**Step 3. Warp group ROIs from normalized CVS space into T1w native space for each subject**

Script: register_FSrois_2mni.sh \
Server: beluga \
CVS parcels dowloaded from Kanwisher group [here](https://web.mit.edu/bcs/nklab/GSS.shtml#download) \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/floc/parcels_kanwisher \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results

Call script within interactive session on beluga (quick):
```bash
./register_FSrois_2mni.sh
```

**Input**:
- the Kanwisher ROI files for each contrast (face, scene, object, body; e.g., cvs_scene_parcels/cvs_scene_parcels/fROIs-fwhm_5-0.0001.nii)
- Subjects' anatomical scan in native space (e.g., floc.fmriprep/sourcedata/smriprep/sub-01_desc-preproc_T1w.nii.gz)
- the fmriprep inverse transformation file from MNI to T1w (e.g., sub-02_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5)

**Output**:
- For each contrast (face, scene, body, object), an ROI volume in MNI space (e.g., object_parcels_cvs2mni.nii)
- For each subject, for each contrast, an ROI volume in native T1w space (e.g., sub-03_face_parcels_mni2t1w.nii)

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

-----------

**Step 5. Extract unique parcels for specific ROIs (e.g., FFA) from normalized CVS parcel files**

The cvs parcel files each contain many ROIs per contrast. Rather than creating a single file with all the parcels from a single fLoc contrasts, create a separate mask (in cvs_avg35 space) for each region of interest.

Script: split_cvs_parcels_per_ROI.py \
Server: beluga \
CVS parcels dowloaded from Kanwisher group [here](https://web.mit.edu/bcs/nklab/GSS.shtml#download) \
Link to paper [here](https://web.mit.edu/bcs/nklab/media/pdfs/julian.neuroimage.2012.pdf) \

Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/floc/parcels_kanwisher \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results

Call script within interactive session on beluga (quick)
```bash
./launch_splitROIs.sh
```

**Input**:
- the Kanwisher ROI files for each contrast (face, scene, object, body; e.g., cvs_scene_parcels/cvs_scene_parcels/fROIs-fwhm_5-0.0001.nii)
**Output**:
- For each contrast (face, scene, body, object), a series of binary ROI masks in cvs_avg35 space (e.g., scene_OPA_cvs2mni.nii). Note that, for each ROI label, the script produces a left, right and bilateral mask

-----------

**Step 6. Warp separate group ROIs from normalized CVS space into T1w native space for each subject**

Basically like step 3, but to convert separate ROI binary masks from cvs_avg35 space into Tw1 space

Script: register_FSrois_2mni_perParcel.sh \
Server: beluga \
Path to data: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results/results/floc/parcels_kanwisher/cvs_per_ROI \
Path to code dir: /home/mstlaure/projects/rrg-pbellec/mstlaure/things_memory_results

Call script within interactive session on beluga (quick):
```bash
./register_FSrois_2mni_perParcel.sh
```

**Input**:
- the series of binary ROI masks extracted from the Kanwisher contrast files in step 5 (e.g., face_FFA_R_cvs2mni.nii)

**Output**:
- For each ROI, a binary mask (volume) in MNI space (e.g., object_parcels_cvs2mni.nii)
- For each subject, for each ROI, a binary mask (volume) in native T1w space (e.g., sub-03_face_FFA_R_mni2t1w.nii)


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
