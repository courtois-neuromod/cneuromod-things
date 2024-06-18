import argparse

from nilearn.image import load_img, new_img_like, index_img, resample_to_img
import numpy as np


def get_arguments():
    parser = argparse.ArgumentParser(
        description='Resamples neuropythy output to T1w space',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number. e.g., 01',
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to cneuromod-things/retinotopy/prf',
    )

    return parser.parse_args()


def export_maps(
    sub,
    data_dir,
    va_img,
    ref_img,
) -> None:
    """
    Create binary mask for each ROI index
    Note: 0 = Not a visual area
    """
    roi_idx = [
        (1, "V1"),
        (2, "V2"),
        (3, "V3"),
        (4, "hV4"),
        (5, "VO1"),
        (6, "VO2"),
        (7, "LO1"),
        (8, "LO2"),
        (9, "TO1"),
        (10, "TO2"),
        (11, "V3b"),
        (12, "V3a"),
    ]
    va = va_img.get_fdata()

    for (i, roi) in roi_idx:
        roi_arr = np.zeros(va.shape)
        roi_arr[np.where(va == i)] = 1.
        roi_img = new_img_like(va_img, roi_arr)
        # nearest extrapolation (preferred for binary mask)
        res_img = resample_to_img(roi_img, ref_img, interpolation='nearest')
        res_img.to_filename(
            f"{data_dir}/prf/sub-{sub}/rois/sub-{sub}_task-retinotopy_space-T1w"
            f"_model-npythy_label-{roi}_desc-nn_mask.nii.gz",
        )
        # also save linear interpolation for convenience
        lres_img = resample_to_img(roi_img, ref_img, interpolation='linear')
        lres_img.to_filename(
            f"{data_dir}/prf/sub-{sub}/rois/sub-{sub}_task-retinotopy_space-T1w"
            f"_model-npythy_label-{roi}_desc-linear_mask.nii.gz",
        )


def resample_npythy(
    sub: str,
    data_dir: str,
) -> None:

    ref_img = index_img(
        f"{data_dir}/fmriprep/sub-{sub}/ses-001/func/sub-{sub}_"
        "ses-001_task-bars_space-T1w_desc-preproc_part-mag_bold.nii.gz",
        0,
    )

    out_path = f"{data_dir}/prf/sub-{sub}/npythy/output"
    # resample neuropythy output to T1w
    for param in ['angle', 'eccen', 'sigma']:
        res_img = resample_to_img(
            f"{out_path}/inferred_{param}.nii.gz", ref_img, interpolation='linear',
        )
        res_img.to_filename(
            f"{out_path}/sub-{sub}_task-retinotopy_space-T1w_model-npythy"
            f"_stats-{param}_statseries.nii.gz",
        )
    res_img = resample_to_img(
        f"{out_path}/inferred_varea.nii.gz", ref_img, interpolation='nearest',
    )
    res_img.to_filename(
        f"{out_path}/sub-{sub}_task-retinotopy_space-T1w_model-npythy"
        "_stats-varea_dseg.nii.gz",
    )

    va_img = load_img(f"{out_path}/inferred_varea.nii.gz")
    export_maps(sub, data_dir, va_img, ref_img)


if __name__ == '__main__':
    '''
    Script resamples neuropythy visual ROIs into T1w functional space and
    exports one binary mask per ROI
    '''
    args = get_arguments()

    resample_npythy(args.sub, args.data_dir)
