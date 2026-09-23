#!/usr/bin/env python3
"""Subscribe to /cloud_map once, save all points (x,y,z) to CSV, then exit."""
import sys
import csv

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2


class CloudExporter(Node):
    def __init__(self, output_path):
        super().__init__('cloud_map_exporter')
        self.output_path = output_path
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        self.sub = self.create_subscription(
            PointCloud2, '/cloud_map', self.callback, qos_profile)
        self.get_logger().info('Waiting for one message on /cloud_map ...')

    def callback(self, msg):
        points = list(pc2.read_points(msg, field_names=('x', 'y', 'z'), skip_nans=True))
        with open(self.output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['x', 'y', 'z'])
            for p in points:
                writer.writerow([p[0], p[1], p[2]])
        self.get_logger().info(f'Saved {len(points)} points to {self.output_path}')
        rclpy.shutdown()


def main():
    output_path = '/tmp/drone_survey_output/cloud_map_export.csv'
    rclpy.init()
    node = CloudExporter(output_path)
    rclpy.spin(node)


if __name__ == '__main__':
    main()
