import glob, os, json
import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from tqdm import tqdm


COL_NAMES = [
                'TrialNumber', 'atypical', 'atypical_log',
                'exclude_session', 'image_name', 'image_category',
                'things_image_nr', 'things_category_nr', 'onset',
                'duration', 'repetition', 'condition', 'response_type',
                'subcondition', 'response_subtype', 'response_txt',
                'response_confidence', 'response_typeConf',
                'response_time', 'session_trial_time', 'delay_days',
                'delay_seconds', 'trials_since_lastrep',
                'highercat27_names', 'highercat53_names',
                'highercat53_num', 'categ_concreteness',
                'categ_wordfreq_COCA', 'categ_nameability',
                'img_nameability', 'categ_recognizability',
                'img_recognizability', 'categ_consistency',
                'img_consistency',
                #'img_memorability',   # need permission to share
                'categ_size',
                'categ_arousal', 'categ_manmade', 'categ_precious',
                'categ_living', 'categ_heavy', 'categ_natural',
                'categ_moves', 'categ_grasp', 'categ_hold',
                'categ_be_moved', 'categ_pleasant',
            ]

COL_MANUAL = [
                'face', 'body', 'lone_object',
                'human_face', 'human_body',
                'nh_mammal_face', 'nh_mammal_body',
                'central_face', 'central_body',
                'artificial_face', 'artificial_body',
                'scene', 'rich_background',
]

def get_arguments():
    parser = argparse.ArgumentParser(
        description="Compiles a .tsv file of trialwise image annotations for all subject's runs"
    )
    parser.add_argument(
        '--events_dir',
        required=True,
        type=str,
        help='path to dataset directory that contains events.tsv files'
    )
    parser.add_argument(
        '--annot_dir',
        required=True,
        type=str,
        help='path to directory that contains the annotation files',
    )
    parser.add_argument(
        '--out_dir',
        required=True,
        type=str,
        help='path to directory where output files are saved',
    )
    parser.add_argument(
        '--sub',
        required=True,
        type=str,
        help='two-digit subject number'
    )

    return parser.parse_args()


def get_vals(event_file, label='image_nr'):
    '''
    Returns values of specified dataframe column as numpy array
    '''
    return pd.read_csv(event_file, sep='\t')[label].to_numpy()


def get_name(row):
    '''
    Returns image name from image path for pandas DF row
    '''
    return row['image_path'].split('/')[-1].split('.')[0]


def get_cat(row):
    '''
    Returns image category from image path for pandas DF row
    '''
    return row['image_path'].split('/')[-2]


def get_respType(row):
    '''
    Return response type based on image condition and subject's accuracy
    '''
    if row['condition']=='seen' and row['error']==False:
        return 'Hit'
    if row['condition']=='seen' and row['error']==True:
        return 'Miss'
    if row['condition']=='unseen' and row['error']==False:
        return 'CR'
    if row['condition']=='unseen' and row['error']==True:
        return 'FA'
    return np.nan


def get_respSubtype(row):
    '''
    Return response subtype based on image subcondition and subject's accuracy
    '''
    if row['subcondition']=='seen-within' and row['error']==False:
        return 'Hit_w'
    if row['subcondition']=='seen-between' and row['error']==False:
        return 'Hit_b'
    if row['subcondition']=='seen-within-between' and row['error']==False:
        return 'Hit_wb'
    if row['subcondition']=='seen-between-within' and row['error']==False:
        return 'Hit_bw'

    if row['subcondition']=='seen-within' and row['error']==True:
        return 'Miss_w'
    if row['subcondition']=='seen-between' and row['error']==True:
        return 'Miss_b'
    if row['subcondition']=='seen-within-between' and row['error']==True:
        return 'Miss_wb'
    if row['subcondition']=='seen-between-within' and row['error']==True:
        return 'Miss_bw'

    if row['subcondition']=='unseen-within' and row['error']==False:
        return 'CR'
    if row['subcondition']=='unseen-between' and row['error']==False:
        return 'CR'

    if row['subcondition']=='unseen-within' and row['error']==True:
        return 'FA'
    if row['subcondition']=='unseen-between' and row['error']==True:
        return 'FA'

    return np.nan


def get_respTypeConf(row):
    '''
    Return response type  based on image condition and subject's accuracy and confidence
    '''
    if row['condition']=='seen' and row['error']==False and row['response_confidence']==False:
        return 'Hit_LC'
    if row['condition']=='seen' and row['error']==False and row['response_confidence']==True:
        return 'Hit_HC'

    if row['condition']=='seen' and row['error']==True and row['response_confidence']==False:
        return 'Miss_LC'
    if row['condition']=='seen' and row['error']==True and row['response_confidence']==True:
        return 'Miss_HC'

    if row['condition']=='unseen' and row['error']==False and row['response_confidence']==False:
        return 'CR_LC'
    if row['condition']=='unseen' and row['error']==False and row['response_confidence']==True:
        return 'CR_HC'

    if row['condition']=='unseen' and row['error']==True and row['response_confidence']==False:
        return 'FA_LC'
    if row['condition']=='unseen' and row['error']==True and row['response_confidence']==True:
        return 'FA_HC'

    return np.nan


def format_cat53(categ53):
    '''
    Transform matrix of 1-hot (1854 concepts x 53 higher order categories)
    into a DataFrame
    '''
    cat53_1854 = [ [] for _ in range(1854) ]
    cat53_1854_num = [ [] for _ in range(1854) ]

    for i, column in enumerate(categ53.columns[2:]):
        indices = np.where(categ53[column].to_numpy() == 1)[0].tolist()
        for idx in indices:
            cat53_1854[idx] = cat53_1854[idx] + [column]
            cat53_1854_num[idx] = cat53_1854_num[idx] + [i]
    d53 = {'cat53_name': cat53_1854, 'cat53_num': cat53_1854_num}
    cat53_df = pd.DataFrame(data=d53)

    return cat53_df


def get_THINGSmatch(row, idx_col, THINGS_colLabel, THINGS_file, usekey=False):
    '''
    Use image/category number from row to index entry in column of interest in THINGSdatabase file
    '''
    idx = row[idx_col] if usekey else row[idx_col]-1
    return THINGS_file[THINGS_colLabel][idx]


def process_files(
    ev_path: str,
    annot_path: str,
    out_path: str,
    sub_num: str,
) -> None:
    '''
    Generates an enriched design matrix for each run (event file),
    with class labels based on image stimuli, their properties
    (from THINGS and THINGSplus datasets), memory conditions,
    and subject's own memory performance (e.g., HIT, FA, CR, Miss,
    plus subject's confidence).

    Save all design matrices in a single concatenated .tsv file
    of trial-wise annotations per participant. Also exports a list of
    image numbers and category numbers for all the stimuli shown to the
    participant throughout the entire task (across sessions).

    Input:
        ev_path: path to bids directory that contains *events.tsv files
        annot_path: path to directory that contains image-wise annotations
        out_path: path to output directory
        sub_num: two-digit subject number
    Output:
        None
    '''
    event_files = sorted(glob.glob(
        f"{ev_path}/sub-{sub-num}/ses-*/func/*events.tsv"
    ))

    '''
    Compile a list of image numbers and a list of category numbers for
    all the images seen by the participant throughout the task (all sessions)
    '''
    image_numbers = [
        get_vals(ef, 'things_image_nr') for ef in tqdm(
            event_files, desc='extracting image numbers from events files',
        )
    ]
    image_categories = [
        get_vals(ef, 'things_category_nr') for ef in tqdm(
            event_files, desc='extracting image categories from events files'
        )
    ]

    image_numbers = np.unique(np.hstack(image_numbers)).astype(int)
    image_categories = np.unique(np.hstack(image_categories)).astype(int)

    imgNum_df = pd.DataFrame(image_numbers, columns=['things_image_numbers'])
    catNum_df = pd.DataFrame(image_categories, columns=['things_image_categories'])

    Path(f"{out_path}/sub-{sub_num}/beh").mkdir(parents=True, exist_ok=True)
    imgNum_df.to_csv(
        f"{out_path}/sub-{sub_num}/beh/"
        f"sub-{sub_num}_task-things_desc-imgNum.tsv",
        sep='\t', header=True, index=False,
    )
    catNum_df.to_csv(
        f"{out_path}/sub-{sub_num}/beh/"
        f"sub-{sub_num}_task-things_desc-catNum.tsv",
        sep='\t', header=True, index=False,
    )

    '''
    Generate concatenated matrix of trial-wise annotations
    '''
    ids = ['subject', 'session', 'run']

    manual_cols = [f"manual_{x}" for x in COL_MANUAL]
    sub_df = pd.DataFrame(columns=ids + COL_NAMES + manual_cols)

    for ev_path in tqdm(event_files, desc='exporting design matrices'):

        sub, ses, _, run, _ = os.path.basename(ev_path).split('_')
        ses_num = ses[-2:]
        run_num = f'0{run[-1]}'

        df = pd.read_csv(ev_path, sep='\t')

        # UPDATE: already inserted in cleaned up event files (skip this step)
        # Add suject, session and run identifiers for concatenation
        #df.insert(loc=0, column=ids[0], value=sub_num, allow_duplicates=True)
        #df.insert(loc=1, column=ids[1], value=ses_num, allow_duplicates=True)
        rn = df['run'][0]
        assert f'{rn:02}' == run_num
        #df.insert(loc=2, column=ids[2], value=run_num, allow_duplicates=True)

        # Add columns generated from events.tsv file data
        df['image_name'] = df.apply(lambda row: get_name(row), axis=1)
        df['image_category'] = df.apply(lambda row: get_cat(row), axis=1)
        df['response_type'] = df.apply(lambda row: get_respType(row), axis=1)
        df['response_subtype'] = df.apply(lambda row: get_respSubtype(row), axis=1)
        df['response_typeConf'] = df.apply(lambda row: get_respTypeConf(row), axis=1)
        df[['things_image_nr', 'things_category_nr']] = df[
            ['things_image_nr', 'things_category_nr']].astype(int)

        # Add columns of annotations imported from THINGS & THINGSplus databases
        categ53 = pd.read_csv(
            f"{annot_path}/THINGS+/category53_wideFormat.tsv", sep= ',')
        # transform matrix of one-hots into DF w two columns before
        # indexing values
        cat53_1854 = format_cat53(categ53)
        df['highercat53_names'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'cat53_name', cat53_1854), axis=1)
        df['highercat53_num'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'cat53_num', cat53_1854), axis=1)

        # Ratings averaged over / categorizations common to images
        # from same category / concept
        tg_concepts = pd.read_csv(
            f"{annot_path}/THINGS+/things_concepts.tsv", sep= '\t')
        df['highercat27_names'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'Bottom-up Category (Human Raters)',
            tg_concepts), axis=1)
        df['categ_wordfreq_COCA'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'COCA word freq (online)',
            tg_concepts), axis=1)
        df['categ_concreteness'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'Concreteness (M)', tg_concepts), axis=1)


        img_concepts = pd.read_csv(
            f"{annot_path}/THINGS+/imageLabeling_objectWise.tsv", sep= ',')
        df['categ_nameability'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'nameability_mean', img_concepts), axis=1)
        df['categ_recognizability'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'recognizability_mean', img_concepts), axis=1)
        df['categ_consistency'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'consistency_mean', img_concepts), axis=1)


        obj_size = pd.read_csv(
            f"{annot_path}/THINGS+/size_meanRatings.tsv", sep= ',')
        df['categ_size'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'Size_mean', obj_size), axis=1)


        obj_properties = pd.read_csv(
            f"{annot_path}/THINGS+/objectProperties_meanRatings.tsv", sep= ',')
        df['categ_manmade'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'manmade_mean', obj_properties), axis=1)
        df['categ_precious'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'precious_mean', obj_properties), axis=1)
        df['categ_living'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'lives_mean', obj_properties), axis=1)
        df['categ_heavy'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'heavy_mean', obj_properties), axis=1)
        df['categ_natural'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'natural_mean', obj_properties), axis=1)
        df['categ_moves'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'moves_mean', obj_properties), axis=1)
        df['categ_grasp'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'grasp_mean', obj_properties), axis=1)
        df['categ_hold'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'hold_mean', obj_properties), axis=1)
        df['categ_be_moved'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'be.moved_mean', obj_properties), axis=1)
        df['categ_pleasant'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'pleasant_mean', obj_properties), axis=1)

        ar = pd.read_csv(
            f"{annot_path}/THINGS+/arousal_meanRatings.tsv", sep= ','
        )
        df['categ_arousal'] = df.apply(lambda row: get_THINGSmatch(
            row, 'things_category_nr', 'arousing_mean', ar), axis=1)

        # Image-specific ratings
        img_labels = pd.read_csv(
            f"{annot_path}/THINGS+/imageLabeling_imageWise.tsv", sep= ',')
        img_labels['image_name'] = img_labels.apply(
            lambda row: row['image'].split('/')[-1].split('.')[0], axis=1)
        img_labels = img_labels.set_index('image_name')
        df['img_nameability'] = df.apply(lambda row: get_THINGSmatch(
            row, 'image_name', 'nameability', img_labels, usekey=True), axis=1)
        df['img_recognizability'] = df.apply(lambda row: get_THINGSmatch(
            row, 'image_name', 'recognizability', img_labels, usekey=True), axis=1)
        df['img_consistency'] = df.apply(lambda row: get_THINGSmatch(
            row, 'image_name', 'naming_consistency', img_labels, usekey=True), axis=1)

        # Image-specific memorability (courtesy of Wilma Bainbridge's group)
        # NOTE: need permission to share
        #img_memo = pd.read_csv(
        #    f"{annot_path}/THINGS+/THINGS_Memorability_Scores.csv", sep= ','
        #)
        #img_memo['image_name'] = img_memo.apply(
        #    lambda row: row['image_name'].split('/')[-1].split('.')[0], axis=1)
        #img_memo = img_memo.set_index('image_name')
        #df['img_memorability'] = df.apply(lambda row: get_THINGSmatch(
        #    row, 'image_name', 'cr', img_memo, usekey=True), axis=1)

        # Add columns of imported manual annotations
        img_manual = pd.read_csv(
            f"{annot_path}/task-things_desc-manual_image-annotations.tsv",
            sep= '\')
        img_manual = img_manual.set_index('image_name')
        for m_name in COL_MANUAL]:
            df[f'manual_{m_name]}'] = df.apply(lambda row: get_THINGSmatch(
                row, 'image_name', m_name, img_manual, usekey=True), axis=1)

        final_df = df[ids + COL_NAMES + manual_cols]
        sub_df = pd.concat((sub_df, final_df), ignore_index=True)

    sub_df.to_csv(
        f"{out_path}/sub-{sub_num}/beh/"
        f"sub-{sub_num}_task-things_desc-annotation-per-trial_beh.tsv",
        sep='\t', header=True, index=False,
    )


if __name__ == '__main__':
    '''
    Script processes events.tsv files to create columns of interest
    for classification analyses.

    Columns include class-wise and image-wise labels and ratings from
    the THINGS+ database, as well as indicators of trial-wise memory performance.

    Values are exported as one .tsv file per subject for which all sessions
    and runs are concatenated.

    Script to be ran on elm within ~/my_venv/retino_venv environment
    '''

    args = get_arguments()

    process_files(args.events_dir, args.annot_dir, args.out_dir, args.sub)
