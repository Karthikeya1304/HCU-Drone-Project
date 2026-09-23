#!/usr/bin/env python3
path = "autonomous_control.py"

with open(path, "r") as f:
    content = f.read()

def replace_once(content, old, new, label):
    n = content.count(old)
    if n != 1:
        raise SystemExit(f"ABORT: expected exactly 1 match for '{label}', found {n}. "
                          f"File may have changed since last dump -- no changes written.")
    return content.replace(old, new)

# 1. imports
old_import = "from sensor_msgs.msg import LaserScan"
new_import = (
    "from sensor_msgs.msg import LaserScan, PointCloud2\n"
    "from sensor_msgs_py.point_cloud2 import read_points_numpy\n"
    "from rclpy.qos import qos_profile_sensor_data\n"
    "import numpy as np"
)
content = replace_once(content, old_import, new_import, "imports")

# 2. add cloud subscriber after the existing lidar_subscriber
old_sub = (
    "        self.lidar_subscriber = self.create_subscription(\n"
    "            LaserScan,\n"
    "            '/world/forest/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan',\n"
    "            self.lidar_callback, 10)\n"
)
new_sub = old_sub + (
    "\n"
    "        self.cloud_subscriber = self.create_subscription(\n"
    "            PointCloud2,\n"
    "            '/lidar/points',\n"
    "            self.cloud_callback, qos_profile_sensor_data)\n"
)
content = replace_once(content, old_sub, new_sub, "subscriber block")

# 3. add latest_cloud attribute
old_attr = "        self.latest_scan = None\n"
new_attr = old_attr + "        self.latest_cloud = None\n"
content = replace_once(content, old_attr, new_attr, "latest_scan attribute")

# 4. add cloud_callback + compute_min_forward_distance right after lidar_callback
old_lidar_cb = (
    "    def lidar_callback(self, msg):\n"
    "        self.latest_scan = msg\n"
    "        n = len(msg.ranges)\n"
    "        if n == 0:\n"
    "            return\n"
    "        center = n // 2\n"
    "        span = max(1, n // 6)\n"
    "        window = msg.ranges[center - span: center + span]\n"
    "        valid = [r for r in window if r > 0.0 and not math.isinf(r) and not math.isnan(r)]\n"
    "        self.min_forward_distance = min(valid) if valid else float('inf')\n"
)
new_block = old_lidar_cb + '''
    def cloud_callback(self, msg):
        self.latest_cloud = msg

    def compute_min_forward_distance(self, target_x, target_y, setpoint_x, setpoint_y,
                                      cone_half_angle_deg=25.0,
                                      min_range=0.3,
                                      z_band=(-1.0, 1.0)):
        """Min obstacle distance within a cone pointed at the current
        target (target_x, target_y), from current position
        (setpoint_x, setpoint_y). Direction-agnostic -- replaces the old
        fixed +X-only sensor-facing check."""
        if self.latest_cloud is None:
            return float('inf')

        pts = read_points_numpy(self.latest_cloud, field_names=('x', 'y', 'z'), skip_nans=True)
        if pts.size == 0:
            return float('inf')

        x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
        dist = np.hypot(x, y)
        range_mask = dist > min_range
        height_mask = (z > z_band[0]) & (z < z_band[1])

        angle_to_target = math.atan2(target_y - setpoint_y, target_x - setpoint_x)
        point_angle = np.arctan2(y, x)
        angle_diff = np.abs(np.arctan2(np.sin(point_angle - angle_to_target),
                                        np.cos(point_angle - angle_to_target)))
        cone_mask = angle_diff <= math.radians(cone_half_angle_deg)

        mask = range_mask & height_mask & cone_mask
        if not np.any(mask):
            return float('inf')
        return float(np.min(dist[mask]))
'''
content = replace_once(content, old_lidar_cb, new_block, "lidar_callback method")

# 5. replace the SURVEY-state obstacle check to use the 3D cone distance
old_survey = '''            target_x, target_y = self.survey_waypoints[self.waypoint_index]

            moving_toward_sensor_facing = (target_x - self.setpoint_x) > 0.05

            if moving_toward_sensor_facing and self.min_forward_distance < self.obstacle_safety_threshold:
                if not self.obstacle_blocking:
                    self.obstacle_blocking = True
                    self.obstacle_block_counter = 0
                    self.get_logger().warn(
                        f'Obstacle detected at {self.min_forward_distance:.2f}m, '
                        f'holding before waypoint {self.waypoint_index + 1}/{len(self.survey_waypoints)}')
                self.obstacle_block_counter += 1
                self.setpoint_x = self.local_position.x
                self.setpoint_y = self.local_position.y

                if self.obstacle_block_counter >= self.obstacle_giveup_cycles:
                    self.get_logger().warn(
                        f'Skipping blocked waypoint {self.waypoint_index + 1}, continuing survey')
                    self.obstacle_blocking = False
                    self.waypoint_index += 1
                return

            if self.obstacle_blocking and self.min_forward_distance > self.obstacle_clear_threshold:
                self.obstacle_blocking = False
                self.get_logger().info('Path clear, resuming survey')
'''
new_survey = '''            target_x, target_y = self.survey_waypoints[self.waypoint_index]

            min_forward_distance_3d = self.compute_min_forward_distance(
                target_x, target_y, self.setpoint_x, self.setpoint_y)

            if min_forward_distance_3d < self.obstacle_safety_threshold:
                if not self.obstacle_blocking:
                    self.obstacle_blocking = True
                    self.obstacle_block_counter = 0
                    self.get_logger().warn(
                        f'Obstacle detected at {min_forward_distance_3d:.2f}m, '
                        f'holding before waypoint {self.waypoint_index + 1}/{len(self.survey_waypoints)}')
                self.obstacle_block_counter += 1
                self.setpoint_x = self.local_position.x
                self.setpoint_y = self.local_position.y

                if self.obstacle_block_counter >= self.obstacle_giveup_cycles:
                    self.get_logger().warn(
                        f'Skipping blocked waypoint {self.waypoint_index + 1}, continuing survey')
                    self.obstacle_blocking = False
                    self.waypoint_index += 1
                return

            if self.obstacle_blocking and min_forward_distance_3d > self.obstacle_clear_threshold:
                self.obstacle_blocking = False
                self.get_logger().info('Path clear, resuming survey')
'''
content = replace_once(content, old_survey, new_survey, "SURVEY obstacle-check block")

with open(path, "w") as f:
    f.write(content)

print("Patch applied successfully to", path)
