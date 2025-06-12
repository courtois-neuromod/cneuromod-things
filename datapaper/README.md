datapaper files
===============

## notebooks

This directory includes jupyter notebooks (and required libraries) with code to re-create figures from the upcoming data paper using data and result files from the current repository.
- `behav_analysis`: plots of performance (accuracy, reaction time) on the continuous image recognition (memory) task, and frequency distributions for the delay periods between matching image repetitions.
- `beta_dimReduction`: showcases dimensionality reductions (t-SNE plots) on the trialwise and imagewise betas (derived from BOLD data with the GLMsingle toolbox), color-coded to reflect image annotations. E.g., object size, animals vs. plants, animals vs. vehicles, etc.
- `beta_ranking`: ranking of imagewise beta scores within ROIs defined with functional localizers (fusiform face area (FFA), extrastriate body area (EBA), and parahipp. place area (PPA). Betas are color-coded to reflect the content of their corresponding image (whether it contains faces, body parts, or elements of scenery). The top 12 images with the highest beta scores in the ranking are also displayed.
- `fixation_compliance`: figures plotting the distribution of gaze position estimated with eye-tracking during image viewing to assess subjects' fixation compliance.
- `qc_motion_response`: figures plotting distributions of response rate per run (proportion of trials with recorded button press), and of fMRI framewise displacement (in mm) averaged per run and for every frame.
- `noiseceil_flatmaps`: voxelwise noice ceilings estimated from trialwise betas, displated on subject-specific cortical flat maps

## figures

Empty directory where notebooks export figures by default.

## report

TODO: add link to preprint
