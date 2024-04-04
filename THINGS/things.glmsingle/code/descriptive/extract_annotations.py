import glob, json, re
import argparse
from functools import singledispatch

import numpy as np
import pandas as pd


COL_NAMES = [
        'image_name', 'image_category',
        'things_image_nr', 'things_category_nr',

        'highercat27_names', 'highercat53_names', 'highercat53_num',
        'categ_concreteness', 'categ_wordfreq_COCA',
        'categ_nameability', 'img_nameability',
        'categ_consistency', 'img_consistency',
        'categ_size', 'categ_arousal', 'categ_manmade',
        'categ_precious', 'categ_living',
        'categ_heavy', 'categ_natural',
        'categ_moves', 'categ_grasp', 'categ_hold',
        'categ_be_moved', 'categ_pleasant',

        'manual_face', 'manual_body', 'manual_lone_object',
        'manual_human_face', 'manual_human_body', 'manual_nh_mammal_face',
        'manual_nh_mammal_body', 'manual_central_face',
        'manual_central_body', 'manual_artificial_face',
        'manual_artificial_body', 'manual_scene', 'manual_rich_background',
]


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Average betas per stimulus image from single-trial GLMsingle betas",
    )
    parser.add_argument(
        '--things_dir',
        required=True,
        type=str,
        help='path to THINGS data directory',
    )

    return parser.parse_args()


def convert(val_name, val):
    if val_name == 'highercat53_names':
        str_list = val.split("'")
        return [str_list[x] for x in range(1, len(str_list), 2)]
    elif val_name == 'highercat53_num':
        str_list = re.split(", ", val[1:-1]) if len(val[1:-1]) > 0 else []
        return [int(x) for x in str_list]
    elif isinstance(val, np.int64):
        return int(val)
    elif isinstance(val, np.float64):
        return float(val)
    else:
        return str(val)


if __name__ == '__main__':
    args = get_arguments()

    annot_list = sorted(
        glob.glob(
            f"{args.things_dir}/things.behaviour/sub-0*/beh/"
            "sub-0*_task-things_desc-perTrial_annotation.tsv"
        )
    )

    df = pd.concat(
        [pd.read_csv(x, sep='\t') for x in annot_list],
        axis=0,
        ignore_index=True,
    )

    img_annot = {}
    for i in range(df.shape[0]):
        img = df['image_name'].iloc[i]
        if img not in img_annot:
            img_annot[img] = {}
            for col_val in COL_NAMES:
                img_annot[img][col_val] = convert(col_val, df[col_val].iloc[i])

    with open(f"{args.things_dir}/things.glmsingle/task-things_imgAnnotations.json", 'w') as outfile:
        json.dump(img_annot, outfile)
