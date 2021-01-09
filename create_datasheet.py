import argparse
import ezdxf
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pickle
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
    return dist_1 != 0 and dist_2 != 0 and round(dist_1 + dist_2,2) == round(distance(l[0],l[1]),2)

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

def create_length_graphic(lines, arcs, folder, fontsize=8):
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

        plt.plot([x_1,x_2], [y_1,y_2],c='k',alpha=0.4,linewidth=linewidth)
        t = plt.text(midpoint[0], midpoint[1], get_letter_id(i+1), c='k', weight="bold", fontsize=fontsize)
        # t.set_bbox(dict(facecolor='red', alpha=0.75, edgecolor='red'))

    for i, arc in enumerate(arcs):
        _arc = arc.dxf
        center, radius = _arc.center, _arc.radius

        start_angle, end_angle = _arc.start_angle, _arc.end_angle

        arc_line = []
        for angle in np.linspace(start_angle, end_angle, 100):
            arc_point = (center.x + np.cos(np.radians(angle)) * radius, center.y + np.sin(np.radians(angle)) * radius)

            arc_line.append(arc_point)

        arc_line = np.array(arc_line)

        plt.plot(arc_line[:,0], arc_line[:,1], c='k', alpha=0.4,linewidth=linewidth)
        t = plt.text(arc_line[50][0], arc_line[50][1], get_letter_id(len(lines)+i+1), c='k', weight="bold", fontsize=fontsize)

    plt.savefig(os.path.join(folder, "lengths"), dpi=400)
    plt.show()
    plt.close()
    return

def create_face_graphic(lines, arcs, folder, fontsize=8, label=False):
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    plt.axis('off')
    plt.tight_layout()

    points = []
    _lines = []

    def onclick(event):
        if event.button == 1:
            print(event.xdata, event.ydata)

            points.append([event.xdata, event.ydata])

            plt.clf()
            ax.set_aspect("equal")
            plt.axis('off')
            plt.tight_layout()

            plot_lines(_lines)
            plot_face_labels(points)
            plot_arcs(arcs)

            plt.draw()
            plt.savefig(os.path.join(folder, "faces"), dpi=400)
            np.save(os.path.join(folder, "polygon_points.npy"), points)

        return

    def plot_lines(lines):
        for line in lines:
            plt.plot([line[0][0], line[1][0]],
                [line[0][1], line[1][1]], c='k', alpha=0.4)
        return

    def plot_face_labels(points):
        for i, point in enumerate(points):
            t = plt.text(point[0], point[1], get_letter_id(i+1), c='k', weight="bold", fontsize=fontsize)
        return

    def plot_arcs(arcs):
        for i, arc in enumerate(arcs):
            _arc = arc.dxf
            center, radius = _arc.center, _arc.radius

            start_angle, end_angle = _arc.start_angle, _arc.end_angle

            arc_line = []
            for angle in np.linspace(start_angle, end_angle, 100):
                arc_point = (center.x + np.cos(np.radians(angle)) * radius, center.y + np.sin(np.radians(angle)) * radius)

                arc_line.append(arc_point)


            arc_line = np.array(arc_line)

            plt.plot(arc_line[:,0], arc_line[:,1], c='k', alpha=0.4)

        return

    for i, line in enumerate(lines):
        x_1, y_1, *_ = line.dxf.start
        x_2, y_2, *_ = line.dxf.end

        _lines.append(((x_1,y_1),(x_2,y_2)))

    for i, arc in enumerate(arcs):
        _arc = arc.dxf
        center, radius = _arc.center, _arc.radius

        start_angle, end_angle = _arc.start_angle, _arc.end_angle

        arc_line = []
        for angle in np.linspace(start_angle, end_angle, 100):
            arc_point = (center.x + np.cos(np.radians(angle)) * radius, center.y + np.sin(np.radians(angle)) * radius)

            arc_line.append(arc_point)


        _arc_lines = [(arc_line[k], arc_line[k+1]) for k in range(len(arc_line) - 1)]

        arc_line = np.array(arc_line)


        plt.plot(arc_line[:,0], arc_line[:,1], c='k', alpha=0.4)

        _lines += _arc_lines

    line_segments = get_line_segments(_lines)

    polygons = list(polygonize(line_segments))

    for i, polygon in enumerate(polygons):
        point = polygon.representative_point()
        points.append([point.x, point.y])

    plot_lines(_lines)
    plot_face_labels(points)
    plt.savefig(os.path.join(folder, "faces"), dpi=400)
    np.save(os.path.join(folder, "polygon_points.npy"), points)

    fig.canvas.mpl_connect("button_press_event", onclick)
    plt.show()
    plt.draw()

    return len(points)

def create_data_sheet(line_count, face_count, folder):
    line_labels = [get_letter_id(n+1) for n in range(line_count)]
    face_labels = [get_letter_id(n+1) for n in range(face_count)]

    max_length = max(line_count, face_count)

    df = pd.DataFrame(columns=["Line Label", "Type (R, H, V, K, E)", "Length (ft.)", "Face Label", "Area (ft.^2)", "Pitch"])

    df["Line Label"] = line_labels + [''] * (max_length - line_count)
    df["Type (R, H, V, K, E)"] = ['-'] * len(line_labels) + [''] * (max_length - line_count)
    df["Length (ft.)"] = ['-'] * len(line_labels) + [''] * (max_length - line_count)
    df["Face Label"] = face_labels + [''] * (max_length - face_count)
    df["Area (ft.^2)"] = ['-'] * len(face_labels) + [''] * (max_length - face_count)
    df["Pitch"] = ['-'] * len(face_labels) + [''] * (max_length - face_count)

    df.to_csv(os.path.join(folder, "data_sheet.csv"), index=False)

    return

def main(folder, fontsize, label=False):
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
    arcs = msp.query("ARC")

    # poly_lines = msp.query("LWPOLYLINE")
    # for poly_line in poly_lines:
    #     print(dir(poly_line.dxf))
    #     print(poly_line.dxf.dxfattribs)
    # a

    create_length_graphic(lines, arcs, folder, fontsize)

    face_count = create_face_graphic(lines, arcs, folder, fontsize, label)

    create_data_sheet(len(lines), face_count, folder)

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    parser.add_argument("--s", dest="fontsize", type=int)
    parser.add_argument("-l", dest="label", action="store_true")

    args = parser.parse_args()

    main(args.folder, args.fontsize, args.label)
