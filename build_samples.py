#!/usr/bin/env python3

## TJ Schultz
## 10/11/21

## Notebook for creating labeled fruit image data from raw blueberry photos
## -- 

import matplotlib.pyplot as pyplot
import glob
import os.path
import sys
from datetime import date
import re
import datetime
import math

from plantcv import plantcv as pcv
import berrycv as bcv  ## local library
import cv2
import numpy as np
from PIL import Image, ExifTags

## program options
pcv.params.debug = "none"
RAWIMGDIR = "input"
SAMPLE_SET_NAME = "30jun2021"

## get the working directory
wd = os.getcwd()

pcv.params.debug_outdir = wd + "/output"

## create subfolders for image data
bcv.create_sub('samples')
sample_parent_dir = "samples/" + SAMPLE_SET_NAME + "/"
bcv.create_sub(sample_parent_dir)

## assembles the sample filename with the metadata provided in the parameters
def assemble_filename_str(dt_original, qr_raw, sample_id, img_type, mean_area):
    
    ## format datetime string
    dt_original_format = str(dt_original.replace(":", "-"))
    
    ## format QR code data
    qr_format = str(qr_raw.replace(":", "+"))
    
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
        
        ## isolate the name to remove the full path
        name = filepath[len(wd)+1:]
        
        ## read the date and time of the photo from a dict of the exif data
        exif_img = Image.open(filepath)
        exif_tags = { ExifTags.TAGS[i]: j for i, j in exif_img._getexif().items() if i in ExifTags.TAGS }
        
        ## store original capture datetime
        dt_og = exif_tags['DateTimeOriginal']

        ## read the QR code information
        qr = bcv.readQR(raw_img)
        
        ## no qr detected, substitute for 'unknown:' with the capture datetime appended
        if qr == "":
            qr = "unknown:" + dt_og
        
        ## crop image to exclude the QR
        ##information
        ## cut into 2/3rds to create sample image
        sample_img = raw_img[:, math.floor(1*(raw_img.shape[1])/3):]
        
        
        
        ## create mask and apply it to the cropped image
        mask = generate_mask(sample_img)
        masked = pcv.apply_mask(img=sample_img, mask=mask, mask_color='white')
        
        ## identify objects
        id_objects,obj_hierarchy = pcv.find_objects(img=sample_img, mask=mask)

        print('Found %d objects in %s' % (len(id_objects), name))
        
        ## create empty list for marker id objects
        img_divisions = 10
        marker_id_objects = []
        while len(marker_id_objects) <= 0 or img_divisions < 7:

            ## create ROIs of the size markers
            marker1_contour, marker1_hierarchy = pcv.roi.rectangle(img=sample_img, x=0, y=0,\
                                                           h=math.floor(1*(sample_img.shape[0])/img_divisions), w=sample_img.shape[1])

            marker2_contour, marker2_hierarchy = pcv.roi.rectangle(img=sample_img, x=0, y=math.floor((img_divisions-1)*(sample_img.shape[0])/img_divisions),\
                                                           h=math.floor(1*(sample_img.shape[0])/img_divisions), w=sample_img.shape[1])

            ## identify markers
            marker1_objects, marker1_obj_hierarchy, marker1_kept_mask, _ = pcv.roi_objects(img=sample_img, roi_contour=marker1_contour, 
                                                                              roi_hierarchy=marker1_hierarchy,
                                                                              object_contour=id_objects,
                                                                              obj_hierarchy=obj_hierarchy, 
                                                                              roi_type='partial')

            marker2_objects, marker2_obj_hierarchy, marker2_kept_mask, _ = pcv.roi_objects(img=sample_img, roi_contour=marker2_contour, 
                                                                              roi_hierarchy=marker2_hierarchy,
                                                                              object_contour=id_objects,
                                                                              obj_hierarchy=obj_hierarchy, 
                                                                              roi_type='partial')

            ## create roi contour region of the sample data
            roi_contour, roi_hierarchy = pcv.roi.rectangle(img=sample_img, x=0, y=math.floor(1*(sample_img.shape[0])/img_divisions),\
                                                           h=math.floor((img_divisions-2)*(sample_img.shape[0])/img_divisions), w=sample_img.shape[1])


            ## find sample roi objects
            roi_objects, roi_obj_hierarchy, roi_kept_mask, obj_area = pcv.roi_objects(img=sample_img, roi_contour=roi_contour, 
                                                                              roi_hierarchy=roi_hierarchy,
                                                                              object_contour=id_objects,
                                                                              obj_hierarchy=obj_hierarchy, 
                                                                              roi_type='partial')

            ## combine marker masks and sample data masks to filter objects
            marker_mask = pcv.logical_or(marker1_kept_mask, marker2_kept_mask)

            ## find items present in both masks
            negative_mask = pcv.invert(pcv.logical_and(roi_kept_mask, marker_mask))

            ## remove shared items from marker and sample masks
            sample_mask = pcv.logical_and(negative_mask, roi_kept_mask)
            marker_mask = pcv.logical_and(negative_mask, marker_mask)

            ## filter objects into two id lists and hierarchies
            marker_id_objects,marker_obj_hierarchy = pcv.find_objects(img=sample_img, mask=marker_mask)


            ## create a new contour, hierarchy of the whole sample image for reporting size markers
            marker_img = pcv.apply_mask(img=sample_img, mask=marker_mask, mask_color='white')
            size_contour, size_hierarchy = pcv.roi.rectangle(img=marker_img, x=0, y=0,\
                                                           h=sample_img.shape[0], w=sample_img.shape[1])
            
            sample_id_objects,sample_obj_hierarchy = pcv.find_objects(img=sample_img, mask=sample_mask)
            try:
                marker_report = pcv.report_size_marker_area(img=marker_img, roi_contour=size_contour, roi_hierarchy=size_hierarchy, \
                                                            marker='detect', objcolor='dark', thresh_channel='v', thresh=120, label="default")
            except:
                img_divisions -= 1 ## reduce divisions -- try again
                continue
            pcv.outputs.add_observation(sample='default', variable='num_markers', trait='number of size markers which contribute to the reported area -- used in determining the mean area', \
                                        method='count of markers', scale='amount', datatype=int, \
                                        value=len(marker_id_objects), label='markers') 
        
        pcv.params.debug = 'none'
        
        ## calculate mean marker area and store for filename assembly
        mean_marker_area = math.floor(pcv.outputs.observations['default']['marker_area']['value'] /\
                                      pcv.outputs.observations['default']['num_markers']['value'])
        
        ## for each object -- o will be a unique id passed into sample_id for the filename metadata
        ## create subdirectories
        sample_dir = sample_parent_dir + str(qr.replace(":", "+") + "/")
        bcv.create_sub(sample_dir)
        for o in range(len(sample_id_objects)):
            
            
            ## crop the mask around the ROI of the current object
            crop_mask = pcv.auto_crop(img=mask, obj=sample_id_objects[o], padding_x=10, padding_y=10, color='image')
            
            ## crop the image around the ROI of the current object
            crop_img = pcv.auto_crop(img=masked, obj=sample_id_objects[o], padding_x=10, padding_y=10, color='image')
            
            ## apply mask to cropped image and write image with filename metadata
            
            final_img = pcv.apply_mask(img=crop_img, mask=crop_mask, mask_color='white')
            #blur_img = pcv.gaussian_blur(img=crop_img, ksize=(17, 17), sigma_x=0, sigma_y=None)
            
            ## create filename
            filename_str = assemble_filename_str(dt_og, qr, o, "VIS", mean_marker_area)
            
            ## save file
            cv2.imwrite(sample_dir + filename_str + '.jpg', final_img)

def main():

    ## get the directory of raw input files and find jpg images
    file_query = wd + "\\" + RAWIMGDIR + "\/**/*.jpg"
    files = glob.glob(file_query, recursive=True)

    files.sort()
    print('%d files found in %s\n' % (len(files), (wd + '\\' + RAWIMGDIR)))

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

if __name__ == "__main__":
    main()
        
