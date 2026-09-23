#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt

CLOUD_CSV = '/tmp/drone_survey_output/cloud_map_export.csv'

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

# Ground-truth tree positions (all 30), copied directly from forest.sdf
# and gz model -p for the Pine Tree_19_* series.
known_trees = [
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
known_grasspatches = [
    (2.71574, -2.80395),
    (-12.2297, -2.64582),
    (2.62754, 12.1062),
    (-12.0931, 11.9289),
]

fig, ax = plt.subplots(figsize=(12, 12))

ax.scatter(px, py, s=1, c='blue', alpha=0.3, label='RTAB-Map /cloud_map points')

tx = [t[1] for t in known_trees]
ty = [t[2] for t in known_trees]
ax.scatter(tx, ty, s=300, marker='^', facecolors='none',
           edgecolors='green', linewidths=2, label='Known tree (ground truth)', zorder=5)
for name, x, y in known_trees:
    ax.annotate(name, (x, y), fontsize=6, xytext=(3, 3), textcoords='offset points')

gx = [g[0] for g in known_grasspatches]
gy = [g[1] for g in known_grasspatches]
ax.scatter(gx, gy, s=100, marker='s', facecolors='none',
           edgecolors='orange', linewidths=1.5, label='Known grasspatch center', zorder=4)

ax.scatter([0], [0], c='red', marker='*', s=250, label='Home', zorder=6)

ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_title('RTAB-Map Point Cloud vs Known Forest Layout (Full 30-Tree Ground Truth)')
ax.legend(loc='upper right', fontsize=8)
ax.axis('equal')
ax.grid(True)

output_path = '/tmp/drone_survey_output/cloud_vs_groundtruth_full.png'
plt.savefig(output_path, dpi=150)
print(f'Comparison plot saved to {output_path}')
