
% add path to GLMsingle matlab code directory
addpath(genpath([code_dir '/GLMsingle/matlab']));

% add path to .h5 data files (vectorized bold data and design matrices)
addpath(genpath([data_dir '/sub-' sub_num '/GLMsingle/input']));

% Parameters specified when calling script (as reference)
%sub_num = '03';
%bold_type = 'MNI';
%bold_type = 'T1w';
%chunk_size = '35000';

% stimulus duration (2 TRs, 1.49s/TR)
stimdur = 2.98;

% load data from subject bold and design .h5 files
% Doc on reading HDF5 in matlab https://www.mathworks.com/help/matlab/ref/h5read.html#mw_5606c3c2-015b-4c12-8653-4c7f53ab2dc1
tr = h5read(['sub-' sub_num '_task-things_sparsedesign.h5'], '/TR');
% Number of TRs per run, and total number of unique image stimuli,
% to generate sparse design matrix from trial onset coordinates.
tr_count = h5read(['sub-' sub_num '_task-things_sparsedesign.h5'], '/TR_count');
total_conditions = h5read(['sub-' sub_num '_task-things_sparsedesign.h5'], '/total_conditions');

% List of valid sessions for that subject
sessions = h5read('task-things_desc-runlist.h5', ['/' sub_num '/sessions']);

% Create list of design and BOLD data matrices
count = 1;
data = {};
design = {};
session_indx = [];

% Generate cross-validation scheme
xvalscheme = {[] [] [] [] [] [] [] [] [] [] [] [] []};

for i = 1:length(sessions)
  ses = int2str(sessions(i));
  runs = h5read('task-things_desc-runlist.h5', ['/' sub_num '/' ses]);
  ses = num2str(sessions(i), '%02d');

  for j = 1:length(runs)
    run_num = int2str(runs(j));
    run_data = transpose(h5read(['sub-' sub_num '_task-things_space-' bold_type '_maskedBOLD.h5'], ['/' ses '/' run_num '/bold']));
    data{count} = run_data;

    run_num = num2str(runs(j), '%02d');
    run_design_coord = h5read(['sub-' sub_num '_task-things_sparsedesign.h5'], ['/' ses '/' run_num '/design_coord']);
    rows = run_design_coord(1, :) + 1;
    cols = run_design_coord(2, :) + 1;
    vals = repelem([1], length(rows));
    design_sparse = sparse(rows, cols, vals, tr_count, total_conditions);
    design{count} = design_sparse;

    session_indx = [session_indx i];
    xvalscheme{mod(count-1, length(xvalscheme)) + 1} = [xvalscheme{mod(count-1, length(xvalscheme)) + 1} count];
    count = count + 1;
  end
end

% Specify GLMsingle options in param dictionary opt
% running matlab on compute canada: https://docs.alliancecan.ca/wiki/MATLAB
%     A = simple ONOFF model
%     B = single-trial estimates using a tailored HRF for every voxel
%     C = like B but with GLMdenoise regressors added into the model
%     D = like C but with ridge regression regularization (tailored to each voxel)
% to save models A (ONOFFl), B (FITHRF), C (FITHRF_GLMDENOISE) and D (FITHRF_GLMDENOISE_RR) in memory (heavy on RAM)
%opt = struct('wantmemoryoutputs',[1 1 1 1]);
% to save only model D (GLMdenoise + fracridge) in memory
%opt = struct('wantmemoryoutputs',[0 0 0 1]);
% to save results without keeping models in memory, to save on RAM
%opt = struct('wantmemoryoutputs',[0 0 0 0]);

% To add session indicator to options, as recommended here:
% https://glmsingle.readthedocs.io/en/latest/wiki.html#what-s-the-deal-with-sessionindicator
% https://www.mathworks.com/help/matlab/ref/struct.html
opt = struct('wantmemoryoutputs',[0 0 0 0], 'sessionindicator', session_indx, 'chunknum', str2double(chunk_size), 'xvalscheme', {xvalscheme});

% Specify output directory
% outputdir = [data_dir '/sub-' sub_num '/GLMsingle/output/'];
outputdir = ['/home/mstlaure/scratch/GLMs/results/sub-' sub_num '/GLMsingle/output/'];

% Run GLMsingle
[results] = GLMestimatesingletrial(design,data,stimdur,tr,[outputdir bold_type],opt);
