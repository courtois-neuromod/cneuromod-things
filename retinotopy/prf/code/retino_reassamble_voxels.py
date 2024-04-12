import os, glob, json
import argparse

import nibabel as nib
from nilearn.masking import unmask
import numpy as np
import pandas as pd
from scipy.io import loadmat, savemat


def get_arguments():
    parser = argparse.ArgumentParser(
        description='Reassamble retinotopy outputs from chunks into brain volumes',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number. e.g., 01',
    )
    parser.add_argument(
        '--chunk_size',
        default=240,
        type=int,
        help='number of voxels per chunk',
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to cneuromod-things/retinotopy/prf'
    )

    return parser.parse_args()


def reassamble(dir_path, sub, mask, num_vox, chunk_size, out):

    flat_output = np.zeros((num_vox,))
    file_path = sorted(glob.glob(os.path.join(dir_path, 'results/analyzePRF/chunked/s' + sub[-2:], 'sub' + sub[-2:] + '_fullbrain_analyzePRF_' + out + '_*.mat')))

    for i in range(int(np.ceil(num_vox/chunk_size))):
        #print(out, i)
        flat_output[i*chunk_size:(i+1)*chunk_size] = loadmat(file_path[i])[out].reshape(-1,)

    savemat(os.path.join(dir_path, 'results/analyzePRF', 'sub' + sub[-2:] + '_fullbrain_' + out + '.mat'), {'sub' + sub[-2:] + '_' + out: flat_output})

    #unflat = unmask(flat_output, mask)
    #nib.save(unflat, os.path.join(dir_path, 'results/analyzePRF', sub + '_fullbrain_' + out + '.nii.gz'))


def get_r2(dir_path, sub, mask):
    '''
    Adapts K Kay's analyzePRF R^2 values from analyzePRF for Neuropythy
    AnalyzePRF exports R^2 as val between ~0 (some vals negative) and ~100

    "The R2 values are computed after projecting out polynomials from both
    the data and the model fit. Because of this projection, values can
    sometimes drop below 0%"

    Neuropythy : variance explained must be a fraction between v such that 0 ≤ v ≤ 1
    '''
    r2 = loadmat(os.path.join(dir_path, 'results/analyzePRF', 'sub' + sub[-2:] + '_fullbrain_R2.mat'))['sub' + sub[-2:] + '_R2'].reshape(-1,)
    # replace nan by 0
    r2 = np.nan_to_num(r2)/100 # convert percentage
    # Cap values between 0 and 1
    r2[r2 < 0.0] = 0.0
    r2[r2 > 1.0] = 1.0
    unflat_r2 = unmask(r2, mask)
    nib.save(unflat_r2, os.path.join(dir_path, 'results/analyzePRF', sub + '_fullbrain_R2.nii.gz'))

    return r2


def get_rfsize(dir_path, sub, conv_factor, mask, r2, threshold):
    '''
    With a standard 2D isotropic gaussian model, rfsize corresponds to sigma

    The analyzePRF model is slightly different:
        rfsize = sigma/sqrt(n) where n is the exponent of the power law function;
        output 'expt' contains pRF exponent estimates (is that n???).

        Similar to the original model (gaussian), except that a static
        power-law nonlinearity is added after summation across the visual field.

        Question: do we need to recalculate sigma from size?
        e.g., sigma = rfsize*np.sqrt(expt)
        (NO! Use outputed rfsize as-is as if it were sigma)
        From paper: https://journals.physiology.org/doi/full/10.1152/jn.00105.2013

        "For a model for which the predicted response to point stimuli does not
        have a Gaussian profile, we could simply stipulate that pRF size is the
        standard deviation of a Gaussian function fitted to the actual profile."

    AnalyzePRF: rfsize is in pixels with 0 lower bound. Stimulus images were
                rescaled from 768x768 to 192x192, which correspond to
                10 deg of visual angle (width of on-screen stimuli)
    Neuropythy: Sigma/pRF size must be in degrees of the visual field
    '''
    rfsize = loadmat(os.path.join(dir_path, 'results/analyzePRF', 'sub' + sub[-2:] + '_fullbrain_rfsize.mat'))['sub' + sub[-2:] + '_rfsize'].reshape(-1,)
    # remove np.inf values and replace w max finite value
    rfs_max = np.max(rfsize[np.isfinite(rfsize)])
    rfsize[rfsize == np.inf] = rfs_max

    # threshold image to only significant voxels (only for visualization)
    if threshold:
        rfsize = rfsize*(r2 > 0.1)

    # convert from pixels to degres of vis angle
    rfsize = rfsize*conv_factor

    unflat_rfsize = unmask(rfsize, mask)
    nib.save(unflat_rfsize, os.path.join(dir_path, 'results/analyzePRF', sub + '_fullbrain_rfsize.nii.gz'))


def get_angles_and_ecc(dir_path, sub, conv_factor, mask, r2, threshold):
    '''
    AnalyzePRF: angle and eccentricity values are in pixel units with a lower bound of 0 pixels.
    Neuropythy: values must be in degrees of visual angle from the fovea.
    '''
    ecc = loadmat(os.path.join(dir_path, 'results/analyzePRF', 'sub' + sub[-2:] + '_fullbrain_ecc.mat'))['sub' + sub[-2:] + '_ecc'].reshape(-1,)
    ang = loadmat(os.path.join(dir_path, 'results/analyzePRF', 'sub' + sub[-2:] + '_fullbrain_ang.mat'))['sub' + sub[-2:] + '_ang'].reshape(-1,)
    # calculate x and y coordinates (in pixels)
    x = np.cos(np.radians(ang))*ecc
    y = np.sin(np.radians(ang))*ecc

    # convert from pixels to degress of visual angle
    ecc *= conv_factor
    x *= conv_factor
    y *= conv_factor

    '''
    AnalyzePRF: angle values range between 0 and 360 degrees.
    0 corresponds to the right horizontal meridian, 90 corresponds to the upper vertical meridian, and so on.
    In the case where <ecc> is estimated to be exactly equal to 0,
    the corresponding <ang> value is deliberately set to NaN.

    Neuropythy: Angle values vary from 0-180.
    Values must be absolute (the doc is not up to date in the Usage manual; repo's readme must up to date)
    0 represents the upper vertical meridian and 180 represents the lower vertical meridian in both hemifields.
    Positive values refer to the right visual hemi-field for the left hemisphere, and vice versa.

    https://github.com/noahbenson/neuropythy/issues?q=is%3Aissue+is%3Aclosed
    '''
    # converts angles from "compass" to "signed north-south" for neuropythy
    ang[np.logical_not(ang > 270)] = 90 - ang[np.logical_not(ang > 270)]
    ang[ang > 270] = 450 - ang[ang > 270]
    ang = np.absolute(ang)

    # only for visualization
    if threshold:
        ecc = ecc*(r2 > 0.1)
        ang = ang*(r2 > 0.1)
        x = x*(r2 > 0.1)
        y = y*(r2 > 0.1)

    unflat_ecc = unmask(ecc, mask)
    unflat_ang = unmask(ang, mask)
    unflat_x = unmask(x, mask)
    unflat_y = unmask(y, mask)

    nib.save(unflat_ecc, os.path.join(dir_path, 'results/analyzePRF', sub + '_fullbrain_ecc.nii.gz'))
    nib.save(unflat_ang, os.path.join(dir_path, 'results/analyzePRF', sub + '_fullbrain_ang.nii.gz'))
    nib.save(unflat_x, os.path.join(dir_path, 'results/analyzePRF', sub + '_fullbrain_x.nii.gz'))
    nib.save(unflat_y, os.path.join(dir_path, 'results/analyzePRF', sub + '_fullbrain_y.nii.gz'))


if __name__ == '__main__':
    '''
    Script takes 1D chunks (voxels,) of analyzePRF output metrics,
    re-concatenates them in order, formats them for neuropythy toolbox
    and unmasks/exports them into brain volumes (nii.gz)

    AnalyzePRF doc (Kendrick Kay's retinotopy toolbox on which CNeuromod retino task was based)
    https://github.com/cvnlab/analyzePRF/blob/master/analyzePRF.m

    Neuropythy doc:
    https://github.com/noahbenson/neuropythy
    https://osf.io/knb5g/wiki/Usage/
    '''
    args = get_arguments()

    process_output(args.data_dir, args.sub, args.chunk_size)


def process_output(
    data_dir: str,
    sub: str,
    chunk_size: int,
) -> None:

    """
    Load mask used to vectorize the detrended bold data

    As a reference: number of voxels per participant
    sub-01: 204387 voxels, 0-851 chunks
    sub-02: 219784 voxels, 0-915 chunks
    sub-03: 197155 voxels, 0-821 chunks
    sub-05: 188731 voxels, 0-786 chunks
    """
    mask = nib.load(
        f"{data_dir}/sub-{sub_num}/prf/input/"
        f"sub-{sub_num}_task-retinotopy_space-T1w_label-brain_desc-unionNonNaN_mask.nii",
    )
    mask_dim = mask.get_fdata().shape
    num_vox = int(np.sum(mask.get_fdata()))

    out_list = ['ang', 'ecc', 'expt', 'gain', 'R2', 'rfsize']

    # re-concatenate chunked voxels and unmask into brain volume (subject's T1w)
    # all files are exported by the function
    for out in out_list:
        flat_out = reassamble(data_dir, sub, mask, num_vox, chunk_size, out)

    # load, process and save volume of R^2 Values
    r2 = get_r2(dir_path, sub, mask)

    '''
    Convert rfsize, x and y from pixel to degrees of visual angle
    The rescaled stimulus is 192x192 pixels for 10 degrees of visual angle (width).
    To convert from pixels to degreees, multiply by 10/192.
    '''
    conv_factor = 10/192

    # load, process and save volumes of population receptive field size,
    # angle, eccentricity, and x and y coordinate values
    get_rfsize(dir_path, sub, conv_factor, mask, r2, args.threshold)
    get_angles_and_ecc(dir_path, sub, conv_factor, mask, r2, args.threshold)
