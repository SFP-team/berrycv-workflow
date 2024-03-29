#!/usr/bin/env python3

"""
Name: analysis_workflow.py
Description: dynamic workflow for inner/outer fruit feature extraction and ml models
Author: TJ Schultz
Date: 11/2/22
"""
import argparse
import sys
import os.path
from datetime import datetime as dt
import re
import time

from plantcv import plantcv as pcv
import berrycv as bcv
import cv2
import numpy as np

## program options
pcv.params.debug = "none"


## get the working directory
wd = os.getcwd()
    
## workflow options for plantcv workflow -- add arguments for plantcv-worfklow.py compatibility
def options():
    parser = argparse.ArgumentParser(description="Imaging processing with PlantCV.",\
                                     prog='python -m mymodule')
    parser.add_argument("-i", "--image", help="Input image file.", required=True)
    parser.add_argument("-r","--result", help="Result file.", required= True )
    parser.add_argument("-w","--writeimg", help="Write out images.", default=False, action="store_true")
    parser.add_argument("-D", "--debug", help="Turn on debug, prints intermediate images.")
    parser.add_argument("-a", "--analysis", \
                        help="List of analysis steps to run separated by space. Includes 'shape', 'color'->", \
                        nargs="*")
    args, _u = parser.parse_known_args()
    return args

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

## main
def main():
    
    #+ get options list
    args = options()

    ## set debug
    pcv.params.debug = args.debug

    ## read image using args flag
    filename = args.image
    sample_img = bcv.read_image(filename)
    
    ## fix the name to remove the full path for output
    name = filename[len(wd)+1:]

    ## if not bad image, sample_img and analyze
    if not len(sample_img) == 0:

        ## output filename
        print("\tFilename: %s" % name)

        ## create mask
        mask = generate_mask(sample_img)
        
        ## identify objects -- should be only one object
        ##id_objects,obj_hierarchy = pcv.find_objects(img=sample_img, mask=mask)

            
        ## set the key to the shortened filename
        key = name

        ## analysis steps

        ## split analysis arg into list
        steps = str(args.analysis[0]).split(' ')

        ## analyze object
        pcv.params.debug = 'none'
        if 'shape' in steps:
            ## identify objects -- should be only one object
            id_objects, obj_hierarchy = pcv.find_objects(img=sample_img, mask=mask)

            ## for each object -- though there should be one per sample photo
            for o in range(len(id_objects)):
                analyze_obj_img = pcv.analyze_object(img=sample_img, obj=id_objects[o], mask=mask, label=key)
        ## analyze color
        if 'color' in steps:
            analyze_col_img = pcv.analyze_color(rgb_img=sample_img, mask=mask, label=key)
        if 'bloom' in steps:
        ## blur img before using naive baysian classifier
            blur_img = pcv.gaussian_blur(img=sample_img, ksize=(17, 17), sigma_x=0, sigma_y=None)


            sc_masks = pcv.naive_bayes_classifier(rgb_img=blur_img,
                                                  pdf_file="models/SK-BL-SC_nbmc.txt")
            masks = pcv.naive_bayes_classifier(rgb_img=blur_img,
                                               pdf_file="models/BL-NBL_nbmc.txt")

            ## normalize masks and calculate the observation values

            sc_masks['scar'] = pcv.logical_and(sc_masks['scar'], mask)
            masks['bloom'] = pcv.logical_and(masks['bloom'], mask)
            masks['nobloom'] = pcv.logical_and(masks['nobloom'], mask)

            masks['bloom'] = pcv.logical_and(masks['bloom'], pcv.invert(sc_masks['scar']))
            masks['nobloom'] = pcv.logical_and(masks['nobloom'], pcv.invert(sc_masks['scar']))

            nb_mc_img = pcv.visualize.colorize_masks([masks['bloom'], masks['nobloom']], \
                                                     colors=['pink', 'blue'])

            nobloom_area = np.count_nonzero(masks['nobloom'])
            bloom_area = np.count_nonzero(masks['bloom'])
            scar_area = np.count_nonzero(sc_masks['scar'])
            bloom_fac = bloom_area / (bloom_area + nobloom_area - scar_area)

            ## add observations

            pcv.outputs.add_observation(sample=key, variable='nobloom_area',
                                        trait='area of nobloom pixels',
                                        method='pixels', scale='pixels', datatype=int,
                                        value=nobloom_area, label=key)

            pcv.outputs.add_observation(sample=key, variable='bloom_area',
                                        trait='area of bloom pixels',
                                        method='pixels', scale='pixels', datatype=int,
                                        value=bloom_area, label=key)

            pcv.outputs.add_observation(sample=key, variable='scar_area',
                                        trait='area of scar pixels',
                                        method='pixels', scale='pixels', datatype=int,
                                        value=scar_area, label=key)

            pcv.outputs.add_observation(sample=key, variable='bloom_factor',
                                        trait='ratio of bloom pixels to all skin pixels',
                                        method='ratio of pixels', scale='percent', datatype=float,
                                        value=bloom_fac, label=key)

            pcv.params.debug = 'none'
        if 'disease' in steps:
            img_hsv = cv2.cvtColor(sample_img, cv2.COLOR_BGR2HSV)
            msk_hue = np.logical_and((img_hsv[:, :, 0] > 0), (img_hsv[:, :, 0] < 25))
            msk_sat = np.logical_and((img_hsv[:, :, 1] > 30), (img_hsv[:, :, 1] < 255))
            total_disease = np.logical_and(msk_hue, msk_sat)
            msk_hue = ~np.logical_and((img_hsv[:, :, 0] > 0), (img_hsv[:, :, 0] < 25))
            msk_sat = np.logical_and((img_hsv[:, :, 1] > 30), (img_hsv[:, :, 1] < 255))
            total_ok = np.logical_and(msk_hue, msk_sat)
            ##body_img = cv2.cvtColor(sample_img, cv2.COLOR_BGR2RGB)
            body_img = sample_img
            disease = body_img.copy()
            healthy = body_img.copy()
            # write original image, disease and healthy parts
            disease[~total_disease] = 255
            cv2.imwrite(os.path.dirname(filename) + '/disease.jpg', disease)
            healthy[~total_ok] = 255
            cv2.imwrite(os.path.dirname(filename) + '/healthy.jpg', healthy)

            disease_fac = np.sum(total_disease) / (np.sum(total_disease) + np.sum(total_ok))
            pcv.outputs.add_observation(sample=key, variable='disease_factor',
                                        trait='ratio of disease pixels to all leaf pixels',
                                        method='ratio of pixels', scale='percent', datatype=float,
                                        value=disease_fac, label=key)
            
        pcv.outputs.save_results(filename=args.result, outformat="json")

if __name__ == '__main__':
    main()


        
        
