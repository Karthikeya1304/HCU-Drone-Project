import os
import sys
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

from px4_msgs.msg import VehicleLocalPosition


class TFBroadcasterNode(Node):
    def __init__(self):
        super().__init__('tf_broadcaster_node')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.local_position_subscriber = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1',
            self.local_position_callback, qos_profile)

        self.tf_broadcaster = TransformBroadcaster(self)

        # Fixed offset from base_link to the lidar's mount point, taken
        # directly from the x500_lidar_2d model.sdf pose (.12 0 .26, no
        # rotation). Published once per cycle as a static-style transform.
        self.lidar_offset_x = 0.12
        self.lidar_offset_y = 0.03
        self.lidar_offset_z = 0.242

        self.timer = self.create_timer(0.05, self.publish_static_lidar_tf)  # 20Hz

        self.get_logger().info('TF broadcaster node started (odom->base_link->camera_link)')

    def local_position_callback(self, msg):
        # NED (PX4) -> ENU-ish ROS convention: for a 2D top-down map this is
        # a straightforward axis relabeling. x_ros = x_ned (north/forward),
        # y_ros = -y_ned (since NED's east is ROS's -y under this simple
        # convention), z_ros = -z_ned (NED down -> ROS up).
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        t.transform.translation.x = float(msg.x)
        t.transform.translation.y = float(-msg.y)
        t.transform.translation.z = float(-msg.z)

        # Yaw-only orientation (heading), converted to a quaternion.
        yaw = -msg.heading  # matching the y-flip above
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(yaw / 2.0)
        t.transform.rotation.w = math.cos(yaw / 2.0)

        self.tf_broadcaster.sendTransform(t)

    def publish_static_lidar_tf(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'camera_link'
        t.transform.translation.x = self.lidar_offset_x
        t.transform.translation.y = self.lidar_offset_y
        t.transform.translation.z = self.lidar_offset_z
        # Camera is pitched 0.6 rad downward in model.sdf (matches
        # x500_depth's include pose) — must match here or RTAB-Map
        # places points using the wrong camera orientation.
        import math
        camera_pitch = 0.6
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = math.sin(camera_pitch / 2.0)
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = math.cos(camera_pitch / 2.0)
        self.tf_broadcaster.sendTransform(t)


LOCK_FILE = '/tmp/tf_broadcaster_active.lock'

def main(args=None):
    if os.path.exists(LOCK_FILE):
        print(f'ERROR: {LOCK_FILE} already exists. Another tf_broadcaster '
              f'node appears to be running already. Refusing to start.')
        sys.exit(1)

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

    rclpy.init(args=args)
    node = TFBroadcasterNode()
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
