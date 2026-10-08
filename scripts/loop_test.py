import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy, qos_profile_sensor_data
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition

DT = 0.05
ALT = -2.5          # NED: negative is up
DIST = 4.0          # metres along NED +x (north)


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
        self.pos = None
        self.sp = None
        self.yaw = 0.0
        self.ticks = 0
        self.phase = 0
        self.phase_t = 0.0
        self.landed_cmd = False
        self.done = False
        self.phases = [
            ('climb', (0.0, 0.0, ALT), 0.8),
            ('hold1', 5.0),
            ('north', (DIST, 0.0, ALT), 0.5),
            ('hold2', 4.0),
            ('east', (DIST, DIST, ALT), 0.5),
            ('hold3', 4.0),
            ('south', (0.0, DIST, ALT), 0.5),
            ('hold4', 4.0),
            ('west', (0.0, 0.0, ALT), 0.5),
            ('hold5', 5.0),
            ('land',),
        ]
        self.create_timer(DT, self.tick)

    def now_us(self):
        return int(self.get_clock().now().nanoseconds / 1000)

    def on_pos(self, m):
        self.pos = (m.x, m.y, m.z)
        self.heading = m.heading

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

    def advance(self):
        ph = self.phases[self.phase]
        if ph[0] == 'land':
            self.land()
            return
        if len(ph) == 3:
            tgt, speed = ph[1], ph[2]
            d = [tgt[i] - self.sp[i] for i in range(3)]
            n = math.sqrt(sum(v * v for v in d))
            step = speed * DT
            if n <= step:
                self.sp = list(tgt)
                self.phase += 1
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
    node.land()
    for _ in range(10):
        rclpy.spin_once(node, timeout_sec=0.05)
    node.destroy_node()
    rclpy.shutdown()


main()
