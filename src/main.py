#!/usr/bin/env python3

"""
Name: main.py
Description: main script for executing all stages of sample segmentation, feature extraction,
and file conversion for workflows from parsed args
Author: TJ Schultz
Date: 8/10/2022
-- various seemingly unused dependencies are imported in this script
    to successfully build the application using pyinstaller
"""

import argparse
import json
import sys
import os
import subprocess
import cv2
import numpy as np
import berrycv as bcv
from plantcv import plantcv as pcv
from sample_workflow import *
from analysis_workflow import *
from mv_means import *
## warning control
python_hand = 'python'
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

## fix multiple options issue with argparser
to_exclude = ['options']
for _m in to_exclude:
    del globals()[_m]

print(os.getcwd())
## define command flags for launching the workflows
def options():
    parser = argparse.ArgumentParser(description="Image processing workflow with PlantCV.")
    parser.add_argument("-a", "--analysis",
                        help="List of analysis steps to run separated by space. Includes 'shape', 'color'->", \
                        nargs="*", required=True)
    parser.add_argument("-i", "--indir", help="Input image folder directory", required=True)
    parser.add_argument("-n","--name", help="Name of the result files without extension.", required=True)
    parser.add_argument("-r", "--resultdir", help="Output directory for results files.", required=True)
    parser.add_argument("-P", "--photobooth", help="Indicate photobooth use (building samples)", action="store_true")
    parser.add_argument("-vv", "--verbose", help="Toggles verbose output during workflow. Used in debugging.", required=False)
    ## read command flags
    args = parser.parse_args()
    print(args)
    return args

## resource path function for use in packaging the executable
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

## obtain args
args = options()

## read configuration files necessary for running all stages of the workflow
## read launch configuration -- config.json
f_missing_message = 'is missing or in an incorrect format. Exiting.'

## define relative paths
sample_config_path = resource_path('./config/sample-workflow_config.json')
analyze_config_path = resource_path('./config/analyze-workflow_config.json')

bcv.create_sub('config')

## read sample extraction workflow configuration -- sample-workflow_config.json
try:
    sample_config = []
    with open(sample_config_path, 'r+') as _f:
        sample_config = json.load(_f)
        sample_config['input_dir'] = str(args.indir)
        sample_config['img_outdir'] = os.path.join(str(args.resultdir), 'samples')
        if args.photobooth:
            sample_config['workflow'] = "sample_workflow.py"
        else:
            sample_config['workflow'] = "sample_leaf_workflow.py"
        _f.seek(0)        ## seek f
        json.dump(sample_config, _f, indent=4)
        _f.truncate()     ## remove end
except:
    print('config/sample-workflow_config.json', f_missing_message)
    sys.exit(1)



## read feature extraction workflow configuration -- analyze-workflow_config.json
try:
    analyze_config = []
    with open(analyze_config_path, 'r+') as _f:
        analyze_config = json.load(_f)
        bcv.create_sub(str(args.resultdir))
        analyze_config['input_dir'] = os.path.join(sample_config['img_outdir'])
        analyze_config['json'] = os.path.join(str(args.resultdir), str(args.name) + "_output.json")

        ## fix img_outdir
        analyze_config['img_outdir'] = str(args.resultdir)

        ## add analysis args
        analyze_config['other_args'] = ['--analysis', ' '.join(args.analysis)]

        _f.seek(0)  ## seek f
        json.dump(analyze_config, _f, indent=4)
        _f.truncate()  ## remove end

except:
    print('config/analyze-workflow_config.json', f_missing_message)
    sys.exit(1)



## apply to main configuration -- config.json
print('Sampling configuration:', sample_config)
print('Analysis configuration:', analyze_config)

## get the working directory
wd_dir = os.getcwd()

## get scripts directory
## -- take the directory or the path of the sys.executable object (different platforms)
s_dir = ''
if os.path.isdir(sys.executable):
    s_dir = os.path.join(sys.executable, 'Scripts')
else:
    s_dir = os.path.join(os.path.dirname(sys.executable), 'Scripts')



## main

## before calling subprocesses, check input_dir for sampling
if not os.path.exists(args.indir):
    print("Input directory non-existent. Check flags.")
    sys.exit(-1)

## call run sample_workflow -- create samples for extraction
print('(1/3)\tSAMPLING')

bcv.create_sub(os.path.join(str(args.resultdir), 'samples'))
subprocess.call([python_hand, os.path.join(s_dir, 'plantcv-workflow.py'), '--config',\
                 'config/sample-workflow_config.json'], shell=False)

print('(2/3)\tANALYSIS')
## call plantcv_workflow.py
subprocess.call([python_hand, os.path.join(s_dir, 'plantcv-workflow.py'), '--config',\
                 'config/analyze-workflow_config.json'], shell=False)

## get output json name
results_json = os.path.join(str(args.resultdir), str(args.name) + "_output.json")

print('(3/3)\tDOWNSTREAM DATA COMPILATION')
## call plantcv_utils.py : json2csv
sample_set_name = str(args.name)
subprocess.call([python_hand, os.path.join(s_dir, 'plantcv-utils.py'), 'json2csv', '-j', results_json,\
                 '-c', os.path.join(args.resultdir, sample_set_name)], shell=False)

subprocess.call([python_hand, 'mv_means.py', '-n', str(args.name), '-i', str(args.resultdir),\
                 '-r', str(args.resultdir)], shell=False)