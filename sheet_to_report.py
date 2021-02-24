from ReportWriter import *
from Roof import *

def main(fontsize):

    folder = "_".join(ADDRESS.split(",")[0].split(" "))

    roof = Roof(os.path.join("../reports", folder), fontsize)

    roof.auto_fill()

    roof.create_length_diagram()
    roof.create_area_diagram()
    roof.create_pitch_diagram()

    roof.create_report()
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--s", dest="fontsize", default=7)

    args = parser.parse_args()

    main(args.fontsize)


