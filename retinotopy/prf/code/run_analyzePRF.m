
% <subject> = subject number, e.g. '01', '02', '03'
% <data_dir> = /path/to/cneuromod-things/retinotopy/prf
% <code_dir> = /path/to/cneuromod-things/retinotopy/prf/code
% <first_chunk> = start up chunk number (int), e.g. 0
% <last_chunk> = end chunk number (int), e.g. 100
% <nwork> = number of parpool workers (int), e.g. 32

% add paths to code and data directories
addpath(genpath(strcat(code_dir,"/analyzePRF")));
addpath(genpath(strcat(data_dir,"/apertures")));
addpath(genpath(strcat(data_dir,"/sub-",sub_num,"/prf/input/chunks")));


% https://www.mathworks.com/matlabcentral/answers/454021-how-to-replace-matlabpool-to-parpool
% https://www.mathworks.com/help/parallel-computing/parpool.html;jsessionid=4f2aaebed69057d75b8436992ba1
% TODO: set number of parallel workers
%(ginkgo : 30) et (elm : 40)
% p = gcp;
% p.NumWorkers

% set parallel computing
% Alliance Canada: https://docs.alliancecan.ca/wiki/MATLAB
% Create a "local" cluster object
% local_cluster = parcluster('local')
% Modify the JobStorageLocation to $SLURM_TMPDIR
% local_cluster.JobStorageLocation = getenv('SLURM_TMPDIR')
% Start the parallel pool
% parpool(local_cluster);
% parpool(32)
parpool(str2num(nwork))

% load apertures
load('task-retinotopy_condition-wedges_desc-perTR_apertures.mat');
load('task-retinotopy_condition-rings_desc-perTR_apertures.mat');
load('task-retinotopy_condition-bars_desc-perTR_apertures.mat');

stimuli = {single(wedges), single(rings), single(bars)};
clear wedges, clear rings, clear bars;

% number of voxels (as a reference)
% sub-01: 204387 voxels, 0-851 chunks
% sub-02: 219784 voxels, 0-915 chunks
% sub-03: 197155 voxels, 0-821 chunks
% sub-05: 188731 voxels, 0-786 chunks

% LOOPS ARE INCLUSIVE IN MATLAB!!! includes last number

for i = first_chunk:last_chunk
    extension = ['_space-T1w_desc-chunk' num2str(i,'%04d') '_bold.mat'];

    sub_wedges = load(strcat('sub-',sub_num,'_task-retinotopy_condition-wedges',extension), strcat('sub',sub_num,'_wedges'));
    sub_wedges = sub_wedges.(strcat('sub',sub_num,'_wedges'))

    sub_rings = load(strcat('sub-',sub_num,'_task-retinotopy_condition-rings',extension), strcat('sub',sub_num,'_rings'));
    sub_rings = sub_rings.(strcat('sub',sub_num,'_rings'))

    sub_bars = load(strcat('sub-',sub_num,'_task-retinotopy_condition-bars',extension), strcat('sub',sub_num,'_bars'));
    sub_bars = sub_bars.(strcat('sub',sub_num,'_bars'))

    data = {single(sub_wedges), single(sub_rings), single(sub_bars)};
    clear sub_wedges, clear sub_rings, clear sub_bars;

    results = analyzePRF(stimuli,data,1.49,struct('seedmode',[0 1 2],'display','off'));

    ang = results.ang
    ecc = results.ecc
    expt = results.expt
    rfsize = results.rfsize
    R2 = results.R2
    gain = results.gain

    out_path = strcat(data_dir,'/sub-',sub_num,'/prf/output/chunks')
    out_file = strcat(out_path,'/sub-',sub_num,'_task-retinotopy_space-T1w_model-analyzepRF_desc-chunk',num2str(i,'%04d'))
    save(strcat(out_file,'_statseries.mat'), 'results')
    save(strcat(out_file,'_ang.mat'), 'ang')
    save(strcat(out_file,'_ecc.mat'), 'ecc')
    save(strcat(out_file,'_expt.mat'), 'expt')
    save(strcat(out_file,'_rfsize.mat'), 'rfsize')
    save(strcat(out_file,'_R2.mat'), 'R2')
    save(strcat(out_file,'_gain.mat'), 'gain')

    clear sub*
    clear results, clear stimuli, clear data
    clear ang, clear ecc, clear expt, clear rfsize, clear R2, clear gain
end

% pipeline output described here:
% https://github.com/cvnlab/analyzePRF/blob/master/analyzePRF.m
