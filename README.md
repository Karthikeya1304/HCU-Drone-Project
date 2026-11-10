# HCU Drone Project

A simulation and mapping project for exploring autonomous drone surveys
using **PX4 SITL, Gazebo Sim, ROS 2 Jazzy, LiDAR, and FAST-LIO2**.

The project is intended to help contributors understand and test a
simulated drone workflow in a forest environment. It includes custom
PX4/Gazebo configuration, ROS 2 utilities, survey scripts, FAST-LIO
configuration, and analysis tools.

> **Important:** This repository describes a simulation and
> software-development workflow. Successful simulation does not certify
> a physical drone for flight. Verify commands, topic names, message
> types, and configuration against your installed software versions.

## Documentation

If you are new to the project, read these documents in order:

1.  **[Installation Guide](docs/INSTALLATION.md)** --- prepare a
    computer and set up the required software.
2.  **[Command Guide](docs/COMMANDS.md)** --- start the simulation and
    inspect topics.
3.  **[Project Architecture](docs/PROJECT_ARCHITECTURE.md)** ---
    understand what each component does and how the parts fit together.
4.  **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** --- diagnose
    common setup, simulation, ROS 2, LiDAR, FAST-LIO2, and Git problems.
5.  **[FAST-LIO Notes](docs/FASTLIO_NOTES.md)** --- project notes about
    FAST-LIO2.

## What does this project do?

At a high level, the workflow is:

1.  **Gazebo Sim** creates a virtual world and simulated drone.
2.  **PX4 SITL** runs the drone's autopilot software in simulation.
3.  The simulated **LiDAR and other sensors** produce measurements.
4.  The configured simulation integration and any required bridge make
    data available to the relevant robotics programs.
5.  **ROS 2** provides communication between supported robotics nodes.
6.  **FAST-LIO2** can process LiDAR and inertial data to estimate motion
    and build a point-cloud map when the sensor inputs and configuration
    are correct.
7.  Project scripts help run survey tests and inspect or analyse
    outputs.

The exact data connections depend on the configuration that is installed
and running. A Gazebo topic is not automatically a ROS 2 topic; check
the active topics and message types.

## Main technologies

  -----------------------------------------------------------------------
  Technology                          Purpose in this project
  ----------------------------------- -----------------------------------
  PX4 SITL                            Runs PX4 autopilot software in a
                                      simulated vehicle setup

  Gazebo Sim                          Simulates the environment, vehicle
                                      model, and configured sensors

  ROS 2 Jazzy                         Communication framework for
                                      robotics nodes and utilities

  LiDAR                               Provides distance measurements used
                                      by mapping software

  FAST-LIO2                           LiDAR-inertial motion estimation
                                      and mapping

  Python                              Survey scripts, tests, and analysis
                                      utilities
  -----------------------------------------------------------------------

## Repository layout

``` text
HCU-Drone-Project/
├── README.md
├── docs/
│   ├── INSTALLATION.md
│   ├── COMMANDS.md
│   ├── PROJECT_ARCHITECTURE.md
│   ├── TROUBLESHOOTING.md
│   └── FASTLIO_NOTES.md
├── fastlio/
│   ├── config/
│   └── lidar_time_patch/
├── px4_custom/
│   ├── airframes/
│   └── gazebo/
│       ├── models/
│       └── worlds/
├── ros2/
│   └── drone_control/
└── scripts/
```

This is a simplified overview. The repository may contain additional
files and subdirectories.

### Important files

-   `px4_custom/airframes/4022_gz_x500_lidar_3d` --- custom PX4 airframe
    configuration.
-   `px4_custom/gazebo/models/x500_lidar_3d/model.sdf` --- custom
    simulated drone model and LiDAR configuration.
-   `px4_custom/gazebo/worlds/forest_lidar.sdf` --- forest simulation
    world.
-   `fastlio/config/gz_x500.yaml` --- FAST-LIO configuration for the
    simulated sensor setup.
-   `fastlio/config/gz_x500_forest.yaml` --- forest-specific FAST-LIO
    configuration.
-   `scripts/survey_forest.py` --- forest survey workflow.
-   `ros2/drone_control/` --- project control and analysis utilities.

## Quick start

The following commands reflect the project's documented local setup.
They assume PX4 is cloned at `~/PX4-Autopilot`, the ROS 2 workspace is
at `~/px4_ros2_ws`, and the survey script is at
`~/HCU-Drone-Project/scripts/survey_forest.py`. If your folders differ,
update the paths.

### 1. Start the Gazebo forest world

Open a terminal:

``` bash
cd ~/PX4-Autopilot

export GZ_CONFIG_PATH=/usr/share/gz:$GZ_CONFIG_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/PX4-Autopilot/Tools/simulation/gz/models:$GZ_SIM_RESOURCE_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins:$GZ_SIM_SYSTEM_PLUGIN_PATH

gz sim -v 4 -r ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf
```

Keep this terminal open while Gazebo is running.

### 2. Start the PX4 LiDAR vehicle

Open a second terminal:

``` bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_lidar_3d
```

If the target is unknown or the model does not load, follow the
[Installation Guide](docs/INSTALLATION.md) and [Troubleshooting
Guide](docs/TROUBLESHOOTING.md).

### 3. Source ROS 2 and run the survey script

Open another terminal:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash

python3 ~/HCU-Drone-Project/scripts/survey_forest.py
```

Run this only after the required simulation and communication components
are running. The script's exact requirements depend on its current code
and configuration.

### 4. Inspect available topics

Gazebo topics:

``` bash
gz topic -l
gz topic -i -t /lidar/points
```

ROS 2 topics, in a terminal with ROS 2 sourced:

``` bash
ros2 topic list
```

Topic names and message types can vary with the running model and bridge
configuration. Use the live output rather than assuming a topic exists.

For additional commands and checks, see the [Command
Guide](docs/COMMANDS.md).

## Outputs and large files

The local FAST-LIO workspace has used this point-cloud directory:

``` text
~/fastlio_ws/src/FAST_LIO_ROS2/PCD/
```

To inspect it:

``` bash
ls -lh ~/fastlio_ws/src/FAST_LIO_ROS2/PCD/
```

Point-cloud files can be very large. Avoid committing generated `.pcd`
files or other large datasets directly to Git unless the repository has
an agreed storage strategy. Keep source code and configuration under
version control; store large outputs separately when appropriate.

## Troubleshooting

If something does not work:

1.  Copy the complete error message.
2.  Check which terminal and command produced it.
3.  Confirm the correct Gazebo world and PX4 vehicle are running.
4.  Inspect Gazebo and ROS 2 topics and message types.
5.  Verify the topic names, frames, and timestamps expected by
    FAST-LIO2.
6.  Change one configuration setting at a time and test again.

Use the [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for detailed
checks. Do not force-push Git history or delete build/data directories
as a first fix.

## Contributing and version control

From the project directory, check the current state before committing:

``` bash
cd ~/HCU-Drone-Project
git status
git diff
```

Stage only the intended files. For example, to commit a documentation
change:

``` bash
git add README.md
git commit -m "Improve project README"
git push origin main
```

If Git reports conflicts, authentication errors, or rejected updates,
read the exact message before attempting a fix.

## Safety and limitations

-   This repository is primarily a simulation and software-development
    project.
-   Simulation behaviour may differ from real hardware.
-   Before any real-world flight, separately verify the airframe,
    propulsion, battery, sensors, failsafes, communications, local
    regulations, and operating environment.
-   Do not assume a topic name or message type from its name alone.
-   Commands and configuration can change between PX4, Gazebo, ROS 2,
    and FAST-LIO versions.

## Maintainer checklist

Before asking someone else to reproduce a result, record:

-   Ubuntu and ROS 2 versions.
-   PX4 and Gazebo versions.
-   The exact launch commands used.
-   Active Gazebo and ROS 2 topics.
-   FAST-LIO configuration file used.
-   Output filenames and where they were saved.
-   Any local modifications to models, worlds, or airframes.

This information makes the project easier to reproduce, review, and
debug.

## LiDAR obstacle avoidance (experimental)

New files for this feature:

-   `scripts/survey_forest_avoid8.py` --- survey with LiDAR obstacle
    avoidance (latest version; `survey_forest_avoid.py` to
    `survey_forest_avoid7.py` are earlier iterations).
-   `px4_custom/gazebo/worlds/forest_lidar_box.sdf` --- copy of the forest
    world with a 1 x 1 x 4 m red test box added.

The script flies the survey waypoints and uses the raw LiDAR point cloud
(`/lidar/points/points`) to avoid obstacles. It does not need FAST-LIO to
be running.

How it works:

-   Only LiDAR points inside a corridor 1 m either side of the travel
    direction count as blocking.
-   Speed falls linearly from full at 4 m to zero at 2 m from the nearest
    point ahead.
-   Avoidance only acts above 1.5 m altitude, within an elevation band of
    -8 to +15 degrees, so the ground is ignored.
-   If blocked for 0.5 s, it picks the side with more clearance and
    sidesteps 3 m, then resumes toward the waypoint.
-   After 4 detours at one waypoint it skips to the next waypoint.
-   The setpoint stops advancing if it gets more than 1.5 m ahead of the
    drone.
-   If no LiDAR data arrives for 1 s, the drone holds position.

Test setup used so far (each step in its own terminal):

1.  Copy the test world to PX4 and start Gazebo with it:

``` bash
cp ~/HCU-Drone-Project/px4_custom/gazebo/worlds/forest_lidar_box.sdf \
   ~/PX4-Autopilot/Tools/simulation/gz/worlds/
cd ~/PX4-Autopilot
export GZ_CONFIG_PATH=/usr/share/gz:$GZ_CONFIG_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/PX4-Autopilot/Tools/simulation/gz/models
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins
gz sim -v 4 -r ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar_box.sdf
```

2.  Start PX4, then at the `pxh>` prompt run `param set NAV_DLL_ACT 0`:

``` bash
cd ~/PX4-Autopilot/build/px4_sitl_default/bin && PX4_GZ_WORLD=forest PX4_SIM_MODEL=x500_lidar_3d PX4_SYS_AUTOSTART=4022 ./px4 -s etc/init.d-posix/rcS -w ~/PX4-Autopilot/build/px4_sitl_default/rootfs
```

3.  Start the DDS agent and the LiDAR bridge:

``` bash
~/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent udp4 -p 8888

source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge '/lidar/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked'
```

4.  Run the script:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash
python3 ~/HCU-Drone-Project/scripts/survey_forest_avoid8.py
```

To stop early, run `commander land` at the `pxh>` prompt and wait for
"Disarmed by landing" before pressing Ctrl+C in the script terminal.
Stopping the script first makes PX4 fall back to return-to-launch.

Status and limitations:

-   Simulation only. One full survey run completed with 0 skipped
    waypoints and 2 detours. It has not been tested more widely.
-   Waypoints `wp9` and `wp10` were moved in this version because the
    earlier positions caused repeated stalls. The cause was not fully
    identified.
-   It only detects obstacles ahead and sidesteps. It is not a path
    planner and does not map the area.
-   Each blocking event logs a `BLOCK` line with the distance ahead,
    sideways offset and height of the nearest point, which helps diagnose
    stalls.
