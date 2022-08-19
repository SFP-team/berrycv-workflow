# bcv-workflow
This repository contains a plantcv workflow tool for performing automatic image-based phenotyping on blueberry samples.

## Overview
The code takes images with QR code labels in the left third of the image and berry samples; segments the image to isolate the objects and labels them with sample metadata. These sample files are then used in constructing a job list for the various workflow analysis scripts used in data extraction.
Once these workflows are complete, the data is stored in a plantcv JSON output file and is converted to a set of .csv files.

## Using bcv-workflow

## Installation

To run from source, use `pip`, or another package manager to install the dependencies in `requirements.txt`.

`pip install -r requirements.txt`

## Flags

Example usage: `main.py -i `_/inputdirectory_ `-n` _resultname_ `-r` _/resultsdirectory_ `-a` object color
- -i, --indir : input directory for raw images, subfolders
- -n, --name : name of the output fileset without extension
- -r, --resultdir : output directory for result files
- -a, --analysis : list of analysis steps to run separated by space. Includes:
  - **shape** : height, object area, convex hull, convex hull area, perimeter, extent x, extent y, longest axis, centroid x coordinate, centroid y coordinate, in bounds QC
  - **color** : color data from RGB, LAB, and HSV color channels as histograms for each


- -vv, --verbose : toggles verbose output during workflow.