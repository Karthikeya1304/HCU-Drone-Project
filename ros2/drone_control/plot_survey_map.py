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

path_points = load_csv(f'{OUTPUT_DIR}/flight_path.csv')
lidar_points = load_csv(f'{OUTPUT_DIR}/lidar_points.csv')

path_x = [p[0] for p in path_points]
path_y = [p[1] for p in path_points]
lidar_x = [p[0] for p in lidar_points]
lidar_y = [p[1] for p in lidar_points]

fig, ax = plt.subplots(figsize=(10, 10))

ax.scatter(lidar_x, lidar_y, s=0.5, c='red', alpha=0.15, label='Detected obstacles (lidar)')
ax.plot(path_x, path_y, c='blue', linewidth=1, label='Flight path', zorder=3)
ax.scatter([0], [0], c='green', marker='*', s=200, label='Home', zorder=4)

known_walls = [
    (5, 0, 1, 20),
    (-3, 5, 10, 1),
    (13, -10, 17, 1),
    (12, 0, 1, 20),
]
for cx, cy, sx, sy in known_walls:
    rect = patches.Rectangle(
        (cx - sx / 2, cy - sy / 2), sx, sy,
        linewidth=1.5, edgecolor='black', facecolor='none',
        linestyle='--', label='Known wall (ground truth)', zorder=2)
    ax.add_patch(rect)

handles, labels = ax.get_legend_handles_labels()
seen = set()
unique = [(h, l) for h, l in zip(handles, labels) if not (l in seen or seen.add(l))]
ax.legend(*zip(*unique))

ax.set_xlabel('X (m, NED)')
ax.set_ylabel('Y (m, NED)')
ax.set_title('Drone Area Survey Map (lidar points vs known walls)')
ax.axis('equal')
ax.grid(True)
ax.set_xlim(-15, 20)
ax.set_ylim(-15, 15)

output_path = f'{OUTPUT_DIR}/survey_map.png'
plt.savefig(output_path, dpi=150)
print(f'Map saved to {output_path}')
