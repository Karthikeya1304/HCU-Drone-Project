#!/usr/bin/env python3
path = "autonomous_control.py"
with open(path, "r") as f:
    content = f.read()

def replace_once(content, old, new, label):
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"ABORT: expected exactly 1 match for '{label}', found {n}.")
    return content.replace(old, new)

old = """    def compute_min_forward_distance(self, target_x, target_y, setpoint_x, setpoint_y,
                                      cone_half_angle_deg=25.0,
                                      min_range=0.3,
                                      z_band=(-1.0, 1.0)):"""
new = """    def compute_min_forward_distance(self, target_x, target_y, setpoint_x, setpoint_y,
                                      cone_half_angle_deg=25.0,
                                      min_range=0.5,  # was 0.3; raised to filter self-hits on the airframe (~0.30-0.37m)
                                      z_band=(-1.0, 1.0)):"""
content = replace_once(content, old, new, "min_range default")

with open(path, "w") as f:
    f.write(content)
print("min_range patch applied")
