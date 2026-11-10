#!/usr/bin/env python3
# Read-only monitor: nearest LiDAR return in eight 45-degree sectors around the drone.
# Frame lidar_sensor_link: x forward, y left. Does not talk to PX4.
import math
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2 as pc2

ELEV_MIN = -8.0    # degrees; lower beams hit the ground at hover height
ELEV_MAX = 15.0
MIN_RANGE = 0.5    # metres; ignore returns from the drone itself
PERIOD = 0.5       # seconds between printed lines
NAMES = ['F', 'FL', 'L', 'BL', 'B', 'BR', 'R', 'FR']


class Sectors(Node):
    def __init__(self):
        super().__init__('lidar_sectors')
        self.last = 0.0
        self.create_subscription(PointCloud2, '/lidar/points/points', self.cb, qos_profile_sensor_data)

    def cb(self, msg):
        now = time.time()
        if now - self.last < PERIOD:
            return
        self.last = now
        a = pc2.read_points(msg, field_names=('x', 'y', 'z'), skip_nans=True)
        x = np.asarray(a['x'], dtype=float)
        y = np.asarray(a['y'], dtype=float)
        z = np.asarray(a['z'], dtype=float)
        rng = np.sqrt(x * x + y * y + z * z)
        elev = np.degrees(np.arctan2(z, np.hypot(x, y)))
        ok = np.isfinite(rng) & (rng >= MIN_RANGE) & (elev >= ELEV_MIN) & (elev <= ELEV_MAX)
        az = np.degrees(np.arctan2(y, x))
        sec = (((az + 22.5) % 360.0) // 45.0).astype(int) % 8
        best = np.full(8, np.inf)
        np.minimum.at(best, sec[ok], rng[ok])
        self.get_logger().info(' '.join(
            '%s %s' % (n, '--' if not math.isfinite(d) else '%.1f' % d) for n, d in zip(NAMES, best)))


def main():
    rclpy.init()
    node = Sectors()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


main()
