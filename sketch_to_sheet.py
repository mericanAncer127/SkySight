from ReportWriter import *
from Roof import *

def main(fontsize):

    folder = "_".join(ADDRESS.split(",")[0].split(" "))

    roof = Roof(os.path.join("../reports", folder), fontsize)

    roof.create_datasheet()
    roof.create_diagram()

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--s", dest="fontsize", default=9)

    args = parser.parse_args()

    main(args.fontsize)


