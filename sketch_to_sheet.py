from Roof import *

def main(folder, fontsize):

    roof = Roof(os.path.join("../reports", folder), fontsize)

    roof.create_datasheet()
    roof.create_diagram()

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--f", dest="folder")
    parser.add_argument("--s", dest="fontsize", default=7)

    args = parser.parse_args()

    main(args.folder, args.fontsize)


