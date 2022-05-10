#!/usr/bin/env python3

"""
Name: main.py
Description: main script for executing all stages of sample segmentation, feature extraction,
and file conversion for workflows
Author: TJ Schultz
Date: 5/9/2022
"""

import argparse
import json
import sys
import os
import subprocess
import berrycv as bcv
from datetime import datetime as dt
import re
import time

## define command flags
def options():
    parser = argparse.ArgumentParser(description="Imaging processing workflow with PlantCV.")
    parser.add_argument("-i", "--indir", help="Input image folder directory", required=False)
    parser.add_argument("-n","--name", help="Name of the result file without extension.", required=False)
    parser.add_argument("-s", "--sampledir", help="Output directory for sample images.", required=False)
    parser.add_argument("-r", "--resultdir", help="Output directory for results files.", required=False)
    parser.add_argument("-D", "--debug", help="Turn on debug. Toggles verbose output during workflow.", required=False)

    ## read command flags
    args = parser.parse_args()
    return args

args = options()

## read configuration files necessary for running all stages of the workflow
## read main configuration -- config.json
f_missing_message = 'is missing or in an incorrect format. Exiting.'
try:
    config = []
    with open('config/config.json') as _f:
        config = json.load(_f).items()
except:
    print('config/config.json', f_missing_message)
    sys.exit(1)

## read sample extraction workflow configuration -- sample-workflow_config.json
try:
    sample_config = []
    with open('config/sample-workflow_config.json', 'r+') as _f:
        sample_config = json.load(_f)


except:
    print('config/sample-workflow_config.json', f_missing_message)
    sys.exit(1)



## read feature extraction workflow configuration -- analyze-workflow_config.json
try:
    analyze_config = []
    with open('config/analyze-workflow_config.json') as _f:
        analyze_config = json.load(_f)
except:
    print('config/analyze-workflow_config.json', f_missing_message)
    sys.exit(1)

## get args using options()

print(args)

## apply to main configuration -- config.json
print(config)
print(sample_config)
print(analyze_config)

## get the working directory
wd_dir = os.getcwd()

## get scripts directory
## -- take the directory or the path of the sys.executable object (different platforms)
s_dir = ''
if os.path.isdir(sys.executable):
    s_dir = os.path.join(sys.executable, 'Scripts')
else:
    s_dir = os.path.join(os.path.dirname(sys.executable), 'Scripts')

s_dir = os.path.dirname(sys.executable)

## display job information
"""
## get the directory of raw input files and find jpg images
file_query = wd_dir + "\\" + RAWIMGDIR + "\/**/*.jpg"
in_files = glob.glob(file_query, recursive=True)
print('%d files found in %s\n' % (len(in_files), (wd_dir + '\\' + RAWIMGDIR)))

    ## go through each file and search for objects
    name_num = 0
    for name in files:
        name_num += 1  ## increment the name count

        pcv.params.debug = "none"
        raw_img = bcv.read_image(name)

        ## if not bad image, analyze
        if not raw_img is None:
            ## print which file is being processed
            print("File#: %d\tFilename: %s" % (name_num, name))

            ## build samples

            build_samples(raw_img, name)
            pcv.params.debug = 'none'
        pcv.outputs.clear()
        """

## main

## create dir paths
bcv.create_sub('plots')

## call run sample_workflow -- create samples for extraction
bcv.create_sub('samples')
subprocess.call(['python', os.path.join(s_dir, 'plantcv-workflow.py'), '--config',
                 'config/sample-workflow_config.json'], shell=False)

## call plantcv_workflow.py
subprocess.call(['python', os.path.join(s_dir, 'plantcv-workflow.py'), '--config',
                 'config/analyze-workflow_config.json'], shell=False)

## get output json name
results_json = analyze_config['json']

## call plantcv_utils.py : json2csv
sample_set_name = args.name
subprocess.call(['python', os.path.join(s_dir, 'plantcv-utils.py'), 'json2csv', '-j', results_json,
                 '-c', sample_set_name], shell=False)