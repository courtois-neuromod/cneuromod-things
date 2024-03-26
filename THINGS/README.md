THINGS datasets
===============

## CNeuroMod-THINGS task description

N=4 participants completed between 33 (`sub-06`) and 36 (`sub-01`, `sub-02`, `sub-03`) fMRI sessions of a continuous recognition task with images from the [THINGS dataset](https://things-initiative.org/). The first session included 3 runs, and all subsequent sessions included 6 runs. Each 4.7 minutes run included 60 trials. For each trial, an image was shown in the center of the screen for 2.98s, followed by a 1.49s ISI. Subjects maintained fixation on a black fixation marker overlaid onto the image center and visible at all times throughout a run. Images were sampled from 720 THINGS categories. `sub-01`, `sub-02`, `sub-03` were shown 6 images per category (4320 unique stimuli), and `sub-06` was shown 5 images for 480 categories and 6 images for the remaining 240 (3840 unique stimuli).  

Each image was shown three times throughout the duration of the experiment (it was repeated once within and once across weekly sessions). For each trial, participants reported whether the image was shown for the first time (“unseen”) or whether it had been shown previously (“seen”), either during the current or a previous session or both. Participants also reported whether or not they felt confident in their answer. Responses (seen/unseen ✕ low/high confidence) were made with the right thumb by pressing one of four buttons (top, bottom, left, right) on a video game controller designed by the team and described in [Harel et al. (2022)](https://psyarxiv.com/m2x6y/). No feedback was given to participants throughout the entire duration of the experiment.

:::{important}
A few sessions were accidentally administered out of the planed order, introducing atypical patterns of repetition for images shown during/after those sessions. Users may want to exclude these sessions from analyses that depend on repetition patterns or memory performance. These include `ses-024`, `ses-025` and `ses-026` for `sub-03`, and `ses-019` to `ses-026` (inclusively) for `sub-06`. fMRI data from `run 6` of `sub-06`'s `ses-008` are excluded from the dataset due to poor brain alignment.
:::

## things.fmriprep

``things.fmriprep`` includes bids-formatted bold data processed with fmriprep in MNI and subject (T1w) space, saved along functional brain masks and noise confounds. The ``sourcedata/things`` submodule includes raw fMRI files, ``*eyetrack.tsv.gz`` files (timestamped gaze positions derived from eye-tracking), ``*events.tsv`` files with trialwise metrics (as described in ``things.fmriprep/sourcedata/things/task-things_events.json``), and scripts to process ``events.tsv`` and eyetracking files.

``sourcedata/things`` also contains the ``things.stimuli`` submodule, which includes image stimuli and image content annotations. Due to permission issues, images and some annotations must be downloaded directly through the [THINGS initiative database](https://osf.io/jum2f/).

## things.behaviour

``things.behaviour`` includes analyses (scripts and output files) of the subjects' performance on the continuous recognition task. Code that associates image ratings and annotations to each fMRI trial is also included.

## things.glmsingle

``things.glmsingle`` includes fMRI analyses and derivatives, including scripts, intermediate steps (e.g., design matrices), and the following output files : trialwise and imagewise beta scores estimated with GLMsingle, voxelwise noise ceilings, and proof-of-principle analyses to showcase the quality of the data.  
