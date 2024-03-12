# Quality Checking notes for CNeuroMod-THING dataset

### Sessions to exclude from behav performance (MEMORY analyses):
SUB-01 \
repeat (scan problem) messes w conditions: 014, 015 (probably a very small issue) \
sleep / missing answers: to user's discretion \
SUB-02: all good \
SUB-03: ses-024, ses-025, ses-026 \
sub-06: ses-019, ses-020, ses-021, 022, 023, 024, 025, 026

***NOTE: a few cleaned up event.tsv files were edited manually after being validated and updated by the clean_events.py script*** \
The added column, 'exclude_session', was changed MANUALLY from FALSE to TRUE for all rows in the following files. \
This flag is to identify sessions that should be excluded from Memory analyses (but they are fine to assess perception) \
sub-03: sessions 24, 25 and 26 (all 6 runs) \
sub-06: sessions 19, 20, 21, 22, 23, 24, 25 and 26 (all 6 runs)

Additional sessions include a few "atypical trials" (those with repetition patterns that
deviate from the planned protocole, e.g. a run was interrupted & repeated, or ran out of order). \
Those trials are flagged with the 'atypical' (bool) and 'atypical_log' (text) columns,
and they (or the runs / sessions that contain them) can be excluded at the
discretion of the experimenter.


### EMPTY psychopy log Files (under /unf/eyetrack): cannot access trialwise timing info
update: date removed from file name for de-identification \
**SUB-01**
- ses-007, runs 1-6
- ses-009, runs 1-5
- ses-009, run 6
- ses-021, runs 4-6
- ses-032, runs 1-4
- ses-034, run 1
- ses-035, runs 1-3

**SUB-02**
- ses-018, runs 1-3
- ses-018, run 4
- ses-018, runs 5-6

**SUB-03**
- ses-035, runs 1-6

**SUB-06**
- ses-004, runs 1-6
- ses-005, runs 1-6
- ses-006, runs 1-6
- ses-007, runs 1-6
- ses-009, runs 1-6
- ses-010, runs 1-6
- ses-031, run 1
- ses-032, run 1
- ses-032, run 2
- ses-032, runs 3-6

**Workaround SOLUTION**: estimate run onset from onset of eyetracker for that run, and add time to trial "onset" value in events file \
Only the following sessions could not be given trialwise timestamps (no eyetracking data, no log files):
- sub-01, ses-007, runs 1-6
- sub-01, ses-021, run 6
- sub-02, ses-018, runs 4-6
- sub-06, ses-007, runs 1-6


### Deviations from pre-planned experimental protocol
***Sub-01, ses-017***: run 4 was somehow skipped, then administered at the very end of the session.  \
Run order was 1, 2, 3, 5, 6, 4, which modified some of the trial conditions  \
Not mentioned in the scan sheet, so I added a comment

***sub-03, session 14*** was ran twice? \
On [date removed], sub-02_ses-004 stimuli were accidentally run for sub-03's ses-014; \
**SOLUTION**: events files from sub-02 sess 004 were copied into session 13b to take the shown stimuli in consideration when validating events files with clean_events.py. LOG files were also copied for trialwise timing. \
*(All "b" sessions are non-valid, in-between sessions whose data were discarded from the final dataset).* \
The [date removed] session can be discarded. \
Note: session 14 was reran again (properly this time) on [date removed] in the proper order
(since ses-004 tests an earlier batch of stimuli all seen weeks before, it should not affect the performance of the other sessions beside increasing the between-session delay and perhaps introducing some interference; But it doesn't "spoil" unseen stimuli or repeats stimuli before their final (3rd) repetition.

***sub-03, session 25*** was accidentally ran instead of session 22... \
sessions 22, 23 and 24 were then ran, then session 25 was ran again a second time... \
SOLUTION: events files from sub-03 sess 025 ran on [date removed] (the first time) copied into session 21b to reflect shown stimuli. \
Files ran on [date removed] (the 2nd time) left as the final session 25. \
LOG files copied

***sub-06, session 20*** ran as sub-01... that session (sub-06, ses-020) is found (on elm) in
/data/neuromod/DATA/cneuromod/things, but not /unf/eyetracker/neuromod/things \
AH! it's saved under sub-01's session 20 under /unf; sub-06 ran on [date removed; earlier date],
sub-01 ran on [date removed; later date] (per google calendar) \
**SOLUTION**: move sub-06's session 20 files from under sub-01's session 20 (keep in dataset!); we may decide later to discard it for memory, but can still be used for vision \
LOG copied

***sub-06, session 19***: \
two "false start" sessions (launched but not completed); \
I gave them run numbers 40 (begining of run 4, between run 3 and the complete run 4) \
and run 50 (between runs 4 and 5), to be considered by clean_events.py during validation but then discarded


### Other resolved issues

***sub-01, session 14*** has 7 events files... \
First run's task was restarted after trial 17 because the scanner stopped, participant closed their eyes when they noticed the scanner stopped to avoid seeing the images. \
RESOLVED: I added a run_0 with only the 17 repeated trials to be considered by clean_events.py at validation (I deleted the rest of the events file manually) \
Edit manually \
first 17 trials: sub-01/ses-014/sub-01_ses-014_202xxxxx-[earlier time stamp]_task-thingsmemory_run-1_events.tsv -> relabelled as run-0 \
keep all trials: sub-01/ses-014/sub-01_ses-014_202xxxxx-[later time stamp]_task-thingsmemory_run-1_events.tsv -> remains run-1

***sub-03, session 1*** date is [date removed] \
FINE: files have correct timing info within directory

***sub-02, ses-008***: \
two event files for run 1, first has no recorded answers, second one has answers \
**RESOLVED**: first file was a test (no participant); the correct file is saved

***sub-06, ses-008***: \
two event files for run 1, the second one has only two recorded answers, first has full answers \
TODO: the wrong file was imported into BIDS, needs to be swaped \
**RESOLVED**

***sub-06, ses-008***: \
bold data from run 6 are misaligned with the other fmriprepped scans. All final analyses
(GLMsingle, noise ceilings, etc) exclude that particular run.
