THINGS behavioural data analysis
================================

Metrics of behavioural performance on the image recognition task (hits, false alarm, d', reaction times) are computed per run, per session (6 runs) and per subject (across all sessions) from run-specific *events.tsv files.

Scores are outputed as .tsv files in the things.behaviour dataset. Output columns are described in task-things_beh_dataset_description.json

Launch the following script once to process all subjects & sessions
```bash
DATADIR="cneuromod-things/THINGS/things.fmriprep/sourcedata/things.raw/events_files"
OUTDIR="cneuromod-things/THINGS/things.behaviour"

python behav_data_extract.py --idir="${DATADIR}" --odir="${OUTDIR}" --clean
```


*Input*:

- All four subjects' *events.tsv files, across sessions (~36) and runs (6 per session), e.g., ``sub-03_ses-17_task-thingsmemory_run-02_events.tsv``


*Output*:

- ``na_report.txt``, a text file that lists every run for which at least one behavioural response is missing (no button press recorded for at least one trial)
- ``sub-0*/beh/sub-0*_task-things_desc-score-per-trial_beh.tsv``, a concatenation of all events.tsv trials (excludes all trials with no button press). Columns and their values correspond to those of events.tsv files, as described in events_descriptors.json
# TODO: change events_descriptors.json to task-things_events_dataset_descriptor.json
- ``sub-0*/beh/sub-0*_task-things_desc-score-per-run_beh.tsv``, performance metrics per run (excludes runs from session 1). Columns are described in things_beh_dataset_description.json
- ``sub-0*/beh/sub-0*_task-things_desc-score-per-session_beh.tsv``, performance metrics per session (includes session 1). Columns are described in things_beh_dataset_description.json
- ``sub-0*/beh/sub-0*_task-things_desc-score-global_beh.tsv``, subject's overall performance metrics on the entire task (excludes session 1 in the averaging). Columns are described in things_beh_dataset_description.json
