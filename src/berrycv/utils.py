#!/usr/bin/env python3
"""
utils.py -- utiities for directory management and file IO
"""
import os.path
import json
import glob
import cv2
import plantcv as pcv
import matplotlib.pyplot as pyplot


## creates subdirectory by name
def create_sub(sub):
    try:
        os.mkdir(sub)
    except Exception:
        if os.path.isdir(sub):
            pass
        else:
            print('Unable to create new directory \'%s\':\n' % sub)
            pass

## reads in an image and makes the color channel adjustments from BGR to RGB
def read_image(name, flip_red_blue=False):
    try:
        img = cv2.imread(name)
        if flip_red_blue:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) ## step necessary to flip channels upon read
        return img
    except Exception:
        print('Unable to open \'%s\':\n' % name)
        return []

## returns a binary mask of the image for use in object detection
def generate_thresh_mask(img):
    
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



## image show func for pyplot output
def show_image(i):
    pyplot.imshow(i)
    pyplot.show()

## reads the config.json file and returns a list of it's items
def readJSONconfig(config_dir):
    ## data list
    data = []

    ## read file
    with open(config_dir) as infile:
        data = json.load(infile)
        
    return data
    """
    try:
        ## data list
        data = []

        ## read file
        with open(config_dir) as infile:
            data = json.load(file)
            
        return data
    except:
        print("Could not open config.json")
        return []"""

