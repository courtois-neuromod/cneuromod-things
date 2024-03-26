cneuromod-things
==============================

Data, scripts and derivatives for the CNeuroMod-THINGS dataset, for which N=4 CNeuroMod participants underwent 33-36 fMRI sessions of a continuous recognition task based on images from the [THINGS dataset](https://things-initiative.org/).

Files related to the main task are found under ``THINGS``:
- ``things.fmriprep`` includes raw and preprocessed bold data, eye-tracking data, ``*events.tsv`` files with trialwise metrics, stimuli and annotations.
- ``things.behaviour`` includes analyses of the subjects' performance on the continuous recognition task.
- ``things.glmsingle`` includes fMRI analyses and derivatives, including trialwise and imagewise beta scores estimated with GLMsingle, voxelwise noise ceilings, and proof-of-principle analyses to showcase the quality of the data.  

In addition, this repository includes data, scripts and derivatives from two complementary vision localizer tasks,
``fLoc`` and ``retino`` (population receptive field), used to derive subject-specific ROIs. ``anatomical`` data
that include flat maps to visualize voxelwise statistics on the cortex are also included.

``datapaper`` includes jupyter notebooks with code to re-create figures from the data paper using data files saved in the current repository.

TODO: add refs to manuscript

Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for this repository.
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    ├── anatomical         <- Anatomical datasets and scripts
    │    ├── README.md          <- Anatomical dataset overview, including links to instructions for flat maps
    │    ├── anat.smriprep         <- smriprep anatomical output
    │    ├── anat.freesurfer       <- freesurfer output, patches to generate flat maps
    │    │      └── doc         
    │    │           └── flatmaps.md   <- Instructions to generate flat maps in pycortex
    │    └── anat.pycortex         <- pycortex database with annotated surfaces that delineate visual ROIs
    │
    ├── floc                    <- fLoc visual localizer datasets and scripts
    │    ├── README.md          <- Overview of fLoc dataset and scripts
    │    ├── floc.fmriprep         <- fmriprep output
    │    │    ├── sub-0*
    │    │    │     └── ses-*
    │    │    │          └── func    <- preprocessed fMRI files in T1w space
    │    │    │               ├── sub-0*_ses-0*_task-fLoc_run-*_space-T1w_desc-preproc_part-mag_bold.nii.gz
    │    │    │               └── sub-0*_ses-0*_task-fLoc_run-*_desc-confounds_part-mag_timeseries.tsv  <- noise confounds
    │    │    │  
    │    │    └── sourcedata         <- raw files
    │    │         └── floc    <- bidsified raw fMRI data & output   
    │    │               ├── sub-0*
    │    │               │     └── ses-*
    │    │               │          └── func
    │    │               │               └── sub-0*_ses-00*_task-fLoc_run-0*_events.tsv  <- events.tsv files
    │    │               └── floc.stimuli
    │    │                     └── images   <- stimulus images per category
    │    │
    │    └── floc.rois        <- fLoc scripts and datasets
    │            ├── code            <- scripts to run glm and generate ROIs
    │            │     ├── README.md    
    │            │     ├── requirements.txt          
    │            │     ├── run_glm    
    │            │     └── make_rois    
    │            │
    │            └── sub-0*
    │                  ├── glm
    │                  │    └── ...
    │                  └── rois
    │                       └── ...
    │
    ├── retino                  <- retinotopy (PRF) visual localizer datasets and scripts
    │    ├── README.md          <- Overview of retinotopy dataset and scripts
    │    ├── retino.fmriprep         <- fmriprep output
    │    │    ├── sub-0*
    │    │    │     └── ses-*
    │    │    │          └── func    <- preprocessed fMRI files in T1w space
    │    │    │               ├── sub-0*_ses-0*_task-{bars, rings, wedges}_space-T1w_desc-preproc_part-mag_bold.nii.gz
    │    │    │               └── sub-0*_ses-0*_task-{bars, rings, wedges}_desc-confounds_timeseries.tsv  <- noise confounds
    │    │    │  
    │    │    └── sourcedata         <- raw files
    │    │         └── retino    <- bidsified raw fMRI data & output   
    │    │               ├── sub-0*
    │    │               │     └── ses-*
    │    │               │          └── func
    │    │               │               └── sub-0*_ses-*_task-{bars, rings, wedges}_events.tsv  <- events.tsv files
    │    │               └── retino.stimuli
    │    │                     ├── images
    │    │                     └── apertures
    │    │
    │    └── retino.prf        <- prf and visual ROIs scripts and datasets
    │            ├── code            <- scripts to run glm single and process output
    │            │     ├── README.md    
    │            │     ├── requirements.txt          
    │            │     ├── run_prf    
    │            │     └── make_rois    
    │            │
    │            └── sub-0*
    │                  ├── temp_files   <- intermediate steps
    │                  │    └── ...
    │                  ├── rois
    │                  │    └── ...
    │                  └── prf
    │                       └── ...
    │
    ├── THINGS                  <- THINGS datasets, scripts and derivatives
    │    ├── README.md          <- Overview of THINGS datasets and scripts
    │    ├── things.fmriprep         <- fmriprep output
    │    │    ├── sub-0*
    │    │    │     └── ses-*
    │    │    │          └── func    <- preprocessed fMRI files in MNI and T1w space
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-MNI152NLin2009cAsym_desc-preproc_part-mag_bold.nii.gz
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-MNI152NLin2009cAsym_desc-brain_part-mag_mask.nii.gz
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-T1w_desc-preproc_part-mag_bold.nii.gz
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-T1w_desc-brain_part-mag_mask.nii.gz    
    │    │    │               └── sub-0*_ses-*_task-things_run-*_desc-confounds_part-mag_timeseries.tsv    <- noise confounds
    │    │    │  
    │    │    └── sourcedata         <- raw files
    │    │         └── things    <- bidsified raw fMRI data & output   
    │    │               ├── sub-0*
    │    │               │     └── ses-*
    │    │               │          └── func
    │    │               │               ├── sub-0*_ses-*_task-thingsmemory_run-*_eyetrack.tsv.gz  <- eyetracking files
    │    │               │               └── sub-0*_ses-*_task-thingsmemory_run-*_events.tsv  <- events.tsv files
    │    │               ├── things.stimuli
    │    │               │     └── annotations <- image content annotations
    │    │               │            ├── README.md    <- manual annotation doc, links to download THINGS+ ratings
    │    │               │            ├── THINGS+  * download dset directly from THINGS+ database
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
    │    │               │     ├── requirements.txt    
    │    │               │     ├── eyetracking            <- scripts to process eyetracking data    
    │    │               │     ├── qc_notes.md       <- notes on QCing runs & sessions        
    │    │               │     └── clean_events.py        <- script to relabel/clean *events.tsv files
    │    │               ├── task-things_desc-wEyetrack_events.json  <- TODO: simplify
    │    │               └── task-things_events.json
    │    │
    │    ├── things.behaviour        <- performance on the image recognition task
    │    │       ├── README.md
    │    │       ├── code
    │    │       │     ├── requirements.txt
    │    │       │     ├── behav_data_annotate.py      <- builds trial-wise annotations   
    │    │       │     └── behav_data_extract.py       <- computes behav scores from events.tsv files
    │    │       ├── sub-0*
    │    │       │     └── beh
    │    │       │          ├── sub-0*_task-things_desc-perTrial_annotation.tsv      
    │    │       │          ├── sub-0*_task-things_catNum.tsv  
    │    │       │          ├── sub-0*_task-things_imgNum.tsv  
    │    │       │          ├── sub-0*_task-things_desc-perTrial_beh.tsv    
    │    │       │          ├── sub-0*_task-things_desc-perRun_beh.tsv    
    │    │       │          ├── sub-0*_task-things_desc-perSession_beh.tsv    
    │    │       │          └── sub-0*_task-things_desc-global_beh.tsv    
    │    │       ├── task-things_desc-perTrial_annotation.json
    │    │       └── task-things_beh.json
    │    │
    │    └── things.glmsingle        <- glm single derivatives
    │            ├── code            <- scripts to run glm single and process output
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
    │            │          └── ...        
    │            │
    │            ├── task-things_runlist.h5    <- list of valid runs per subject
    │            │
    │            └── sub-0*
    │                  ├── glmsingle
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
    │                  │          ├── sub-0*_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz.nii.gz  
    │                  │          └── sub-0*_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.mat
    │                  │
    │                  ├── qc   <- quality checks
    │                  │    └── sub-0*_task-things_headmotion.tsv
    │                  ├── top_image
    │                  │    └── ...
    │                  └── tsne
    │                       └── ...
    │            
    │
    └── datapaper          <- Report, figures, visualization notebooks
        ├── figures        <- Graphics and figures from the report
        ├── notebooks      <- Code to generate datapaper figures
        │       ├── behav_analysis.ipynb      <- behav figures     
        │       └── head_motion.ipynb         <- framewise displacement figs    
        └── report         <- Data paper manuscript

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
