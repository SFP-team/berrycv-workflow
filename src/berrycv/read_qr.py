#!/usr/bin/env python3
"""
Name: read_qr.py
Description: utiities for reading QR data in sample images
Author: TJ Schultz
Date: 10/19/2021
"""

import pyzbar.pyzbar
from pyzbar.pyzbar import decode as decodeQR
import numpy
import re
import warnings

## reads a qr code in the image, returns a string of the data
def readQR(img):
    
    try:
        
        ## decode the data using pyzbar decode
        qr_data = decodeQR(img)[0][0]

        ## truncate the non-data
        if (len(qr_data) > 3):
            qr_data = qr_data[:-2].decode()

        ## print the data if found, return without beginning and end
        if qr_data is not None and len(qr_data) != 0:
            print("QR code read as: \"%s\"\n" % qr_data)
            return qr_data

    except:
        ## return a null label
        print("No QR code detected.\n")
        return ""

## returns the full structure given by pyzbar
def getQRStruct(img):
    try:
        ## decode the data using pyzbar decode
        qr_data = decodeQR(img)

        ## print the data if found, return without beginning and end
        if qr_data is not None and len(qr_data) != 0:
            ## print("QR code read as: \"%s\"\n" % qr_data[0][0])
            return qr_data

    except:
        ## return a null label
        print("No QR code detected.\n")
        return ""

## returns a dictionary containing the unpacked QR code from post-harvest photos in key-value pairs
def unpackQR(qr_raw, keys, delim):
    keys = ["Selection ID", "Row", "Pos", "Rep", "Time", "Order"]
    qr_dict = {}
    if qr_raw.__contains__("unknown"):
        ## qr dictionary of unknown qr label
        qr_dict = {
            "Selection ID": "unknown",
            "Row": "0",
            "Pos": "0",
            "Rep": "0",
            "Time": "0",
            "Order": "0"
        }
    else:
        warnings.filterwarnings("ignore")

        ## reset the delimeter in the string to be the 
        qr_text = qr_raw.replace(delim, ":")

        ## qr dictionary
        qr_dict = {
            "Selection ID": "",
            "Row": "",
            "Pos": "",
            "Rep": "",
            "Time": "",
            "Order": ""
        }
        
        ## unpack qr code
        ## _s       -- string variable to walk along the text with a key length
        ## s_data   -- the data read in before the proceeding key is found
        ## _index   -- index of value in q
        
        _s = ""
        s_data = ""
        _index = 0

        ## split the text by delimeter to obtain mismatched keys and values
        q = qr_text.split(":")
        
        ## loop through strings to extract the data for each key
        ## for each key in the passed ordered key array
        for _s in q:

            ## get index in split string
            _index = q.index(_s)

            ## first key, no data
            if _index == 0:
                continue
            
            ## last value
            if _index == len(q) - 1:

                ## set the last value of the qr dictionary
                qr_dict[keys[len(keys) - 1]] = q[_index]
                
            ## middle value
            else:
                ## define k fron _index
                k = keys[_index]
                
                
                ## set data for qr_dict
                s_data = q[_index]
                ## remove the key in the current member of q
                s_data = s_data.replace(k, "")

                ## key removed, pass read data into last value, reset s_data
                qr_dict[keys[_index - 1]] = s_data
                s_data = ""          
    
    return qr_dict
    
