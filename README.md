# HCU Drone Project
## Autonomous Drone Simulation, Forest Survey, 3D LiDAR Mapping, and Navigation

**Project type:** Drone simulation and autonomous forest mapping  
**Platform:** Ubuntu 24.04 LTS  
**Middleware:** ROS 2 Jazzy  
**Autopilot:** PX4 Autopilot  
**Simulator:** Gazebo Sim  
**Mapping software:** FAST-LIO2  
**Repository:** [Karthikeya1304/HCU-Drone-Project](https://github.com/Karthikeya1304/HCU-Drone-Project)

---

## 1. Introduction

### What is this project?

The HCU Drone Project is a robotics project that uses a simulated drone to explore an environment, collect distance measurements, and create a three-dimensional representation of its surroundings.

The current setup includes a simulated quadcopter, a 3D LiDAR sensor, a forest environment, autonomous survey scripts, and mapping tools.

The main goal is to understand how a drone can move through an environment and use sensor data to build a map.

This repository stores the project-specific software, configuration files, simulation models, and scripts required to develop and reproduce the project.

### What problem does this project address?

Forests and other large environments can be difficult to inspect manually. A drone equipped with suitable sensors can collect environmental data while moving through an area.

The techniques demonstrated in this project can support research into:

- Autonomous drone navigation.
- Three-dimensional environmental mapping.
- Simultaneous localization and mapping (SLAM).
- Forest inspection and tree-position analysis.
- Robotics simulation and sensor integration.
- Autonomous survey planning.

**Important:** This repository describes a simulation-based workflow. A successful simulation does not automatically mean that the same system is safe or ready for real-world drone flight.

---

## 2. Understand the Project in Simple Words

You do not need prior drone knowledge to understand the project. Start with these basic concepts.

### What is a drone?

A drone is an aircraft that can fly without a person sitting inside it. This project uses a quadcopter, which has four propellers.

By changing the speed of its four motors, a quadcopter can take off, land, move forward or sideways, rotate, and maintain its position.

### What is PX4?

PX4 is the autopilot software. It receives commands and controls the simulated drone's movement.

Think of PX4 as the drone's flight-control system.

### What is Gazebo?

Gazebo is a simulator. It creates a virtual world containing objects, trees, lighting, a drone, and simulated sensors.

The drone can move around this world without needing a physical aircraft.

### What is ROS 2?

ROS 2 stands for Robot Operating System 2. Despite its name, it is not a complete operating system like Ubuntu.

It is a software framework that allows different robotics programs to communicate. For example, one program can publish LiDAR measurements while another program uses those measurements to build a map.

### What is LiDAR?

LiDAR stands for Light Detection and Ranging.

A LiDAR sensor measures distances to objects. A 3D LiDAR measures distances in multiple directions, allowing it to collect points around the drone.

### What is a point cloud?

A point cloud is a collection of points representing the surfaces of objects in three-dimensional space.

Each point has a position described using three coordinates:

- **X:** left or right.
- **Y:** forward or backward.
- **Z:** up or down.

Millions of points can collectively represent trees, walls, the ground, and other objects.

### What is FAST-LIO2?

FAST-LIO2 is a LiDAR-inertial mapping algorithm. It combines LiDAR measurements with inertial sensor measurements to estimate movement and build a map.

The inertial measurement unit (IMU) measures acceleration and angular velocity. These measurements help estimate how the drone moves.

### What is SLAM?

SLAM stands for Simultaneous Localization and Mapping.

In simple words, SLAM helps a robot estimate where it is while creating a map of its surroundings.

### How do these components work together?

```text
             Forest Environment
                     |
                     v
               Gazebo Sim
        (Virtual drone and sensors)
                     |
                     v
                PX4 Autopilot
          (Controls drone movement)
                     |
                     v
                 ROS 2
       (Connects robotics software)
                     |
                     v
             3D LiDAR + IMU Data
                     |
                     v
                 FAST-LIO2
         (Estimates motion and maps)
                     |
                     v
              3D Point Cloud
              and Survey Data
```

This diagram is a conceptual overview. The exact data connections depend on the simulation configuration and the ROS 2/Gazebo bridges that are running.

---

## 3. Software Requirements

The current development setup uses the following software.

| Software | Purpose |
|---|---|
| Ubuntu 24.04 LTS | Main operating system |
| ROS 2 Jazzy | Robotics communication framework |
| PX4 Autopilot | Flight-control software |
| Gazebo Sim | Virtual environment and sensor simulation |
| FAST-LIO2 | LiDAR-inertial mapping |
| Python 3 | Survey scripts and automation |
| Git | Version control |
| GitHub | Online source-code repository |

The commands below assume that these tools have already been installed and configured on the development computer. Installation procedures can vary by software version.

### Check your installed versions

Open a terminal and run:

```bash
lsb_release -a
```

This displays the Ubuntu version.

```bash
echo "$ROS_DISTRO"
```

This displays the active ROS 2 distribution in the current terminal. The expected value is `jazzy` after the ROS environment has been sourced.

```bash
gz sim --version
```

This checks the installed Gazebo Sim version.

```bash
git --version
```

This checks Git.

---

## 4. Repository Structure

The repository is organised into folders so that each part of the project is easy to locate.

```text
HCU-Drone-Project/
|
|-- README.md
|-- .gitignore
|
|-- docs/
|   |-- FASTLIO_NOTES.md
|
|-- fastlio/
|   |-- config/
|   |   |-- gz_x500.yaml
|   |   |-- gz_x500_forest.yaml
|   |
|   |-- lidar_time_patch/
|       |-- lidar_time_patch/
|       |-- package.xml
|       |-- setup.py
|       |-- setup.cfg
|
|-- px4_custom/
|   |-- airframes/
|   |   |-- 4022_gz_x500_lidar_3d
|   |
|   |-- gazebo/
|       |-- models/
|       |   |-- x500_lidar_3d/
|       |       |-- model.config
|       |       |-- model.sdf
|       |
|       |-- worlds/
|           |-- forest_lidar.sdf
|           |-- construction_site.sdf
|           |-- default_fastlio.sdf
|           |-- lunar_terrain.sdf
|
|-- ros2/
|   |-- drone_control/
|       |-- drone_control/
|       |-- config/
|       |-- test/
|       |-- package.xml
|       |-- setup.py
|       |-- autonomous-control and mapping utilities
|
|-- scripts/
    |-- camera_test.py
    |-- hop_test.py
    |-- loop_test.py
    |-- red_object_detection.py
    |-- survey_forest.py
```

The tree above is a simplified overview. Use the actual file list on GitHub for the complete list of files.

### What does each folder do?

**`docs/`**

Contains project notes and documentation. For example, `FASTLIO_NOTES.md` records information related to the FAST-LIO workflow.

**`fastlio/config/`**

Contains configuration files for running FAST-LIO2 with the simulated drone and forest environment. These files specify settings used by the mapping software.

**`fastlio/lidar_time_patch/`**

Contains a ROS 2 package that includes a Python utility for adding a time field to point-cloud data. The exact fields required depend on the input message and the mapping pipeline.

**`px4_custom/airframes/`**

Contains the project-specific PX4 airframe configuration for the simulated 3D LiDAR drone.

**`px4_custom/gazebo/models/`**

Contains the custom simulated drone model. Its SDF file describes the model, its LiDAR sensor, sensor placement, and sensor settings.

**`px4_custom/gazebo/worlds/`**

Contains simulation environments. For example, `forest_lidar.sdf` describes the forest world used for surveying.

**`ros2/drone_control/`**

Contains ROS 2 control utilities, coordinate and mapping-related scripts, configuration files, and analysis tools.

**`scripts/`**

Contains standalone Python scripts for tests and drone survey tasks. The forest survey script is `survey_forest.py`.

---

## 5. Important Commands Before Running the Project

### Step 1: Open a terminal

In Ubuntu, press `Ctrl + Alt + T`.

### Step 2: Open the PX4 directory

```bash
cd ~/PX4-Autopilot
```

The `cd` command changes the current directory.

### Step 3: Check the custom model

```bash
ls Tools/simulation/gz/models/x500_lidar_3d/
```

The directory should contain the custom model files, including `model.sdf` and `model.config`.

### Step 4: Check the custom airframe

```bash
ls ROMFS/px4fmu_common/init.d-posix/airframes/4022_gz_x500_lidar_3d
```

This verifies that the custom airframe file exists.

### Step 5: Check the survey script

```bash
ls -l ~/HCU-Drone-Project/scripts/survey_forest.py
```

This checks that the survey script exists in the project repository.

---

## 6. Running the Forest Simulation

The following workflow uses the custom forest world and simulated 3D LiDAR model.

**Run each major program in its own terminal.** Do not close a terminal while its program is needed by another component.

### Terminal 1: Start Gazebo

First, open the PX4 directory:

```bash
cd ~/PX4-Autopilot
```

Set the Gazebo resource paths:

```bash
export GZ_CONFIG_PATH=/usr/share/gz:$GZ_CONFIG_PATH

export GZ_SIM_RESOURCE_PATH=$HOME/PX4-Autopilot/Tools/simulation/gz/models:$GZ_SIM_RESOURCE_PATH

export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins:$GZ_SIM_SYSTEM_PLUGIN_PATH
```

These variables help Gazebo locate models and simulation plugins.

Start the forest world:

```bash
gz sim -v 4 -r ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf
```

Command explanation:

- `gz sim` starts Gazebo Sim.
- `-v 4` enables detailed logging.
- `-r` starts the simulation running.
- The final argument specifies the forest world file.

Wait for the world to load.

### Terminal 2: Start the PX4 simulated drone

Open another terminal and run:

```bash
cd ~/PX4-Autopilot
```

Start the custom simulated drone:

```bash
make px4_sitl gz_x500_lidar_3d
```

Explanation:

- `make` runs the PX4 build and simulation target.
- `px4_sitl` selects Software-in-the-Loop simulation.
- `gz_x500_lidar_3d` selects the custom Gazebo drone model.

Software-in-the-Loop means the flight-control software runs on the computer rather than on a physical flight controller.

Wait for PX4 to start and connect to the simulation.

**Important:** Do not disable PX4 safety checks just to make a warning disappear. Investigate connection, sensor, or configuration errors first.

### Terminal 3: Inspect Gazebo topics

Open a third terminal:

```bash
gz topic -l
```

This lists the topics available in Gazebo.

Check the LiDAR topic:

```bash
gz topic -i -t /lidar/points
```

This displays the message type and publisher/subscriber information for the topic.

The configured sensor topic is `/lidar/points`. The actual message type and available data must be checked in the running simulation.

To inspect messages:

```bash
gz topic -e -t /lidar/points
```

Use this carefully: LiDAR messages can be large, and printing them continuously can fill the terminal quickly.

For more information about Gazebo topics, inspect the output of `gz topic -h`.

---

## 7. Understanding the ROS 2 Environment

ROS 2 uses a workspace to organise packages. A workspace contains source code and, after building, generated installation files.

This project uses a ROS 2 workspace at `~/px4_ros2_ws` and a separate FAST-LIO workspace at `~/fastlio_ws`.

### Load the ROS 2 environment

In a terminal where you want to run ROS 2 tools:

```bash
source /opt/ros/jazzy/setup.bash
```

This makes the installed ROS 2 Jazzy commands and packages available.

Load the project's ROS 2 workspace:

```bash
source ~/px4_ros2_ws/install/setup.bash
```

Load the FAST-LIO workspace when using packages built in that workspace:

```bash
source ~/fastlio_ws/install/setup.bash
```

If a workspace has not been built, its `install/setup.bash` file may not exist.

### List ROS 2 topics

```bash
ros2 topic list
```

Topics are named communication channels. One program can publish messages to a topic, and other programs can subscribe to it.

### Inspect a topic

```bash
ros2 topic info /topic_name
```

Replace `/topic_name` with a real topic from `ros2 topic list`.

### Read messages

```bash
ros2 topic echo /topic_name
```

This prints messages published to the selected topic. Do not use a guessed topic name; check the list first.

### Check ROS 2 packages

```bash
ros2 pkg list
```

This lists packages available in the currently sourced ROS 2 environment.

---

## 8. FAST-LIO2 Mapping

FAST-LIO2 estimates motion and builds a point-cloud map using LiDAR and inertial measurements.

### What does FAST-LIO2 produce?

Depending on the configuration, it can produce:

- Estimated sensor or robot motion.
- Point-cloud data.
- A map of the surrounding environment.
- Diagnostic information about sensor data and mapping.

The exact outputs depend on the launch configuration and running topics.

### Check the FAST-LIO source directory

```bash
ls ~/fastlio_ws/src/FAST_LIO_ROS2/
```

### Check the mapping launch file

```bash
ls ~/fastlio_ws/src/FAST_LIO_ROS2/launch/
```

The project contains `mapping.launch.py`.

Before launching it, inspect the launch arguments:

```bash
source /opt/ros/jazzy/setup.bash
source ~/fastlio_ws/install/setup.bash
ros2 launch fast_lio mapping.launch.py --show-args
```

If ROS 2 reports that `fast_lio` cannot be found, check the package name in `package.xml` and whether the workspace has been built and sourced correctly.

Use the launch arguments shown by your installed version to select the correct configuration file. Do not assume that a launch argument has the same name across every FAST-LIO2 version.

### Check generated point-cloud files

The current workflow has produced point-cloud files in:

```text
~/fastlio_ws/src/FAST_LIO_ROS2/PCD/
```

List the files:

```bash
ls -lh ~/fastlio_ws/src/FAST_LIO_ROS2/PCD/
```

The `-l` option shows file details, and `-h` displays file sizes in a readable format.

A `.pcd` file stores point-cloud data. These files can be large because they may contain millions of points.

**Note:** Point-cloud files are generated data, not source code. They should be managed separately from the main Git repository if they are very large.

---

## 9. Running the Forest Survey Script

The project includes an autonomous forest survey script.

The previously used command is:

```bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash
python3 ~/HCU-Drone-Project/scripts/survey_forest.py
```

Run this only after the required simulation and ROS 2 connections are running and the script's expected inputs are available.

### What does this command do?

1. Loads the ROS 2 Jazzy environment.
2. Loads the project's installed ROS 2 packages.
3. Runs the Python survey script.

The script is intended to carry out the configured forest survey using the project’s drone-control workflow.

### Inspect the script

To read the source code:

```bash
less ~/HCU-Drone-Project/scripts/survey_forest.py
```

Press `q` to exit `less`.

To see the beginning of the file:

```bash
head -n 40 ~/HCU-Drone-Project/scripts/survey_forest.py
```

To check the Python syntax without running the survey:

```bash
python3 -m py_compile ~/HCU-Drone-Project/scripts/survey_forest.py
```

A successful syntax check produces no error output.

### Survey output

The previous survey workflow produced an odometry log at:

```text
~/survey_odom_2026-10-12.txt
```

It also produced point-cloud files under the FAST-LIO `PCD` directory.

These are examples of generated outputs from the recorded survey run, not guaranteed filenames for every future run.

---

## 10. Understanding the Results

### Odometry

Odometry is an estimate of how far the drone has moved and where it is located.

The survey log can help you understand the drone's movement through the environment.

### Point-cloud map

A point-cloud map contains 3D points measured by the simulated sensor.

The points can be visualised using compatible point-cloud tools. The map quality depends on sensor configuration, calibration, motion estimation, and the data collected.

### Tree-position analysis

The repository contains scripts for comparing point-cloud data with known tree locations.

Examples include:

```text
ros2/drone_control/compute_tree_accuracy.py
ros2/drone_control/compute_tree_accuracy_full.py
ros2/drone_control/plot_cloud_vs_groundtruth.py
ros2/drone_control/plot_cloud_vs_groundtruth_full.py
ros2/drone_control/plot_full_comparison.py
ros2/drone_control/plot_survey_map.py
```

These scripts are analysis utilities. Their required command-line arguments and input files should be checked in their source code before execution.

To inspect a script:

```bash
less ~/HCU-Drone-Project/ros2/drone_control/plot_survey_map.py
```

To see how a Python script is intended to be called, check its help support or inspect its argument-parsing section.

---

## 11. Troubleshooting

### Problem: `No such file or directory`

Possible causes:

- The file path is incorrect.
- The workspace has not been created.
- The package has not been installed.
- The command was run from the wrong directory.

Check the path with:

```bash
ls -l /path/to/file
```

Replace `/path/to/file` with the actual path.

### Problem: `Package not found`

Source the relevant environment:

```bash
source /opt/ros/jazzy/setup.bash
source ~/fastlio_ws/install/setup.bash
```

Then check:

```bash
ros2 pkg list
```

If the package is still missing, check whether the workspace was built successfully.

### Problem: Gazebo cannot find a model

Check the model directory:

```bash
ls ~/PX4-Autopilot/Tools/simulation/gz/models/x500_lidar_3d/
```

Check the resource path:

```bash
echo "$GZ_SIM_RESOURCE_PATH"
```

The model directory must be discoverable by Gazebo.

### Problem: LiDAR topic is missing

List available Gazebo topics:

```bash
gz topic -l
```

Inspect the expected topic:

```bash
gz topic -i -t /lidar/points
```

Confirm that Gazebo is running, the drone model has spawned, and the sensor is enabled.

### Problem: ROS 2 does not show the expected sensor topic

Gazebo topics and ROS 2 topics are not necessarily the same.

Check Gazebo topics:

```bash
gz topic -l
```

Check ROS 2 topics:

```bash
ros2 topic list
```

A suitable bridge may be required to transfer data between Gazebo and ROS 2. Verify that the correct bridge is running and configured for the sensor message type.

### Problem: Git says `nothing to commit, working tree clean`

This means Git sees no new changes in the current repository.

Check:

```bash
cd ~/HCU-Drone-Project
git status
```

Git does not automatically track changes made in separate directories such as `~/PX4-Autopilot` or `~/fastlio_ws`. Copy the relevant project-specific files into this repository before committing them.

---

## 12. GitHub Workflow

Git is a version-control system. It tracks changes to files and records them in commits.

GitHub hosts the repository online so that the project can be shared and reviewed.

### Check the repository

```bash
cd ~/HCU-Drone-Project
git status
```

### Add a new file or updated file

```bash
git add scripts/survey_forest.py
```

Replace the path with the file you changed.

To stage all changes in the current repository:

```bash
git add .
```

Review staged changes before committing:

```bash
git diff --cached --stat
git status
```

### Commit changes

```bash
git commit -m "Describe your changes"
```

Replace the message with a short description, such as:

```bash
git commit -m "Update forest survey documentation"
```

### Push changes to GitHub

```bash
git push origin main
```

### Verify synchronization

```bash
git status
```

If there are no pending changes and the branch is up to date with `origin/main`, the local repository is synchronized with GitHub.

### Important Git rules

- Do not upload passwords, API keys, private credentials, or personal access tokens.
- Do not commit build and install directories unless they are intentionally required.
- Avoid committing huge point-cloud files directly. Standard GitHub Git uploads reject individual files larger than 100 MB.
- If large datasets must be shared, consider Git LFS or a separate dataset-storage solution.
- Do not delete the `.git` folder to fix a normal Git error.

---

## 13. Safety and Limitations

This repository contains simulation and development software. The fact that a drone flies successfully in Gazebo does not prove that the system is ready for physical flight.

Before using any physical aircraft, additional work may be required, including:

- Hardware integration and electrical checks.
- Flight-controller and sensor calibration.
- Communication and failsafe testing.
- Geofence and emergency-stop configuration.
- Battery and motor safety checks.
- Testing in a controlled environment with appropriate supervision.
- Compliance with applicable aviation regulations.

The simulation and analysis results should be interpreted within the limits of the models and assumptions used.

---

## 14. Future Improvements

Possible future development work includes:

- Improving the reliability of autonomous survey missions.
- Improving LiDAR and IMU integration.
- Testing mapping quality under different sensor configurations.
- Adding clearer launch scripts and automated environment checks.
- Creating reproducible mapping and analysis workflows.
- Documenting map accuracy and survey coverage.
- Adding visualisation screenshots and example output maps.
- Developing a digital twin for further simulation and analysis.

These are potential improvements, not claims that every feature is already implemented.

---

## 15. Quick Command Reference

| Task | Command |
|---|---|
| Open project repository | `cd ~/HCU-Drone-Project` |
| Open PX4 directory | `cd ~/PX4-Autopilot` |
| Start forest world | `gz sim -v 4 -r ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf` |
| Start simulated drone | `make px4_sitl gz_x500_lidar_3d` |
| List Gazebo topics | `gz topic -l` |
| Inspect LiDAR topic | `gz topic -i -t /lidar/points` |
| List ROS 2 topics | `ros2 topic list` |
| List point-cloud files | `ls -lh ~/fastlio_ws/src/FAST_LIO_ROS2/PCD/` |
| Inspect survey script | `less ~/HCU-Drone-Project/scripts/survey_forest.py` |
| Run survey script | `python3 ~/HCU-Drone-Project/scripts/survey_forest.py` after sourcing the required ROS environments |
| Check Git status | `git status` |
| Upload changes | `git add . && git commit -m "Describe changes" && git push origin main` |

---

## 16. Conclusion

The HCU Drone Project brings together drone simulation, autopilot software, robotics communication, 3D LiDAR sensing, and mapping.

Gazebo provides the virtual environment. PX4 controls the simulated aircraft. ROS 2 connects the robotics software. FAST-LIO2 processes sensor measurements to estimate movement and build a map. Python scripts support survey automation and analysis.

The purpose of this repository is to make the project easier to understand, reproduce, extend, and review.

A new contributor should read this README first, verify the software versions, follow the simulation instructions, and then explore the individual scripts and configuration files.

