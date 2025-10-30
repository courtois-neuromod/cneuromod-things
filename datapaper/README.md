datapaper files
===============

## notebooks

This directory includes jupyter notebooks (and required libraries) with code to re-create figures from the upcoming data paper using data and result files from the current repository.
- `annotated_betas_per_ROI`: plots distributions of (imagewise and trialwise) beta scores within ROIs defined with functional localizers (fusiform face area (FFA), extrastriate body area (EBA), and parahipp. place area (PPA). Beta distributions are split according to the content of their corresponding image (whether it contains faces, body parts, or elements of scenery). The top 12 images with the highest beta scores in a given ROI are also shown as a mosaic. 
- `behav_analysis`: plots of performance (accuracy, reaction time) on the continuous image recognition (memory) task, and frequency distributions for the delay periods between matching image repetitions.
- `beta_dimReduction`: showcases dimensionality reductions (t-SNE plots) on the trialwise and imagewise betas (derived from BOLD data with the GLMsingle toolbox), color-coded to reflect image annotations. E.g., object size, animals vs. plants, animals vs. vehicles, etc.
- `brain_flatmaps`: noise ceilings, average TSNR maps, and voxelwise t-scores estimated with t-tests contrasting betas across memory conditions (within- and between-session Hits versus Correct Rejections), displated on subject-specific cortical flat maps.
- `fixation_compliance`: figures plotting the distribution of gaze position estimated with eye-tracking during image viewing to assess subjects' fixation compliance.
- `qc_motion_response`: figures plotting distributions of response rate per run (proportion of trials with recorded button press), and of fMRI framewise displacement (in mm) averaged per run and for every frame.

## figures

Empty directory where notebooks export figures by default.


