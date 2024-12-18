Pycortex dataset
================

## Pycortex dataset description

This dataset contains full-brain flat patches that can be used to project CNeuroMod brain data onto flat maps. Flat patches were cut manually with [TKSurfer (Freesurfer version 6.0.0)](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) for each CNeuromod subject, and imported from their native Freesurfer into [Pycortex](https://github.com/gallantlab/pycortex).

The original flat patches are saved under ``cneuromod-things/anatomical/smriprep/sourcedata/freesurfer/sub-0*/surf`` as ``{lh, rh}.full.flat.patch.3d``, ``{lh, rh}.full.flat.patch.3d.out`` and ``{lh, rh}.full.patch.3d``

The pycortex sub-repository contains:
- ``db``, a Pycortex filestore (database) in which individual subjects' maps and transformations are stored. For ``sub-01``, ``sub-02`` and ``sub-03``, who completed fMRI visual localizer tasks, full-brain flat maps are annotated with visual ROIs that were traced manually in Inkscape. ROI labels include low-level visual areas [``V1``, ``V2`` and ``V3``] identified with retinotopy, and face areas [``FFA: fusiform face area``, ``OFA: occipital face area`` and ``pSTS: posterior superior temporal sulcus`` ], body [``extrastriate body area: EBA``] and place areas [``PPA: parahippocampal place area``, ``OPA: occipital place area`` and ``MPA: medial place area``] identified with fLoc.
- ``docs/flatmaps.md``, an instruction manual that details how to import Freesurfer patches into Pycortex, how to annotate them with Inkscape, and how to project volumetric brain data onto cortical flat maps.

**Links and documentation**
- Flat maps for dummies: https://docs.google.com/document/d/19EgtxN0BezHSO1hqkfmzzcpVCPRjrOcBDvrkXp0owxk/edit
- Pycortex repo: https://github.com/gallantlab/pycortex

------------

## Installation

To use the pycortex dataset to visualize CNeuroMod data onto subject-specific flat maps, you need to install [Freesurfer](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) (recommended version: 7.3.2) and Pycortex.

To install Pycortex, follow the steps below.
Source: https://github.com/gallantlab/pycortex

```bash
# First, install some required dependencies (if not already installed)
pip install -U setuptools wheel numpy cython
# Install the latest release of pycortex from pip
pip install -U pycortex==1.2.5
```

For the installation to work, you need to downgrade ``nibabel`` to version ``3.0``, and ``numpy`` to version ``1.23.4``
```bash
pip install -U nibabel==3.0
pip install -U numpy==1.23.4
```

Install ``ipython`` to help configure pycortex and test your installation
```bash
pip install ipython==8.7.0
```

In ipython, print the location of the pycortex ``config`` file.
```python
import cortex
cortex.options.usercfg
```

Also print the location of the default pycortex ``filestore`` (the database, analogous to Freesurfer's ``SUBJECTS_DIR``). This is where Pycortex looks for subjects files like maps and transformations.
```python
import cortex
cortex.database.default_filestore
```

Edit the config file manually to replace the file store's default path with the absolute path to ``cneuromod-things/anatomical/pycortex/db``.\
E.g., Replace
```bash
filestore = build/bdist.linux-x86_64/wheel/pycortex-1.2.2.data/data/share/pycortex/db
```
With:
```bash
filestore = /abs/path/to/cneuromod-things/anatomical/pycortex/db
```

Also replace the relative path of the default color map with its absolute path.\
E.g., if you installed Pycortex in a virtual env, replace:
```bash
colormaps = build/bdist.linux-x86_64/wheel/pycortex-1.2.2.data/data/share/pycortex/colormaps
```
With:
```bash
colormaps = /abs/path/to/my/pycortex_venv/share/pycortex/colormaps
```

Test your pycortex installation by running the following code in ipython:
```bash
$ SUBJECTS_DIR="path/to/cneuromod-things/anatomical/smriprep/sourcedata/freesurfer"
$ ipython
In [1]: import cortex
In [2]: import nibabel as nib
In [3]: import numpy as np

In [4]: pycortex_db_dir = 'path/to/cneuromod-things/anatomical/pycortex/db'

In [5]: s = '01'
In [6]: vol = f'{pycortex_db_dir}/sub-{s}/transforms/align_auto_ref/ref.nii.gz'
In [7]: vol_arr = np.swapaxes(nib.load(vol).get_fdata(), 0, -1)
In [8]: cmap = 'Retinotopy_RYBCR' # try others?
In [9]: surf_vol = cortex.Volume(vol_arr, f'sub-{s}', 'align_auto', vmin=np.nanmin(vol_arr), vmax=np.nanmax(vol_arr), cmap=cmap)

In [10]: cortex.webshow(surf_vol, recache=True)
```
A window should open in your default web browser featuring a placeholder EPI volume projected on sub-01's surface map.


------------

## Visualize brain data with Pycortex

Here are instructions to visualize a volume of brain data on a cortical flat map in Pycortex.  As an example, I am loading the noise ceilings derived from the THINGS task saved under ``cneuromod-things/THINGS/glmsingle/sub-*/glmsingle/output``.

In your shell, set the Freesurfer ``SUBJECTS_DIR`` variable to match the location of ``cneuromod-things/anatomical/smriprep/sourcedata/freesurfer``
```bash
SUBJECTS_DIR="path/to/cneuromod-things/anatomical/smriprep/sourcedata/freesurfer"
```

Then, run the following command lines in ipython:
```python
import cortex
import nibabel as nib
import numpy as np

'''
Load your results map (volume)
'''
# specify subject number
s = '01'
# specify path to the volume you want to visualize
data_dir = f'path/to/cneuromod-things/glmsingle/sub-{s}/glmsingle/output'
# Load the functional volume (here ref image as placeholder)
vol = f'{data_dir}/sub-{s}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz'
# Convert volume to array and swap its axes
vol_arr = np.swapaxes(nib.load(vol).get_fdata(), 0, -1)

'''
Threshold your color map
Voxels whose values are set to NaN are not displayed in Pycortex
Min and max values only set the range of the color bar
'''
vol_thresh = 0.0
vol_arr[vol_arr < vol_thresh] = np.nan
min_val = 0.0
max_val = np.nanmax(vol_arr)

'''
Select a color map
https://gallantlab.org/pycortex/colormaps.html
In the Pycortex interface, click on the color bar and scroll through available options
'''
cmap = 'magma'

'''
Project the volume metrics onto the cortical surface
using a transformation from T1w space to surface.

This transformation was generated at Step 4
in the cneuromod-things/pycortex/doc/flatmaps.md manual
'''
surf_vol = cortex.Volume(
    vol_arr,
    f'sub-{s}',
    'align_auto',
    vmin=min_val,
    vmax=max_val,
    cmap=cmap,
)

'''
Visualize the volume on a cortical flat map in the interactive
Pycortex interface.
'''
cortex.webshow(surf_vol, recache=True)
```

This last command will open a window in your default web browser. To view the surface as a flat map in the interface, click ``Open Control:surface`` (top right), and drag the ``unfold`` slider from ``0`` to ``1``. The visualization of ROIs drawn in Inkscape can be managed under ``rois``. Different options are available for brightness, opacity, interpolation, to view or hide ROI labels, etc.


------------

## Exporting Images

You can use ``matplotlib`` to export high-resolution images of cortical flatmaps generated with Pycortex.

In your shell, set the Freesurfer ``SUBJECTS_DIR`` variable to match the location of ``cneuromod-things/anatomical/smriprep/sourcedata/freesurfer``
```bash
SUBJECTS_DIR="path/to/cneuromod-things/anatomical/smriprep/sourcedata/freesurfer"
```

The run the following command lines in ipython:
```python
import cortex
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

'''
Follow the same steps as above to project your volume of results onto a cortical surface.
'''
s = '01'
data_dir = f'path/to/cneuromod-things/glmsingle/sub-{s}/glmsingle/output'
vol = f'{data_dir}/sub-{s}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-noiseCeilings_statmap.nii.gz'
vol_arr = np.swapaxes(nib.load(vol).get_fdata(), 0, -1)
vol_thresh = 0.0
vol_arr[vol_arr < vol_thresh] = np.nan

surf_vol = cortex.Volume(
    vol_arr,
    f'sub-{s}',
    'align_auto',
    vmin=0.0,
    vmax=np.nanmax(vol_arr),
    cmap='magma',
)

'''
Create and save the image
Examples of use: https://python.hotexamples.com/examples/cortex/-/quickshow/python-quickshow-function-examples.html
'''
fig = plt.figure(figsize=(17,10))

# flat map without the color bar
cortex.quickshow(
    surf_vol,
    pixelwise=True,
    with_colorbar=False,
    nanmean=True,
    with_curvature=True,
    sampler='trilinear',
    with_labels=False,
    with_rois=True,
    curv_brightness=1.0,
    dpi=300,
    fig=fig,
)
fig.savefig(f'/abs/path/to/figure_dir/sub-{s}_noiseCeil.png', dpi=300)

# flat map with a color bar (e.g., to edit into a composite figure)
fig = cortex.quickshow(
    surf_vol,
    pixelwise=True,
    colorbar_location='left',
    nanmean=True,
    with_curvature=True,
)
fig.savefig(f'/abs/path/to/figure_dir/sub-{s}_noiseCeil_wCbar.png', dpi=300)
```
