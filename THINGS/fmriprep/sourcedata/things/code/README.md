THINGS source data analyses
===========================

**Validation & Updating of Events.tsv files**

``clean_events.py`` processes raw ``*events.tsv`` files outputted by Psychopy to validate and correct (if necessary) the condition, subcondition and accuracy metrics, based on the images previously shown to a participant throughout the multi-session task. The script also computes the duration of delays between image repetitions (in days for between-session repeats, and in seconds for within-session repeats).

The raw input data processed by this script contains scan dates, which are subject identifiers. For confidentiality, they cannot be released publicly in this directory. Nevertheless, the script is provided as a reference.

The file ``qc_notes.md`` contains additional details about any issue with the experiment, and how it was resolved.

*Input*:

- A subject's raw ``*events.tsv`` files, across sessions (~36) and runs (6 per session), identified by scan date. E.g., ``sub-01_ses-012_202*****-******_task-thingsmemory_run-2_events.tsv``
- A subject's ``sub-*_scandates.txt`` file, a text file that lists all sessions and their date of acquisition.
- A subject's raw ``*.log`` files outputted by Psychopy, with logged timestamps per trial (note that a session can produce multiple log files if psychopy was stopped and relauched). E.g., ``sub-01_ses-012_202xxxxx-xxxxxx.log``
- If needed: a subject's ``sub-*_ses-*_202xxxxx-xxxxxx.pupil/task-thingsmemory_run-*/000/eye0_timestamps.npy`` eyetracking timestamp files to derive onset trial-wise onset times within each run.

*Output*:

- De-identified, validated and updated ``*events.tsv`` files (to be released). Columns and their values are described in ``cneuromod-things/THINGS/fmriprep/sourcedata/things/task-things_events.json``
- ``sub-*_desc-run_errorReport.txt``, a text file that lists every run for which there is no psychopy log file (in those cases, trialwise timestamps are estimated from eyetracking data), or for which atypical entries (needing corrections) were flagged.
- ``sub-*_desc-trial_errorReport.txt``, a text file that lists every trial for which a correction was made (e.g., to the repetition number, condition, subcondition or accuracy) due to a deviation from the pre-planned protocol (e.g., a session was administered out of order).
- ``sub-*_task-things_concatTrials.tsv``, a temp file that concatenates all trials across sessions, for QCing (cannot be released because it contains scanning dates).
