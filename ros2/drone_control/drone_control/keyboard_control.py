import sys
import os
import termios
import tty
import select

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleStatus


class KeyboardControlNode(Node):
    def __init__(self):
        super().__init__('keyboard_control_node')

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

        self.vehicle_status = VehicleStatus()

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.yaw = 0.0

        self.step_xy = 0.1
        self.step_z = 0.1
        self.step_yaw = 0.1

        self.offboard_setpoint_counter = 0
        self.armed_and_offboard = False
        self.landing_requested = False

        self.stdin_fd = sys.stdin.fileno()
        self.original_term_settings = termios.tcgetattr(self.stdin_fd)
        tty.setraw(self.stdin_fd)
        termios.tcflush(self.stdin_fd, termios.TCIFLUSH)

        self.timer = self.create_timer(0.1, self.timer_callback)

        self.print_instructions()
        self.get_logger().info('Keyboard control node started')

    def print_instructions(self):
        msg = (
            "\r\n--- Keyboard Drone Control ---\r\n"
            "Arrow keys : move forward/back/left/right\r\n"
            "W / S      : increase / decrease altitude\r\n"
            "A / D      : yaw left / right\r\n"
            "SPACE      : hold position\r\n"
            "L          : land\r\n"
            "Q          : quit (restores terminal safely)\r\n"
            "-------------------------------\r\n"
        )
        sys.stdout.write(msg)
        sys.stdout.flush()

    def get_key_nonblocking(self):
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if not dr:
            return None

        ch = sys.stdin.read(1)

        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            if ch2 == '[':
                return {'A': 'UP', 'B': 'DOWN', 'C': 'RIGHT', 'D': 'LEFT'}.get(ch3, None)
            return None

        return ch

    def vehicle_status_callback(self, msg):
        self.vehicle_status = msg

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
        msg.position = [self.x, self.y, self.z]
        msg.yaw = self.yaw
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

    def timer_callback(self):
        self.publish_offboard_control_mode()
        self.publish_trajectory_setpoint()

        if self.offboard_setpoint_counter < 11:
            self.offboard_setpoint_counter += 1

        if self.offboard_setpoint_counter == 10:
            self.publish_vehicle_command(
                VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
            self.publish_vehicle_command(
                VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
            self.armed_and_offboard = True
            sys.stdout.write('\r\nArmed + Offboard requested. Use W to climb, then arrows to move.\r\n')
            sys.stdout.flush()

        if self.offboard_setpoint_counter <= 10:
            return

        key = self.get_key_nonblocking()
        if key is not None:
            self.get_logger().info(f'Key received: {key!r}')

        if key == 'q' or key == 'Q':
            sys.stdout.write('\r\nQuit requested, landing first...\r\n')
            sys.stdout.flush()
            self.landing_requested = True
            self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)

        elif key == 'l' or key == 'L':
            sys.stdout.write('\r\nLanding...\r\n')
            sys.stdout.flush()
            self.landing_requested = True
            self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)

        elif self.landing_requested:
            pass

        elif key == 'UP':
            self.x += self.step_xy
        elif key == 'DOWN':
            self.x -= self.step_xy
        elif key == 'LEFT':
            self.y -= self.step_xy
        elif key == 'RIGHT':
            self.y += self.step_xy
        elif key == 'w' or key == 'W':
            self.z -= self.step_z
        elif key == 's' or key == 'S':
            self.z += self.step_z
            if self.z > 0.0:
                self.z = 0.0
        elif key == 'a' or key == 'A':
            self.yaw -= self.step_yaw
        elif key == 'd' or key == 'D':
            self.yaw += self.step_yaw
        elif key == ' ':
            pass

        # Checked every cycle now, not just when a key was pressed,
        # so we reliably catch the moment PX4 actually disarms.
        if self.landing_requested and self.vehicle_status.arming_state == VehicleStatus.ARMING_STATE_DISARMED:
            sys.stdout.write('\r\nDisarmed. Shutting down.\r\n')
            sys.stdout.flush()
            self.restore_terminal()
            rclpy.shutdown()

    def restore_terminal(self):
        termios.tcsetattr(self.stdin_fd, termios.TCSADRAIN, self.original_term_settings)


LOCK_FILE = '/tmp/drone_control_active.lock'


def main(args=None):
    if os.path.exists(LOCK_FILE):
        print(f"ERROR: {LOCK_FILE} already exists. Another control node "
              f"(keyboard_control or autonomous_control) appears to be "
              f"running already. Refusing to start to avoid conflicting "
              f"setpoints. If you're sure nothing else is running, delete "
              f"this file manually and try again.")
        sys.exit(1)

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

    rclpy.init(args=args)
    node = KeyboardControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.restore_terminal()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


if __name__ == '__main__':
    main()
