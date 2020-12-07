import argparse
from collections import defaultdict
import ezdxf
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pickle
from shapely.ops import polygonize, linemerge

COLOR_DICT = {
    "R": "red",
    "H": "orange",
    "V": "blue",
    "K": "green",
    "E": "black"
}

def get_letter_id(num):
    """
    Get Excel-like column letter from index num
    """
    s = ""
    while num > 0:
        num, remainder = divmod(num - 1, 26)
        s = chr(65 + remainder) + s
    return s

def get_midpoint(p1, p2):
    """
    Get point equidistant to points p1 and p2
    """
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def point_lies_on_line(p, l):
    """
    Return true if point p lies on line l excluding endpoints,
    false otherwise
    """
    dist_1 = distance(p,l[0])
    dist_2 = distance(p,l[1])
    return dist_1 != 0 and dist_2 != 0 and dist_1 + dist_2 == distance(l[0],l[1])

def get_line_segments(lines):
    """
    Return all line segments formed by lines. If a line point
    intersects another line, the line will be broken into two
    line segments.
    """
    segments = []

    # Iterate over lines
    for line in lines:
        # Find line points that intersect this line
        intersecting_points = []
        for ref_line in lines:
            if ref_line == line:
                continue

            for point in ref_line:
                if point_lies_on_line(point,line):
                    intersecting_points.append(point)

        intersecting_points = sorted(intersecting_points)
        _line = sorted(line)

        if len(intersecting_points) == 0:
            segments.append(line)
        else:
            points = [line[0]] + intersecting_points + [line[1]]
            for i in range(len(intersecting_points)+1):
                segments.append((points[i], points[i+1]))

    return segments

def create_length_diagram(lines, lengths, colors, folder, fontsize=8):
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    plt.axis('off')
    plt.tight_layout()

    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        midpoint = get_midpoint((x_1, y_1), (x_2, y_2))

        plt.plot([x_1,x_2], [y_1,y_2], c=colors[i], alpha=0.5)
        t = plt.text(midpoint[0], midpoint[1], lengths[i], c='k', weight="bold", fontsize=fontsize)
        # t.set_bbox(dict(facecolor='white', alpha=0.75, edgecolor='black'))
    
    plt.savefig(os.path.join(folder, "Length"), dpi=400)
    plt.close()
    return

def create_face_diagrams(lines, areas, pitches, folder, fontsize=8):

    _lines = []
    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        _lines.append(((x_1,y_1),(x_2,y_2)))

    line_segments = get_line_segments(_lines)

    polygons = list(polygonize(line_segments))

    polygon_points = np.load(os.path.join(folder, "polygon_points.npy"))

    for data, diagram_name in zip([areas, pitches], ["Area", "Pitch"]):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis('off')
        plt.tight_layout()

        for _line in _lines:
            plt.plot(
                [_line[0][0],_line[1][0]],
                [_line[0][1],_line[1][1]],
                c='k', alpha=0.4)

        for i, polygon in enumerate(polygon_points):
            if pd.isnull(data[i]):
                break

            point = polygon_points[i]
            
            t = plt.text(point[0], point[1], int(data[i]), c='k', weight="bold", fontsize=fontsize)
            # t.set_bbox(dict(facecolor='white', alpha=0.75, edgecolor='black'))

        plt.savefig(os.path.join(folder, diagram_name), dpi=400)
        plt.close()

    return

def get_data(folder):
    df = pd.read_csv(glob(folder + "/*.csv")[0])

    def make_maps():
        roof_line_map = defaultdict(int)
        pitch_area_map = defaultdict(int)

        for i, row in df.iterrows():
            if not pd.isnull(row["Length (ft.)"]):
                roof_line_map[row["Type (R, H, V, K, E)"]] += \
                    row["Length (ft.)"]
            
            if not pd.isnull(row["Area (ft.^2)"]):
                pitch_area_map[row["Pitch"]] += \
                    row["Area (ft.^2)"]

        return (
            roof_line_map,
            pitch_area_map,
            df["Area (ft.^2)"].count()
            )

    # try:
    #     print("Lengths:")
    #     for key in ["R","H","V","K","E"]:
    #         print("{} length: {}".format(key, sum(df.loc[df["Type (R, H, V, K, E)"] == key]["Length (ft.)"])))
    # except:
    #     pass

    # try:
    #     print("\nTotal Area: {}".format(sum(df["Area (ft.^2)"].fillna(0))))
    # except:
    #     pass

    return (
        [COLOR_DICT[key] for key in df["Type (R, H, V, K, E)"]],
        list(df["Length (ft.)"]),
        list(df["Area (ft.^2)"]),
        list(df["Pitch"]),
        make_maps()
        )

def create_diagrams(folder, fontsize):
    drawing = ezdxf.readfile(glob(folder+"/*.dxf")[0])
    msp = drawing.modelspace()

    lines = msp.query("LINE")

    colors, lengths, areas, pitches, maps = get_data(folder)

    create_length_diagram(lines, lengths, colors, folder, fontsize)

    create_face_diagrams(lines, areas, pitches, folder, fontsize)

    return maps

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    parser.add_argument("--s", dest="fontsize", type=int)

    args = parser.parse_args()

    create_diagrams(args.folder, args.fontsize)