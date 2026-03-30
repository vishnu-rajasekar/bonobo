from math import atan2
from math import cos
from math import sin
from math import sqrt


def add(a, b):
    return [float(a[0]) + float(b[0]), float(a[1]) + float(b[1]), float(a[2]) + float(b[2])]


def sub(a, b):
    return [float(a[0]) - float(b[0]), float(a[1]) - float(b[1]), float(a[2]) - float(b[2])]


def scale(vec, factor):
    return [float(vec[0]) * float(factor), float(vec[1]) * float(factor), float(vec[2]) * float(factor)]


def dot(a, b):
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])


def cross_z(a, b):
    return float(a[0]) * float(b[1]) - float(a[1]) * float(b[0])


def magnitude(vec):
    return sqrt(dot(vec, vec))


def unit(vec, tolerance=1e-12):
    mag = magnitude(vec)
    if mag <= tolerance:
        return None
    return [float(vec[0]) / mag, float(vec[1]) / mag, float(vec[2]) / mag]


def distance(a, b):
    return magnitude(sub(a, b))


def rotate_z(vec, theta):
    c = cos(theta)
    s = sin(theta)
    return [
        float(vec[0]) * c - float(vec[1]) * s,
        float(vec[0]) * s + float(vec[1]) * c,
        float(vec[2]),
    ]


def angle_xy(vec):
    return atan2(float(vec[1]), float(vec[0]))


def project_point_to_segment(point, segment_a, segment_b, tolerance=1e-12):
    ab = sub(segment_b, segment_a)
    ap = sub(point, segment_a)
    denom = dot(ab, ab)
    if denom <= tolerance:
        return [float(segment_a[0]), float(segment_a[1]), float(segment_a[2])]
    t = max(0.0, min(1.0, dot(ap, ab) / denom))
    return add(segment_a, scale(ab, t))


def directed_ray_intersection(point_a, dir_a, point_b, dir_b, eps=1e-9):
    det = cross_z(dir_a, dir_b)
    if abs(det) < eps:
        return None
    delta = sub(point_b, point_a)
    ta = cross_z(delta, dir_b) / det
    tb = cross_z(delta, dir_a) / det
    if ta < 0.0 or tb < 0.0:
        return None
    return add(point_a, scale(dir_a, ta))


def bidirected_ray_intersection(point_a, dir_a, point_b, dir_b, eps=1e-9):
    det = cross_z(dir_a, dir_b)
    if abs(det) < eps:
        return None
    delta = sub(point_b, point_a)
    ta = cross_z(delta, dir_b) / det
    return add(point_a, scale(dir_a, ta))


def inside_rect(point, bounds):
    return bounds["min"][0] <= point[0] <= bounds["max"][0] and bounds["min"][1] <= point[1] <= bounds["max"][1]

