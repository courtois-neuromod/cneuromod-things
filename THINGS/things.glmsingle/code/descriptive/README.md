
Descriptive analyses
================================

## Step 1. Organize image annotations in a .json for easy access

Script compiles THINGS, THINGSplus and manual annotations in a dictionary
for each image in the dataset to facilitate access during descriptive analyses.

Launch the script to compile all annotations for all subjects
```bash
DATADIR="cneuromod-things/THINGS"

python extract_annotations.py --things_dir="${DATADIR}"
```

*Input*:

- All subjects' ``things.behaviour/sub-{sub_num}/beh/sub-{sub_num}_task-things_desc-perTrial_annotation.tsv`` files.

*Output*:

- ``things.glm/task-things_imgAnnotations.json``, a dictionary with THINGS, THINGSplus and manual annotations for each image in the dataset, with image names as key.

------------------

## Step 2. Rank images per beta score within each voxel

preleminary step: generate ROI masks for low and high level visual areas with fLoc and pRF (retino) analyses


------------------

# Step 3. Ccompute metrics to generate t-SNE plots
