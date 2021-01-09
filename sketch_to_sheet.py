import argparse
import ezdxf
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from tqdm import tqdm
from shapely import geometry
from shapely.ops import polygonize

EPSILON = 1e-15

def get_letter_id(num):
    """
    Get Excel-like column letter from index num
    """
    num += 1
    s = ""
    while num > 0:
        num, remainder = divmod(num - 1, 26)
        s = chr(65 + remainder) + s
    return s

def distance(p1, p2):
    return np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

class Roof:
    def __init__(
        self,
        folder,
        fontsize=8
    ):
        self.folder = folder
        self.fontsize = fontsize
        self.lines = self.get_all_lines()
        self.line_segments = self.get_line_segments()

        _line_segments = [
            ((l.x1, l.y1), (l.x2, l.y2)) for l in self.line_segments
        ]
        self.facets = list(polygonize(_line_segments))
        self.facet_segment_ids = dict((get_letter_id(i), []) for i in range(len(self.facets)))
        self.facet_segment_lengths = dict((get_letter_id(i), []) for i in range(len(self.facets)))

        for i, facet in enumerate(self.facets):
            facet_id = get_letter_id(i)
            for segment in self.line_segments:
                is_in_facet = True
                for point in [(segment.x1, segment.y1), (segment.x2, segment.y2)]:
                    if not geometry.Point(*point).distance(facet) < EPSILON:
                        is_in_facet = False
                        break

                if is_in_facet:
                    self.facet_segment_ids[facet_id].append(segment.id)
                    self.facet_segment_lengths[facet_id].append(segment.drawing_length)

    def get_line_by_id(self, _id):
        return list(filter(lambda line: line.id == _id, self.lines))[0]

    def get_measured_lines(self, lines):
        return filter(lambda line: line.is_measured(), lines)

    def get_all_lines(self):
        sketch = ezdxf.readfile(os.path.join(self.folder, "sketch.dxf"))

        msp = sketch.modelspace()

        lines_query = msp.query("LINE")
        arcs_query = msp.query("ARC")
        
        polylines_query = msp.query("LWPOLYLINE")
        lw_lines_queries = []
        lw_arcs_queries = []
        for polyline in polylines_query:
            res = polyline.explode()
            lw_lines_queries.append(res.query("LINE"))
            lw_arcs_queries.append(res.query("ARC"))

        lines = []
        line_count = 0
        for line_query in lines_query:
            line = line_query.dxf
            line_start = line.start
            line_end = line.end

            lines.append(
                Line(
                    line_start[0],
                    line_end[0],
                    line_start[1],
                    line_end[1],
                    _id=get_letter_id(line_count)
                )
            )
            line_count += 1
        
        for lw_lines_query in lw_lines_queries:
            for line_query in lw_lines_query:
                line = line_query.dxf
                line_start = line.start
                line_end = line.end

                lines.append(
                    Line(
                        line_start[0],
                        line_end[0],
                        line_start[1],
                        line_end[1],
                        _id=get_letter_id(line_count)
                    )
                )
                line_count += 1

        for arc_query in arcs_query:
            arc = arc_query.dxf
            center, radius = arc.center, arc.radius
            start_angle, end_angle = arc.start_angle, arc.end_angle

            lines.append(
                Line(
                    center=center,
                    radius=radius,
                    start_angle=start_angle,
                    end_angle=end_angle,
                    _id=get_letter_id(line_count)
                )
            )
            line_count += 1

        for lw_arcs_query in lw_arcs_queries:
            for arc_query in lw_arcs_query:
                arc = arc_query.dxf
                center, radius = arc.center, arc.radius
                start_angle, end_angle = arc.start_angle, arc.end_angle

                lines.append(
                    Line(
                        center=center,
                        radius=radius,
                        start_angle=start_angle,
                        end_angle=end_angle,
                        _id=get_letter_id(line_count)
                    )
                )
                line_count += 1

        return lines

    def get_line_segments(self):
        line_segments = []

        intersections = dict((line, []) for line in self.lines)

        for i, line in enumerate(self.lines):

            start_point = (line.x1, line.y1)
            end_point = (line.x2, line.y2)

            for j, ref_line in enumerate(self.lines):

                if i == j:
                    continue

                for point in [start_point, end_point]:

                    if ref_line.point_on_line(point):
                        intersections[ref_line].append(point)

        for line in self.lines:
            line_segments += line.intersections_to_segments(
                intersections[line]
            )

        return line_segments

    def create_datasheet(self):
        line_count = len(self.lines)
        face_count = len(self.facets)

        line_labels = [get_letter_id(n) for n in range(line_count)]
        face_labels = [get_letter_id(n) for n in range(face_count)]


        max_length = max(line_count, face_count)

        df = pd.DataFrame(columns=["Line Label", "Type (R, H, V, K, E)", "Length (ft.)", "Face Label", "Area (ft.^2)", "Pitch"])

        df["Line Label"] = line_labels + [''] * (max_length - line_count)
        df["Type (R, H, V, K, E)"] = ['-'] * len(line_labels) + [''] * (max_length - line_count)
        df["Length (ft.)"] = ['-'] * len(line_labels) + [''] * (max_length - line_count)
        df["Face Label"] = face_labels + [''] * (max_length - face_count)
        df["Area (ft.^2)"] = ['-'] * len(face_labels) + [''] * (max_length - face_count)
        df["Pitch"] = ['-'] * len(face_labels) + [''] * (max_length - face_count)

        df.to_csv(os.path.join(self.folder, "data_sheet.csv"), index=False)
        return

    def create_line_graphic(self):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis('off')
        plt.tight_layout()

        linewidth = 2
        if self.fontsize and int(self.fontsize) < 5:
            linewidth = 1

        for i, line in enumerate(self.lines):
            if line.is_arc():

                arc_line = []
                for angle in np.linspace(line.start_angle, line.end_angle, 100):
                    arc_point = (line.center.x + np.cos(np.radians(angle)) * line.radius, line.center.y + np.sin(np.radians(angle)) * line.radius)

                    arc_line.append(arc_point)

                arc_line = np.array(arc_line)

                plt.plot(arc_line[:,0], arc_line[:,1], c='k', alpha=0.4,linewidth=linewidth)
                t = plt.text(arc_line[50][0], arc_line[50][1], get_letter_id(len(lines)+i), c='k', weight="bold", fontsize=self.fontsize)
            else:
                midpoint = line.get_midpoint()

                plt.plot([line.x1, line.x2], [line.y1, line.y2],c='k',alpha=0.4,linewidth=linewidth)
                t = plt.text(midpoint[0], midpoint[1], get_letter_id(i), c='k', weight="bold", fontsize=self.fontsize)

        plt.savefig(os.path.join(self.folder, "lengths"), dpi=400)
        plt.show()
        plt.close()
        return

    def create_facet_graphic(self):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis('off')
        plt.tight_layout()

        for i, facet in enumerate(self.facets):
            plt.plot(*facet.exterior.xy, 'k')
            center = facet.representative_point()
            plt.text(center.x, center.y, get_letter_id(i), c='k', weight="bold", fontsize=self.fontsize)

        plt.savefig(os.path.join(self.folder, "faces"), dpi=400)
        plt.show()
        plt.close()
        return

class Facet:
    def __init__(
        self,
        points
    ):
        self.points = points
        self.point_set = frozenset(points)

class Line:
    def __init__(
        self,
        x1=None,
        x2=None,
        y1=None,
        y2=None,
        center=None,
        radius=None,
        start_angle=None,
        end_angle=None,
        line_type = None, # Eave (E), Ridge (R), Hip (H), Valley (V), Rake (K)
        _id=None
    ):

        if center:
            # Line is an arc
            self.x1 = None
            self.x2 = None
            self.y1 = None
            self.y2 = None
            self.center = center
            self.radius = radius
            self.start_angle = start_angle
            self.end_angle = end_angle
        else:
            # Line is a straight line
            self.x1 = x1
            self.x2 = x2
            self.y1 = y1
            self.y2 = y2
            self.center = None
            self.radius = None
            self.start_angle = None
            self.end_angle = None

        self.id = _id
        self.line_type = line_type
        self.drawing_length = self.get_drawing_length()
        self.real_length = None

    def is_arc(self):
        return self.center is not None

    def is_measured(self):
        return self.real_length is not None

    def get_drawing_length(self):
        if self.is_arc():
            return 2 * self.radius * np.pi * (self.end_angle - self.start_angle) / 360
        else:
            return distance((self.x1,self.y1),(self.x2,self.y2))

    def set_real_length(self, length):
        self.real_length = length

    def set_line_type(self, line_type):
        self.line_type = line_type

    def get_real_length(self, line):
        """
        Use the real length and drawing length
        of line given in argument to estimate
        real length of this line
        """
        assert line.real_length, "Given line has no real length"

        return line.real_length * self.drawing_length / line.drawing_length

    def get_average_real_length(self, lines):
        """
        Use multiple lines with known real length and
        drawing length to estimate real length of this line
        """
        return np.mean(self.get_real_length(line) for line in lines)

    def point_on_line(self, point):
        d1 = distance(point, (self.x1, self.y1))
        d2 = distance(point, (self.x2, self.y2))

        return round(d1 + d2, 3) == round(self.drawing_length, 3) and \
            d1 != 0 and d2 != 0

    def get_midpoint(self):
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def intersections_to_segments(self, intersections):
        segments = []

        intersections = sorted(intersections,
            key=lambda point: distance(point, (self.x1, self.y1)))

        points = [(self.x1, self.y1)] + \
            intersections + \
            [(self.x2, self.y2)]

        for i in range(len(points)-1):
            segments.append(
                Line(
                    points[i][0],
                    points[i+1][0],
                    points[i][1],
                    points[i+1][1],
                    _id=self.id
                )
            )

        return segments
    
    def get_slope(self):
        if self.x2 == self.x1:
            self.x1 += EPSILON

        return (self.y2 - self.y1) / (self.x2 - self.x1)


    def angle(self, line):

        s1 = self.get_slope()
        s2 = line.get_slope()

        return abs(np.degrees(np.arctan((s2 - s1) / (EPSILON + 1 + (s2 * s1)))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--f", dest="folder")
    parser.add_argument("--s", dest="fontsize", type=int)

    args = parser.parse_args()

    roof = Roof(args.folder, args.fontsize)

    roof.create_datasheet()

    roof.create_line_graphic()

    roof.create_facet_graphic()

