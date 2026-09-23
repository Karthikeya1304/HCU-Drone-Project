#!/usr/bin/env python3
path = "autonomous_control.py"

with open(path, "r") as f:
    content = f.read()

def replace_once(content, old, new, label):
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"ABORT: expected exactly 1 match for '{label}', found {n}. No changes written.")
    return content.replace(old, new)

# 1. add an altitude tolerance alongside position_tolerance
old_tol = "        self.position_tolerance = 0.3\n"
new_tol = old_tol + "        self.altitude_tolerance = 0.5  # meters, for real (not setpoint) climb confirmation\n"
content = replace_once(content, old_tol, new_tol, "position_tolerance")

# 2. gate the TAKEOFF -> SURVEY transition on actual measured altitude
old_takeoff = """        if self.flight_state == 'TAKEOFF':
            if self.setpoint_z > self.cruise_altitude:
                self.setpoint_z -= 0.02
            elif self.distance_xy(self.setpoint_x, self.setpoint_y) < self.position_tolerance:
                self.get_logger().info('Reached cruise altitude, starting area survey')
                self.flight_state = 'SURVEY'
"""
new_takeoff = """        if self.flight_state == 'TAKEOFF':
            if self.setpoint_z > self.cruise_altitude:
                self.setpoint_z -= 0.02
            if (self.has_position
                    and abs(self.local_position.z - self.cruise_altitude) < self.altitude_tolerance):
                self.get_logger().info(
                    f'Reached cruise altitude (actual z={self.local_position.z:.2f}), '
                    f'starting area survey')
                self.flight_state = 'SURVEY'
"""
content = replace_once(content, old_takeoff, new_takeoff, "TAKEOFF altitude-transition block")

with open(path, "w") as f:
    f.write(content)

print("Patch applied successfully to", path)
