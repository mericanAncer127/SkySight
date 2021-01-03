from sketch_to_sheet import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--f", dest="folder")

    args = parser.parse_args()

    roof = Roof(args.folder)
