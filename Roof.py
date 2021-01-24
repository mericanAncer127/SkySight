import argparse
from collections import defaultdict
import ezdxf
import glob
from helper_functions import *
import itertools
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from ReportWriter import *
from shapely.geometry import Point
from shapely.ops import polygonize
from sklearn.linear_model import LinearRegression


EPSILON = 1e-8

LINE_TYPE_COLOR_MAP = {
    "E": "black",
    "R": "red",
    "V": "blue",
    "H": "orange",
    "K": "green"
}

class Roof:
    def __init__(self, folder, fontsize):
        self.folder = folder
        self.fontsize = fontsize

        self.lines = self.get_lines()
        self.line_segments = self.get_line_segments()
        self.facets = self.get_facets()

        self.df = None
        df_file = os.path.join(folder, "data_sheet.csv")
        if os.path.isfile(df_file):
            self.df = pd.read_csv(df_file)

            self.line_type_map = pd.Series(
                self.df["Type"].values,
                index=self.df["Line Label"]
            ).to_dict()

            self.line_length_map = pd.Series(
                self.df["Length"].values,
                index=self.df["Line Label"]
            )

            self.line_3D_length_map = dict.fromkeys(self.df["Line Label"])

            self.facet_area_map = pd.Series(
                self.df["Area"].values,
                index=self.df["Facet Label"]
            )

            self.facet_pitch_map = pd.Series(
                self.df["Pitch"].values,
                index=self.df["Facet Label"]
            )

            self.facet_area_map = {k: v for k, v in self.facet_area_map.items() if type(k) is str}
            self.facet_pitch_map = {k: v for k, v in self.facet_pitch_map.items() if type(k) is str}

            self.facet_line_id_map = defaultdict(set)
            for facet_id, facet in self.facets.items():
                boundary = facet.boundary
                for line_id, segments in self.line_segments.items():
                    for segment in segments:
                        p1, p2 = Point(*segment[0]), Point(*segment[1])
                        if boundary.distance(p1) < EPSILON and \
                            boundary.distance(p2) < EPSILON:

                            self.facet_line_id_map[facet_id].add(line_id)


    def get_lines(self):
        lines = {}
        sketch = ezdxf.readfile(os.path.join(self.folder, "sketch.dxf"))

        msp = sketch.modelspace()

        lines_query = msp.query("LINE")

        polylines_query = msp.query("LWPOLYLINE")
        lw_lines_queries = []
        for polyline in polylines_query:
            res = polyline.explode()
            lw_lines_queries.append(res.query("LINE"))

        line_count = 0
        for line_query in lines_query:
            line = line_query.dxf
            line_start = line.start
            line_end = line.end

            lines[get_letter_id(line_count)] = sorted([
                [line_start[0], line_start[1]],
                [line_end[0], line_end[1]]
            ])

            line_count += 1

        for lw_lines_query in lw_lines_queries:
            for line_query in lw_lines_query:
                line = line_query.dxf

                line_start = line.start
                line_end = line.end

                lines[get_letter_id(line_count)] = sorted([
                    [line_start[0], line_start[1]],
                    [line_end[0], line_end[1]]
                ])

                line_count += 1

        return lines

    def intersections_to_line_segments(self, line, intersections):
        intersections = sorted(intersections, key=lambda point: distance(point, line[0]))

        points = [line[0]] + \
            intersections + \
            [line[1]]

        line_segments = []
        for i in range(1, len(points)):
            line_segments.append(
                [points[i-1], points[i]]
            )

        return line_segments

    def get_line_segments(self):
        line_segments = defaultdict(list)
        intersections = defaultdict(list)

        for line_id, line in self.lines.items():
            for _line_id, ref_line in self.lines.items():
                if line_id == _line_id:
                    continue

                for point in ref_line:
                    d1 = distance(line[0], point)
                    d2 = distance(line[1], point)

                    if d1 != 0 and d2 != 0 and \
                        d1 + d2 == distance(line[0], line[1]):

                        intersections[line_id].append(point)

        for line_id, line in self.lines.items():
            line_segments[line_id] = self.intersections_to_line_segments(
                line, intersections[line_id]
            )

        return line_segments

    def get_facets(self):
        all_line_segments = list(itertools.chain(*self.line_segments.values()))
        polygons = polygonize(all_line_segments)

        return dict((get_letter_id(i), polygon) for i, polygon in enumerate(polygons))

    def create_datasheet(self):
        df = pd.DataFrame(
            columns=[
                "Line Label",
                "Type",
                "Length",
                "Facet Label",
                "Pitch",
                "Area"
            ]
        )

        df["Line Label"] = self.lines.keys()
        df["Facet Label"] = list(self.facets.keys()) + [''] * (len(self.lines) - len(self.facets))

        df.to_csv(os.path.join(self.folder, "data_sheet.csv"), index=False)
        return

    def create_diagram(self):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis("off")
        plt.tight_layout()

        for line_id, line in self.lines.items():
            plt.plot(
                [line[0][0], line[1][0]],
                [line[0][1], line[1][1]],
                'k',
                alpha=0.4
            )

            mp = midpoint(line)
            plt.text(
                mp[0],
                mp[1],
                line_id,
                c="k",
                ha="center",
                va="center",
                fontsize=self.fontsize,
                weight="bold",
                rotation=angle(line),
                bbox=dict(boxstyle="square,pad=0.0", fc="white", ec="none")
            )

        for facet_id, facet in self.facets.items():
            center = facet.centroid
            if not facet.contains(center):
                center = facet.representative_point()

            plt.text(
                center.x,
                center.y,
                facet_id,
                c="r",
                ha="center",
                va="center",
                fontsize=self.fontsize,
                weight="bold"
            )

        plt.savefig(
            os.path.join(self.folder, "diagram"),
            bbox_inches="tight",
            dpi=400
        )
        plt.show()
        return

    def get_facet_flat_line_id(self, facet_id):
        ret = None
        longest = 0

        for line_id in self.facet_line_id_map[facet_id]:
            if self.line_type_map[line_id].upper() in ["E", "R"]:
                sketch_length = distance(*self.lines[line_id])
                if sketch_length > longest:
                    ret = line_id
                    longest = sketch_length

        return ret

    def get_3D_sketch_length(self, line_id):
        line = self.lines[line_id]

        if self.line_type_map[line_id].upper() in ["E", "R"]:
            return distance(*line)

        for facet_id, line_ids in self.facet_line_id_map.items():
            if line_id in line_ids:
                ref_line_id = self.get_facet_flat_line_id(facet_id)
                ref_line = self.lines[ref_line_id]

                angle = angle_between(line, ref_line)

                slope = np.arctan(self.facet_pitch_map[facet_id] / 12)

                ground_angle = slope * np.sin(angle)

                return distance(*line) / ground_angle

        return None

    def get_average_scale_factor(self):
        scale_factors = []
        for line_id, sketch_length_3D in self.line_3D_length_map.items():
            scale_factors.append(sketch_length_3D / self.line_length_map[line_id])

        return np.median(scale_factors)

    def auto_fill(self):
        X, Y = [], []
        for line_id, length in self.line_length_map.items():
            if not np.isnan(length):
                sketch_length_3D = self.get_3D_sketch_length(line_id)
                self.line_3D_length_map[line_id] = sketch_length_3D

                X.append(sketch_length_3D)
                Y.append(length)

        X, Y = np.array(X).reshape(-1, 1), np.array(Y)

        reg = LinearRegression(fit_intercept=False).fit(X, Y)

        reg_slope = reg.coef_

        for line_id, length in self.line_length_map.items():
            if np.isnan(length):
                x = self.get_3D_sketch_length(line_id)
                self.line_3D_length_map[line_id] = x

                _x, _y = closest_sample(x, X, Y)

                self.line_length_map[line_id] = int(predict(x, _x, _y, reg_slope))

        scale_factor = self.get_average_scale_factor()

        for facet_id, area in self.facet_area_map.items():
            if np.isnan(area):
                facet = self.facets[facet_id]
                slope = np.arctan(self.facet_pitch_map[facet_id] / 12)

                sketch_area_3D = facet.area / np.cos(slope)

                area = int(sketch_area_3D / scale_factor**2)
                if area % 2 != 0:
                    area += 1

                self.facet_area_map[facet_id] = area
        return

    def create_length_diagram(self):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis("off")
        plt.tight_layout()

        for line_id, line in self.lines.items():
            plt.plot(
                [line[0][0], line[1][0]],
                [line[0][1], line[1][1]],
                LINE_TYPE_COLOR_MAP[self.line_type_map[line_id].upper()],
                alpha=0.7
            )

            mp = midpoint(line)
            plt.text(
                mp[0],
                mp[1],
                int(self.line_length_map[line_id]),
                c="k",
                ha="center",
                va="center",
                fontsize=self.fontsize,
                weight="bold",
                rotation=angle(line),
                bbox=dict(boxstyle="square,pad=0.0", fc="white", ec="none")
            )

        plt.savefig(
            os.path.join(self.folder, "Length"),
            bbox_inches="tight",
            dpi=400
        )
        return

    def create_area_diagram(self):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis("off")
        plt.tight_layout()

        for line_id, line in self.lines.items():
            plt.plot(
                [line[0][0], line[1][0]],
                [line[0][1], line[1][1]],
                'k',
                alpha=0.4
            )

        for facet_id, facet in self.facets.items():
            center = facet.centroid
            if not facet.contains(center):
                center = facet.representative_point()

            plt.text(
                center.x,
                center.y,
                self.facet_area_map[facet_id],
                c="k",
                ha="center",
                va="center",
                fontsize=self.fontsize,
                weight="bold"
            )

        plt.savefig(
            os.path.join(self.folder, "Area"),
            bbox_inches="tight",
            dpi=400
        )
        return

    def create_pitch_diagram(self):
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        plt.axis("off")
        plt.tight_layout()

        for line_id, line in self.lines.items():
            plt.plot(
                [line[0][0], line[1][0]],
                [line[0][1], line[1][1]],
                'k',
                alpha=0.4
            )

        for facet_id, facet in self.facets.items():
            center = facet.centroid
            if not facet.contains(center):
                center = facet.representative_point()

            plt.text(
                center.x,
                center.y,
                int(self.facet_pitch_map[facet_id]),
                c="k",
                ha="center",
                va="center",
                fontsize=self.fontsize,
                weight="bold"
            )

        plt.savefig(
            os.path.join(self.folder, "Pitch"),
            bbox_inches="tight",
            dpi=400
        )
        return

    def create_report(self):

        roof_line_map = defaultdict(int)
        for line_id, length in self.line_length_map.items():
            roof_line_map[self.line_type_map[line_id].upper()] += int(length)

        pitch_area_map = defaultdict(int)
        for facet_id, area in self.facet_area_map.items():
            pitch_area_map[self.facet_pitch_map[facet_id]] += area

        measurements = [
            sum(self.facet_area_map.values()),
            len(self.facets),
            '{0:,.0f}'.format(max(pitch_area_map, key=pitch_area_map.get)) + "/12",
            roof_line_map["R"],
            roof_line_map["H"],
            roof_line_map["V"],
            roof_line_map["K"],
            roof_line_map["E"],
            pitch_area_map
        ]

        writer = ReportWriter(
            self.folder,
            ADDRESS,
            COMPANY,
            CONTACT,
            measurements
        )

        writer.create_report()

        return

