import csv
import math
import os
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from px4_msgs.msg import (
    OffboardControlMode,
    TrajectorySetpoint,
    VehicleCommand,
    VehicleStatus,
    VehicleLocalPosition,
)
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py.point_cloud2 import read_points_numpy
from rclpy.qos import qos_profile_sensor_data
import numpy as np


def generate_lawnmower_grid(x_min, x_max, y_min, y_max, lane_spacing):
    waypoints = []
    y = y_min
    going_right = True
    while y <= y_max + 1e-6:
        if going_right:
            waypoints.append((x_min, y))
            waypoints.append((x_max, y))
        else:
            waypoints.append((x_max, y))
            waypoints.append((x_min, y))
        going_right = not going_right
        y += lane_spacing
    return waypoints


class AutonomousControlNode(Node):
    def __init__(self):
        super().__init__('autonomous_control_node')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_publisher = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', qos_profile)

        self.vehicle_status_subscriber = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status_v1',
            self.vehicle_status_callback, qos_profile)
        self.local_position_subscriber = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1',
            self.local_position_callback, qos_profile)

        self.lidar_subscriber = self.create_subscription(
            LaserScan,
            '/world/forest/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan',
            self.lidar_callback, 10)

        self.cloud_subscriber = self.create_subscription(
            PointCloud2,
            '/lidar/points',
            self.cloud_callback, qos_profile_sensor_data)

        self.vehicle_status = VehicleStatus()
        self.local_position = VehicleLocalPosition()
        self.has_position = False
        self.latest_scan = None
        self.latest_cloud = None

        self.min_forward_distance = float('inf')
        self.obstacle_safety_threshold = 1.2
        self.obstacle_clear_threshold = 1.8
        self.obstacle_blocking = False
        self.obstacle_block_counter = 0
        self.obstacle_giveup_cycles = 30

        self.cruise_altitude = -12.0
        self.home_xy = (0.0, 0.0)

        # Pulled x_max back to 3.5 (from 4.0): wall face is at x=4.5, so this
        # gives a full 1m clearance margin - no waypoint should trigger the
        # obstacle stop anymore, giving genuinely complete grid coverage.
        self.survey_waypoints = generate_lawnmower_grid(
            x_min=-21, x_max=24, y_min=-36, y_max=12, lane_spacing=3.0)
        self.waypoint_index = 0
        self.position_tolerance = 0.3
        self.altitude_tolerance = 0.5  # meters, for real (not setpoint) climb confirmation

        self.max_step_xy = 0.05

        self.setpoint_x = 0.0
        self.setpoint_y = 0.0
        self.setpoint_z = 0.0
        self.setpoint_yaw = 0.0

        self.offboard_setpoint_counter = 0
        self.flight_state = 'TAKEOFF'
        self.final_land_counter = 0
        self.final_land_timeout_cycles = 100  # 10s at 10Hz before force-disarm

        # --- Mapping data ---
        self.flight_path = []      # list of (x, y, z, timestamp)
        self.lidar_points = []     # list of (world_x, world_y) obstacle hits
        self.record_counter = 0
        self.record_every_n_cycles = 5   # throttle lidar recording (~2 Hz at 10Hz timer)
        self.output_dir = '/tmp/drone_survey_output'
        os.makedirs(self.output_dir, exist_ok=True)

        self.timer = self.create_timer(0.1, self.timer_callback)

        self.get_logger().info(
            f'Autonomous control node started (area survey mission, '
            f'{len(self.survey_waypoints)} waypoints, incremental setpoints, '
            f'lidar obstacle avoidance + map recording to {self.output_dir})')

    def vehicle_status_callback(self, msg):
        self.vehicle_status = msg

    def local_position_callback(self, msg):
        self.local_position = msg
        self.has_position = True

    def lidar_callback(self, msg):
        self.latest_scan = msg
        n = len(msg.ranges)
        if n == 0:
            return
        center = n // 2
        span = max(1, n // 6)
        window = msg.ranges[center - span: center + span]
        valid = [r for r in window if r > 0.0 and not math.isinf(r) and not math.isnan(r)]
        self.min_forward_distance = min(valid) if valid else float('inf')

    def cloud_callback(self, msg):
        self.latest_cloud = msg

    def compute_min_forward_distance(self, target_x, target_y, setpoint_x, setpoint_y,
                                      cone_half_angle_deg=25.0,
                                      min_range=0.5,  # was 0.3; raised to filter self-hits on the airframe (~0.30-0.37m)
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
        idx = np.argmin(dist[mask])
        cx, cy, cz = x[mask][idx], y[mask][idx], z[mask][idx]
        self.get_logger().info(
            f'[DEBUG] closest obstacle point (sensor frame): '
            f'x={cx:.2f} y={cy:.2f} z={cz:.2f} dist={dist[mask][idx]:.2f}')
        return float(np.min(dist[mask]))

    def record_lidar_points(self):
        """Convert the latest full scan to world-frame (x, y) points using
        the drone's current position and heading, for later map plotting."""
        if self.latest_scan is None or not self.has_position:
            return
        msg = self.latest_scan
        drone_x = self.local_position.x
        drone_y = self.local_position.y
        drone_yaw = self.local_position.heading  # radians

        max_recording_range = 8.0  # meters; farther readings amplify small
                                      # heading errors into large position
                                      # errors, so only keep close, reliable hits
        angle = msg.angle_min
        for r in msg.ranges:
            if 0.0 < r <= max_recording_range and not math.isnan(r):
                world_angle = angle + drone_yaw
                px = drone_x + r * math.cos(world_angle)
                py = drone_y + r * math.sin(world_angle)
                self.lidar_points.append((px, py))
            angle += msg.angle_increment

    def publish_offboard_control_mode(self):
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher.publish(msg)

    def publish_trajectory_setpoint(self):
        msg = TrajectorySetpoint()
        msg.position = [self.setpoint_x, self.setpoint_y, self.setpoint_z]
        msg.yaw = self.setpoint_yaw
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.trajectory_setpoint_publisher.publish(msg)

    def publish_vehicle_command(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = param1
        msg.param2 = param2
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)

    def distance_xy(self, x, y):
        dx = self.local_position.x - x
        dy = self.local_position.y - y
        return math.sqrt(dx * dx + dy * dy)

    def step_setpoint_toward(self, target_x, target_y):
        dx = target_x - self.setpoint_x
        dy = target_y - self.setpoint_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist <= self.max_step_xy or dist == 0.0:
            self.setpoint_x = target_x
            self.setpoint_y = target_y
        else:
            self.setpoint_x += dx / dist * self.max_step_xy
            self.setpoint_y += dy / dist * self.max_step_xy

    def send_arm_and_offboard(self):
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)

    def save_map_files(self):
        path_file = os.path.join(self.output_dir, 'flight_path.csv')
        with open(path_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['x', 'y', 'z'])
            writer.writerows(self.flight_path)

        points_file = os.path.join(self.output_dir, 'lidar_points.csv')
        with open(points_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['x', 'y'])
            writer.writerows(self.lidar_points)

        self.get_logger().info(
            f'Saved {len(self.flight_path)} path points to {path_file} and '
            f'{len(self.lidar_points)} lidar points to {points_file}')

    def timer_callback(self):
        self.publish_offboard_control_mode()
        self.publish_trajectory_setpoint()

        if self.has_position and self.flight_state not in ('TAKEOFF',):
            self.flight_path.append(
                (round(self.local_position.x, 3),
                 round(self.local_position.y, 3),
                 round(self.local_position.z, 3)))

        self.record_counter += 1
        if self.record_counter >= self.record_every_n_cycles:
            self.record_counter = 0
            self.record_lidar_points()

        if self.flight_state == 'TAKEOFF' and self.offboard_setpoint_counter <= 10:
            if self.offboard_setpoint_counter < 11:
                self.offboard_setpoint_counter += 1
            if self.offboard_setpoint_counter == 10:
                if self.has_position:
                    self.setpoint_x = self.local_position.x
                    self.setpoint_y = self.local_position.y
                self.send_arm_and_offboard()
                self.get_logger().info('Sent initial Offboard mode + Arm commands')
                self.arm_verify_counter = 0
            return

        # Verify PX4 actually armed, rather than blindly trusting our own
        # counter. If arming was rejected (e.g. a preflight check failure),
        # this catches it instead of silently "flying" a mission that never
        # physically left the ground.
        if self.offboard_setpoint_counter == 11 and self.flight_state == 'TAKEOFF':
            self.arm_verify_counter = getattr(self, 'arm_verify_counter', 0) + 1
            if self.vehicle_status.arming_state == VehicleStatus.ARMING_STATE_ARMED:
                self.offboard_setpoint_counter = 12  # confirmed armed, proceed normally
            elif self.arm_verify_counter >= 30:  # 3s at 10Hz
                self.get_logger().error(
                    'Arm command was not accepted by PX4 after 3s (likely a preflight '
                    'check failure - check PX4 console). Aborting mission.')
                self.flight_state = 'DONE'
            return

        if self.flight_state == 'TAKEOFF':
            if self.setpoint_z > self.cruise_altitude:
                self.setpoint_z -= 0.02
            if (self.has_position
                    and abs(self.local_position.z - self.cruise_altitude) < self.altitude_tolerance):
                self.get_logger().info(
                    f'Reached cruise altitude (actual z={self.local_position.z:.2f}), '
                    f'starting area survey')
                self.flight_state = 'SURVEY'

        elif self.flight_state == 'SURVEY':
            if self.waypoint_index >= len(self.survey_waypoints):
                self.get_logger().info('Survey complete, returning home')
                self.flight_state = 'RETURN_HOME'
                return

            target_x, target_y = self.survey_waypoints[self.waypoint_index]

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

            if self.obstacle_blocking:
                self.setpoint_x = self.local_position.x
                self.setpoint_y = self.local_position.y
                return

            self.step_setpoint_toward(target_x, target_y)
            self.setpoint_z = self.cruise_altitude

            if self.distance_xy(target_x, target_y) < self.position_tolerance:
                self.get_logger().info(
                    f'Reached survey waypoint {self.waypoint_index + 1}/{len(self.survey_waypoints)} '
                    f'at ({target_x:.1f}, {target_y:.1f})')
                self.waypoint_index += 1

        elif self.flight_state == 'RETURN_HOME':
            home_x, home_y = self.home_xy
            self.step_setpoint_toward(home_x, home_y)
            self.setpoint_z = self.cruise_altitude

            if self.distance_xy(home_x, home_y) < self.position_tolerance:
                self.get_logger().info('Arrived home, landing')
                self.flight_state = 'FINAL_LAND'
                self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)

        elif self.flight_state == 'FINAL_LAND':
            if self.vehicle_status.arming_state == VehicleStatus.ARMING_STATE_DISARMED:
                self.get_logger().info('Vehicle disarmed. Area survey mission complete.')
                self.save_map_files()
                self.flight_state = 'DONE'
            else:
                self.final_land_counter += 1
                if self.final_land_counter == self.final_land_timeout_cycles:
                    self.get_logger().warn(
                        'PX4 landed-state detector appears stuck (known SITL quirk); '
                        'force-disarming after timeout to complete the mission safely.')
                    self.publish_vehicle_command(
                        VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
                        param1=0.0, param2=21196.0)

        elif self.flight_state == 'DONE':
            pass


LOCK_FILE = '/tmp/drone_control_active.lock'


def main(args=None):
    if os.path.exists(LOCK_FILE):
        print(f"ERROR: {LOCK_FILE} already exists. Another control node "
              f"appears to be running already. Refusing to start.")
        sys.exit(1)

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

    rclpy.init(args=args)
    node = AutonomousControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


if __name__ == '__main__':
    main()
