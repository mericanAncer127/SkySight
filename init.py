import argparse
import os
from ReportWriter import *
import subprocess

REPORT_FOLDER_PATH = "../reports"

def init():
    name = "_".join(ADDRESS.split(",")[0].split(" "))

    folder_name = os.path.join(REPORT_FOLDER_PATH, name)

    try:
        os.mkdir(folder_name)
        os.mkdir(os.path.join(folder_name, "ims"))
    except:
        print(f"Folder '{folder_name}' already exists")

    return

if __name__ == "__main__":
    init()

