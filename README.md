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
    │    ├── data               <- Anatomical datasets
    │    │   ├── anat.smriprep         <- smriprep anatomical output
    │    │   ├── anat.freesurfer       <- freesurfer output, patches to generate flat maps
    │    │   └── anat.pycortex         <- pycortex database with annotated surface maps with visual ROIs
    │    │
    │    └── doc         
    │         └── flatmaps.md   <- Instructions to generate flat maps in pycortex
    │
    ├── fLoc                    <- fLoc visual localizer datasets and scripts
    │    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    │    ├── README.md          <- fLoc readme with overview of dataset and scripts
    │    ├── data               <- fLoc dataset and derivatives
    │    │   ├── fLoc.fmriprep         <- fmriprep output
    │    │   │    └── sourcedata          <- raw fMRI files
    │    │   │         └── fLoc.raw       
    │    │   │               ├── bidsified raw fMRI data
    │    │   │               ├── fLoc.stimuli
    │    │   │               └── events.tsv files
    │    │   │
    │    │   ├── fLoc.glm        <- glm single files
    │    │   └── fLoc.rois       <- ROIs with categorical preferences
    │    │
    │    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │    │                         generated with `pip freeze > requirements.txt`
    │    │
    │    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    │    ├── src                <- Source code for use in this project.
    │    │   ├── __init__.py    <- Makes src a Python module
    │    │   │
    │    │   ├── data           <- Data preparation scripts
    │    │   │   └── make_dataset.py
    │    │   │
    │    │   └── features       <- Scripts to build and organize features
    │    │       └── build_features.py
    │    │
    │    └── tox.ini            <- tox file with settings for running tox; see tox.testrun.org    
    │
    ├── retino                  <- retinotopy (PRF) visual localizer datasets and scripts
    │    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    │    ├── README.md          <- Overview of retinotopy dataset and scripts
    │    ├── data               <- retinotopy dataset and derivatives
    │    │   ├── retino.fmriprep         <- fmriprep output
    │    │   │    └── sourcedata         <- raw fMRI files
    │    │   │         └── retino.raw       
    │    │   │               ├── bidsified raw fMRI data
    │    │   │               ├── retino.stimuli
    │    │   │               └── events.tsv files
    │    │   │
    │    │   ├── retino.prf        <- prf files
    │    │   └── retino.rois       <- ROIs from  PRF results
    │    │
    │    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │    │                         generated with `pip freeze > requirements.txt`
    │    │
    │    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    │    ├── src                <- Source code for use in this project.
    │    │   ├── __init__.py    <- Makes src a Python module
    │    │   │
    │    │   ├── data           <- Data preparation scripts
    │    │   │   └── make_dataset.py
    │    │   │
    │    │   └── features       <- Scripts to build and organize features
    │    │       └── build_features.py
    │    │
    │    └── tox.ini            <- tox file with settings for running tox; see tox.testrun.org
    │
    ├── THINGS                  <- THINGS datasets, scripts and derivatives
    │    ├── README.md          <- Overview of THINGS datasets and scripts
    │    ├── things.fmriprep         <- fmriprep output
    │    │    └── sourcedata         <- raw fMRI files
    │    │         └── things.raw       
    │    │               ├── bidsified raw fMRI data
    │    │               ├── things.stimuli
    │    │               │     └── things.annotations <- image content annotations and manual
    │    │               ├── bidsified eyetracking data
    │    │               └── cleaned up events.tsv files
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
    │    │       └── task-thingsmemory_beh_dataset_description.json
    │    │
    │    └── things.glmsingle        <- glm single derivatives
    │
    └── datapaper          <- Report, figures and visualization notebooks
        ├── figures        <- Generated graphics and figures from the report
        ├── notebooks      <- Code to generate paper figures from data
        └── report         <- Data paper manuscript

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
