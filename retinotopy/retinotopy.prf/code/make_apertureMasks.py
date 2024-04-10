import os
import argparse
from pathlib import Path

import numpy as np
from scipy.io import savemat


def get_arguments():

    parser = argparse.ArgumentParser(
        description='Make stimulus masks from Psychopy task frames for retinotopy analysis'
    )
    parser.add_argument(
        '--data_dir',
        required=True,
        type=str,
        help='absolute path to cneuromod-things/retinotopy directory',
    )
    parser.add_argument(
        '--per_slice',
        action='store_true',
        default=False,
        help='if True, outputs aperture masks per brain slice as well as per TR',
    )

    return parser.parse_args()


def make_apertures(
    data_dir: str,
    per_slice: bool,
) -> None:
    """."""

    tasks = ['bars', 'rings', 'wedges']
    TR = 1.49
    # task's frames per second (rate of aperture change)
    fps = 15.0

    stim_path = Path(
        f"{data_dir}/retinotopy.fmriprep/sourcedata/retinotopy/retino.stimuli/"
    )
    out_path = Path(f"{data_dir}/retinotopy.prf/apertures")

    for task in tasks:
        # frames per task
        fpt = 469 if task is 'wedges' else 420

        if task is 'bars':
            ind = [0, 1, 0, 1, 2, 3, 2, 3]
            reverse = [False, False, True, True, False, False, True, True]
            task_frames = np.load(
                f"{stim_path}/apertures_bars.npz"
            )['apertures']
        else:
            ind = np.repeat(0, 8)
            reverse = [False, False, False, False, True, True, True, True]
            if task is 'wedges':
                task_frames = np.load(
                    f"{stim_path}/apertures_wedge_newtr.npz"
                )['apertures']
            else:
                task_frames = np.load(
                    f"{stim_path}/apertures_ring.npz"
                )['apertures']

        """
        Normalize to values between 0 and 1...
        Current values ranges between 0 and 255
        """
        scaled_frames = task_frames / 255.0

        """
        Cycle onset times (in s) validated from task output files across 3 tasks,
        over 6 sessions, for 3 subjects.
        Averages in seconds from sub-01, sub-02 and sub-03, ses-002 to ses-006
        """
        onsets = [
            16.033847, 47.3222376, 78.615124, 109.897517,
            153.194802, 184.478802, 215.772451, 247.061259,
        ]

        """
        16s of instructions, 4 cycles of ~32s, 12s pause, 4 cycles of ~32s,
        16s of instructions.

        202 TRs acquired
        """
        frame_sequence = np.zeros([768, 768, int(300*fps)])

        def get_cycle(frames, index, flip_order):
            f = frames[:, :, index:index+fpt]
            if flip_order:
                f = np.flip(f, axis=2)
            return f

        """
        8 cycles
        """
        for i in range(8):
            idx_frames = ind[i]*28*15
            idx_seq = int(np.round(onsets[i] / (1.0/fps)))
            frame_sequence[:, :, idx_seq:idx_seq+fpt] = get_cycle(
                scaled_frames, idx_frames, reverse[i])

        savemat(
            f"{out_path}/task-retinotopy_condition-{task}_desc-perFrame_apertures.mat",
            {task: frame_sequence.astype('bool')}
        )


        if per_slice:
            '''
            Create a set of frames for a particular brain slice.

            From the shown frames, the frame that is closest in time
            to a brain slice's time of acquisition is chosen for that particular
            slice.

            15 = brain slices per TR (60 slices/ TR, with 4 multibands)
            300s / 1.49s = number of TRs (202)
            '''
            bslice_per_TR = 15

            total_slices = int(np.floor(300/TR)*15)
            frame_slice = np.zeros([768, 768, total_slices])

            for slice in range(total_slices):
                idx = int(np.round((slice * TR * fps) / bslice_per_TR))
                frame_slice[:, :, slice] = frame_sequence[:, :, idx]

            savemat(
                f"{out_path}/task-retinotopy_condition-{task}_desc-perSlice_apertures.mat",
                {task: frame_slice.astype('bool')}
            )

            '''
            Just a different way to reslice the frames:
                For each brain slice (each of 15),
                a binary frame is chosen for each TR
            Outputs 15 different files
            '''
            for slice_num in range(bslice_per_TR):
                slice_frames = np.zeros([768, 768, int(np.floor(300/TR))])

                for t in range(int(np.floor(300/TR))):
                    idx = int(np.round(TR*fps*(t + (slice_num/bslice_per_TR))))
                    slice_frames[:, :, t] = frame_sequence[:, :, idx]

                savemat(
                    f"{out_path}/task-retinotopy_condition-{task}_desc-perTR_slice-{slice_num}_apertures.mat",
                    {f"{task}_slice{slice_num}": slice_frames.astype('bool')}
                )

        '''
        Frames averaged per TR
        202 TRs in total to match the number of TRs in a run's bold file
        '''
        frame_TR = np.zeros([768, 768, int(np.ceil(300/TR))])

        for f in range(frame_TR.shape[2]):
            idx_0 = int(np.round(f*fps*TR))
            idx_n = int(np.round((f+1)*fps*TR))
            frame_TR[:, :, f] = np.mean(
                frame_sequence[:, :, idx_0:idx_n], axis=2)

        # Save output
        savemat(
            f"{out_path}/task-retinotopy_condition-{task}_desc-perTR_apertures.mat",
            {task: frame_TR.astype('f4')}
        )


if __name__ == '__main__':
    '''
    For each of the three retinotopy tasks (bars, rings and wedges),
    a series of frames is reconstructed from the Psychopy task script and the
    aperture frames (retino.stimuli); aperture frame rate is 15 frames per sec.

    Frames (apertures) are then averaged within TR to downsample their temporal
    resolution to match the bold signal acquisition.

    The output is a .mat file that contains a dictionary with a single
    numpy array with frames per TR (dim 768x768x202 = h, w, f).
    Values are float [0, 1] to encode the partial viewing of stimuli within a
    given pixel throughout a TR, due to aperture movement.

    Note that these float stimuli are adapted for Kendrick Kay's
    analyzePRF toolbox (on which the cneuromod retino task is based),
    but that other retinotopy toolboxes require binary masks.

    Additional script outputs can include binary frames (masks) resliced
    per brain slice (to account for slice-timing).

    The CNeuroMod Psychopy task script lives here:
    https://github.com/courtois-neuromod/task_stimuli/blob/master/src/tasks/retinotopy.py
    '''
    args = get_arguments()

    make_apertures(args.data_dir, args.per_slice)
