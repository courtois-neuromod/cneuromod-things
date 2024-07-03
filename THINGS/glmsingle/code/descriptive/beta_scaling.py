import glob, sys
from pathlib import Path

import numpy as np
import nilearn
from nilearn.masking import apply_mask, intersect_masks
from sklearn import manifold
from sklearn.decomposition import PCA
import nibabel as nib
import tqdm

import argparse


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Applies dimensionality reduction to ROI-specific beta scores",
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to cneuromod-things project repo',
    )
    parser.add_argument(
        '--sub_num',
        required=True,
        type=str,
        help='two-digit subject number',
    )
    parser.add_argument(
        '--n_comp',
        default=2,
        type=int, help='number of dimensions (components) in final visualization'
    )
    parser.add_argument(
        '--skip_pca',
        action='store_true',
        default=False,
        help='if True, do not apply PCA before scaling',
    )
    parser.add_argument(
        '--n_iter',
        default=2000,
        type=int,
        help='number of iterations',
    )
    parser.add_argument(
        '--perplex',
        default=100,
        type=int,
        help='perplexity',
    )
    parser.add_argument(
        '--learn_rate',
        default=500,
        type=int,
        help='learning rate',
    )
    parser.add_argument(
        '--random_state',
        default=0,
        type=int,
        help='random seed',
    )
    parser.add_argument(
        '--perImg',
        action='store_true',
        default=False,
        help='if true, use beta scores averaged per image, else treat each trial separately',
    )
    parser.add_argument(
        '--nc_cutoff',
        default=1000,
        type=int,
        help='number of voxels with highest noise ceilings included in each ROI',
    )

    return parser.parse_args()


def get_betas(args):
    '''
    Load beta scores
    if args.perImg: (per image)
        - normalized (z-scored) betas are averaged per image
        - only images with 3 repetitions are included
        - dim = (images, voxels)
    else:
        - normalized (z-scored) betas per single trial
        - blank trials (no reccorded response) are excluded
        - dim = (trials, voxels)

    img_idx:
        - the row number indexes the image name (label), and its
        corresponding beta values in the betas file
        -  dim=(images,) if args.perImg else (trials,)
    '''
    sub_num = args.sub_num
    beta_path = Path(
        f"{args.data_dir}/THINGS/glmsingle/sub-{sub_num}/descriptive/"
    )
    desc = "perImage" if args.perImg else "perTrial"
    betas = np.load(
        f"{beta_path}/sub-{sub_num}_task-things_space-T1w_stats-betas_"
        f"desc-{desc}_statseries.npy",
        allow_pickle=True,
    )
    img_idx = np.load(
        f"{beta_path}/sub-{sub_num}_task-things_desc-{desc}_labels.npy",
        allow_pickle=True,
    )
    # Load THINGS brain mask used to generate beta arrays
    things_mask = nib.load(
        f"{args.data_dir}/THINGS/glmsingle/sub-{sub_num}/glmsingle/input/"
        f"sub-{sub_num}_task-things_space-T1w_label-brain_desc-unionNonNaN_"
        "mask.nii",
    )

    return betas, img_idx, things_mask


def get_floc_masks(args, things_mask):
    """
    Create the following masks from fLoc task results:
    - face_FFA_OFA: FFA + OFA ROIs identified with fLoc
    - scene_PPA_MPA_OPA: PPA + MPA + OPA ROIs identified with fLoc
    - floc_3contrasts: union of intersections between Kanwisher parcels (face, body and place,
      all warped to T1w space) and voxels with t > 3.72 on at least one of the three
      GLM contrasts from the fLoc task (faces, bodies, places).
    - floc_3contrasts_lt (low threshold): union of intersections between Kanwisher parcels
      (face, body and place, warped to T1w space) and voxels with t > 2.5
      on any of the three GLM contrasts from the fLoc task (faces, bodies, places).
    """
    sub_num = args.sub_num
    floc_masks_path = Path(
        f"{args.data_dir}/fLoc/rois/sub-{sub_num}/rois/task-derived"
    )

    floc_rois = [
        "face_roi-FFA", "face_roi-OFA",
        "scene_roi-MPA", "scene_roi-OPA", "scene_roi-PPA",
    ]
    floc_roi_masks = []
    for rname in floc_rois:
        rpath = glob.glob(
            f"{floc_masks_path}/sub-{sub_num}_task-floc_space-T1w_stats-"
            f"tscores_contrast-{rname}_cutoff-*_desc-unsmooth_mask.nii.gz"
        )
        assert len(rpath) == 1
        floc_roi_masks.append(
            apply_mask(nib.load(rpath[0]), things_mask).astype(bool)
        )

    floc_contrasts = ["faces", "places", "bodies"]
    floc_contrast_masks = [
        apply_mask(nib.load(
            f"{floc_masks_path}/sub-{sub_num}_task-floc_space-T1w_stats-"
            f"tscores_contrast-{cname}_cutoff-3.72_desc-unsmooth_mask.nii.gz",
        ), things_mask).astype(bool) for cname in floc_contrasts
    ]
    """
    Lower-threshold alternative to floc_contrast_masks
    """
    floc_3contrasts_lt = get_floc_lowthesh(args, things_mask)

    return (
        (floc_roi_masks[0] + floc_roi_masks[1]).astype(bool),
        (floc_roi_masks[2] + floc_roi_masks[3] + floc_roi_masks[4]).astype(bool),
        np.sum(np.stack(floc_contrast_masks), axis=0).astype(bool),
        floc_3contrasts_lt,
    )


def get_floc_lowthesh(args, things_mask):
    """
    Function loads the (NSD fLoc) t-contrasts and the Kanwisher parcels and
    computes the intersection of parcels & t > 2.5 for the face, scene and body
    contrasts, respectively, then it computes the union between the 3 masks.

    Note: replicates an older t-SNE analysis that used a fLoc task cutoff of
    t >=2.5 within the face, scene and body Kanwisher parcels.

    These intersection masks (t-scores + parcels) are not included in the latest dset;
    the current intersection masks uses a higher threshold (t > 3.72, alpha = 0.0001)
    """
    sub_num = args.sub_num
    mask_list = []

    for c in [('body', 'bodies'), ('face', 'faces'), ('scene', 'places')]:
        # threshold subject contrast from fLoc task (NSD contrast)
        dmap = nib.load(
            f"{args.data_dir}/fLoc/rois/sub-{sub_num}/glm/"
            f"sub-{sub_num}_task-floc_space-T1w_model-GLM_stats-tscores_"
            f"contrast-{c[1]}_desc-unsmooth_statseries.nii.gz"
        )
        thresh_dmap = nib.nifti1.Nifti1Image(
            (dmap.get_fdata() > 2.5).astype("int32"),
            affine=dmap.affine,
        )

        # load subject-specific parcel warped from CVS to MNI to T1w space
        parcel = nib.load(
            f"{args.data_dir}/fLoc/rois/sub-{sub_num}/rois/from_atlas/"
            f"sub-{sub_num}_parcel-kanwisher_space-T1w_contrast-{c[0]}_mask.nii" # TODO: rename probseg?
        )
        # transform probseg mask into binary mask
        parcel = nib.nifti1.Nifti1Image(
            (parcel.get_fdata() >=2).astype("int32"),
            affine=parcel.affine,
        )
        # resample parcel to functional space
        rs_parcel = nilearn.image.resample_to_img(
            parcel, dmap, interpolation='nearest',
        )

        join_mask = intersect_masks(
            [thresh_dmap, rs_parcel],
            threshold=1,
            connected=False,
        )
        mask_list.append(apply_mask(join_mask, things_mask))

    return np.sum(np.stack(mask_list), axis=0).astype(bool)


def get_retino_mask(args, things_mask):
    """
    Create the following mask from retinotopy task results:
    - v1_v2_v3: V1 + V2 + V3 ROIs identified with retinotopy + Neuropythy
    """
    sub_num = args.sub_num
    retino_roi_masks = [
        apply_mask(nib.load(
            f"{args.data_dir}/retinotopy/prf/sub-{sub_num}/rois/"
            f"sub-{sub_num}_task-retinotopy_space-T1w_model-npythy_"
            f"label-{roi}_desc-nn_mask.nii.gz",
        ), things_mask).astype(bool) for roi in ["V1", "V2", "V3"]
    ]

    return np.sum(np.stack(retino_roi_masks), axis=0).astype(bool)


def get_noiseCeil_mask(args, things_mask):
    """
    Create the following mask from THINGS noise ceilings:
    - top_NC: voxels (default number is 1000) with highest noise ceiling values,
    regarless of location or categorical preference.
    """
    sub_num = args.sub_num
    # load and mask noise ceiling map to be in same space as betas
    flat_noiseceil = apply_mask(nib.load(
        f"{args.data_dir}/THINGS/glmsingle/sub-{sub_num}/glmsingle/output/"
        f"sub-{sub_num}_task-things_space-T1w_model-fitHrfGLMdenoiseRR_"
        "stats-noiseCeilings_statmap.nii.gz",
    ), things_mask)

    nc_thresh = np.sort(flat_noiseceil)[-args.nc_cutoff]

    return (flat_noiseceil >= nc_thresh).astype(bool)


def get_mask_list(args, things_mask):
    """
    ROI masks are:
    - face_FFA_OFA: FFA + OFA ROIs identified with fLoc
    - scene_PPA_MPA_OPA: PPA + MPA + OPA ROIs identified with fLoc
    - V1_V2_V3: V1 + V2 + V3 ROIs identified with retinotopy + Neuropythy
    - floc_3contrasts: union between Kanwisher parcels (face, body and place,
      warped to T1w space) and voxels with t > 3.72 on any of the three
      GLM contrasts from the fLoc task (faces, bodies, places).
    - floc_3contrasts_lt (low threshold): union between Kanwisher parcels
      (face, body and place, warped to T1w space) and voxels with t > 2.5
      on any of the three GLM contrasts from the fLoc task (faces, bodies, places).
    - top_NC: voxels (default number is 1000) with highest noise ceiling values,
    regarless of location or categorical preference.
    """
    # Get ROI masks from the fLoc task
    (
        face_FFA_OFA,
        scene_PPA_MPA_OPA,
        floc_3contrasts,
        floc_3contrasts_lt,
    ) = get_floc_masks(args, things_mask)

    # Get ROI mask from the retinotopy task
    v1_v2_v3 = get_retino_mask(args, things_mask)

    top_NC = get_noiseCeil_mask(args, things_mask)

    return [
        ('face_FFA_OFA', face_FFA_OFA),
        ('scene_PPA_MPA_OPA', scene_PPA_MPA_OPA),
        ('V1_V2_V3', v1_v2_v3),
        ('floc_3contrasts', floc_3contrasts),
        ('floc_3contrasts_lowthresh', floc_3contrasts_lt),
        ('top_NC', top_NC),
    ]


def compute_tsne(args, betas, mask_list):
    """."""
    tsne_results = {}
    nvox_list = []

    for mask_name, roi_mask in tqdm.tqdm(mask_list, desc = 'computing t-SNE'):
        betas_roi = betas.T[roi_mask].T
        nvox_list.append(np.sum(roi_mask))

        if args.skip_pca:
            init = 'pca'
        else:
            betas_pca = PCA(n_components=50, svd_solver='full').fit(betas_roi)
            flipSigns = np.sum(betas_pca.components_, axis=1) < 0   # fix PC signs
            X = betas_pca.transform(betas_roi)
            X[:, flipSigns] *= -1
            init = X[:,:2] / np.std(X[:,0]) * 0.0001
            betas_roi = X

        scaling_model = manifold.TSNE(
            n_components=args.n_comp,
            perplexity=args.perplex, # default set to 100 like NSD
            init=init, # random, pca, custom...
            #metric="euclidean", #If metric is “precomputed”, X is assumed to be a distance matrix, e.g., NSD used RDMs
            n_iter=args.n_iter, # 1000 is sklearn default; doubled to 2000
            learning_rate=args.learn_rate, # usually in the [10.0, 1000.0] range; default around 200 showed signs that too low so increased to 500
            random_state=args.random_state,
        )

        betas_tsne = scaling_model.fit_transform(betas_roi)
        tsne_results[mask_name] = betas_tsne

    return tsne_results, nvox_list


def save_tsne(args, img_idx, mask_list, tsne_results, nvox_list):
    """
    Format results and save as numpy arrays
    """
    desc = "perImage" if args.perImg else "perTrial"
    out_path = Path(
        f"{args.data_dir}/THINGS/glmsingle/sub-{args.sub_num}/descriptive/"
        f"sub-{args.sub_num}_task-things_space-T1w_stats-tSNE_label-visualROIs_"
        f"desc-{desc}_statseries.npz"
    )

    np.savez(
        out_path,
        image_names=img_idx,
        mask_list=np.array([m[0] for m in mask_list]),
        vox_per_mask=np.array(nvox_list),
        face_FFA_OFA=tsne_results['face_FFA_OFA'],
        scene_PPA_MPA_OPA=tsne_results['scene_PPA_MPA_OPA'],
        V1_V2_V3=tsne_results['V1_V2_V3'],
        floc_3contrasts=tsne_results['floc_3contrasts'],
        floc_3contrasts_lowthresh=tsne_results['floc_3contrasts_lowthresh'],
        top_NC=tsne_results['top_NC']
    )


if __name__ == '__main__':
    """
    Script applies t-sne dimensionality reduction to beta scores contained
    within ROI masks.

    Betas scores are:
    - unsmoothed
    - normalized (z-scored)
    - either trial-specific (exclude trials with no reccorded response), or
      averaged per image (only images with 3 repetitions).
    """
    args = get_arguments()

    betas, img_idx, things_mask = get_betas(args)

    mask_list = get_mask_list(args, things_mask)

    tsne_results, nvox_list = compute_tsne(args, betas, mask_list)

    save_tsne(args, img_idx, mask_list, tsne_results, nvox_list)
