#!/usr/bin/env python3
"""Compute nearest RTAB-Map cloud point distance to each of the 30 known trees (2D, x/y)."""
import csv
import math

CLOUD_CSV = '/tmp/drone_survey_output/cloud_map_export.csv'

known_trees = [
    # Original 11
    ("Pine Tree_11", 10.0031, 4.69601),
    ("Pine Tree_12", 9.38057, 2.24489),
    ("Pine Tree_13", 8.95187, -2.43736),
    ("Pine Tree_14", 9.54099, -5.29967),
    ("Pine Tree_15", 8.56424, -7.36834),
    ("Pine Tree_16", 7.04987, -9.30259),
    ("Pine Tree_17", 4.64341, -9.56548),
    ("Pine Tree_18", 2.39497, -9.53658),
    ("Pine Tree_19", -0.978211, -9.12685),
    ("Pine Tree_20", -6.60386, -9.4906),
    ("Pine Tree_21", -11.7872, -9.60952),
    # Pine Tree_19_* series (19 trees), poses from `gz model -m <name> -p`
    ("Pine Tree_19_1", -17.6272, 5.0484),
    ("Pine Tree_19_2", -18.7952, -4.79736),
    ("Pine Tree_19_3", -18.6571, 13.5589),
    ("Pine Tree_19_4", -13.7446, 18.3234),
    ("Pine Tree_19_5", 20.1207, 7.17708),
    ("Pine Tree_19_6", -3.71164, 21.6207),
    ("Pine Tree_19_7", -7.45162, 17.9798),
    ("Pine Tree_19_8", -3.88653, 25.1364),
    ("Pine Tree_19_9", -4.09489, 29.0163),
    ("Pine Tree_19_10", 21.3008, 12.6766),
    ("Pine Tree_19_11", 20.1494, 19.5156),
    ("Pine Tree_19_12", 13.1837, 8.1871),
    ("Pine Tree_19_13", 20.0557, 23.4209),
    ("Pine Tree_19_14", 20.8101, 27.2073),
    ("Pine Tree_19_15", 18.508, 32.5244),
    ("Pine Tree_19_16", 12.3362, 33.1989),
    ("Pine Tree_19_17", 7.92068, 33.4253),
    ("Pine Tree_19_18", 4.19562, 33.3749),
    ("Pine Tree_19_19", -3.1997, 32.8927),
]

def load_csv(path):
    rows = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            rows.append([float(v) for v in row])
    return rows

points = load_csv(CLOUD_CSV)
px = [p[0] for p in points]
py = [p[1] for p in points]

print(f"Loaded {len(points)} cloud points")
print(f"Comparing against {len(known_trees)} known trees")
print(f"{'Tree':<16} {'Nearest dist (m)':>18}")
print("-" * 36)

distances = []
for name, tx, ty in known_trees:
    min_d = min(math.hypot(x - tx, y - ty) for x, y in zip(px, py))
    distances.append(min_d)
    print(f"{name:<16} {min_d:>18.3f}")

avg = sum(distances) / len(distances)
print("-" * 36)
print(f"{'AVERAGE':<16} {avg:>18.3f}")
print(f"{'MIN':<16} {min(distances):>18.3f}")
print(f"{'MAX':<16} {max(distances):>18.3f}")
