import math
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy, qos_profile_sensor_data
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2 as pc2

DT = 0.05
ALT = -2.5          # NED: negative is up
DIST = 4.0          # metres along NED +x (north)
SPEED = 0.5         # m/s between survey waypoints
D_SLOW = 4.0        # m; start slowing when the nearest return in the travel direction is closer
D_STOP = 2.0        # m; stop advancing the setpoint at or below this
MIN_ALT = 1.5       # m; avoidance acts only above this altitude (ground is in the beam band lower down)
ELEV_MIN = -8.0     # degrees; lower beams hit the ground at hover height
ELEV_MAX = 15.0
MIN_RANGE = 0.5     # m; ignore returns from the drone itself
DETOUR_SIDE = 3.0  # m; sideways offset of the detour waypoint
MAX_LEAD = 1.5      # m; stop advancing the setpoint if it is further than this ahead of the drone


class Hop(Node):
    def __init__(self):
        super().__init__('hop_test')
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        self.p_mode = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', qos)
        self.p_sp = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos)
        self.p_cmd = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos)
        self.create_subscription(VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1',
                                 self.on_pos, qos_profile_sensor_data)
        self.create_subscription(PointCloud2, '/lidar/points/points', self.on_cloud, qos_profile_sensor_data)
        self.pos = None
        self.sectors = [float('inf')] * 8
        self.cloud_t = None
        self.sp = None
        self.yaw = 0.0
        self.ticks = 0
        self.phase = 0
        self.phase_t = 0.0
        self.landed_cmd = False
        self.done = False
        self.blocked_t = 0.0
        self.detours = 0
        self.wp_detours = 0
        self.detour_tgt = None
        self.last_dmin = float('inf')
        self.last_k = 0
        self.phases = [
            ('climb', (0.0, 0.0, ALT), 0.8),
            ('hold1', 5.0),
            ('wp1', (-3.5, -12.0, ALT), SPEED),
            ('wp2', (10.0, -12.0, ALT), SPEED),
            ('wp3', (16.0, 3.0, ALT), SPEED),
            ('wp4', (24.0, 2.0, ALT), SPEED),
            ('wp5', (28.0, 9.0, ALT), SPEED),
            ('wp6', (26.0, 14.0, ALT), SPEED),
            ('wp7', (14.0, 14.0, ALT), SPEED),
            ('wp8', (13.0, 6.0, ALT), SPEED),
            ('wp9', (3.0, 4.0, ALT), SPEED),
            ('wp10', (-4.0, 3.0, ALT), SPEED),
            ('home', (0.0, 0.0, ALT), SPEED),
            ('hold3', 5.0),
            ('land',),
        ]
        self.create_timer(DT, self.tick)

    def now_us(self):
        return int(self.get_clock().now().nanoseconds / 1000)

    def on_pos(self, m):
        self.pos = (m.x, m.y, m.z)
        self.heading = m.heading

    def on_cloud(self, msg):
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
        self.sectors = [float(v) for v in best]
        self.cloud_t = self.get_clock().now().nanoseconds / 1e9

    def avoid_scale(self, d):
        self.last_dmin = float('inf')
        if math.hypot(d[0], d[1]) < 0.05 or self.pos is None or -self.pos[2] < MIN_ALT:
            return 1.0
        now = self.get_clock().now().nanoseconds / 1e9
        if self.cloud_t is None or now - self.cloud_t > 1.0:
            if self.ticks % 20 == 0:
                self.get_logger().info('AVOID  no recent LiDAR data, holding')
            return 0.0
        az = self.heading - math.atan2(d[1], d[0])
        k = int(((math.degrees(az) + 22.5) % 360.0) // 45.0) % 8
        dmin = min(self.sectors[(k - 1) % 8], self.sectors[k], self.sectors[(k + 1) % 8])
        self.last_dmin = dmin
        self.last_k = k
        s = max(0.0, min(1.0, (dmin - D_STOP) / (D_SLOW - D_STOP)))
        if s < 1.0 and self.ticks % 20 == 0:
            self.get_logger().info('AVOID  nearest %.1f m  speed scale %.2f' % (dmin, s))
        return s

    def cmd(self, command, p1=0.0, p2=0.0):
        m = VehicleCommand()
        m.timestamp = self.now_us()
        m.command = command
        m.param1 = float(p1)
        m.param2 = float(p2)
        m.target_system = 1
        m.target_component = 1
        m.source_system = 1
        m.source_component = 1
        m.from_external = True
        self.p_cmd.publish(m)

    def land(self):
        if not self.landed_cmd:
            self.cmd(21)
            self.landed_cmd = True
            self.land_t = 0.0
            self.get_logger().info('LAND command sent')

    def tick(self):
        if self.landed_cmd:
            self.land_t += DT
            if self.land_t > 20.0:
                self.done = True
            return
        if self.pos is None:
            return
        if self.sp is None:
            self.sp = list(self.pos)
            self.yaw = self.heading
            self.get_logger().info('start position (NED): %s heading %.3f' % (self.pos, self.yaw))
        t = self.now_us()
        om = OffboardControlMode()
        om.timestamp = t
        om.position = True
        self.p_mode.publish(om)
        self.ticks += 1
        if self.ticks == 20:
            self.cmd(176, 1, 6)      # offboard
            self.cmd(400, 1)         # arm
            self.get_logger().info('offboard + arm sent')
        if self.ticks >= 40:
            self.advance()
        sp = TrajectorySetpoint()
        sp.timestamp = t
        sp.position = [float(v) for v in self.sp]
        sp.yaw = float(self.yaw)
        self.p_sp.publish(sp)
        if self.ticks % 20 == 0:
            self.get_logger().info('phase %s  sp=(%.2f, %.2f, %.2f)  pos=(%.2f, %.2f, %.2f)' % (
                self.phases[self.phase][0], *self.sp, *self.pos))

    def make_detour(self, d):
        if self.wp_detours >= 4:
            self.get_logger().info('DETOUR limit reached, holding')
            return
        n = math.hypot(d[0], d[1])
        ux, uy = d[0] / n, d[1] / n
        k = self.last_k
        s = self.sectors
        left = min(s[(k + 1) % 8], s[(k + 2) % 8])
        right = min(s[(k - 1) % 8], s[(k - 2) % 8])
        if max(left, right) < DETOUR_SIDE + 1.0:
            self.get_logger().info('DETOUR both sides tight (L %.1f R %.1f), holding' % (left, right))
            return
        sgn = 1.0 if left >= right else -1.0
        tgt = (self.sp[0] + sgn * uy * DETOUR_SIDE, self.sp[1] - sgn * ux * DETOUR_SIDE, ALT)
        self.detour_tgt = tgt
        self.detours += 1
        self.wp_detours += 1
        self.phase_t = 0.0
        self.get_logger().info('DETOUR %s  clear L %.1f R %.1f  via (%.2f, %.2f)' % ('left' if sgn > 0 else 'right', left, right, tgt[0], tgt[1]))

    def advance(self):
        ph = self.phases[self.phase]
        if ph[0] == 'land':
            self.land()
            return
        if len(ph) == 3:
            tgt, speed = ph[1], ph[2]
            if self.detour_tgt is not None:
                tgt = self.detour_tgt
            d = [tgt[i] - self.sp[i] for i in range(3)]
            n = math.sqrt(sum(v * v for v in d))
            track = 0.0 if math.dist(self.sp, self.pos) > MAX_LEAD else 1.0
            sc = self.avoid_scale(d)
            step = speed * DT * sc * track
            if sc < 0.05 and self.last_dmin <= D_STOP + 0.5 and track > 0:
                self.blocked_t += DT
                if self.blocked_t > 3.0:
                    self.blocked_t = 0.0
                    if self.detour_tgt is not None:
                        self.detour_tgt = None
                        self.get_logger().info('DETOUR blocked, abandoned')
                    else:
                        self.make_detour(d)
                    return
            else:
                self.blocked_t = 0.0
            if n <= step or (self.detour_tgt is not None and n < 0.5):
                self.sp = list(tgt)
                if self.detour_tgt is not None:
                    self.detour_tgt = None
                else:
                    self.phase += 1
                    self.wp_detours = 0
                self.phase_t = 0.0
            else:
                self.sp = [self.sp[i] + d[i] / n * step for i in range(3)]
        else:
            self.phase_t += DT
            if self.phase_t >= ph[1]:
                self.phase += 1
                self.phase_t = 0.0


def main():
    rclpy.init()
    node = Hop()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        pass
    if rclpy.ok():
        node.land()
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.05)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


main()
