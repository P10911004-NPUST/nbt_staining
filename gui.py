import os
import base64
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageTk
from urllib.request import urlopen
import tkinter as tk
from tkinter import filedialog, PhotoImage
import multiprocessing as mp
from multiprocessing import freeze_support

from nbt_intensity import nbt_intensity

try:
    icon_url = urlopen(
        "https://raw.githubusercontent.com/mylab-root/NBT-staining/main/NBT_intensity_calculator/icon.ico"
    )
    icon = icon_url.read()
    icon_url.close()
except:
    print("Warning: Check icon_url.")


def get_folder_path():
    global input_folder_dir, img_list
    f = filedialog.askdirectory()
    folder_path.set(f)
    input_folder_dir = folder_path.get()
    img_list = [
        os.path.join(input_folder_dir, i)
        for i in os.listdir(input_folder_dir)
        if i.lower().endswith((".jpg", ".jpeg", "tif", "tiff", "png", ".bmp"))
    ]
    folder_img_num.set(f"Load in {len(img_list)} images")


def run_nbt():
    folder_path = input_folder_dir
    img_list = [
        os.path.join(folder_path, i)
        for i in os.listdir(folder_path)
        if i.lower().endswith(("jpg", "jpeg", "tif", "tiff", "png"))
    ]

    output_dir = os.path.join(
        os.path.dirname(folder_path), "OUT_" + os.path.basename(folder_path)
    )

    df0 = {
        "img_name": [],
        "background_intensity": [],
        "nbt_area": [],
        "nbt_intensity": [],
        "avg_nbt": [],
        "trim_avg_nbt": [],
    }

    pool = mp.Pool()
    res = pool.map(nbt_intensity, img_list)
    pool.close()
    pool.join()
    df0["img_name"] = [i[0] for i in res]
    df0["background_intensity"] = [i[1] for i in res]
    df0["nbt_area"] = [i[2] for i in res]
    df0["nbt_intensity"] = [i[3] for i in res]
    df0["avg_nbt"] = [i[4] for i in res]
    df0["trim_avg_nbt"] = [i[5] for i in res]
    df0 = pd.DataFrame.from_dict(df0)

    output_csv = os.path.join(
        output_dir, "OUT_" + os.path.basename(folder_path) + ".csv"
    )

    df0.to_csv(output_csv, index=False)

    folder_img_num.set("Finished !")


if __name__ == "__main__":

    freeze_support()

    ############################################################################
    # Interface
    ############################################################################
    root = tk.Tk()

    try:
        icon = ImageTk.PhotoImage(data=icon)
        root.iconphoto(False, icon)
    except:
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
        pass

    root.title("NBT staining intensity")
    root.geometry("450x350")
    title_label = tk.Label(root, text="NBT intensity", font=("Calibri 20 bold")).pack()

    ############################################################################
    # Tk variables
    ############################################################################
    folder_path = tk.StringVar()
    folder_img_num = tk.StringVar()
    # nbt_label_log = tk.StringVar()

    ############################################################################
    # Folder selection
    ############################################################################
    folder_frame = tk.Frame(master=root).pack(pady=20, padx=20, fill="both")

    folder_button = tk.Button(
        master=folder_frame,
        text="Select folder",
        font="Calibri 15",
        command=get_folder_path,
    ).pack(padx=20, side="top")

    folder_label = tk.Label(
        master=folder_frame,
        text="Select folder containing images",
        font=("Calibri 15"),
        textvariable=folder_img_num,
    ).pack(padx=20, pady=50, side="bottom")

    ############################################################################
    # Run NBT
    ############################################################################

    nbt_frame = tk.Frame(master=root).pack(padx=20, pady=20, fill="both")

    nbt_button = tk.Button(
        master=nbt_frame,
        text="Run",
        font="Calibri 15",
        command=run_nbt,
    ).pack(padx=20, side="top", anchor="center")

    # nbt_label = tk.Label(
    #    master=nbt_frame,
    #    text="",
    #    font=("Calibri 13"),
    #    textvariable=nbt_label_log,
    # ).pack(padx=20, side="bottom", anchor="center")

    root.mainloop()
