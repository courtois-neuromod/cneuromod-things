Importing flat maps into Pycortex
=================================
Instructions to import full-brain flat patches from Freesurfer to [Pycortex](https://github.com/gallantlab/pycortex)

Flat patches were cut using [TKSurfer (Freesurfer version 6.0.0)](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) for each CNeuromod subject. \
They are saved under ``anat.freesurfer/sub-0*/surf/`` (https://github.com/courtois-neuromod/anat.freesurfer)

**Links and documentation**
- Flat maps for dummies: https://docs.google.com/document/d/19EgtxN0BezHSO1hqkfmzzcpVCPRjrOcBDvrkXp0owxk/edit
- Pycortex repo: https://github.com/gallantlab/pycortex

------------
**Step 1. Install pycortex**

Source: https://github.com/gallantlab/pycortex

```bash
# First, install some required dependencies (if not already installed)
pip install -U setuptools wheel numpy cython
# Install the latest release of pycortex from pip
pip install -U pycortex
```

Note that, for my installation to work, I had to downgrade ``nibabel`` to version ``3.0``, and ``numpy`` to version ``1.23.4``
```bash
pip install -U nibabel==3.0
pip install -U numpy==1.23.4
```

Install ``ipython`` to help configure pycortex and test your installation
```bash
pip install ipython
```

In ipython, print the location of the default pycortex ``filestore`` (the database, analogous to Freesurfer's ``SUBJECTS_DIR``). This is where the subjects' individual files are saved, including maps and transformations.
```python
import cortex
cortex.database.default_filestore
```

Print the location of the pycortex ``config`` file
```python
import cortex
cortex.options.usercfg
```

Edit the config file manually to specify the wanted location for the pycortex filestore (database).\
Replacing the file store's relative path (default) with its absolute path can help.\
E.g., Replace
```bash
filestore = build/bdist.linux-x86_64/wheel/pycortex-1.2.2.data/data/share/pycortex/db
```
With:
```bash
filestore = /abs/path/to/venv/pycortex_venv/share/pycortex/db
```

In the config file, also replace the relative path of the color map with its absolute path.\
E.g., Replace:
```bash
colormaps = build/bdist.linux-x86_64/wheel/pycortex-1.2.2.data/data/share/pycortex/colormaps
```
With:
```bash
colormaps = /abs/path/to/venv/pycortex_venv/share/pycortex/colormaps
```

Test your pycortex installation by running the demo in ipython:
```bash
$ ipython
In [1]: import cortex
In [2]: cortex.webshow(cortex.Volume.random("S1", "fullhead"))
```
A web browser window should pop up with a demo subject.


------------
**Step 2. Import Freesurfer subject data into pycortex**

You need to have ``Freesurfer`` installed as a dependency.\
https://surfer.nmr.mgh.harvard.edu/

This step imports Freesurfer subject data (surfaces and volumes) into the pycortex filestore (database) specified in your pycortex config file (e.g., ``/abs/path/to/venv/pycortex_venv/share/pycortex/db``)

In your bash shell, set the ``SUBJECTS_DIR`` variable (Freesurfer's default subject data directory) to the repository that contains the CNeuromod freesurfer data (e.g., ``anat.freesurfer``)
```bash
SUBJECTS_DIR="/abs/path/to/neuromod/anat.freesurfer"
```

Then launch ipython
```python
import cortex

# specify path to freesurfer repo
fs_dir = '/abs/path/to/neuromod/anat.freesurfer'

# import each cneuromod participant's data into pycortex
slist = ['01', '02', '03', '04', '05', '06']
for s in slist:
    cortex.freesurfer.import_subj(fs_subject=f'sub-{s}',
                                  cx_subject=f'sub-{s}',
                                  freesurfer_subject_dir=fs_dir,
                                  )
```

------------
**Step 3. Generate mean epi images from functional runs**

For each CNeuroMod subject, generate a single mean epi image from a single run of bold data preprocessed with ``fmriprep``. It can be any run, from any task (``friends``, ``mario``, ``localizer``, ``cneuromod-things``, resting state). This bold file will be used to generate a transformation from functional space to Freesurfer/pycortex surface space, so that any volume of functional data (activation map, noise ceilings, retinotopy results, R2 values, t-contrasts) can be projected onto the subject's flat map.

For each subject, select a run of bold data that is either in native (T1w) space or in MNI (normalized) space, depending on the data you are working with.

In ipython:
```python
import glob
import nibabel as nib
from nilearn.image.image import mean_img

outdir_refimg = '/abs/path/to/ref_imgages'
slist = ['01', '02', '03', '04', '05', '06']

for s in slist:
    bold_path = glob.glob(f'/abs/path/to/data/friends_T1w/sub-{s}/ses-010/func/sub-{s}_ses-010_task-s0*_space-T1w_desc-preproc_bold.nii.gz')[0]
    run_epi = nib.load(bold_path)
    mean_epi = mean_img(run_epi)
    nib.save(mean_epi, f'{outdir_refimg}/sub-{s}/ref.nii.gz')
```

------------
**Step 4. Generate transforms from functional space (T1w or MNI) to Freesurfer surface space**

First, save each subject's mean epi image (``ref.nii.gz`` from step 2) into the pycortex filestore. \
E.g.,
```bash
cd /abs/path/to/venv/pycortex_venv/share/pycortex/db/sub-01/transforms
mkdir align_auto_ref
cp /abs/path/to/ref_imgages/sub-01/ref.nii.gz align_auto_ref
```

In your bash shell, set the ``SUBJECTS_DIR`` variable to your Freesurfer data directory
```bash
SUBJECTS_DIR="/abs/path/to/neuromod/anat.freesurfer"
```
Note that the ``cortex.align.automatic`` function requires matching directory names for the same subject in Freesurfer's ``SUBJECTS_DIR`` and in ``pycortex/db`` in order to work.

In ipython:
```python
import cortex

# specify path to pycortex filestore (database)
pycortex_db_dir = '/abs/path/to/venv/pycortex_venv/share/pycortex/db'

# import each cneuromod participant's data into pycortex
slist = ['01', '02', '03', '04', '05', '06']

for s in slist:
    cortex.align.automatic(
        f'sub-{s}', 'align_auto',
        f'{pycortex_db_dir}/sub-{s}/transforms/align_auto_ref/ref.nii.gz'
    )
```

------------
**Step 5. Import Freesurfer flat maps into Pycortex**

Flat maps, or patches, live in ``anat.freesurfer/sub-0*/surf`` under the name "full", to indicate cortical patches that include most of the cortex (excluding some of the medial surface).

In your bash shell, set the ``SUBJECTS_DIR`` variable to your Freesurfer data directory
```bash
SUBJECTS_DIR="/abs/path/to/neuromod/anat.freesurfer"
```
Warning: the following command line should **only be ran once to import a NEW flat map**. If maps are annotated (e.g., using Inkscape to draw ROIs), running this command line again will overwrite the ``overlay.svg`` file on which the annotations displayed in ``pycortex`` are saved, and annotations will be lost.

In ipython:
```python
import cortex

# import each cneuromod participant's data into pycortex
slist = ['01', '02', '03', '04', '05', '06']

for s in slist:
    cortex.freesurfer.import_flat(f'sub-{s}','full', ['lh','rh'], f'sub-{s}')
```

------------
**Step 6. Visualize functional data in pycortex**

Here is an example of how to visualize a functional volume on a flat map in pycortex. For simplicity, I'm loading the mean epi volume (``ref.nii.gz``) that was used to compute the transformation from volume to surface. It's not a particularly informative map, but it's a quick way to test whether volumes are loading properly into pycortex and gain familiarity with the interface.

In your shell, set the ``SUBJECTS_DIR`` variable to your Freesurfer data directory
```bash
SUBJECTS_DIR="/abs/path/to/neuromod/anat.freesurfer"
```

In ipython:
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
data_dir = '/abs/path/to/venv/pycortex_venv/share/pycortex/db'
# Load the functional volume (here ref image as placeholder)
vol = f'{data_dir}/sub-{s}/transforms/align_auto_ref/ref.nii.gz'
# Convert volume to array and swap its axes
vol_arr = np.swapaxes(nib.load(vol).get_fdata(), 0, -1)

'''
Threshold your color map
Voxels whose values are set to NaN are not displayed
Min and max values only set the range of the color bar
'''
vol_thresh = 3.7
vol_arr[vol_arr < vol_thresh] = np.nan
min_val = 0.0
max_val = np.nanmax(vol_arr)

'''
Select a color map
https://gallantlab.org/pycortex/colormaps.html
In the Pycortex interface, clic on the color bar to see available options
'''
cmap = 'terrain' #'magma'

'''
Convert the volume to surface space usin the transformation from step 4
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
Visualize volume in pycortex web browser interface
'''
cortex.webshow(surf_vol, recache=True)
```

The web interface will open a window in your default web browser. To view the surface as a flat map with the interface, click ``Open Control:surface`` (top right), and drag the ``unfold`` slider from ``0`` to ``1``. The visualization of ROIs drawn in Inkscape can be managed under ``rois``. Different options are available for brightness, opacity, etc.


------------
**Step 7. Drawing ROI boundaries in Inkscape**

Install ``Inkscape`` to draw ROI boundaries on flat surface. Depending on your installation, you may need to specify the Inkscape path in the pycortex config file ``~/.config/pycortex/options.cfg`` under ``dependency paths``

In your shell, set the ``SUBJECTS_DIR`` variable to your Freesurfer data directory
```bash
SUBJECTS_DIR="/abs/path/to/neuromod/anat.freesurfer"
```

In ipython:
```python
import cortex
import nibabel as nib
import numpy as np

'''
Load the volume(s) you wish to use to guide ROI boundary drawing
'''
# specify subject number
s = '01'
# specify path to the volume(s) you want to use
retino_path = f'/abs/path/to/retinotopy/data/results/sub-{s}'
floc_roi_path = f'/abs/path/to/floc/data/results/sub-{s}'

vareas = f'{retino_path}/npythy/resampled_vareas.nii.gz'
vareas_arr = np.swapaxes(nib.load(vareas).get_fdata(), 0, -1)
vareas_arr[vareas_arr == 0] = np.nan

'''
Transform volume into surface
'''
vareas_vol = cortex.Volume(
    vareas_arr,
    f'sub-{s}',
    'align_auto',
    vmin=np.nanmin(vareas_arr),
    vmax=np.nanmax(vareas_arr),
    cmap='Retinotopy_RYBCR',
)

'''
Import flattened surface file into Inkscape to guide the drawing of ROI boundaries
Add layers of ROI annotations on the overlay.SVG file that is loaded in pycortex

This command opens the Inkscape interface
'''
cortex.add_roi(
    vareas_vol,
    **dict(
        colorbar_location='left',
        pixelwise=True,
        nanmean=True,
        with_curvature=True,
    ),
)

'''
NOTE: this step (cortex.add_roi) can be repeated many times per subject to load
additional surfaces in Inkscape in order to draw / validate ROIs boundries with
multiple statistical maps.
E.g.,
'''
FFA_path = f'{floc_roi_path}/fLoc_T1w_FFA.nii.gz'
FFA_arr = np.swapaxes(nib.load(FFA_path).get_fdata(), 0, -1)
FFA_arr[FFA_arr <= 0] = np.nan
FFA_vol = cortex.Volume(
    FFA_arr,
    f'sub-{s}',
    'align_auto',
    vmin=np.nanmin(FFA_arr),
    vmax=np.nanmax(FFA_arr),
)

cortex.add_roi(
    FFA_vol,
    **dict(
        colorbar_location='left',
        pixelwise=True,
        nanmean=True,
        with_curvature=True,
    ),
)
```

Drawing ROI boundaries in Inkscape:
- label each image used as reference to trace ROI boundaries (e.g. ``FFA``). On the right menu, select the ``Layers and Objects`` tab. Under ``data``, rename the ``img_new_roi`` layer appropriately (right click, select ``rename layer``)
- create one ROI layer per drawn ROI (even if these ROIs are derived from the same data map). Under ``rois:shapes``, right click, select ``Add Layer`` (directly under ``shapes``). Rename the ``new_roi`` layer with relevant ROI name (``V1``, ``V2``, etc): right click, ``Rename Layer``. Note that this name is the ROI label that will be displayed in pycortex (although label display can be turned off).
- On the ROI layer, draw each ROI (typically one drawn ``object`` per hemishpere, on the same layer, so that each side receives its own label).
- To draw: select the ``pencil`` tool (icon is on the left-hand side menu; ``Draw freehand lines (P)``);
https://inkscape-manuals.readthedocs.io/en/latest/pencil-tool.html
- At the bottom left, select the ``stroke colour``: white or black stroke, no fill. (e.g., ``Fill: None``, ``Stroke: white``). Click on the colour to set the fill color, hold shift and click on colour to set the stroke color.
- In the top right menu, under ``Mode``, select ``Create Bspline path``. Set ``smoothing`` (e.g., ``17.0``)
- In the top right-hand menu, select the ``Fill and stroke style`` tab, then the ``Stroke style`` sub-tab. Set stroke ``width`` (e.g., ``4.0`` pixels (px))
- You can zoom in to draw more easily
- Click on the relevant ROI layer, then hold the left mouse button and trace the ROI contour on the image. This action will create a sub-layer path object directly under the ROI layer. Use a single continuous stroke per ROI per hemisphere: each stroke creates a different path object who receives the ROI label when displayed (one ROI label per hemisphere is typical). Multiple strokes (paths) per ROI within the same hemishpere will generate multiple ROI labels when displayed in Pycortex (although those can be turned off).
- When you're done tracing from a given data map, click ``File:Save`` (top left menu), and then close Inkscape. Do not use ``Save As``. Changes (ROI annotations) will be saved directly on the subject's ``overlay.svg`` file. The next time you load a volume as a surface in pycortex (e.g., as shown in Step 6 above), the ROI boundaries you drew and their labels will be visible. The visualization of ROIs drawn in Inkscape can be managed under ``rois`` in the pycortex interface.

------------
**Step 8. Save images**

Once you are happy with the images you see in pycortex, you can export them using ``matplotlib``

In your shell, set the ``SUBJECTS_DIR`` variable to your Freesurfer data directory
```bash
SUBJECTS_DIR="/abs/path/to/neuromod/anat.freesurfer"
```

In ipython:
```python
import cortex
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

'''
Follow the same steps as in Step 6 to transform your volume into surface.
This time, drawn ROIs should be visible.
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
Create and save the image
Examples of use: https://python.hotexamples.com/examples/cortex/-/quickshow/python-quickshow-function-examples.html
'''
fig = plt.figure(figsize=(17,10))

# without color bar
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
fig.savefig(f'/abs/path/to/project/figures/sub-{s}_results.png', dpi=300)

# with color bar
fig = cortex.quickshow(
    surf_vol,
    pixelwise=True,
    colorbar_location='left',
    nanmean=True,
    with_curvature=True,
)
fig.savefig(f'/abs/path/to/project/figures/sub-{s}_wCbar.png', dpi=300)
```
