#!/usr/bin/env python3
path = "autonomous_control.py"
with open(path, "r") as f:
    content = f.read()

def replace_once(content, old, new, label):
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"ABORT: expected exactly 1 match for '{label}', found {n}.")
    return content.replace(old, new)

old = """        mask = range_mask & height_mask & cone_mask
        if not np.any(mask):
            return float('inf')
        return float(np.min(dist[mask]))"""
new = """        mask = range_mask & height_mask & cone_mask
        if not np.any(mask):
            return float('inf')
        idx = np.argmin(dist[mask])
        cx, cy, cz = x[mask][idx], y[mask][idx], z[mask][idx]
        self.get_logger().info(
            f'[DEBUG] closest obstacle point (sensor frame): '
            f'x={cx:.2f} y={cy:.2f} z={cz:.2f} dist={dist[mask][idx]:.2f}')
        return float(np.min(dist[mask]))"""
content = replace_once(content, old, new, "compute_min_forward_distance return")

with open(path, "w") as f:
    f.write(content)
print("Debug patch applied")
