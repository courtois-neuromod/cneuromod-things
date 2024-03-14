from pathlib import Path

import h5py
import numpy as np


if __name__ == '__main__':
    '''
    Dumb little script outputs one .h5 file of runs nested under sessions per subject,
    to import in matlab and loop over while running GLMsingle
    '''
    data_path = Path('../../').resolve()

    h5file = h5py.File(f"{data_path}/task-things_desc-runlist.h5",'w')

    sub_list = ['01', '02', '03', '06']

    for sub in sub_list:
        h5file.create_group(sub)

        subj_h5file = h5py.File(
            f'{data_path}/sub-{sub}/GLMsingle/input/sub-{sub}_task-things_space-T1w_maskedBOLD.h5', 'r'
        )

        subj_sessions = [str(x) for x in subj_h5file.keys() if x != 'TR']
        h5file[sub].create_dataset('sessions', data=np.array(subj_sessions).astype(int))

        for subj_ses in subj_sessions:
            subj_runs = [int(x) for x in subj_h5file[subj_ses].keys()]
            h5file[sub].create_dataset(str(int(subj_ses)), data=subj_runs)

        subj_h5file.close()

    h5file.close()
