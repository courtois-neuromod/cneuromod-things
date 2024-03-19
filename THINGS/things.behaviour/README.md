THINGS behavioural data analyses
================================

## Image Recognition Performance Metrics

Metrics of behavioural performance on the continuous image recognition task (hits, false alarm, d', reaction times) are computed per run, per session (6 runs except for session 1) and per subject (across all sessions) from run-specific ``*events.tsv`` files.

Scores are outputed as ``.tsv`` files in the ``things.behaviour`` dataset. Output columns are described in ``task-things_beh_dataset_description.json``

Launch the following script to process all subjects & sessions
```bash
DATADIR="cneuromod-things/THINGS/things.fmriprep/sourcedata/things"
OUTDIR="cneuromod-things/THINGS/things.behaviour"

python code/behav_data_memoperformance.py --idir="${DATADIR}" --odir="${OUTDIR}" --clean
```

Of note, a handful of sessions had their planned patterns of repetition affected by a session administered out of order (sub-03's sessions 24, 25 and 26; sub-06's sessions 19 to 26). These sessions included "atypical trials" (e.g., images shown more than 3 times), and were excluded from the computation of behavioural performance metrics (they were flagged with ``exclude_session == True`` in their ``*events.tsv`` file).

*Input*:

- All four subjects' ``*events.tsv`` files, across sessions (~36) and runs (6 per session), e.g., ``sub-03_ses-17_task-thingsmemory_run-02_events.tsv``


*Output*:

- ``na_report.txt``, a text file that lists every run for which at least one behavioural response is missing (no button press recorded for at least one trial)
- ``sub-0*/beh/sub-0*_task-things_desc-score-per-trial_beh.tsv``, a concatenation of all events.tsv trials (excludes all trials with no button press). Columns and their values correspond to those of events.tsv files, as described in ``cneuromod-things/THINGS/things.fmriprep/sourcedata/things/task-things_events_description.json``
- ``sub-0*/beh/sub-0*_task-things_desc-score-per-run_beh.tsv``, performance metrics per run (excludes runs from session 1). Columns are described in ``things_beh_dataset_description.json``
- ``sub-0*/beh/sub-0*_task-things_desc-score-per-session_beh.tsv``, performance metrics per session (includes session 1). Columns are described in ``things_beh_dataset_description.json``
- ``sub-0*/beh/sub-0*_task-things_desc-score-global_beh.tsv``, subject's overall performance metrics on the entire task (excludes session 1 in the averaging). Columns are described in ``things_beh_dataset_description.json``



## Trial-Wise Image Ratings and Annotations

Image ratings from the [THINGS](https://things-initiative.org/) and THINGSplus datasets and manual image annotations produced for CNeuroMod-things are attributed to each trial to perform representation analyses. Annotated trials are outputed as ``.tsv`` files per subject in the ``things.behaviour`` dataset.

For this script to run, the following annotation files must be downloaded from the [THINGS object concept and object image database](https://osf.io/jum2f/), and saved directly under ``cneuromod-things/THINGS/things.fmriprep/sourcedata/things/annotations/THINGS+``:
* ``THINGS/things_concepts.tsv``
* ``THINGSplus/Metadata/Concept-specific/arousal_meanRatings.tsv``
* ``THINGSplus/Metadata/Concept-specific/category53_wideFormat.tsv``
* ``THINGSplus/Metadata/Concept-specific/objectProperties_meanRatings.tsv``
* ``THINGSplus/Metadata/Concept-specific/size_meanRatings.tsv``
* ``THINGSplus/Metadata/Image-specific/imageLabeling_imageWise.tsv``
* ``THINGSplus/Metadata/Image-specific/imageLabeling_objectWise.tsv``

Output columns are described in ...
#TODO make file task-things_trial-annotations_dataset_description.json

Launch the following script to process a subject's sessions
```bash
EVDIR="cneuromod-things/THINGS/things.fmriprep/sourcedata/things"
ANDIR="cneuromod-things/THINGS/things.fmriprep/sourcedata/things/things.stimuli/annotations"
OUTDIR="cneuromod-things/THINGS/things.behaviour"

python code/behav_data_annotate.py --events_dir="${EVDIR}" --annot_dir="${ANDIR}" --out_dir="${OUTDIR}" --sub="01"
```

*Input*:

- A subject's ``*events.tsv`` files, across sessions (~36) and runs (6 per session), e.g., ``sub-03_ses-17_task-thingsmemory_run-02_events.tsv``
- Various annotation files saved under ``things.stimuli/annotations``. E.g., ``task-things_desc-manual_image-annotations.tsv``

*Output*:

- ``sub-0*/beh/sub-0*_task-things_desc-annotation-per-trial_beh.tsv``, trialwise annotations for a concatenation of all events.tsv files. Columns are described in ``task-things_trial-annotations_dataset_description.json`` (TODO: make .json file)
- ``sub-0*/beh/sub-0*_task-things_desc-catNum.tsv``, list of categories of images shown to the subject throughout the experiment
- ``sub-0*/beh/sub-0*_task-things_desc-imgNum.tsv``, list of image numbers for images shown to the subject throughout the experiment
