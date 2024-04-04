import glob, os, sys
import nibabel as nib
import nilearn
from nilearn.masking import unmask, apply_mask, intersect_masks
from nilearn.glm import threshold_stats_img
from nilearn.image import threshold_img
import numpy as np
from nilearn.image import smooth_img
from scipy.io import loadmat

import argparse


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Produces subject-specific ROIs in native space from fLoc contrasts and group ROIs"
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to data directory',
    )
    parser.add_argument(
        '--no_data',
        action='store_true',
        default=False,
        help='if true, generate ROI masks from noise-ceilings rather than task t-scores',
    )
    parser.add_argument(
        '--use_smooth_bold',
        action='store_true',
        default=False,
        help='if true, use t-scores derived from smoothed BOLD data, else unsmoothed',
    )
    parser.add_argument(
        '--one_cluster',
        action='store_true',
        default=False,
        help='if true, only keep the largest cluster of active voxels within each hemi',
    )
    parser.add_argument(
        '--alpha',
        default=0.0001,
        type=float,
        help='alpha value for false positive rate, uncorrected',
    )
    parser.add_argument(
        '--fwhm',
        default=5,
        type=int,
        help='smoothing parameter to apply to group-derived ROI mask',
    )
    parser.add_argument(
        '--percent_cluster',
        default=0.8,
        type=float,
        help='proportion of voxels in the group-derived ROI mask to set'
             ' the max voxel count in the final ROI mask',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number',
    )

    return parser.parse_args()


def create_subject_rois(
    data_dir: str,
    sub_num: str,
    alpha: float=0.0001,
    fwhm: int=8,
    percent_cluster: float=0.8,
    use_smooth_bold: bool=False,
    single_cluster: bool=False,
) -> None:
    """."""

    roi_list = [
        ['body_roi-EBA'],
        ['face_roi-FFA', 'face_roi-OFA', 'face_roi-pSTS'],
        ['scene_roi-MPA', 'scene_roi-OPA', 'scene_roi-PPA'],
    ]

    # Kanwisher-style contrasts
    #contrast_list = ['bodyMinObject', 'faceMinObject', 'sceneMinObject']

    # NSD contrasts (corresponds better to fLoc)
    contrast_list = ['bodies', 'faces', 'places']
    hemi = ['L', 'R']

    for i, c in enumerate(contrast_list):
        # load subject contrast from fLoc task
        sm = "smooth" if use_smooth_bold else "unsmooth"
        dmap = nib.load(
            f"{data_dir}/fLoc/floc.rois/sub-{sub_num}/glm/"
            f"sub-{sub_num}_task-floc_space-T1w_model-GLM_stats-tscores_"
            f"contrast-{c}_desc-{sm}_statseries.nii.gz"
        )

        # threshold contrast map (cluster size, uncorrected false positive rate)
        thresh_dmap, tshold = threshold_stats_img(
            dmap,
            alpha=alpha,
            height_control="fpr",
            cluster_threshold=20,
            two_sided=False,
        )

        dm_mask = nib.nifti1.Nifti1Image(
            (thresh_dmap.get_fdata() > tshold).astype(int),
            affine=dmap.affine,
        )

        # process subject-specific ROI masks warped from CVS to MNI to T1w space
        for roi in roi_list[i]:

            # per hemi to balance voxel count between both hemispheres
            hemi_masks = []
            tvals = []
            vcount = 0
            for i, h in enumerate(hemi):
                parcel = nib.load(
                    f"{data_dir}/fLoc/floc.rois/sub-{sub_num}/rois/from_atlas/"
                    f"sub-{sub_num}_parcel-kanwisher_space-T1w_contrast-"
                    f"{roi}_desc-{h}_mask.nii",
                )

                """
                Resample parcel to functional T1w space (epi space)
                Threshold liberally
                """
                rs_parcel = nilearn.image.resample_to_img(
                    parcel, dmap, interpolation='continuous',
                )
                rs_parcel = nib.nifti1.Nifti1Image(
                    (rs_parcel.get_fdata() > 0.001).astype(int),
                    affine=rs_parcel.affine,
                )

                parcel_nvox = int(
                    np.floor(np.sum(rs_parcel.get_fdata())*percent_cluster)
                )

                # smooth parcel to include more voxels
                rs_parcel_sm = smooth_img(imgs=rs_parcel, fwhm=fwhm)
                rs_parcel_sm = nib.nifti1.Nifti1Image(
                    (rs_parcel_sm.get_fdata() > 0.01).astype(int),
                    affine=rs_parcel_sm.affine,
                )

                """
                Create mask of voxels above cutoff threshold within the wider
                smoothed mask
                """
                wide_mask = intersect_masks(
                    [dm_mask, rs_parcel_sm],
                    threshold=1,
                    connected=single_cluster,
                )

                tval = ("%.2f" % tshold)
                t_cutoff = tshold
                """
                IF the number of voxels in the intersection mask
                (> thresh t-scores & smoothed group ROI)
                is greater than the group parcel's voxel count (before smoothing).
                """
                if np.sum(wide_mask.get_fdata()) > parcel_nvox:
                    """
                    mask the activation mask to include only intersect mask voxels
                    """
                    masked_threshvox = apply_mask(thresh_dmap, wide_mask)
                    assert np.sum(masked_threshvox > 0) == np.sum(wide_mask.get_fdata())
                    """
                    Calculate cutoff value:
                    Rank voxels per value, and keep only the n voxels with the
                    higher t-scores scores, where n = the group parcel's voxel count
                    """
                    t_cutoff = np.sort(masked_threshvox)[-parcel_nvox]
                    select_dm_mask = nib.nifti1.Nifti1Image(
                        (thresh_dmap.get_fdata() >= t_cutoff).astype(int),
                        affine=thresh_dmap.affine,
                    )
                    """
                    Recalculate wide mask w only above-cutoff voxels
                    """
                    wide_mask = intersect_masks(
                        [select_dm_mask, rs_parcel_sm],
                        threshold=1,
                        connected=single_cluster,
                    )
                    tval = ("%.2f" % t_cutoff)

                if np.sum(wide_mask.get_fdata()) > 0:
                    """
                    Extra step to remove very small clusters from final ROI mask
                    """
                    parcel_dmap = unmask(
                        apply_mask(thresh_dmap, wide_mask),
                        wide_mask,
                    )

                    ct = 20 if use_smooth_bold else 5
                    parcel_thresh_dmap = threshold_img(
                        parcel_dmap,
                        threshold=t_cutoff,
                        cluster_threshold=ct,
                        two_sided=False
                    )

                    wide_mask = nib.nifti1.Nifti1Image(
                        (parcel_thresh_dmap.get_fdata() > t_cutoff).astype(int),
                        affine=parcel_thresh_dmap.affine,
                    )

                    vcount += int(np.sum(wide_mask.get_fdata()))
                    tvals.append(float(tval))
                    hemi_masks.append(wide_mask)

            if len(hemi_masks) > 0:

                final_mask = intersect_masks(
                    hemi_masks, threshold=0, connected=False,
                )
                tvalue = str(min(tvals))

                nib.save(
                    final_mask,
                    f"{data_dir}/fLoc/floc.rois/sub-{sub_num}/rois/task-derived"
                    f"/sub-{sub_num}_task-floc_space-T1w_stats-tscores_"
                    f"contrast-{roi}_cutoff-{tvalue}_nvox-{vcount}_fwhm-{fwhm}_ratio-{percent_cluster}_"
                    f"desc-{sm}_mask.nii.gz",
                )


def create_subject_rois_noData(
    data_dir: str,
    sub_num: str,
    fwhm: int=8,
    single_cluster: bool=False,
) -> None:
    """
    Produce ROI masks without fLoc contrast maps, using noise ceiling map derived
    from main THINGS task.
    """
    # load noise ceiling data
    noiseceil = nib.load(
        f"/{data_dir}/THINGS/things.glmsingle/sub-{sub_num}/glmsingle/output/"
        f"sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_stats-"
        "noiseCeilings_statmap.nii.gz",
    )

    roi_list = [
        ['body_roi-EBA'],
        ['face_roi-FFA', 'face_roi-OFA', 'face_roi-pSTS'],
        ['scene_roi-MPA', 'scene_roi-OPA', 'scene_roi-PPA'],
    ]

    # Kanwisher-style contrasts (first iteration)
    #contrast_list = ['bodyMinObject', 'faceMinObject', 'sceneMinObject']

    # NSD contrasts (corresponds better to fLoc task we ran)
    contrast_list = ['bodies', 'faces', 'places']
    hemi = ['L', 'R']

    for i, c in enumerate(contrast_list):

        # load and process group-derived ROI masks warped from CVS to MNI to T1w space
        for roi in roi_list[i]:

            # separately per hemisphere, to balance voxels between hemis
            hemi_masks = []
            tvals = []
            vcount = 0
            for i, h in enumerate(hemi):
                parcel = nib.load(
                    f"{data_dir}/fLoc/floc.rois/sub-{sub_num}/rois/from_atlas/"
                    f"sub-{sub_num}_parcel-kanwisher_space-T1w_contrast-"
                    f"{roi}_desc-{h}_mask.nii",
                )

                """
                Resample parcel from anat to functional T1w space (epi space)
                Threshold liberally
                """
                rs_parcel = nilearn.image.resample_to_img(
                    parcel,
                    noiseceil,
                    interpolation='continuous',
                )
                rs_parcel = nib.nifti1.Nifti1Image(
                    (rs_parcel.get_fdata() > 0.001).astype(int),
                    affine=rs_parcel.affine,
                )

                parcel_nvox = 50 # set maximum voxel count per parcel
                tshold = 0.1  # minimum noise ceiling value to include in ROI

                """
                Smooth resampled parcel to include neighboring regions
                """
                rs_parcel_sm = smooth_img(
                    imgs=rs_parcel,
                    fwhm=fwhm,
                )
                rs_parcel_sm = nib.nifti1.Nifti1Image(
                    (rs_parcel_sm.get_fdata() > 0.01).astype(int),
                    affine=rs_parcel_sm.affine,
                )
                wide_mask = rs_parcel_sm

                """
                Rank in-mask voxels per noise ceiling value.
                Keep only the n voxels with the higher scores,
                where n = the group parcel's voxel count.
                """
                masked_ncvox = apply_mask(noiseceil, wide_mask)
                sorted_NC = np.sort(masked_ncvox)
                nc_cutoff = sorted_NC[-parcel_nvox]
                # reduce vox count until cutoff noise ceil is >= threshold
                while nc_cutoff < tshold and parcel_nvox > 5:
                    parcel_nvox -= 1
                    nc_cutoff = sorted_NC[-parcel_nvox]

                select_mask = nib.nifti1.Nifti1Image(
                    (noiseceil.get_fdata() >= nc_cutoff).astype(int),
                    affine=noiseceil.affine,
                )
                # re-generate wide mask w only voxels above noise-ceiling cutoff
                wide_mask = intersect_masks(
                    [select_mask, rs_parcel_sm],
                    threshold=1,
                    connected=single_cluster,
                )
                tval = ("%.2f" % nc_cutoff)

                if np.sum(wide_mask.get_fdata()) > 0:
                    vcount += int(np.sum(wide_mask.get_fdata()))
                    tvals.append(float(tval))
                    hemi_masks.append(wide_mask)

            if len(hemi_masks) > 0:

                final_mask = intersect_masks(
                    hemi_masks, threshold=0, connected=False,
                )
                tvalue = str(min(tvals))  # lowest threshold between the 2 hemi
                nib.save(
                    final_mask,
                    f"{data_dir}/fLoc/floc.rois/sub-{sub_num}/rois/task-derived"
                    f"/sub-{sub_num}_task-floc_space-T1w_stats-noiseCeil_"
                    f"contrast-{roi}_cutoff-{tvalue}_nvox-{vcount}_fwhm-{fwhm}"
                    f"_mask.nii.gz",
                )


if __name__ == '__main__':
    """
    Script produces ROI masks in subject space from subject's fLoc contrasts,
    using group-derived ROI masks as priors.
    """
    args = get_arguments()

    if args.no_data:
        """
        for sub-06 who did not complete the fLoc task
        """
        create_subject_rois_noData(
            args.data_dir, args.sub, args.fwhm, args.one_cluster,
        )

    else:
        create_subject_rois(
            args.data_dir,
            args.sub,
            args.alpha,
            args.fwhm,
            args.percent_cluster,
            args.use_smooth_bold,
            args.one_cluster,
        )
