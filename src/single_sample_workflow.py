#!/usr/bin/env python3

"""
Name: single_sample_workflow.py
Description: sample creation workflow with a single object mask
Author: TJ Schultz
Date: 6/7/2023
"""

import matplotlib.pyplot as pyplot
import glob
import os.path
import sys
import argparse
from datetime import date
import re
import datetime
import math

from plantcv import plantcv as pcv
import berrycv as bcv  ## local library
import cv2
import numpy as np
from PIL import Image, ExifTags

## workflow options for plantcv workflow -- add arguments for plantcv-workflow.py compatibility
def options():
    parser = argparse.ArgumentParser(description="Imaging processing with PlantCV.",\
                                     prog='python -m mymodule')
    parser.add_argument("-i", "--image", help="Input image file.", required=True)
    parser.add_argument("-r","--result", help="Result file.", required= False )
    parser.add_argument("-o", "--outdir", help="Output directory for image files.", required=False)
    parser.add_argument("-w","--writeimg", help="Write out images.", default=False, action="store_true")
    parser.add_argument("-D", "--debug", help="Turn on debug, prints intermediate images.")
    args, _u = parser.parse_known_args()
    return args

##

## get the working directory
wd = os.getcwd()

## get args as namespaces dictionary
args = vars(options())
## create SAMPLE_SUBSET_NAME
SAMPLE_SUBSET_NAME = os.path.dirname(args['image'])
## create subfolders for image data
sample_parent_dir = os.path.join(str(args['outdir']))
error_parent_dir = sample_parent_dir.replace('samples', 'error')

bcv.create_sub(sample_parent_dir)

## assembles the sample filename with the metadata provided in the parameters
def assemble_filename_str(dt_original, qr_raw, sample_id, img_type, mean_area):

    ## format datetime string
    dt_original_format = str(dt_original.replace(":", "-"))

    ## format QR code data
    qr_format = str(qr_raw.replace(":", "+"))
    qr_format = str(qr_format.replace("|", "+"))

    ## format id
    sample_id_format = str(sample_id)

    ## format img_type
    img_type_format = str(img_type)

    ## format mean area
    mean_area_format = str(mean_area)

    ## return filename string
    return ("%s_%s_%s_%s_%s" % (dt_original_format, qr_format, sample_id_format, img_type_format, mean_area_format))

## returns a binary mask of the image for use in object detection
def generate_mask(img):

    ## first isolate the saturation channel, threshold it
    s = pcv.rgb2gray_hsv(rgb_img=img, channel='s')
    s_th = pcv.threshold.triangle(gray_img=s, max_value=255, object_type='light', xstep=20)


    ## then isolate the lightness channel, threshold it
    l = pcv.rgb2gray_lab(rgb_img=img, channel='l')
    l_th = pcv.threshold.triangle(gray_img=l, max_value=255, object_type='dark')

    ## blur the saturation and lightness image to soften small features
    s_th_blur = pcv.median_blur(gray_img=s_th, ksize=5)
    l_th_blur = pcv.median_blur(gray_img=l_th, ksize=5)

    ## 'logical or' the images to create a joined binary image
    ls = pcv.logical_or(s_th_blur, l_th_blur)

    ## pass a filled image back after logical-or joining the inverted fill
    ls_fill = pcv.fill(bin_img=ls, size=1000)

    ls_fill_inv = pcv.fill(bin_img=pcv.invert(ls_fill), size=1000)

    ls_or_final = pcv.logical_or(pcv.invert(ls_fill_inv), ls_fill)
    return ls_or_final


## sample isolation and labeling workflow -- creates labeled images for workflow parallelization. filename provided for redundancy
def build_samples(raw_img, filepath):

        ## get the working directory
        wd = os.getcwd()

        try:
            ## read the date and time of the photo from a dict of the exif data
            exif_img = Image.open(filepath)
            exif_tags = { ExifTags.TAGS[i]: j for i, j in exif_img._getexif().items() if i in ExifTags.TAGS }

            ## store original capture datetime
            dt_og = exif_tags['DateTimeOriginal']
        except:
            dt_og = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S').replace('\..*','')

        ## crop image to exclude the QR
        ## information
        ## cut qr portion off
        #sample_img = raw_img[math.floor(raw_img.shape[0] / 6):23*math.floor(raw_img.shape[0] / 24), :]
        sample_img = raw_img
        qr_imgw = raw_img[:math.floor(raw_img.shape[0] / 6), :]
        qr_img = cv2.cvtColor(qr_imgw, cv2.COLOR_BGR2GRAY)
        qr = None
        for i in range(130):

            ret, qr_imgt = cv2.threshold(qr_img,100 + i,255,cv2.THRESH_TOZERO)
            ## read the QR code information
            qr = bcv.getQRStruct(qr_imgt)

            if (qr is not None):
                break

        ## no qr detected, substitute for name
        if not qr:
            ## isolate the name in filename to remove the full path and extension
            ## correct for underscores in filenames for the plantbarcodes with dashes ('_' is the chosen delimeter for metadata)
            name = os.path.basename(filepath).split('.')[0].replace('_', '-')
            qr = name
        else:
            qr = bcv.readQR(qr_imgt)
            print("QR: " + qr)

        qr = qr.replace(",", "+")


        ## create mask and apply it to the cropped image
        mask = generate_mask(sample_img)
        masked = pcv.apply_mask(img=sample_img, mask=mask, mask_color='white')

        ## identify objects
        id_objects,obj_hierarchy = pcv.find_objects(img=sample_img, mask=mask)
        print('\t')
        print('Found %d objects in %s' % (len(id_objects), filepath))

        pcv.params.debug = 'none'

        ## for each object -- o will be a unique id passed into sample_id for the filename metadata
        ## create subdirectories
        s_d = str(qr.replace(":", "+"))
        s_d = str(s_d.replace("|", "+") + "/")
        sample_dir = os.path.join(sample_parent_dir, s_d)
        print("sample_dir: " + sample_dir)

        bcv.create_sub(sample_dir)

        ## apply mask to cropped image and write image with filename metadata

        final_img = masked
        o = 0 ## single object id, no marker area used
        mean_marker_area = 0
        ## create filename
        filename_str = assemble_filename_str(dt_og, qr.replace(",", ":"), o, "VIS", mean_marker_area)

        ## save file
        cv2.imwrite(sample_dir + filename_str + '.jpg', final_img)
        cv2.imwrite(sample_dir + filename_str + '_tag.jpg', qr_imgw)


def main():

    pcv.params.debug = "none"
    raw_img = bcv.read_image(args['image'])

    ## if not bad image, analyze
    if not raw_img is None:
        ## build samples
        build_samples(raw_img, args['image'])
        pcv.params.debug = 'none'
        pcv.outputs.clear()



if __name__ == "__main__":
    main()

