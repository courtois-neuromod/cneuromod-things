cneuromod-things
==============================

Data, scripts and derivatives for the CNeuroMod-THINGS dataset

TODO: Add task and dataset description

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
    │    │    │               ├── sub-0*_ses-*_task-things_run-*_space-T1w_desc-preproc_part-mag_bold.nii.gz
    │    │    │               └── sub-0*_ses-*_task-things_run-*_desc-confounds_part-mag_timeseries.tsv  <- noise confounds
    │    │    │  
    │    │    └── sourcedata         <- raw files
    │    │         └── things    <- bidsified raw fMRI data & output   
    │    │               ├── sub-0*
    │    │               │     └── ses-*
    │    │               │          └── func
    │    │               │               ├── sub-0*_ses-*_task-thingsmemory_run-*_eyetrack.tsv.gz  <- eyetracking files
    │    │               │               └── sub-0*_ses-*_task-thingsmemory_run-*_events.tsv  <- events.tsv files
    │    │               ├── things.stimuli
    │    │               │     └── things.annotations <- image content annotations and manual
    │    │               ├── code
    │    │               │     ├── README.md
    │    │               │     ├── requirements.txt    
    │    │               │     ├── eyetracking       <- scripts to process eyetracking data    
    │    │               │     └── events_relabel.py  <- script to relabel *events.tsv files
    │    │               ├── task-things_eyetrack_description.json
    │    │               └── task-things_events_description.json
    │    │
    │    ├── things.behaviour        <- performance on the image recognition task
    │    │       ├── code
    │    │       │     ├── README.md    
    │    │       │     ├── requirements.txt        
    │    │       │     └── behav_data_extract.py    <- computes behav scores from events.tsv files
    │    │       ├── sub-0*
    │    │       │     └── beh
    │    │       │          ├── sub-0*_task-things_desc-score-per-trial_beh.tsv    
    │    │       │          ├── sub-0*_task-things_desc-score-per-run_beh.tsv    
    │    │       │          ├── sub-0*_task-things_desc-score-per-session_beh.tsv    
    │    │       │          └── sub-0*_task-things_desc-score-global_beh.tsv    
    │    │       └── task-things_beh_dataset_description.json
    │    │
    │    └── things.glmsingle        <- glm single derivatives
    │            ├── code            <- scripts to run glm single and process output
    │            │     ├── README.md    
    │            │     ├── requirements.txt        
    │            │     ├── preprocessing    
    │            │     ├── glmsingle        
    │            │     └── noiseceilings    
    │            │
    │            └── sub-0*
    │                  ├── temp_files   <- intermediate steps
    │                  │    └── ...
    │                  ├── GLMsingle
    │                  │    ├── TYPEA_ONOFF.mat    
    │                  │    ├── TYPEB_FITHRF.mat   
    │                  │    ├── TYPEC_FITHRF_GLMDENOISE.mat
    │                  │    ├── TYPED_FITHRF_GLMDENOISE_RR.mat  
    │                  │    ├── sub-0*_task-things_headmotion.tsv       
    │                  │    ├── sub-0*_task-things_space-T1w_res-func_desc-betas-per-img.h5  
    │                  │    ├── sub-0*_task-things_space-T1w_res-func_desc-betas-per-trial.h5  
    │                  │    ├── sub-0*_task-things_space-T1w_res-func_desc-GM_mask.nii.gz  
    │                  │    └── sub-0*_task-things_space-T1w_res-func_modelD_noise-ceilings.mat
    │                  │
    │                  ├── top_image
    │                  │    └── ...
    │                  └── tsne
    │                       └── ...
    │            
    │
    └── datapaper          <- Report, figures, visualization notebooks
        ├── figures        <- Graphics and figures from the report
        ├── notebooks      <- Code to generate figures from the data
        └── report         <- Data paper manuscript

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
