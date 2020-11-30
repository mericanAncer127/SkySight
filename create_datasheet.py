import argparse
import ezdxf
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from shapely.ops import polygonize, linemerge

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

def create_length_graphic(lines, folder):
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    plt.axis('off')
    plt.tight_layout()

    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        midpoint = get_midpoint((x_1, y_1), (x_2, y_2))

        plt.plot([x_1,x_2], [y_1,y_2],c='k')
        t = plt.text(midpoint[0], midpoint[1], get_letter_id(i+1), c='w', weight="bold", fontsize=7)
        t.set_bbox(dict(facecolor='red', alpha=0.75, edgecolor='red'))
    
    plt.savefig(os.path.join(folder, "lengths"))
    plt.close()
    return

def create_face_graphic(lines, folder):
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    plt.axis('off')
    plt.tight_layout()

    _lines = []
    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        _lines.append(((x_1,y_1),(x_2,y_2)))

        plt.plot([x_1,x_2], [y_1,y_2],c='k')
    
    line_segments = get_line_segments(_lines)

    polygons = list(polygonize(line_segments))

    for i, polygon in enumerate(polygons):
        centroid = polygon.centroid

        t = plt.text(centroid.x, centroid.y, get_letter_id(i+1), c='w', weight="bold", fontsize=7)
        t.set_bbox(dict(facecolor='red', alpha=0.75, edgecolor='red'))

    plt.savefig(os.path.join(folder, "faces"))
    plt.close()

    return len(polygons)

def create_data_sheet(line_count, face_count, folder):
    line_labels = [get_letter_id(n+1) for n in range(line_count)]
    face_labels = [get_letter_id(n+1) for n in range(face_count)]

    max_length = max(line_count, face_count)

    df = pd.DataFrame(columns=["Line Label", "Type (R, H, V, K, E)", "Length (ft.)", "Face Label", "Area (ft.^2)", "Pitch (0-12)"])
    
    df["Line Label"] = line_labels + [''] * (max_length - line_count)
    df["Type (R, H, V, K, E)"] = ['-'] * len(line_labels) + [''] * (max_length - line_count)
    df["Length (ft.)"] = ['-'] * len(line_labels) + [''] * (max_length - line_count)
    df["Face Label"] = face_labels + [''] * (max_length - face_count)
    df["Area (ft.^2)"] = ['-'] * len(face_labels) + [''] * (max_length - face_count)
    df["Pitch (0-12)"] = ['-'] * len(face_labels) + [''] * (max_length - face_count)

    df.to_csv(os.path.join(folder, "data_sheet.csv"), index=False)

    return

def main(folder):
    """
    Creates graphics and accompanying CSV file for
    measurement labeling.

    Two graphics are generated:
        1. Roof lines graphic
        2. Roof faces graphic
    
    The line graphic is used for length measurements. The
    faces graphic is used for area and pitch measurements.
    """
    drawing = ezdxf.readfile(glob(folder+"/*.dxf")[0])
    msp = drawing.modelspace()

    lines = msp.query("LINE")

    create_length_graphic(lines, folder)

    face_count = create_face_graphic(lines, folder)

    create_data_sheet(len(lines), face_count, folder)

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")

    args = parser.parse_args()

    main(args.folder)
