THINGS fMRI data QCing
================================

## Compile head motion metrics

Launch the following script to process a subject's sessions
```bash
DATADIR="cneuromod-things/THINGS/data/fmriprep"
OUTDIR="cneuromod-things/THINGS/data/glmsingle"

python compile_headmotion.py --data_dir="${DATADIR}" --out_dir="${OUTDIR}" --sub="01"
```


*Input*:

- A subject's ``desc-confounds`` files outputed by fmriprep for each run. E.g., ``sub-06_ses-30_task-things_run-5_desc-confounds_part-mag_timeseries.tsv``

*Output*:

- ``sub-0*/qc/sub-0*_task-things_headmotion.tsv``, a concatenation of framewise motion for all runs. Includes framewise displacement (in mm), as well as 6 motion coordinates (translation and rotation in x, y and z).
