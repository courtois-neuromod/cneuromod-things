THINGS source data analyses
===========================

**Validation & Updating of Events.tsv files**

``clean_events.py`` processes raw ``*events.tsv`` files outputted by Psychopy to validate and correct (if necessary) the condition, subcondition and accuracy metrics, based on the images previously shown to a participant throughout the multi-session task. The script also computes the duration of delays between image repetitions (in days for between-session repeats, and in seconds for within-session repeats).

The raw input data processed by this script contains scan dates, which are subject identifiers. For confidentiality, they cannot be released publicly in this directory. Nevertheless, the script is provided as a reference.

The file ``qc_notes.md`` contains additional details about any issue with the experiment, and how it was resolved.

*Input*:

- A subject's raw ``*events.tsv`` files, across sessions (~36) and runs (6 per session), identified by scan date. E.g., ``sub-01_ses-012_202*****-******_task-thingsmemory_run-2_events.tsv``
- A subject's ``sub-*_scandates.txt`` file, a text file that lists all sessions and their date of acquisition.
- A subject's raw ``*events.tsv`` files, across sessions (~36) and runs (6 per session), e.g., ``sub-03_ses-17_task-thingsmemory_run-02_events.tsv``

*Output*:

- De-identified, validated and updated ``*events.tsv`` files (to be released). Columns and their values are described in ``cneuromod-things/THINGS/things.fmriprep/sourcedata/things/task-things_events_description.json``
- ``sub-*_error_run_report.txt``, a text file that lists every run for which there is no psychopy log file (trial timestamps need to be estimated from eyetracking data), or for which atypical entries (needing corrections) were flagged.
- ``sub-*_error_trial_report.txt``, a text file that lists every trial for which a correction was made (e.g., to the repetition number, condition, subcondition or accuracy) due to a deviation from the pre-planned protocol (e.g., a session was administered out of order).
- ``sub-*_things_concattrials.tsv``, a temp file that concatenates all trials across sessions, for QCing (cannot be released because it contains scanning dates).
