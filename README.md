cneuromod-things
==============================

Data, scripts and derivatives for the CNeuroMod-THINGS dataset, for which N=4 CNeuroMod participants underwent 33-36 fMRI sessions of a continuous recognition task based on images from the [THINGS dataset](https://things-initiative.org/).

Files related to the main task are found under ``THINGS``:
- ``THINGS/fmriprep`` includes raw and preprocessed bold data, eye-tracking data, ``*events.tsv`` files with trialwise metrics, stimuli and annotations.
- ``THINGS/behaviour`` includes analyses of the subjects' performance on the continuous recognition task and of fixation compliance.
- ``THINGS/glmsingle`` includes fMRI analyses and derivatives, including trialwise and imagewise beta scores estimated with GLMsingle, voxelwise noise ceilings, and proof-of-principle analyses to showcase the quality of the data.  

In addition, this repository includes data, scripts and derivatives from two complementary vision localizer tasks,
``fLoc`` and ``retino`` (population receptive field), used to derive subject-specific ROIs. ``anatomical`` data
that include flat maps to visualize voxelwise statistics on the cortex are also included.

``datapaper`` includes jupyter notebooks with code to re-create figures from the data paper using data and results files saved in the current repository.

TODO: add refs to manuscript

Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for this repository.
    ├── anatomical         <- Anatomical datasets and scripts
    │    ├── README.md          <- Anatomical dataset overview, links to flat map instructions
    │    ├── smriprep           <- smriprep anatomical output
    │    │      ├── sub-0*         
    │    │      │    └── anat   
    │    │      │         └── sub-0*_label-GM_probseg.nii.gz   <- fmriprep grey matter mask  
    │    │      └── sourcedata         
    │    │            └── freesurfer       <- freesurfer output
    │    │                   ├── doc         
    │    │                   │    └── flatmaps.md   <- Instructions to generate flat maps in pycortex
    │    │                   └── sub-0*    
    │    │                        └── surf   
    │    │                              ├── {lh, rh}.full.patch.3d        <- patches to create flat maps       
    │    │                              ├── {lh, rh}.full.flat.patch.3d      
    │    │                              └── {lh, rh}.full.flat.patch.3d.out       
    │    └── pycortex
    │          ├── README.md
    │          ├── doc
    │          │    └── flatmap.md      <- Instructions to generate flat maps in pycortex
    │          └── db     <- database of pycortex files with annotated surfaces that delineate visual ROIs
    │               └── sub-0*
    │                     ├── anatomicals
    │                     ├── surfaces
    │                     ├── transforms    
    │                     └── overlays.svg  <- annotated with manually traced ROIs for sub-01, 02 and 03
    │
    ├── fLoc                  <- fLoc visual localizer dataset and scripts
    │    ├── README.md        <- Overview of fLoc dataset and scripts
    │    ├── fmriprep         <- fmriprep output
    │    │    ├── sub-0*
    │    │    │     └── ses-*
    │    │    │          └── func    <- preprocessed fMRI files in T1w space
    │    │    │               ├── sub-0*_ses-0*_task-fLoc_run-*_space-T1w_desc-preproc_part-mag_bold.nii.gz
    │    │    │               └── sub-0*_ses-0*_task-fLoc_run-*_desc-confounds_part-mag_timeseries.tsv  <- noise confounds
    │    │    │  
    │    │    └── sourcedata     <- raw files
    │    │         └── floc      <- bidsified raw fMRI data & output   
    │    │               ├── sub-0*
    │    │               │     └── ses-*
    │    │               │          └── func
    │    │               │               └── sub-0*_ses-00*_task-fLoc_run-0*_events.tsv  <- events.tsv files
    │    │               └── stimuli
    │    │                     └── images   <- stimulus images per category
    │    │
    │    └── rois               <- fLoc derivative datasets and scripts
    │            ├── code       <- scripts to run glm and generate ROIs
    │            │     ├── README.md    
    │            │     ├── requirements.txt          
    │            │     ├── fLoc_makedesign.py
    │            │     ├── fLoc_firstLevel_nilearn.py  
    │            │     ├── fLoc_split_CVSparcels_perROI.py  
    │            │     └── fLoc_reconcile_parcelMasks.py
    │            │
    │            ├── standard_masks
    │            │     ├── kanwisher_parcels
    │            │     │    ├── cvs            
    │            │     │    │    ├── cvs_body_parcels
    │            │     │    │    ├── cvs_face_parcels
    │            │     │    │    ├── cvs_object_parcels
    │            │     │    │    ├── cvs_scene_parcels
    │            │     │    │    └── readme.txt            
    │            │     │    └── mni            
    │            │     │         └── parcel-kanwisher_space-MNI152T1_res-2mm_contrast-{body, face, object, scene}_mask.nii
    │            │     └── standard_rois  <- unilateral and bilateral ROI masks in CVS and MNI space
    │            │          ├── parcel-kanwisher_space-CVSavg35_contrast-face_roi-{FFA, OFA, pSTS}_desc-{L, R, bilat}_mask.nii
    │            │          ├── parcel-kanwisher_space-MNI152T1_contrast-face_roi-{FFA, OFA, pSTS}_desc-{L, R, bilat}_mask.nii
    │            │          ├── parcel-kanwisher_space-CVSavg35_contrast-scene_roi-{PPA, OPA, MPA}_desc-{L, R, bilat}_mask.nii    
    │            │          ├── parcel-kanwisher_space-MNI152T1_contrast-scene_roi-{PPA, OPA, MPA}_desc-{L, R, bilat}_mask.nii    
    │            │          ├── parcel-kanwisher_space-CVSavg35_contrast-body_roi-EBA_desc-{L, R, bilat}_mask.nii
    │            │          └── parcel-kanwisher_space-MNI152T1_contrast-body_roi-EBA_desc-{L, R, bilat}_mask.nii
    │            │
    │            └── sub-0*
    │                  ├── glm               <- first-level GLM contrast on fLoc BOLD data
    │                  │    ├── sub-*_task-floc_model-GLM_design.h5
    │                  │    ├── sub-*_task-floc_space-T1w_label-brain_desc-unionNonNaN_mask.nii
    │                  │    ├── sub-*_task-floc_space-T1w_label-brain_desc-unionNaN_mask.nii
    │                  │    ├── sub-*_task-floc_space-T1w_model-GLM_stats-{betas, tscores}_contrast-*_desc-smooth_statseries.nii.gz    
    │                  │    └── sub-*_task-floc_space-T1w_model-GLM_stats-{betas, tscores}_contrast-*_desc-unsmooth_statseries.nii.gz
    │                  └── rois
    │                       ├── from_atlas       <- Kanwisher parcels and ROI masks warped to subject space
    │                       │     ├── sub-*_parcel-kanwisher_space-T1w_contrast-{body, face, object, scene}_mask.nii    
    │                       │     ├── sub-*_parcel-kanwisher_space-T1w_contrast-face_roi-{FFA, OFA, pSTS}_desc-{L, R, bilat}_mask.nii   
    │                       │     ├── sub-*_parcel-kanwisher_space-T1w_contrast-scene_roi-{PPA, OPA, MPA}_desc-{L, R, bilat}_mask.nii    
    │                       │     └── sub-*_parcel-kanwisher_space-T1w_contrast-body_roi-EBA_desc-{L, R, bilat}_mask.nii
    │                       └── task-derived     <- parcels and ROI masks derived from the fLoc task
    │                             ├── sub-*_task-floc_space-T1w_stats-tscores_contrast-*_cutoff-*_desc-smooth_mask.nii.gz    
    │                             ├── sub-*_task-floc_space-T1w_stats-tscores_contrast-*_cutoff-*_desc-unsmooth_mask.nii.gz
    │                             ├── sub-*_task-floc_space-T1w_stats-tscores_contrast-*_roi-*_cutoff-*_nvox-*_fwhm-*_ratio-*_desc-smooth_mask.nii.gz
    │                             └── sub-*_task-floc_space-T1w_stats-tscores_contrast-*_roi-*_cutoff-*_nvox-*_fwhm-*_ratio-*_desc-unsmooth_mask.nii.gz
    │
    ├── retinotopy              <- retinotopy (pRF) visual localizer datasets and scripts
    │    ├── README.md          <- Overview of retinotopy dataset and scripts
    │    ├── fmriprep           <- retinotopy fmriprep output
    │    │    ├── sub-0*
    │    │    │     └── ses-*
    │    │    │          └── func    <- preprocessed fMRI files in T1w space
    │    │    │               ├── sub-0*_ses-0*_task-{bars, rings, wedges}_space-T1w_desc-preproc_part-mag_bold.nii.gz
    │    │    │               └── sub-0*_ses-0*_task-{bars, rings, wedges}_desc-confounds_timeseries.tsv  <- noise confounds
    │    │    │  
    │    │    └── sourcedata         <- raw files
    │    │         └── retinotopy    <- bidsified raw fMRI data & output   
    │    │               ├── sub-0*
    │    │               │     └── ses-*
    │    │               │          └── func
    │    │               │               └── sub-0*_ses-*_task-{bars, rings, wedges}_events.tsv  <- events.tsv files
    │    │               └── stimuli
    │    │                     ├── {grid, images, scenes}.npz
    │    │                     └── apertures_{bars, ring, wedge_newtr}.npz
    │    │
    │    └── prf                  <- population receptive fiels scripts and derivatives (e.g., visual ROIs)
    │         ├── code            <- scripts to run glm single and process output
    │         │     ├── README.md    
    │         │     ├── requirements.txt          
    │         │     ├── analyzePRF   <- analyzePRF repo submodule (a3ac908)  
    │         │     ├── retino_make_apertureMasks.py
    │         │     ├── retino_prepare_BOLD.py
    │         │     ├── retino_run_analyzePRF.m
    │         │     └── retino_reassamble_voxels.py
    │         │
    │         ├── apertures       <- aperture masks that delineate task field of view
    │         │     ├── task-retinotopy_condition-bars_desc-perTR_apertures.mat
    │         │     ├── task-retinotopy_condition-rings_desc-perTR_apertures.mat
    │         │     └── task-retinotopy_condition-wedges_desc-perTR_apertures.mat
    │         │
    │         └── sub-0*
    │               ├── prf       <- population receptive fields input and output files
    │               │    ├── input
    │               │    │     ├── sub-0*_task-retinotopy_space-T1w_label-brain_desc-unionNaN_mask.nii    
    │               │    │     ├── sub-0*_task-retinotopy_space-T1w_label-brain_desc-unionNonNaN_mask.nii    
    │               │    │     └── chunks    
    │               │    │            ├── sub-0*_task-retinotopy_condition-bars_space-T1w_desc-chunk{chunk_num}_bold.mat
    │               │    │            ├── sub-0*_task-retinotopy_condition-rings_space-T1w_desc-chunk{chunk_num}_bold.mat    
    │               │    │            └── sub-0*_task-retinotopy_condition-wedges_space-T1w_desc-chunk{chunk_num}_bold.mat
    │               │    └── output
    │               │          ├── sub-0*_task-retinotopy_space-T1w_model-analyzepRF_label-brain_stats-{stat}_statseries.nii.gz
    │               │          ├── sub-0*_task-retinotopy_space-T1w_model-analyzePRF_label-brain_stats-{stat}_desc-npythy_statseries.nii.gz
    │               │          └── chunks    
    │               │                 ├── sub-*_task-retinotopy_space-T1w_model-analyzePRF_stats-ang_desc-chunk{chunk_num}_statseries.mat
    │               │                 ├── sub-*_task-retinotopy_space-T1w_model-analyzePRF_stats-ecc_desc-chunk{chunk_num}_statseries.mat   
    │               │                 ├── sub-0*_task-retinotopy_space-T1w_model-analyzePRF_stats-rfsize_desc-chunk{chunk_num}_statseries.mat
    │               │                 └── sub-0*_task-retinotopy_space-T1w_model-analyzePRF_stats-R2_desc-chunk{chunk_num}_statseries.mat
    │               ├── npythy       <- NeuroPythy toolbox input and output files
    │               │    ├── input
    │               │    │     ├── lh.s*_prf_{ang, ecc, x, y, R2, rfsize}.mgz      
    │               │    │     └── rh.s*_prf_{ang, ecc, x, y, R2, rfsize}.mgz
    │               │    └── output
    │               │          ├── inferred_{angle, eccen, sigma, varea}.mgz
    │               │          ├── {lh, rh}.inferred_{angle, eccen, sigma, varea}.mgz
    │               │          ├── {lh, rh}.retinotopy.sphere.reg
    │               │          ├── inferred_{angle, eccen, sigma, varea}_fsorient.nii.gz
    │               │          ├── sub-*_task-retinotopy_space-T1w_res-anat_model-npythy_atlas-varea_dseg.nii.gz   
    │               │          ├── sub-*_task-retinotopy_space-T1w_res-anat_model-npythy_stats-{angle, eccen, sigma}_statseries.nii.gz           
    │               │          ├── sub-*_task-retinotopy_space-T1w_res-func_model-npythy_atlas-varea_dseg.nii.gz    
    │               │          └── sub-*_task-retinotopy_space-T1w_res-func_model-npythy_stats-{angle, eccen, sigma}_statseries.nii.gz
    │               └── rois       <- visual ROI masks    
    │                    ├── sub-*_task-retinotopy_space-T1w_model-npythy_label-{roi}_desc-nn_mask.nii.gz
    │                    └── sub-*_task-retinotopy_space-T1w_model-npythy_label-{roi}_desc-linear_mask.nii.gz
    │
    ├── THINGS                    <- THINGS datasets, scripts and derivatives
    │    ├── README.md            <- Overview of THINGS datasets and scripts
    │    ├── fmriprep      <- fmriprep output
    │    │    ├── sub-0*
    │    │    │     └── ses-*
    │    │    │          └── func    <- preprocessed fMRI files in MNI and T1w space
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-MNI152NLin2009cAsym_desc-preproc_part-mag_bold.nii.gz
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-MNI152NLin2009cAsym_desc-brain_part-mag_mask.nii.gz
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-T1w_desc-preproc_part-mag_bold.nii.gz
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-T1w_desc-brain_part-mag_mask.nii.gz    
    │    │    │               └── sub-0*_ses-*_task-things_run-*_desc-confounds_part-mag_timeseries.tsv    <- noise confounds
    │    │    │  
    │    │    └── sourcedata      <- raw files
    │    │         └── things     <- bidsified raw fMRI data & output   
    │    │               ├── sub-0*
    │    │               │     └── ses-*
    │    │               │          └── func
    │    │               │               ├── sub-0*_ses-*_task-things_run-*_eyetrack.tsv.gz  <- eye-tracking files
    │    │               │               └── sub-0*_ses-*_task-things_run-*_events.tsv  <- events.tsv files
    │    │               ├── stimuli
    │    │               │     ├── images_fmri <- stimulus images per category
    │    │               │     └── annotations <- image annotations
    │    │               │            ├── README.md    <- annotation doc, links to download THINGS+ ratings
    │    │               │            ├── THINGS+      <- download annotations directly from THINGS+ database
    │    │               │            │     ├── arousal_meanRatings.tsv
    │    │               │            │     ├── category53_wideFormat.tsv
    │    │               │            │     ├── imageLabeling_imageWise.tsv  
    │    │               │            │     ├── imageLabeling_objectWise.tsv
    │    │               │            │     ├── objectProperties_meanRatings.tsv  
    │    │               │            │     ├── size_meanRatings.tsv    
    │    │               │            │     └── things_concepts.tsv   
    │    │               │            ├── task-things_desc-manual_annotation.json
    │    │               │            └── task-things_desc-manual_annotation.tsv
    │    │               ├── code
    │    │               │     ├── README.md
    │    │               │     ├── cleanup             <- scripts to validate events.tsv files    
    │    │               │     │      ├── requirements.txt       
    │    │               │     │      ├── qc_notes.md          <- notes on QCing runs & sessions        
    │    │               │     │      └── clean_events.py      <- script to relabel/clean *events.tsv files
    │    │               │     └── eyetracking         <- scripts to process eye-tracking data
    │    │               │            ├── requirements.txt    
    │    │               │            ├── step1_eyetrack_prep.py      <- exports raw gaze to numpy, plots qc charts        
    │    │               │            ├── step2_eyetrack_prep.py      <- drift corrects, exports gaze and fixation metrics
    │    │               │            ├── step3_reconcile_events.py   <- add fixation metrics to events files
    │    │               │            └── utils.py                    <- support functions
    │    │               │    
    │    │               └── task-things_events.json       <- defines columns in events.tsv files
    │    │
    │    ├── behaviour        <- performance on the image recognition task & fixation compliance
    │    │       ├── README.md
    │    │       ├── code
    │    │       │     ├── requirements.txt
    │    │       │     ├── analyze_fixations.py        <- processes trial-wise fixations
    │    │       │     ├── behav_data_annotate.py      <- builds trial-wise image annotations   
    │    │       │     └── behav_data_extract.py       <- computes memory scores from events.tsv files
    │    │       ├── sub-0*
    │    │       │     ├── fix
    │    │       │     │    ├── sub-0*_task-things_desc-fixCompliance_statseries.tsv
    │    │       │     │    └── sub-0*_task-things_desc-driftCor_gaze.tsv
    │    │       │     └── beh
    │    │       │          ├── sub-0*_task-things_desc-perTrial_annotation.tsv      
    │    │       │          ├── sub-0*_task-things_catNum.tsv  
    │    │       │          ├── sub-0*_task-things_imgNum.tsv  
    │    │       │          ├── sub-0*_task-things_desc-perTrial_beh.tsv    
    │    │       │          ├── sub-0*_task-things_desc-perRun_beh.tsv    
    │    │       │          ├── sub-0*_task-things_desc-perSession_beh.tsv    
    │    │       │          └── sub-0*_task-things_desc-global_beh.tsv    
    │    │       ├── task-things_desc-perTrial_annotation.json
    │    │       ├── task-things_desc-fixCompliance_statseries.json    
    │    │       └── task-things_beh.json
    │    │
    │    └── glmsingle        <- GLMsingle derivatives (voxel-wise betas, noise ceilings)
    │            ├── code            <- scripts to run GLMsingle and process output
    │            │     ├── requirements.txt      
    │            │     ├── qc
    │            │     │    ├── README.md               
    │            │     │    └── compile_headmotion.py   
    │            │     ├── glmsingle       
    │            │     │    ├── GLMsingle  <- GLMsingle repo submodule (c4e298e)    
    │            │     │    ├── README.md       
    │            │     │    ├── GLMsingle_makedesign.py                   
    │            │     │    ├── GLMsingle_preprocBOLD.py
    │            │     │    ├── GLMsingle_makerunlist.py  
    │            │     │    ├── GLMsingle_cleanmask.py  
    │            │     │    ├── GLMsingle_run.m    
    │            │     │    ├── GLMsingle_noiseceilings.py          
    │            │     │    ├── GLMsingle_betasPerTrial.py  
    │            │     │    └── GLMsingle_betasPerImg.py
    │            │     └── descriptive    
    │            │          ├── README.md         
    │            │          ├── extract_annotations.py  
    │            │          ├── rank_img_perVox.py  
    │            │          └── beta_scaling.py        
    │            │
    │            ├── task-things_runlist.h5             <- list of valid runs per subject
    │            ├── task-things_imgAnnotations.json    <- dictionary of compiled image annotations
    │            │
    │            └── sub-0*
    │                  ├── glmsingle  <- GLMsingle input and output (voxelwise betas, noise ceilings)
    │                  │    ├── input    
    │                  │    │     ├── sub-*_task-things_model-glmsingle_desc-sparse_design.h5
    │                  │    │     ├── sub-*_task-things_imgDesignNumbers.json
    │                  │    │     ├── sub-*_task-things_space-T1w_maskedBOLD.h5     
    │                  │    │     ├── sub-*_task-things_space-T1w_label-brain_desc-union_mask.nii
    │                  │    │     ├── sub-*_task-things_space-T1w_label-brain_desc-unionNonNaN_mask.nii
    │                  │    │     ├── sub-*_task-things_space-T1w_label-brain_desc-unionNaN_mask.nii
    │                  │    │     └── ...    
    │                  │    └── output    
    │                  │          ├── T1w
    │                  │          │     ├── TYPEA_ONOFF.mat    
    │                  │          │     ├── TYPEB_FITHRF.mat   
    │                  │          │     ├── TYPEC_FITHRF_GLMDENOISE.mat
    │                  │          │     └── TYPED_FITHRF_GLMDENOISE_RR.mat  
    │                  │          ├── sub-0*_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-imageBetas_desc-zscore_statseries.h5  
    │                  │          ├── sub-0*_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-imageBetas_statseries.h5  
    │                  │          ├── sub-0*_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-trialBetas_desc-zscore_statseries.h5
    │                  │          ├── sub-0*_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-trialBetas_statseries.h5        
    │                  │          └── sub-0*_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz
    │                  │
    │                  ├── qc     <- quality checks
    │                  │    └── sub-0*_task-things_headmotion.tsv
    │                  └── descriptive   <- annotated beta rankings and t-SNE plots per visual ROIs
    │                       ├── sub-*_task-things_desc-{perImage, perTrial}_labels.npy
    │                       ├── sub-*_task-things_space-T1w_stats-{betas, ranks}_desc-{perImage, perTrial}_statseries.npy
    │                       ├── sub-*_task-things_space-T1w_contrast-*_roi-*_cutoff-*_nvox-*_stats-{ranks, betas, noiceCeilings}_desc-{perImage, perTrial}_statseries.npy  
    │                       └── sub-*_task-things_space-T1w_stats-tSNE_label-visualROIs_desc-{perImage, perTrial}_statseries.npz    
    │            
    │
    └── datapaper          <- Report, figures, visualization notebooks
        ├── figures        <- Graphics and figures from the report
        ├── notebooks      <- Code to generate datapaper figures
        │       ├── behav_analysis.ipynb        <- behav figures     
        │       ├── beta_ranking.ipynb          <- beta ranking figures          
        │       ├── beta_dimReduction.ipynb     <- beta t-SNE plots    
        │       ├── fixation_compliance.ipynb   <- gaze position distribution  
        │       ├── noiseCeil_flatmaps.ipynb    <- noise ceilings projected on cortical flat maps    
        │       └── head_motion.ipynb           <- framewise displacement figs  
        └── report         <- Data paper manuscript     <- TODO

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
