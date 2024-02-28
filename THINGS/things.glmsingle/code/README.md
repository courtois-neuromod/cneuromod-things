THINGS behavioural data analysis
================================

Metrics of behavioural performance on the image recognition task (hits, false alarm, d', reaction times) are computed per run, per session (6 runs) and per subject (across all sessions) from run-specific *events.tsv files.

Scores are outputed as .tsv files in the things.behaviour dataset. Output columns are described in task-things_beh_dataset_description.json

Server: elm \
Path to data: /data/neuromod/DATA/cneuromod/things \
Path to code dir: /home/mariestl/cneuromod/THINGS/things_memory_results \
Script: behav_data_extract.py

Launch the following script once to process all subjects & sessions
```bash
DATADIR="./THINGS/data/things.fmriprep/sourcedata/things.raw/events_files"
OUTDIR="./THINGS/data/things.behaviour"

python behav_data_extract.py --idir="${DATADIR}" --odir="${OUTDIR}" --clean
```


*Input*:

- All four subjects' *events.tsv files, across sessions (~36) and runs (6 per session), e.g., ``sub-03_ses-17_task-things_run-02_events.tsv``


*Output*:

- ``na_report.txt``, a text file that lists every run for which at least one behavioural response is missing (no button press recorded for at least one trial)
- ``behav_per_trial.tsv``, a concatenation of all events.tsv trials (excludes all trials with no button press). Columns and their values correspond to those of events.tsv files, as described in events_descriptors.json
- ``behav_per_run.tsv``, performance metrics per run (excludes runs from session 1). Columns are described in things_beh_dataset_description.json
- ``behav_per_session.tsv``, performance metrics per session (includes session 1). Columns are described in things_beh_dataset_description.json
- ``behav_per_subject.tsv``, performance metrics per subject (excludes session 1 in the averaging). Columns are described in things_beh_dataset_description.json
