import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointCloud2, PointField
import numpy as np
import sensor_msgs_py.point_cloud2 as pc2

class AddTimeField(Node):
    def __init__(self):
        super().__init__('add_time_field')
        qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.pub = self.create_publisher(PointCloud2, '/lidar/points_timed', qos)
        self.sub = self.create_subscription(
            PointCloud2, '/lidar/points/points', self.cb, qos)

    def cb(self, msg: PointCloud2):
        points = list(pc2.read_points(
            msg, field_names=('x', 'y', 'z', 'intensity', 'ring'), skip_nans=False))
        points = [p for p in points if np.isfinite(p[0]) and np.isfinite(p[1]) and np.isfinite(p[2])]
        n = len(points)

        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1),
            PointField(name='ring', offset=16, datatype=PointField.UINT16, count=1),
            PointField(name='time', offset=20, datatype=PointField.FLOAT32, count=1),
        ]

        dtype = np.dtype([
            ('x', np.float32), ('y', np.float32), ('z', np.float32),
            ('intensity', np.float32), ('ring', np.uint16), ('_pad', np.uint16),
            ('time', np.float32)])

        arr = np.zeros(n, dtype=dtype)
        for i, p in enumerate(points):
            arr[i]['x'], arr[i]['y'], arr[i]['z'] = p[0], p[1], p[2]
            arr[i]['intensity'] = p[3]
            arr[i]['ring'] = int(p[4])
            arr[i]['time'] = 0.0

        out = PointCloud2()
        out.header = msg.header
        out.height = 1
        out.width = n
        out.is_dense = False
        out.is_bigendian = False
        out.fields = fields
        out.point_step = dtype.itemsize
        out.row_step = out.point_step * n
        out.data = arr.tobytes()
        self.pub.publish(out)

def main():
    rclpy.init()
    rclpy.spin(AddTimeField())

if __name__ == '__main__':
    main()
