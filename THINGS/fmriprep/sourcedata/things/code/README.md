THINGS events.tsv and eye-tracking analyses
===========================================

# Events.tsv files validation & correction

``cleanup/clean_events.py`` processes raw ``*events.tsv`` files outputted by Psychopy to validate and correct (if necessary) the condition, subcondition and accuracy metrics, based on the images previously shown to a participant throughout the multi-session task. The script also computes the duration of delays between image repetitions (in days for between-session repeats, and in seconds for within-session repeats).

The raw input data processed by this script contains scan dates, which are subject identifiers. For confidentiality, they cannot be released publicly in this repository. Nevertheless, the script is provided as a reference.

The file ``qc_notes.md`` contains additional details about any issue with the experiment and how it was resolved.

**Input**:
- A subject's raw ``*events.tsv`` files, across sessions (~36) and runs (6 per session), identified by scan date. E.g., ``sub-01_ses-012_202*****-******_task-thingsmemory_run-2_events.tsv``
- A subject's ``sub-*_scandates.txt`` file, a text file that lists all sessions and their date of acquisition.
- A subject's raw ``*.log`` files outputted by Psychopy, with logged timestamps per trial (note that a session can produce multiple log files if psychopy was stopped and relauched). E.g., ``sub-01_ses-012_202xxxxx-xxxxxx.log``
- If needed: a subject's ``sub-*_ses-*_202xxxxx-xxxxxx.pupil/task-thingsmemory_run-*/000/eye0_timestamps.npy`` eyetracking timestamp files to derive onset trial-wise onset times within each run.

**Output**:
- De-identified, validated and updated ``*events.tsv`` files (to be released). Columns and their values are described in ``cneuromod-things/THINGS/fmriprep/sourcedata/things/task-things_events.json``
- ``sub-*_desc-run_errorReport.txt``, a text file that lists every run for which there is no psychopy log file (in those cases, trialwise timestamps are estimated from eyetracking data), or for which atypical entries (needing corrections) were flagged.
- ``sub-*_desc-trial_errorReport.txt``, a text file that lists every trial for which a correction was made (e.g., to the repetition number, condition, subcondition or accuracy) due to a deviation from the pre-planned protocol (e.g., a session was administered out of order).
- ``sub-*_task-things_concatTrials.tsv``, a temp file that concatenates all trials across sessions, for QCing (cannot be released because it contains scanning dates).

--------------------

# Eye-tracking data processing

The steps below compile, drift correct and analyze eye-tracking data collected while participants completed the THINGS task. Data were acquired with a custom pipeline that integrated [Pupil Lab](https://pupil-labs.com/)'s open source software with [PsychoPy](https://www.psychopy.org/).

Note that data processed during Steps 1 to 3 contain identifiers (e.g., scan dates, movies of the subject's eye ``eye0.mp4``). To protect confidentiality, these files cannot be released publicly in the current repository. However, the scripts used to process the raw data for these steps are provided as a reference.


## Step 1. Export and QC gaze data  

**1.1 Extract gaze data from Pupil Labs files and produce charts for QCing**

The script ``eyetracking/step1_eyetrack_prep.py``:
- compiles an overview of available eyetracking files (``pupils.pldata``, ``gaze.pldata`` and ``eye0.mp4``, which are exported by the pupil software, and Psychopy log files) and exports a list of existing files (``file_list.tsv``).
- exports gaze data from Pupil Labs files (``gaze.pldata``) to ``.npz``
- generates plots of gaze and pupil positions over time (per run) to QC the data (e.g., flag camera freezes, missing pupils, excessive drift, etc)

To run, the script requires CNeuroMod's forked version of the Pupil software repository ([link](https://github.com/courtois-neuromod/pupil/tree/gigevision_rebase), commit ``dd26b6a``) to be installed as a sub-module, as well as dependencies specified in the repo's README and requirements.txt.

**Input**:
- ``*events.tsv`` files across sessions (~36) and runs (6 per session), identified by scan date. E.g., ``sub-01_ses-012_202*****-******_task-thingsmemory_run-2_events.tsv``
- ``sub-*_ses-*_2021xxxx-xxxxxx.log`` files outputted by Psychopy
- ``sub-*_ses-*_2021xxxx-xxxxxx.pupil`` directories with ``pupil.pldata``, ``eye0.mp4`` and ``gaze.pldata`` files

**Output**:
- ``sub-*_ses-*_run-*_2021xxxx-xxxxxx_task-thingsmemory_gaze2D.npz``, timestamped gaze and pupil position (uncorrected for drift) per run.
- ``sub-*_ses-*_run-*_2021xxxx-xxxxxx_task-thingsmemory_QCplot.png``, a series of charts of uncorrected gaze and pupil position plotted over time in x and y.
- ``file_list.tsv``, a compilation of existing eye-tracking files per run for the entire dataset.


**1.2 Offline manual quality check**

Assess the quality of each run by reviewing the graphs generated in Step 1, and
compile a list of clean runs to apply gaze drift correction (in Step 2).

Open ``file_list.tsv`` (created in Step 1) as a spreadsheet, and enter QC info:
- Add columns ``no_pupil_data``, ``DO_NOT_USE``, ``pupilConf_thresh``, ``Pass_DriftCorr``, ``Fails_DriftCorr`` and ``notes``
- Enter "1" under "no_pupil_data" for runs without eye-tracking data
- Enter "1" under "DO_NOT_USE" for runs to be excluded (corrupt/no data)
- Detail any issue under "notes" (e.g., gaps, drifts, low confidence data...)

Save this spreadsheet as ``QCed_file_list.tsv`` in the ``QC_gaze`` directory created inside the specified output directory by ``eyetracking/step1_eyetrack_prep.py``. Note that some runs might require the pupil confidence threshold to be lowered below the default (0.9). In ``QCed_file_list.tsv``, enter the new confidence threshold parameter under ``pupilConf_thresh`` [0.0-1.0] for that run.


## Step 2. Drift correction

**2.1 Adjust gaze drift correction parameters (iterative process)**

This step corrects drift and exports plots of drift-corrected gaze to perform quality checks.

The script ``eyetracking/step2_eyetrack_prep.py`` performs drift correction on runs of gaze data according to parameters specified in ``QCed_file_list.tsv`` (created in Step 1.2), and generates charts of uncorrected and corrected gaze positions over time to help flag runs that fail drift correction.

It can be ran for multiple iterations, adjusting parameters like confidence threshold (``pupilConf_thresh``) per run in ``QCed_file_list.tsv`` and reviewing the charts of drift-corrected gaze until runs are considered well-corrected or beyond fixing.

Compile a final list of runs to drift-correct and export in a bids-compliant format: in ``QCed_file_list.tsv``, enter ``1`` under ``Fails_DriftCorr`` or ``Pass_DriftCorr``, depending. Save this final list as ``QCed_finalbids_list.tsv`` in the ``QC_gaze`` directory (inside the specified output directory).


**Input**:
- ``QCed_file_list.tsv``, a working list of runs to drift correct.
- ``sub-*_ses-*_run-*_2021xxxx-xxxxxx_task-thingsmemory_gaze2D.npz``, timestamped gaze and pupil position (uncorrected for drift) per run.
- ``info.player.json`` files to derive run onset time.
- ``*events.tsv`` files across sessions (~36) and runs (6 per session), identified by scan date. E.g., ``sub-01_ses-012_202*****-******_task-thingsmemory_run-2_events.tsv``
- ``sub-*_ses-*_2021xxxx-xxxxxx.log`` files outputted by PsychoPy

**Output**:
- ``sub-*_ses-*_run-*_2021xxxx-xxxxxx_task-thingsmemory_DCplot.png``, a series of charts of corrected gaze and pupil position plotted over time in x and y.


**2.2 Export drift corrected gaze and eye-tracking metrics**

Re-run the ``eyetracking/step2_eyetrack_prep.py`` script one last time, this time adding the ``--is_final`` flag as an argument.

The script:
-  performs drift correction on runs of gaze data according to parameters specified in ``QCed_finalbids_list.tsv``
- exports gaze and pupil metrics in bids-compliant format (``.tsv.gz``), according to proposed [bids extension guidelines](https://bids-specification--1128.org.readthedocs.build/en/1128/modality-specific-files/eye-tracking.html#sidecar-json-document-eyetrackjson)
- exports ``*events.tsv`` files with added trial-wise metrics of fixation compliance.

**Input**:
- ``QCed_finalbids_list.tsv``, a finalized list of runs to drift correct.
- ``sub-*_ses-*_run-*_2021xxxx-xxxxxx_task-thingsmemory_gaze2D.npz``, timestamped gaze and pupil position (uncorrected for drift) per run.
- ``info.player.json`` files to derive run onset time.
- ``*events.tsv`` files across sessions (~36) and runs (6 per session), identified by scan date. E.g., ``sub-01_ses-012_202*****-******_task-thingsmemory_run-2_events.tsv``
- ``sub-*_ses-*_2021xxxx-xxxxxx.log`` files outputted by PsychoPy

**Output**:
- ``sub-*_ses-*_2021xxxx-xxxxxx_task-thingsmemory_run-*_events.tsv``, ``events.tsv`` files with added fixation compliance metrics.
- ``sub-*_ses-*_task-things_run-*_eyetrack.tsv.gz``, BIDs compliant eye-tracking data, including timestamped pupil and gaze position (uncorrected and drift-corrected).


## Step 3. Reconcile events.tsv files

The script ``eyetracking/step3_reconcile_events.py`` reconciles two sets of ``events.tsv`` files. It extracts the trial-wise eye-tracking metrics added to events.tsv files (from Step 2.2), and inserts these metrics into the validated and cleaned up events.tsv files that contain additional behavioural metrics (those produced with the ``cleanup/clean_events.py`` script).

Note that a handful of ``raw events.tsv`` files required manual relabelling to be properly associated with their validated file (e.g., ``sub-06``'s ``ses-020`` was accidentally ran and saved under sub-01), so this step is not fully automated.

The fixation compliance metrics included in the output ``events.tsv`` files are described in ``cneuromod-things/THINGS/fmriprep/sourcedata/things/task-things_events.json``


**Input**:
- ``sub-*_ses-*_2021xxxx-xxxxxx_task-thingsmemory_run-*_events.tsv``, ``events.tsv`` files with added fixation compliance metrics.

**Output**:
- ``sub-*_ses-*_task-things_run-*_events.tsv``, validated ``events.tsv`` files with added behavioural and fixation compliance metrics.
