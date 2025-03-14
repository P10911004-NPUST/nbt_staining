import os
import re
import cv2
import numpy as np
import pandas as pd
import skimage.filters as skf_filters
from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen
from matplotlib import pyplot as plt

from filters import *

font_url = "https://github.com/mylab-root/mylab-root.github.io/blob/main/assets/webfonts/HarmonyOS_Sans_Medium.ttf?raw=true"

img = cv2.imread("./test/gus_img/GUS_R02_pCr02_20241017_RAW_ch00.tif", cv2.IMREAD_COLOR)[:, :, ::-1]

height, width, depth = img.shape

R, G, B = cv2.split(img)
R = cv2.bitwise_not(R) * 1.0
G = cv2.bitwise_not(G) * 1.0
B = cv2.bitwise_not(B) * 1.0

root_pixels = ((R + G + B) > 150) * 1.0

ExR = (R + R + R + R + R) - G - G - G
ExR = np.reshape(ExR, -1)
ExR = (ExR - np.min(ExR)) / (np.max(ExR) - np.min(ExR))
ExR = np.reshape(ExR, (height, width))
ExR = ExR * root_pixels
#ExR = np.uint8(ExR)

plt.subplot(221), plt.imshow(R, cmap="gray"), plt.title("R"), plt.axis("off")
plt.subplot(222), plt.imshow(G, cmap="gray"), plt.title("G"), plt.axis("off")
plt.subplot(223), plt.imshow(B, cmap="gray"), plt.title("B"), plt.axis("off")
plt.subplot(224), plt.imshow(ExR, cmap="gray"), plt.title("ExR"), plt.axis("off")
plt.show()
# font = {"family": "sans", "weight": "bold", "size": 5}
# matplotlib.rc("font", **font)
# matplotlib.rc("image", cmap="gray")
# matplotlib.use("agg")


#def nbt_intensity(img):
#    img_name = "NA"
#    nbt_area = None
#    total_nbt_intensity = None
#    nbt_intensity_per_area = None
#    raw_img, roi, contours = None, None, None

#    try:
#        # if the input is the img directory
#        if isinstance(img, str):
#            raw_img = cv2.imread(img, cv2.IMREAD_COLOR)[:, :, ::-1]
#            img_name = os.path.basename(img)
#            img_dir = os.path.dirname(img)

#            output_img_name = "OUT_" + img_name
#            output_img_dir = os.path.join(
#                os.path.dirname(img_dir), "OUT_" + os.path.basename(img_dir)
#            )

#            if not os.path.exists(output_img_dir):
#                os.mkdir(output_img_dir)

#        # if the input is a numpy array
#        elif isinstance(img, np.ndarray):
#            raw_img = img
#        else:
#            print("Input should be an image directory or a numpy ndarray object")

#        h, w, d = raw_img.shape
#        _, _, B = cv2.split(raw_img)
#        B = cv2.bitwise_not(B)
        
#        GRAY = cv2.cvtColor(raw_img, cv2.COLOR_RGB2GRAY)
#        GRAY = cv2.bitwise_not(GRAY)  # Black background

#        # Using only blue band signal or directly apply the 8-bit grey signal?
#        # Currently, use the weighted average of both (the blue band alone could be not enough sensitive to the staining)
#        B = np.uint8( (GRAY * 2.0 + B * 3.0) / 5 )

#        try:
#            thresh = skf_filters.threshold_multiotsu(B, classes=3)
#        except:
#            thresh = [0, 0, 255]

#        roi = B >= np.max(thresh)

#        # Background intensity
#        background_roi = np.double(B <= np.min(thresh))
#        background_intensity = cv2.bitwise_not(GRAY)  # White background
#        background_intensity = np.double(background_intensity) * background_roi
#        background_intensity = np.quantile(background_intensity, 0.9)
#        #background_intensity = background_intensity.flatten()
#        #if np.max(background_intensity) > 0:
#        #    quantile_thresh = np.quantile(background_intensity, 0.9)
#        #    background_intensity = np.average(background_intensity[background_intensity > quantile_thresh])
#        #else:
#        #    background_intensity = 255

#        # The filtering process requires uint8 values
#        # Convert boolean to double, and convert to uint8
#        roi = np.multiply(roi, 255).astype(np.uint8)

#        # Filtering process
#        for _ in range(10):
#            roi = cv2.medianBlur(roi, 11)
#            roi = min_filter(roi, (11, 11), iteration=1)
#            roi = cv2.medianBlur(roi, 11)
#            roi = max_filter(roi, (11, 11), iteration=1)

#        # Create contour
#        contours, hierarchy = cv2.findContours(
#            roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
#        )

#        # convert back to 0 or 1 (floats)
#        roi = roi / 255.0

#        # NBT staining area (pixels)
#        nbt_area = np.sum(roi)

#        # NBT staining intensity (sum of digital number of the staining area)
#        total_nbt_intensity = np.sum((B * 1.0) * roi)

#        # Average NBT intensity
#        average_nbt = total_nbt_intensity / nbt_area if nbt_area > 0 else 0

#        # Averaged only values greater than percentile 30%
#        masked_B = np.double(B) * roi
#        masked_B = masked_B.flatten()
#        if np.max(masked_B) > 0:
#            quantile_thresh = np.quantile(masked_B, 0.3)
#            trim_average_nbt = np.average(masked_B[masked_B > quantile_thresh])
#        else:
#            trim_average_nbt = 0

#        # Plotting
#        ## Draw contour line on a blank image
#        contours = cv2.drawContours(B * 0, contours, -1, (200, 200, 100), thickness=2)
#        ## Show the coutour as red color
#        contours = cv2.merge([contours, contours, contours * 0])
#        ## Combined the original image with the contour line
#        contours = cv2.addWeighted(raw_img, 1, contours, 1, 0)

#        if isinstance(img, str):
#            contours = Image.fromarray(contours)
#            try:
#                draw = ImageDraw.Draw(contours)
#                font = ImageFont.truetype(urlopen(font_url), size=70)
#                draw.text(
#                    (30, 10),
#                    f"Avg_NBT: {round(trim_average_nbt, 4)} = {round(total_nbt_intensity / 1_000_000, 4)} M / {nbt_area} pixels",
#                    (255, 0, 0),
#                    font=font,
#                )
#            except:
#                print("Warning: Check font_url.")

#            contours.save(os.path.join(output_img_dir, output_img_name))
#            print(f"Saving to: {img_dir}/{img_name}")

#    except:
#        print(f"Problematic image: {img_dir}/{img_name}")
#        contours = B * 0
#        # The image is all white, no staining
#        if np.max(B) == 0:
#            nbt_area = 0
#            total_nbt_intensity = 0
#            average_nbt = 0
#            trim_average_nbt = 0
#        else:
#            # if the image is problematic
#            nbt_area = "NA"
#            total_nbt_intensity = "NA"
#            average_nbt = "NA"
#            trim_average_nbt = "NA"

#        if isinstance(img, str):
#            contours = Image.fromarray(contours)
#            draw = ImageDraw.Draw(contours)
#            font = ImageFont.truetype(urlopen(font_url), size=70)
#            draw.text(
#                (30, 10),
#                f"Intensity: {round(total_nbt_intensity / 1_000_000, 4)} M",
#                (255, 0, 0),
#                font=font,
#            )
#            contours.save(os.path.join(output_img_dir, output_img_name))

#    return img_name, background_intensity, nbt_area, total_nbt_intensity, average_nbt, trim_average_nbt

