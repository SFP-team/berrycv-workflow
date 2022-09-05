import os.path

import pandas as pd
import argparse
import glob

# for generating image tables of the color means by plantbarcode
from PIL import Image, ImageDraw
IMAGE = 0

def options():
    parser = argparse.ArgumentParser(description="Image processing workflow with PlantCV.",\
                                     prog='python -m mymodule')
    parser.add_argument("-n", "--name", help="Name from main args", required=True)
    parser.add_argument("-i", "--indir", help="Input image folder directory", required=True)
    parser.add_argument("-r", "--resultdir", help="Output directory for results files.", required=True)

    ## read command flags
    args, _u = parser.parse_known_args()
    return args


args = options()
path = os.path.join(os.getcwd(), str(args.indir))
cspace_domains = ['blue_frequencies', 'green_frequencies', 'red_frequencies',\
                  'lightness_frequencies', 'green-magenta_frequencies', 'blue-yellow_frequencies',\
                  'hue_frequencies', 'saturation_frequencies', 'value_frequencies']

# fix in dir


# load dataframes
masterdf = pd.DataFrame()
for f in glob.glob(path + '/**/*.csv', recursive=True):
    # only color data

    if 'multi' not in f:
        continue
    df = pd.read_csv(f)

    # append the dataframe to the master dataframe
    if masterdf.size < 1:
        masterdf = df
    else:
        masterdf = masterdf.append(df)

# now for each independent plantbarcode, and sampleid
# store the means in a new dataframe
means = pd.DataFrame(columns=(['plantbarcode', 'id'] + cspace_domains))
try:
    pbcs = masterdf['plantbarcode'].unique()
except:
    pbcs = pd.DataFrame()
# get unique plantbarcodes
for p in pbcs:
    # get unique ids
    ids = masterdf[masterdf['plantbarcode'] == p]['id'].unique()

    for i in ids:
        # return the subset of the dataframe containing the relevant color data
        sample = masterdf[masterdf['plantbarcode'] == p]
        sample = sample[sample['id'] == i]

        # calculate the prob means for the sample in every colorspace
        row = {}
        for dim in cspace_domains:
            sum = 0
            trait = sample[sample['trait'] == dim]
            for label in trait['label'].unique():
                sum += (float(trait[trait['label'] == label]['value'].mean()) / 100.00) * label
            row[dim] = sum

        # add information to row before appending to the result dataframe
        row['plantbarcode'] = p
        row['id'] = i
        means = means.append(pd.DataFrame([row]))

## get str of args name
name = str(args.name)
means.to_csv(os.path.join(str(args.resultdir), name + '_mv_means.csv'), index=False)

# calculate population means -- drop id values
means.drop('id', axis=1)
pop_means = means.groupby('plantbarcode', as_index=False)[cspace_domains].mean()
pop_means.to_csv(os.path.join(str(args.resultdir), name + '_mv_pop_means.csv'), index=False)

agg = pd.DataFrame(columns=(['plantbarcode'] + cspace_domains))

for p in pbcs:
    sample = means[means['plantbarcode'] == p]
    row = {}
    for dim in cspace_domains:
        sum = 0
        for val in sample[dim]:
            sum += val
        row[dim] = sum / sample[dim].size
    row['plantbarcode'] = p
    agg = agg.append(pd.DataFrame([row]))
agg.to_csv('mv_means.csv', index=False)

img = None

for p in pbcs:
    r = int(agg[agg['plantbarcode']==p]['red_frequencies'])
    g = int(agg[agg['plantbarcode']==p]['green_frequencies'])
    b = int(agg[agg['plantbarcode']==p]['blue_frequencies'])
    i = Image.new('RGB', (60, 30), color = (r, g, b))
    if img is None:
        img = i
    else:
        dst = Image.new('RGB', (img.width, img.height + i.height))
        dst.paste(img, (0, 0))
        dst.paste(i, (0, img.height))
        img = dst
if IMAGE:
    img.save('img.jpg')