retinotopy dataset
==================

## retinotopy task description

Three participants (`sub-01`, `sub-02`, `sub-03`) completed multiple sessions (6 for `sub-01` and `sub-02`, 5 for `sub-03`) of a retinotopy task adapted from [Kay et al. (2013)](https://doi.org/10.1152/jn.00105.2013) and implemented in Psychopy. This task was designed to derive population receptive field (pRF) properties at the voxel level and to delineate ROIs from the early visual cortex.

Each session included three 5-minutes functional runs, each of which used a different aperture shape : `ring`, `bar` or `wedge`. A run included eight cycles during which an aperture moved slowly across the stimulated visual field to reveal a portion of visual pattern designed to drive both low-level and high-level visual areas. Patterns were drawn randomly at a rate of 15 fps from the [Human Connectome Project retinotopy stimuli](https://doi.org/10.1167/18.13.23) (downloaded [here](http://kendrickkay.net/analyzePRF)).

The stimulated visual field was a circular area with a diameter corresponding to 10 degrees of visual angle. `ring` runs featured a thick circle aperture that expanded from and contracted toward the screen center. `wedge` runs featured a wedge aperture rotating clockwise and counter-clockwise. `bar` runs featured a wide bar aperture sweeping across the screen in 8 different directions. Participants fixated their gaze on a central dot and pressed a button whenever the dot changed color.

## retinotopy.fmriprep

``retinotopy.fmriprep`` includes bids-formatted bold data processed with fmriprep in MNI and subject (T1w) space, saved along functional brain masks and noise confounds. The ``sourcedata/retinotopy`` submodule includes raw fMRI files, and ``*events.tsv`` files with bloc and imagewise metrics.

``sourcedata/retinotopy`` also contains the ``stimuli`` submodule, which includes the apertures and image stimuli.

## retinotopy.prf

``retinotopy.prf`` includes fMRI analyses and derivatives, including scripts to derive population receptive fields with the [analyzePRF toolbox](https://github.com/cvnlab/analyzePRF), pRF results (e.g., voxelwise receptive field size and eccentricity), and binary masks of early visual cortex ROIs estimated with [the Neuropythy toolbox](https://github.com/noahbenson/neuropythy).

ROIs include: ``V1``, ``V2``, ``V3``, ``hV4``, ``V01``, ``V02``, ``L01``, ``L02``, ``T01``, ``T02``, ``V3a`` and  ``V3b.``  
