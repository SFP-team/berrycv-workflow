# bcv-workflow
This repository contains a plantcv workflow tool for performing automatic image-based phenotyping on blueberry samples.

## Overview
The code takes images with QR code labels and berry samples and segments the image to isolate the objects and labels them with sample metadata. These sample files are then used in constructing a job list for the various workflow analysis scripts used in data extraction.
Once these workflows are complete, the data is stored in a plantcv JSON output file and is converted to a set of .csv files.

## Using bcv-workflow

## Installation

Tested on linux and windows with python 3.10

Firstly, install Anaconda (https://www.anaconda.com/download/) and create a virtual environment.

Once pulled, to run from source, use `pip` to install the python dependencies in `requirements.txt`.

- `pip install -r requirements.txt`

to test:
on Linux:   ./main.py -i ../examples -n tess -r test -a color
* if command invalid, try to allow access by using chmod 
on Windows: python main.py -i ../examples -n tess -r test -a color

## Flags

Example usage: `main.py -i `_/inputdirectory_ `-n` _resultname_ `-r` _/resultsdirectory_ `-a` _color_ _[...]_
- -i, --indir : input directory for raw images, subfolders
- -n, --name : name of the output fileset without extension
- -r, --resultdir : output directory for result files
- -a, --analysis : list of analysis steps to run separated by space. Includes:
  - **shape** : height, object area, convex hull, convex hull area, perimeter, extent x, extent y, longest axis, centroid x coordinate, centroid y coordinate, in bounds QC
  - **color** : color data from RGB, LAB, and HSV color channels as histograms for each
  - **bloom** : utilizes color models created to mask 'bloom' and 'no-bloom' elements in the berry sample photos and creates additional columns of single-valued data for these feature areas
  - **disease** : produces a disease factor column as a proportion of the pixels below a hue threshold for disease out of the total pixels
- -P : using the photo booth for input photos, no flag uses sample_leaf_workflow.py
- -S : using the scanner for input photos, produces a single sample image as a mask of the whole input image (not separate samples), no flag uses sample_leaf_workflow.py
