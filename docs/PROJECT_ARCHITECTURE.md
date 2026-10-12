# HCU Drone Project --- Architecture Explained

This document explains how the project components fit together, using
beginner-friendly language. It describes the intended workflow in this
repository. Exact topic names and connections must be verified on the
running computer because they depend on the installed PX4, Gazebo, ROS
2, and FAST-LIO versions.

## 1. The big picture

The project simulates a quadcopter moving through a forest and
collecting 3D LiDAR data. PX4 controls the simulated vehicle, Gazebo
provides the virtual world and simulated sensors, ROS 2 connects
robotics programs, and FAST-LIO2 processes LiDAR and inertial
measurements to estimate motion and build a point-cloud map. Python
scripts help run the survey and analyse results.

``` text
                         HCU Drone Project
                                 |
                   +-------------+-------------+
                   |                           |
                   v                           v
              Gazebo Sim                  PX4 Autopilot
        Virtual forest, drone,        Flight-control logic
         and simulated sensors                 |
                   |                           |
                   +-----------+---------------+
                               |
                      Simulation integration
                               |
                               v
                             ROS 2
                 Robotics messages and programs
                               |
                   +-----------+-----------+
                   |                       |
                   v                       v
              Sensor data             Control scripts
             LiDAR and IMU        Survey and other tools
                   |
                   v
                FAST-LIO2
         Motion estimation and mapping
                   |
                   v
             3D point-cloud map
                   |
                   v
         Visualisation and analysis tools
```

This is a conceptual diagram, not a guarantee that every arrow is
implemented by a single direct connection. PX4, Gazebo, and ROS 2 can
use different bridges and interfaces. Check the running topics and
configuration files to confirm the exact data path.

## 2. What each component does

### Gazebo Sim --- the virtual world

Gazebo creates the simulated environment. In this project, the forest
world contains the environment in which the drone flies. The custom
model file defines the simulated drone and its LiDAR sensor.

Project files: - `px4_custom/gazebo/worlds/forest_lidar.sdf` -
`px4_custom/gazebo/models/x500_lidar_3d/model.sdf` -
`px4_custom/gazebo/models/x500_lidar_3d/model.config`

### PX4 Autopilot --- flight control

PX4 is the autopilot software. It runs the flight-control logic and uses
the simulation integration to control the simulated vehicle.

Project-specific airframe: -
`px4_custom/airframes/4022_gz_x500_lidar_3d`

The airframe file configures the PX4 vehicle startup for this simulation
target. It is not a replacement for the full PX4 source repository.

### ROS 2 --- communication between robotics programs

ROS 2 is a framework for communication between robotics processes.
Programs can publish messages to named topics, subscribe to those
topics, and exchange sensor or control information.

The project includes ROS 2 utilities in: - `ros2/drone_control/` -
`fastlio/lidar_time_patch/`

Gazebo topics do not automatically become ROS 2 topics. A suitable
bridge or integration must be running when data needs to cross between
the two systems.

### LiDAR --- distance measurements

The custom Gazebo model configures a simulated 3D LiDAR sensor. LiDAR
measurements represent distances to surfaces in the environment.

The model currently specifies the topic `/lidar/points`. Check the
running simulation to confirm the actual message type:

``` bash
gz topic -l
gz topic -i -t /lidar/points
```

Do not assume the topic's message type from its name alone.

### IMU --- movement measurements

An inertial measurement unit measures acceleration and angular velocity.
FAST-LIO2 uses inertial measurements along with LiDAR data to estimate
movement. The exact IMU source and ROS topic must be checked in the
running setup.

### FAST-LIO2 --- motion estimation and mapping

FAST-LIO2 processes LiDAR and inertial measurements to estimate motion
and build a point-cloud map.

Relevant repository files include: - `fastlio/config/gz_x500.yaml` -
`fastlio/config/gz_x500_forest.yaml` - `fastlio/lidar_time_patch/`

The configuration files control how FAST-LIO handles the selected sensor
input. Their specific settings should be reviewed before changing sensor
topics, frames, or timing.

### Python survey scripts --- mission automation

The repository's `scripts/survey_forest.py` is used to run the
configured forest survey workflow. Other scripts provide tests and
utilities.

Files include: - `scripts/survey_forest.py` - `scripts/hop_test.py` -
`scripts/loop_test.py` - `scripts/camera_test.py` -
`scripts/red_object_detection.py`

The precise behaviour of each script is defined by its source code and
configuration. Inspect a script before running it.

### Analysis tools --- understand the map

The repository includes scripts for comparing point-cloud maps with
reference tree locations and plotting survey data.

Examples: - `ros2/drone_control/compute_tree_accuracy.py` -
`ros2/drone_control/compute_tree_accuracy_full.py` -
`ros2/drone_control/plot_cloud_vs_groundtruth.py` -
`ros2/drone_control/plot_cloud_vs_groundtruth_full.py` -
`ros2/drone_control/plot_full_comparison.py` -
`ros2/drone_control/plot_survey_map.py`

These are analysis utilities. They may require particular input files
and arguments; inspect each script before use.

## 3. What happens during a survey?

The intended high-level workflow is:

1.  **Load the forest:** Gazebo reads `forest_lidar.sdf` and creates the
    virtual environment.
2.  **Spawn the drone:** PX4 and Gazebo start the custom `x500_lidar_3d`
    vehicle.
3.  **Simulate sensors:** Gazebo produces LiDAR and other configured
    sensor measurements.
4.  **Connect the data:** The configured simulation integration and ROS
    2 bridge make required data available to the relevant programs.
5.  **Estimate motion and map:** FAST-LIO2 processes the sensor data to
    estimate movement and create a point cloud.
6.  **Run the survey:** `survey_forest.py` executes the project's
    configured survey logic when its required connections are available.
7.  **Review the results:** Point-cloud and odometry outputs can be
    inspected and analysed.

The actual startup order and exact connection commands are documented in
`COMMANDS.md`. The bridge and FAST-LIO launch details should be verified
against the installed versions before treating them as fixed commands.

## 4. Important files and why they matter

  ----------------------------------------------------------------------------------------
  File or folder                                       Role
  ---------------------------------------------------- -----------------------------------
  `scripts/survey_forest.py`                           Forest survey workflow

  `scripts/hop_test.py`                                Test script; inspect source for
                                                       exact behaviour

  `scripts/loop_test.py`                               Test script; inspect source for
                                                       exact behaviour

  `scripts/camera_test.py`                             Camera test utility

  `scripts/red_object_detection.py`                    Red-object detection utility

  `px4_custom/airframes/4022_gz_x500_lidar_3d`         Custom PX4 airframe configuration

  `px4_custom/gazebo/models/x500_lidar_3d/model.sdf`   Custom drone model and LiDAR
                                                       configuration

  `px4_custom/gazebo/worlds/forest_lidar.sdf`          Forest simulation environment

  `fastlio/config/gz_x500.yaml`                        FAST-LIO configuration for the
                                                       simulated sensor setup

  `fastlio/config/gz_x500_forest.yaml`                 Forest-specific FAST-LIO
                                                       configuration

  `fastlio/lidar_time_patch/`                          ROS 2 package with point-cloud
                                                       time-field utility

  `ros2/drone_control/`                                Control, mapping, and analysis
                                                       utilities

  `docs/COMMANDS.md`                                   Terminal commands and run workflow

  `docs/INSTALLATION.md`                               Setup and installation guide
  ----------------------------------------------------------------------------------------

## 5. How to inspect the live system

### List Gazebo topics

``` bash
gz topic -l
```

Lists the topics currently available in Gazebo.

### Inspect the LiDAR topic

``` bash
gz topic -i -t /lidar/points
```

Shows the topic's message type and publisher information.

### List ROS 2 topics

In a terminal where ROS 2 is sourced:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash
ros2 topic list
```

This lists the topics ROS 2 can currently see. If a needed sensor topic
is missing, check the bridge and message type rather than assuming the
sensor is broken.

### Inspect a ROS 2 topic

Replace `/topic_name` with an actual topic from the list:

``` bash
ros2 topic info /topic_name
```

This shows information about publishers and subscribers.

## 6. Where output data goes

The development setup has used the FAST-LIO point-cloud directory:

``` text
~/fastlio_ws/src/FAST_LIO_ROS2/PCD/
```

List its contents:

``` bash
ls -lh ~/fastlio_ws/src/FAST_LIO_ROS2/PCD/
```

A `.pcd` file stores a point cloud. The survey workflow has also used an
odometry log in the home directory. Output paths can change based on the
launch and save configuration, so check the current run rather than
assuming every run produces the same filenames.

Generated maps may be large. Keep source code and configuration in Git;
use a suitable large-file or dataset storage solution for large
point-cloud outputs.

## 7. Common misconceptions

-   **Gazebo is not PX4.** Gazebo simulates the world and sensors; PX4
    runs flight-control logic.
-   **ROS 2 is not the autopilot.** It connects robotics programs and
    data flows.
-   **LiDAR is not itself a map.** It produces distance measurements;
    mapping software processes them into a map.
-   **A point cloud is not automatically a perfect reconstruction.**
    Sensor settings, timing, calibration, motion estimates, and
    environmental geometry affect quality.
-   **A successful simulation does not certify a physical drone.**
    Real-world flight requires separate hardware, safety, and regulatory
    validation.
-   **A topic name does not guarantee a message type.** Inspect the
    actual running topic.
-   **A file in this repository is not automatically installed into
    PX4.** Project-specific models and airframes may need to be copied
    into the appropriate PX4 directories as described in
    `INSTALLATION.md`.

## 8. Further reading

-   `README.md` --- project overview.
-   `COMMANDS.md` --- terminal commands and workflow.
-   `INSTALLATION.md` --- installation and setup.
-   `FASTLIO_NOTES.md` --- project notes about FAST-LIO.

The goal of this document is to help new contributors understand the
purpose of each major component and how the pieces fit together. Exact
commands and data connections should always be verified against the
running installation.
