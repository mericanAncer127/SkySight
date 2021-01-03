import argparse
import os

REPORT_FOLDER_PATH = "../reports"

def init(name):
    folder_name = os.path.join(REPORT_FOLDER_PATH, name)

    try:
        os.mkdir(folder_name)
        os.mkdir(os.path.join(folder_name, "ims"))
    except:
        print(f"Folder '{folder_name}' already exists")

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", dest="name")

    args = parser.parse_args()

    init(args.name)
