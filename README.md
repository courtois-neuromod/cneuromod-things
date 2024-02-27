cneuromod-things
==============================

Data, scripts and derrivatives for the CNeuroMod-THINGS dataset

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
    ├── THINGS                  <- THINGS datasets and scripts
    │    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    │    ├── README.md          <- Overview of THINGS datasets and scripts
    │    ├── data               <- THINGS datasets and derivatives
    │    │   ├── things.fmriprep         <- fmriprep output
    │    │   │    └── sourcedata         <- raw fMRI files
    │    │   │         └── things.raw       
    │    │   │               ├── bidsified raw fMRI data
    │    │   │               ├── things.stimuli
    │    │   │               ├── things.eyetracking
    │    │   │               └── events.tsv files
    │    │   │
    │    │   ├── things.behaviour           <- performance on the image recognition task
    │    │   ├── things.annotations         <- image content annotations and manual
    │    │   └── things.glmsingle           <- glm single derivatives
    │    │
    │    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │    │                         generated with `pip freeze > requirements.txt`
    │    │
    │    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    │    ├── src                <- Source code for use in this project.
    │    │   ├── __init__.py    <- Makes src a Python module
    │    │   │
    │    │   ├── behaviour        <- Behaviour analysis scripts
    │    │   │   └── make_dataset.py
    │    │   │
    │    │   ├── eyetracking       <- Scripts to analyse eye-tracking data
    │    │   │   └── eye_track.py
    │    │   │
    │    │   ├── data           <- fMRI data preparation scripts
    │    │   │   └── make_dataset.py
    │    │   │
    │    │   └── features       <- Scripts to extract betas and noise ceiling
    │    │       └── build_features.py
    │    │
    │    └── tox.ini            <- tox file with settings for running tox; see tox.testrun.org
    │
    └── datapaper          <- Report, figures and visualization notebooks
        ├── figures        <- Generated graphics and figures from the report
        ├── notebooks      <- Code to generate paper figures from data
        └── report         <- Data paper manuscript

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
