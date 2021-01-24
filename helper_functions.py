import numpy as np
import xlsxwriter

get_letter_id = xlsxwriter.utility.xl_col_to_name

def distance(p1, p2):
    return np.sqrt(sum([(v1-v2)**2 for v1, v2 in zip(p1, p2)]))

def midpoint(line):
    return [(line[0][0] + line[1][0]) / 2, (line[0][1] + line[1][1]) / 2]

def angle(line):
    return np.degrees(np.arctan2(
        line[1][1] - line[0][1],
        line[1][0] - line[0][0]
    ))

def unit_vector(vector):
    return vector / np.linalg.norm(vector)

def angle_between(line1, line2):
    v1 = (line1[1][0] - line1[0][0], line1[1][1] - line1[0][1])
    v2 = (line2[1][0] - line2[0][0], line2[1][1] - line2[0][1])

    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)

    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

def closest_sample(x, X, Y):
    ret = None
    min_dist = float("inf")

    for _x, _y in zip(X.ravel(), Y):
        dist = abs(x - _x)
        if dist < min_dist:
            ret = (_x, _y)
            min_dist = dist

    return ret

def predict(x, _x, _y, slope):
    return _y + (x - _x) * slope
