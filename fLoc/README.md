fLoc datasets
===============

## fLoc task description

Three CNeuroMod participants (`sub-01`, `sub-02`, `sub-03`) completed six sessions of fLoc, a functional localizer task designed to identify brain regions responding preferentially to specific stimulus categories. The task was based on a [Psychopy implementation](https://github.com/NBCLab/pyfLoc) of the [Stanford VPN lab's fLoc task](https://doi.org/10.1523/JNEUROSCI.4822-14.2015) using stimuli from the fLoc functional localizer package (downloaded [here](https://github.com/VPNL/fLoc)).

Each session included two functional runs of 3.85 minutes with randomly ordered ~6s blocks of rapidly presented images from one of five categories : `faces`, `places`, `bodies`, `objects` and `characters`. Each block included 12 trials for which an image from the block’s category was displayed centrally for 0.4s, followed by a 0.095-0.1s ISI. Subjects were instructed to fixate on a red dot in the middle of the screen and to press a button whenever the same image appeared twice in a row (the “one-back” task variation). Blocks of baseline condition during which the red fixation dot appeared on a grey background for 5.96s were also intermixed in the block sequence. Each run included 6 blocks from each of the five categories and 6 blocks of baseline. For each session, the first run included images from the house (`places`), body (`body parts`), word (`characters`), adult (`faces`) and car (`objects`) fLoc package sub-categories. The second run included images from the corridor (`places`), limb (`body parts`), word (`characters`), adult (`faces`) and instrument (`objects`) sub-categories.


## fLoc/fmriprep

The ``fLoc/fmriprep`` submodule includes bids-formatted bold data preprocessed with fmriprep in MNI and native subject (T1w) space, saved with functional brain masks and noise confounds.

It contains the ``sourcedata/floc`` submodule, which includes:
- raw fMRI files
- ``*events.tsv`` files with bloc and imagewise metrics.
- the ``stimuli`` submodule, which includes the task stimulus images.
- the ``code`` directory with scripts to check and update the ``*events.tsv`` files

## fLoc/rois

The ``fLoc/rois`` submodule includes:
- ``code``, which includes the scripts to derive functional ROIs from subject-specific fMRI data constrained by group priors. The **pipeline to derive ROIs** is described in ``fLoc/rois/code/README.md`` along with instructions to run the different scripts.
- ``standard_masks``, ROI masks (in CVS and MNI space) extracted from group-derived parcels from the Kanwisher group. Parcels can be downloaded [here](https://web.mit.edu/bcs/nklab/GSS.shtml#download).
- ``sub-0*``, subject-specific derivatives, including intermediate results (e.g., group-derived ROIs warped to native subject space, glm contrasts from the fLoc task), and **task-derived binary masks of ROIs known for their categorical preferences for faces, scenes and body parts**, in subject (T1w) space.

ROIs include the:
> * ``FFA``: fusiform face area
> * ``OFA``: occipital face area
> * ``pSTS``: posterior superior temporal sulcus (face preference)
> * ``PPA``: parahippocampal place area
> * ``OPA``: occipital place area
> * ``MPA``: medial place area
> * ``EBA``: extrastriate body area

**NOTE:**\
``sub-06`` completed the main cneuromod-things task but not the fLoc task. To obtain functional ROI masks for that subject, we substituted GLM contrasts derived from the fLoc tasks with voxelwise noise ceilings estimated with data from the main THINGS task.
