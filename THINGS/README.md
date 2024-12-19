THINGS datasets
===============

## CNeuroMod-THINGS task description

Four CNeuroMod participants completed between 33 (`sub-06`) and 36 (`sub-01`, `sub-02`, `sub-03`) fMRI sessions of a continuous recognition task with images from the [THINGS dataset](https://things-initiative.org/). The first session included 3 runs, and all subsequent sessions included 6 runs. Each 4.7 minutes run included 60 trials. For each trial, an image was shown in the center of the screen for 2.98s, followed by a 1.49s ISI. Subjects maintained fixation on a black fixation marker overlaid onto the image center and visible at all times throughout a run. Images were sampled from 720 THINGS categories. `sub-01`, `sub-02`, `sub-03` were shown 6 images per category (4320 unique stimuli), and `sub-06` was shown 5 images for 480 categories and 6 images for the remaining 240 (3840 unique stimuli).  

Each image was shown three times throughout the duration of the experiment (it was repeated once within and once across weekly sessions). For each trial, participants reported whether the image was shown for the first time (“unseen”) or whether it had been shown previously (“seen”), either during the current or a previous session or both. Participants also reported whether or not they felt confident in their answer. Responses (seen/unseen ✕ low/high confidence) were made with the right thumb by pressing one of four buttons (top, bottom, left, right) on a video game controller designed by the team and described in [Harel et al. (2022)](https://psyarxiv.com/m2x6y/). No feedback was given to participants throughout the entire duration of the experiment.

Note: A few sessions were accidentally administered out of the planed order, introducing atypical patterns of repetition for images shown during/after those sessions. Users may want to exclude these sessions from analyses that depend on repetition patterns or memory performance. These include `ses-024`, `ses-025` and `ses-026` for `sub-03`, and `ses-019` to `ses-026` (inclusively) for `sub-06`. fMRI data from `run 6` of `sub-06`'s `ses-008` are excluded from the dataset due to poor brain alignment.

## THINGS/fmriprep

The ``THINGS/fmriprep`` submodule includes bids-formatted bold data preprocessed with fmriprep in MNI and native subject (T1w) space, saved with functional brain masks and noise confounds.

It contains the ``sourcedata/things`` submodule, which includes:
- raw fMRI files
- ``*eyetrack.tsv.gz`` files, timestamped gaze positions per run derived from eye-tracking
- ``*events.tsv`` files with trialwise metrics (e.g., image shown, repeat condition, memory performance, reaction time, trialwise metrics of fixation compliance), whose columns are described in ``THINGS/fmriprep/sourcedata/things/task-things_events.json``
- the ``code`` directory with scripts to process ``*events.tsv`` files and eyetracking files (see ``THINGS/fmriprep/sourcedata/things/code/README.md`` for pipeline description and instructions to run the scripts).
- the ``stimuli`` submodule, which includes image ratings (e.g., size, how natural) and content annotations (e.g., the presence of faces, body parts and elements of scenery; see ``THINGS/fmriprep/sourcedata/things/stimuli/annotations/README.md``), and a placeholder directory to save the THINGS image stimuli (``THINGS/fmriprep/sourcedata/things/stimuli/images_fmri``) needed to run certain scripts. Due to permission requirements, image files must be downloaded directly from the [THINGS initiative database](https://osf.io/jum2f/).

TODO: Explain here how to download and save images from THINGS initiative

TODO: create special branch things.stimuli:
- update annotations readme to describe things+ annotations;
- add things+ annotation files for version control
- remove images
- link to submodule from cneuromod.things

## THINGS/behaviour

The ``THINGS/behaviour`` submodule includes the ``code`` directory with scripts to extract metrics of performance on the continuous recognition task, to assign image ratings and annotations to each task trial, and to derive trial-wise metrics of fixation compliance from eye-tracking data. See ``THINGS/behaviour/README.md`` for pipeline descriptions and instructions to run the various scripts.

``THINGS/behaviour`` also includes ``sub-0*`` directories, which contain subject-specific derivatives. Those include:
- trialwise, run-wise, session-wise and global **metrics of behavioural performance on the memory task** (``THINGS/behaviour/sub-0*/beh/sub-0*_task-things_desc-{perTrial, perRun, perSession, global}_beh.tsv``; see ``THINGS/behaviour/task-things_beh.json`` for column descriptions)
- **trialwise image annotations concatenated across all runs** (``THINGS/behaviour/sub-0*/beh/sub-0*_task-things_desc-perTrial_annotation.tsv``; see ``THINGS/behaviour/task-things_desc-perTrial_annotation.json`` for column descriptions)
- **trialwise fixation compliance metrics derived from eye-tracking data** (``THINGS/behaviour/sub-0*/fix/sub-0*_task-things_desc-fixCompliance_statseries.tsv``; see ``THINGS/behaviour/task-things_desc-fixCompliance_statseries.json`` for column descriptions).


## THINGS/glmsingle

The ``THINGS/glmsingle`` submodule includes the ``code`` directory, which includes three sets of scripts:
- ``qc``,  which compiles measures of framewise displacement between fMRI volumes (see ``THINGS/glmsingle/code/qc/README.md`` for instructions to run the script).
- ``glmsingle``, which computes **trialwise and imagewise beta scores** from cneuromod-things fMRI data using [GLMsingle](https://github.com/cvnlab/GLMsingle) and estimates **voxelwise noise ceilings** (see ``THINGS/glmsingle/code/glmsingle/README.md`` for pipeline description and instructions to run the scripts). For all scripts to run, the [GLMsingle repository](https://github.com/courtois-neuromod/GLMsingle)
needs to be installed as a [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
under ``THINGS/glmsingle/code/glmsingle`` (commit ``c4e298e``).
- ``descriptive``,  which conducts proof-of-principle analyses to showcase the quality of the data (e.g., dimensionality reduction with image annotations, ranking of beta scores per image within visual ROIs) (see ``THINGS/glmsingle/code/descriptive/README.md`` for pipeline description and instructions to run the scripts).

``THINGS/glmsingle`` also includes ``sub-0*`` directories, which contain subject-specific derivatives. Those include:
- input and output files for GLMsingle. Outputs of interest include **trialwise and imagewise beta scores** and **voxelwise noise ceilings** (saved under ``THINGS/glmsingle/sub-0*/glmsingle/output``). See ``THINGS/glmsingle/code/glmsingle/README.md`` for details.
- head motion (framewise displacement) metrics saved under ``THINGS/glmsingle/sub-0*/qc``. See ``THINGS/glmsingle/code/qc/README.md`` for details.
- files used to produce annotated visualisations (t-SNE plots, annotated beta rankings within visual ROIs) under ``THINGS/glmsingle/sub-0*/descriptive``. See ``THINGS/glmsingle/code/descriptive/README.md`` for details. Figures can be generated from these files with notebooks found under ``cneuromod-things/datapaper/notebooks``.
