Anatomical datasets
===============

## smriprep

This submodule contains anatomical data processed with the Structural MRI PREProcessing pipeline (sMRIPrep).
Data are available for all 6 CNeuroMod participants, including the 4 individuals who completed the cneuromod-things task (`sub-01`, `sub-02`, `sub-03` and `sub-06`).

`smriprep` contains two submodules:
- `raw` : the 6 participants' raw anatomical scans, including a series of T1w scans
- **`freesurfer`**: the 6 participants' freesurfer database. Beside the standard freesurfer volume, surface and transformation files, this repository also includes **full brain flat patches** that can be used to project CNeuroMod brain data onto flat maps. Flat patches were cut manually with [TKSurfer (Freesurfer version 6.0.0)](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) for each CNeuromod subject, are are saved under ``smriprep/sourcedata/freesurfer/sub-0*/surf`` as ``{lh, rh}.full.flat.patch.3d``, ``{lh, rh}.full.flat.patch.3d.out`` and ``{lh, rh}.full.patch.3d``.


## pycortex

For each CNeuromod subject (n=6), full brain flat patches were imported from their native Freesurfer into [Pycortex](https://github.com/gallantlab/pycortex) to project CNeuroMod brain data onto flat cortical surfaces for visualization.

The `pycortex` submodule contains:
- ``db``, a Pycortex filestore (database) in which individual subjects' maps and transformations are stored for all 6 CNeuroMod subjects. For ``sub-01``, ``sub-02`` and ``sub-03``, who completed two fMRI visual localizer tasks, full-brain flat maps are annotated with visual ROIs that were traced manually in Inkscape based on GLM contrasts. ROI labels include low-level visual areas [``V1``, ``V2`` and ``V3``] identified with retinotopy, and face areas [``FFA: fusiform face area``, ``OFA: occipital face area`` and ``pSTS: posterior superior temporal sulcus`` ], body [``extrastriate body area: EBA``] and place areas [``PPA: parahippocampal place area``, ``OPA: occipital place area`` and ``MPA: medial place area``] identified with fLoc.
- ``docs/using_flatmaps.md``, an instruction manual that details how to import Freesurfer patches into Pycortex, to annotate them with Inkscape, and to project volumetric brain data onto cortical flat maps.
