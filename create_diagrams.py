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
    num += 1
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

def create_length_diagram(lines, arcs, lengths, colors, folder, fontsize=8):
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    plt.axis('off')
    plt.tight_layout()

    linewidth = 2
    if fontsize and int(fontsize) < 5:
        linewidth = 1

    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        midpoint = get_midpoint((x_1, y_1), (x_2, y_2))

        plt.plot([x_1,x_2], [y_1,y_2], c=colors[i], alpha=0.5, linewidth=linewidth)
        t = plt.text(midpoint[0], midpoint[1], int(lengths[i]), c='k', weight="bold", fontsize=fontsize, ha="center")
        # t.set_bbox(dict(facecolor='white', alpha=0.75, edgecolor='black'))

    for i, arc in enumerate(arcs):
        _arc = arc.dxf
        center, radius = _arc.center, _arc.radius

        start_angle, end_angle = _arc.start_angle, _arc.end_angle

        arc_line = []
        for angle in np.linspace(start_angle, end_angle, 100):
            arc_point = (center.x + np.cos(np.radians(angle)) * radius, center.y + np.sin(np.radians(angle)) * radius)

            arc_line.append(arc_point)

        arc_line = np.array(arc_line)

        plt.plot(arc_line[:,0], arc_line[:,1], c='k', alpha=0.4, linewidth=linewidth)
        t = plt.text(arc_line[50][0], arc_line[50][1], get_letter_id(len(lines)+i), c='k', weight="bold", fontsize=fontsize, ha="center")


    plt.savefig(os.path.join(folder, "Length"), dpi=400)
    plt.close()
    return

def create_face_diagrams(polygons, areas, pitches, folder, fontsize=8):

    # _lines = []
    # for i, line in enumerate(lines):
    #     x_1, y_1, *_ = line.dxf.start
    #     x_2, y_2, *_ = line.dxf.end

    #     _lines.append(((x_1,y_1),(x_2,y_2)))

    # line_segments = get_line_segments(_lines)

    # polygons = list(polygonize(line_segments))

    # polygon_points = np.load(os.path.join(folder, "polygon_points.npy"))

    for data, diagram_name in zip([areas, pitches], ["Area", "Pitch"]):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis('off')
        plt.tight_layout()

        for i, polygon in enumerate(polygons):
            plt.plot(*polygon.exterior.xy, 'k', alpha=0.4)

            point = polygon.centroid
            if not polygon.contains(point):
                point = polygon.representative_point()

            t = plt.text(point.x, point.y, int(data[i]), c='k', weight="bold", fontsize=fontsize, ha="center")

        plt.savefig(os.path.join(folder, diagram_name), dpi=400)
        plt.close()

    return

def get_data(folder, datasheet="data_sheet.csv"):
    df = pd.read_csv(os.path.join(folder, datasheet))

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

def create_diagrams(roof, fontsize, datasheet="data_sheet.csv"):
    drawing = ezdxf.readfile(glob(roof.folder+"/*.dxf")[0])
    msp = drawing.modelspace()

    lines = msp.query("LINE")
    arcs = msp.query("ARC")

    colors, lengths, areas, pitches, maps = get_data(roof.folder, datasheet=datasheet)

    create_length_diagram(lines, arcs, lengths, colors, roof.folder, fontsize)

    create_face_diagrams(roof.facets, areas, pitches, roof.folder, fontsize)

    return maps

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    parser.add_argument("--s", dest="fontsize", type=int)

    args = parser.parse_args()

    create_diagrams(args.folder, args.fontsize)
