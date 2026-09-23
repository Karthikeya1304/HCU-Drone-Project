#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = '/tmp/drone_survey_output'

def load_csv(path):
    rows = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            rows.append([float(v) for v in row])
    return rows

flight_path = load_csv(f'{OUTPUT_DIR}/flight_path.csv')
cloud = load_csv(f'{OUTPUT_DIR}/cloud_map_export.csv')

fx = [p[0] for p in flight_path]
fy = [p[1] for p in flight_path]
cx = [p[0] for p in cloud]
cy = [p[1] for p in cloud]

known_trees = [
    ("Pine Tree_11", 10.0031, 4.69601), ("Pine Tree_12", 9.38057, 2.24489),
    ("Pine Tree_13", 8.95187, -2.43736), ("Pine Tree_14", 9.54099, -5.29967),
    ("Pine Tree_15", 8.56424, -7.36834), ("Pine Tree_16", 7.04987, -9.30259),
    ("Pine Tree_17", 4.64341, -9.56548), ("Pine Tree_18", 2.39497, -9.53658),
    ("Pine Tree_19", -0.978211, -9.12685), ("Pine Tree_20", -6.60386, -9.4906),
    ("Pine Tree_21", -11.7872, -9.60952), ("Pine Tree_19_1", -17.6272, 5.0484),
    ("Pine Tree_19_2", -18.7952, -4.79736), ("Pine Tree_19_5", 20.1207, 7.17708),
    ("Pine Tree_19_12", 13.1837, 8.1871),
]

fig, ax = plt.subplots(figsize=(12, 12))

ax.scatter(cx, cy, s=1, c='blue', alpha=0.3, label='RTAB-Map /cloud_map points (SLAM output)', zorder=2)
ax.plot(fx, fy, c='purple', linewidth=1.5, label='ACTUAL flight path (from PX4 telemetry)', zorder=3)

tx = [t[1] for t in known_trees]
ty = [t[2] for t in known_trees]
ax.scatter(tx, ty, s=250, marker='^', facecolors='none', edgecolors='green',
           linewidths=2, label='Known tree (ground truth)', zorder=4)
for name, x, y in known_trees:
    ax.annotate(name, (x, y), fontsize=7, xytext=(3, 3), textcoords='offset points')

ax.scatter([0], [0], c='red', marker='*', s=250, label='Home', zorder=5)

ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_title('Real Flight Path vs SLAM Point Cloud vs Ground Truth')
ax.legend(loc='upper right', fontsize=9)
ax.axis('equal')
ax.grid(True)

output_path = f'{OUTPUT_DIR}/full_comparison.png'
plt.savefig(output_path, dpi=150)
print(f'Saved to {output_path}')
