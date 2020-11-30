import argparse
import ezdxf
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
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

def create_length_diagram(lines, lengths, colors, folder):
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    plt.axis('off')
    plt.tight_layout()

    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        midpoint = get_midpoint((x_1, y_1), (x_2, y_2))

        plt.plot([x_1,x_2], [y_1,y_2], c=colors[i])
        t = plt.text(midpoint[0], midpoint[1], lengths[i], c='k', weight="bold", fontsize=7)
        t.set_bbox(dict(facecolor='white', alpha=0.75, edgecolor='black'))
    
    plt.savefig(os.path.join(folder, "Length"))
    plt.close()
    return

def create_face_diagrams(lines, areas, pitches, folder):

    _lines = []
    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        _lines.append(((x_1,y_1),(x_2,y_2)))

        plt.plot([x_1,x_2], [y_1,y_2],c='k')
    
    line_segments = get_line_segments(_lines)

    polygons = list(polygonize(line_segments))

    for data, diagram_name in zip([areas, pitches], ["Area", "Pitch"]):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis('off')
        plt.tight_layout()

        for _line in _lines:
            plt.plot(
                [_line[0][0],_line[1][0]],
                [_line[0][1],_line[1][1]],
                c='k')

        for i, polygon in enumerate(polygons):
            centroid = polygon.centroid
            
            t = plt.text(centroid.x, centroid.y, int(data[i]), c='k', weight="bold", fontsize=7)
            t.set_bbox(dict(facecolor='white', alpha=0.75, edgecolor='black'))

        plt.savefig(os.path.join(folder, diagram_name))
        plt.close()

    return

def get_data(folder):
    df = pd.read_csv(glob(folder + "/*.csv")[0])

    return (
        [COLOR_DICT[key] for key in df["Type (R, H, V, K, E)"]],
        list(df["Length (ft.)"]),
        list(df["Area (ft.^2)"]),
        list(df["Pitch (0-12)"])
        )

def main(folder):
    drawing = ezdxf.readfile(glob(folder+"/*.dxf")[0])
    msp = drawing.modelspace()

    lines = msp.query("LINE")

    colors, lengths, areas, pitches = get_data(folder)

    create_length_diagram(lines, lengths, colors, folder)

    create_face_diagrams(lines, areas, pitches, folder)

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")

    args = parser.parse_args()

    main(args.folder)