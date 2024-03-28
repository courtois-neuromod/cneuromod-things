import glob, os, sys
import argparse
from pathlib import Path

import nibabel as nib
import nilearn
import numpy as np

from nilearn.masking import unmask, apply_mask, intersect_masks
from nilearn.glm import threshold_stats_img


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Produces parcels of category-sensitive voxels from fLoc contrasts and group priors"
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to data directory',
    )
    parser.add_argument(
        '--use_betas',
        action='store_true',
        default=False,
        help='if TRUE, create parcels based on beta values; default uses t-scores',
    )
    parser.add_argument(
        '--use_smooth',
        action='store_true',
        default=False,
        help='if true, use contrasts derived from smoothed BOLD, else use unsmoothed',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str, help='two-digit subject number',
    )
    parser.add_argument(
        '--alpha',
        default=0.0001,
        type=float,
        help='alpha value for false positive rate, uncorrected',
    )

    return parser.parse_args()


def create_subject_parcels(
    data_dir: str,
    sub_num: str,
    alpha: float=0.0001,
    use_betas: bool=False,
    use_smooth: bool=False,
) -> None:
    """."""
    dtype = 'betas' if use_betas else 'tscores'
    sm = 'smooth' if use_smooth else 'unsmooth'

    c_list = ['body', 'face', 'object', 'scene']
    c_kanwisher = ['bodyMinObject', 'faceMinObject', 'objectMinRest', 'sceneMinObject']
    c_nsd = ['bodies', 'faces', 'objects', 'places']

    for c, k, n in zip(c_list, c_kanwisher, c_nsd):
        # load subject contrast from fLoc task (kanwisher group)
        dmap_k = nib.load(
            f"{data_dir}/sub-{sub_num}/glm/sub-{sub_num}_task-floc_space-T1w_"
            f"model-GLM_stats-{dtype}_contrast-{k}_desc-{sm}_statseries.nii.gz"
        )

        # load subject contrast from fLoc task (NSD)
        dmap_n = nib.load(
            f"{data_dir}/sub-{sub_num}/glm/sub-{sub_num}_task-floc_space-T1w_"
            f"model-GLM_stats-{dtype}_contrast-{n}_desc-{sm}_statseries.nii.gz"
        )

        # load and process subject-specific parcel warped from CVS to MNI to T1w space
        parcel = nib.load(
            f"{data_dir}/sub-{sub_num}/rois/from_atlas/"
            f"sub-{sub_num}_parcel-kanwisher_space-T1w_contrast-{c}_mask.nii" # TODO: rename probseg?
        )
        # transform probseg mask into binary mask
        parcel = nib.nifti1.Nifti1Image(
            (parcel.get_fdata() >=2).astype(int),
            affine=parcel.affine,
        )
        # resample parcel to functional space
        rs_parcel = nilearn.image.resample_to_img(
            parcel, dmap_k, interpolation='nearest',
        )

        thresh_dmap_k, tshold_k = threshold_stats_img(
            dmap_k,
            alpha=alpha,
            height_control="fpr",
            cluster_threshold=20,
            two_sided=False,
        )
        tval_k = ("%.2f" % tshold_k)

        dmk_mask = nib.nifti1.Nifti1Image(
            (thresh_dmap_k.get_fdata() > tshold_k).astype(int),
            affine=dmap_k.affine,
        )
        submask_k = intersect_masks(
            [dmk_mask, rs_parcel],
            threshold=1,
            connected=False,
        )
        nib.save(
            submask_k,
            f"{data_dir}/sub-{sub_num}/rois/task-derived/"
            f"sub-{sub_num}_task-floc_space-T1w_stats-{dtype}_contrast-{k}_"
            f"alpha-{alpha}_cutoff-{tval_k}_desc-{sm}_mask.nii.gz",
        )

        thresh_dmap_n, tshold_n = threshold_stats_img(
            dmap_n,
            alpha=alpha,
            height_control="fpr",
            cluster_threshold=20,
            two_sided=False,
        )
        tval_n = ("%.2f" % tshold_n)

        dmn_mask = nib.nifti1.Nifti1Image(
            (thresh_dmap_n.get_fdata() > tshold_n).astype(int),
            affine=dmap_n.affine,
        )
        submask_n = intersect_masks(
            [dmn_mask, rs_parcel],
            threshold=1,
            connected=False,
        )
        nib.save(
            submask_n,
            f"{data_dir}/sub-{sub_num}/rois/task-derived/"
            f"sub-{sub_num}_task-floc_space-T1w_stats-{dtype}_contrast-{n}_"
            f"alpha-{alpha}_cutoff-{tval_n}_desc-{sm}_mask.nii.gz",
        )


if __name__ == '__main__':
    """
    Script produces parcels of category-sensitive voxels in subject space from
    subject's fLoc contrasts, using group parcels as priors.
    """
    args = get_arguments()

    create_subject_parcels(
        args.data_dir, args.sub, args.alpha, args.use_betas, args.use_smooth,
    )
