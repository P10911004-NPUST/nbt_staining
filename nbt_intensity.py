import os
import math
import re
import cv2
import numpy as np
import pandas as pd
import skimage.filters as skf_filters
from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen

from filters import *
from feature_scaling import *

font_url = "https://github.com/mylab-root/mylab-root.github.io/blob/main/assets/webfonts/HarmonyOS_Sans_Medium.ttf?raw=true"

# font = {"family": "sans", "weight": "bold", "size": 5}
# matplotlib.rc("font", **font)
# matplotlib.rc("image", cmap="gray")
# matplotlib.use("agg")


def nbt_intensity(img):
    img_name = "NA"
    nbt_area = None
    total_nbt_intensity = None
    average_nbt = None
    raw_img, roi, contours = None, None, None

    try:
        # if the input is the img directory
        if isinstance(img, str):
            raw_img = cv2.imread(img, cv2.IMREAD_COLOR)[:, :, ::-1]
            img_name = os.path.basename(img)
            img_dir = os.path.dirname(img)

            output_img_name = "OUT_" + img_name
            output_img_dir = os.path.join(
                os.path.dirname(img_dir), "OUT_" + os.path.basename(img_dir)
            )

            if not os.path.exists(output_img_dir):
                os.mkdir(output_img_dir)

        # if the input is a numpy array
        elif isinstance(img, np.ndarray):
            raw_img = img
        else:
            print("Input should be an image directory or a numpy ndarray object")

        h, w, d = raw_img.shape
        _, _, B = cv2.split(raw_img)
        B = cv2.bitwise_not(B)
        
        GRAY = cv2.cvtColor(raw_img, cv2.COLOR_RGB2GRAY)
        GRAY = cv2.bitwise_not(GRAY)  # convert to white object and black background

        # Using only blue band signal or directly apply the 8-bit grey signal?
        # Currently, use the weighted average of both (the blue band alone could be not enough sensitive to the staining)
        B_double = (2.0 * GRAY + 3.0 * B) / 5.0
        B_double = min_max_scaling(B_double, range = [0, 255])
        B = np.uint8(B_double)
        
        try:
            B_filtered = cv2.medianBlur(B, 31)
            B_filtered = cv2.GaussianBlur(B_filtered, (25, 25), 0)
            thresh = skf_filters.threshold_multiotsu(B_filtered, classes = 5)
        except:
            thresh = [0, 0, 0, 0, 255]

        roi = B > np.median(thresh)

        # kernel size (adjusted according to the ROI size compare to the whole image)
        ks = np.sum(roi) / (h * w) * 1000
        ks = math.ceil(ks)
        ks = ks + 1 if ks % 2 == 0 else ks  # coerce to odd
        ks = 21 if ks > 21 else ks  # kernel size should not more than 21
        ks = 11 if ks < 11 else ks  # kernel size should not less than 11

        # Background intensity
        background_roi = np.double(B <= np.min(thresh))
        background_intensity = cv2.bitwise_not(GRAY)  # White background
        background_intensity = np.double(background_intensity) * background_roi
        background_intensity = np.quantile(background_intensity, 0.9)

        # The filtering process requires uint8 values
        # Convert boolean to double, and convert to uint8
        roi = roi.astype(np.uint8)
        #roi = np.multiply(roi, 255).astype(np.uint8)

        # Filtering process
        for _ in range(ks):  # 10
            roi = cv2.medianBlur(roi, ks)
            roi = min_filter(roi, (ks, ks), iteration = 1) 
            roi = cv2.medianBlur(roi, ks)
            roi = max_filter(roi, (ks, ks), iteration = 1)

        # Create contour
        contours, hierarchy = cv2.findContours(
            roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # convert back to 0 or 1 (floats)
        #roi = roi / 255.0
        roi = roi.astype(np.double)

        # NBT staining area (pixels)
        nbt_area = np.sum(roi)

        # NBT staining intensity (sum of digital number of the staining area)
        total_nbt_intensity = np.sum(B_double * roi)
        #total_nbt_intensity = np.sum((B * 1.0) * roi)

        # Average NBT intensity
        average_nbt = total_nbt_intensity / nbt_area if nbt_area > 0 else 0

        # Averaged only values greater than percentile 30%
        masked_B = B_double * roi
        masked_B = masked_B.flatten()
        if np.max(masked_B) > 0:
            quantile_thresh = np.quantile(masked_B, 0.3)
            trim_average_nbt = np.average(masked_B[masked_B > quantile_thresh])
        else:
            trim_average_nbt = 0

        # Plotting
        ## Draw contour line on a blank image
        contours = cv2.drawContours(B * 0, contours, -1, (200, 200, 100), thickness=4)
        ## Show the coutour as yellow (R + G) color
        contours = cv2.merge([contours, contours, contours * 0])
        ## Combined the original image with the contour line
        contours = cv2.addWeighted(raw_img, 1, contours, 1, 0)

        if isinstance(img, str):
            contours = Image.fromarray(contours)
            try:
                draw = ImageDraw.Draw(contours)
                font = ImageFont.truetype(urlopen(font_url), size=70)
                draw.text(
                    (30, 10),
                    f"Avg_NBT: {round(trim_average_nbt, 4)} = {round(total_nbt_intensity / 1_000_000, 4)} M / {nbt_area} pixels",
                    (255, 0, 0),
                    font=font,
                )
            except:
                print("Warning: Check font_url.")

            contours.save(os.path.join(output_img_dir, output_img_name))
            print(f"Saving to: {img_dir}/{img_name} ; ks_ratio: {ks} / {h * w} = {ks / (h * w)}")

    except:
        print(f"Problematic image: {img_dir}/{img_name}")
        contours = B * 0
        # The image is all white, no staining
        if np.max(B) == 0:
            nbt_area = 0
            total_nbt_intensity = 0
            average_nbt = 0
            trim_average_nbt = 0
        else:
            # if the image is problematic
            nbt_area = "NA"
            total_nbt_intensity = "NA"
            average_nbt = "NA"
            trim_average_nbt = "NA"

        if isinstance(img, str):
            contours = Image.fromarray(contours)
            draw = ImageDraw.Draw(contours)
            font = ImageFont.truetype(urlopen(font_url), size=70)
            draw.text(
                (30, 10),
                f"Intensity: {round(total_nbt_intensity / 1_000_000, 4)} M",
                (255, 0, 0),
                font=font,
            )
            contours.save(os.path.join(output_img_dir, output_img_name))

    return img_name, background_intensity, total_nbt_intensity, nbt_area, average_nbt, trim_average_nbt


