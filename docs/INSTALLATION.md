# HCU Drone Project --- Installation Guide

This guide is for someone setting up the HCU Drone Project on a **new
Ubuntu computer**. It assumes the project is intended to use Ubuntu
24.04, ROS 2 Jazzy, PX4 SITL, Gazebo Sim, and the project's FAST-LIO2
ROS 2 workspace.

> **Read first:** The existing developer computer has already been
> configured and tested. A clean installation on another computer may
> need extra dependency fixes. Follow the stages in order and stop when
> a verification command fails. These instructions are for simulation,
> not for flying a physical drone.

## 1. What you will install

  -----------------------------------------------------------------------
  Component                           Why it is needed
  ----------------------------------- -----------------------------------
  Ubuntu 24.04 LTS                    Operating system

  Git                                 Downloads and tracks project source
                                      files

  ROS 2 Jazzy                         Lets robotics programs exchange
                                      messages

  PX4 Autopilot                       Flight-control software

  Gazebo Sim                          Virtual world, drone model, and
                                      simulated sensors

  FAST-LIO2 ROS 2                     Processes LiDAR and IMU data for
                                      mapping

  HCU Drone Project repository        Project-specific scripts,
                                      configurations, models, and worlds
  -----------------------------------------------------------------------

### Official references

-   ROS 2 Jazzy installation:
    https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
-   PX4 Ubuntu development setup:
    https://docs.px4.io/main/en/dev_setup/dev_env_linux
-   PX4 Gazebo simulation: https://docs.px4.io/main/en/sim_gazebo_gz/
-   FAST-LIO2 ROS 2 source used as a reference:
    https://github.com/Ericsii/FAST_LIO_ROS2

The official PX4 setup instructions currently describe Ubuntu 24.04 and
install a PX4 development toolchain and Gazebo Harmonic. Gazebo Sim 8 is
the Harmonic generation. Check the official documentation if the PX4
version in this project changes.

## 2. Before installing

Open a terminal with `Ctrl+Alt+T`.

Check Ubuntu:

``` bash
lsb_release -a
```

Check available disk space:

``` bash
df -h ~
```

Check memory:

``` bash
free -h
```

PX4, Gazebo, ROS 2, and FAST-LIO2 can use substantial CPU, RAM, and disk
space. Point-cloud maps can also become large.

Update Ubuntu packages:

``` bash
sudo apt update
sudo apt upgrade
```

Restart if Ubuntu requests it.

## 3. Install Git and basic tools

``` bash
sudo apt install -y git curl wget gnupg lsb-release build-essential cmake
```

Check Git:

``` bash
git --version
```

## 4. Install ROS 2 Jazzy

Follow the official ROS 2 Jazzy Ubuntu instructions:
https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

Choose the **Desktop Install** if you need the common ROS tools and
visualisation utilities, or the **ROS-Base Install** if you
intentionally want a minimal, headless setup. For a beginner using
simulation and visualisation, Desktop Install is usually more
convenient.

The ROS website is the authoritative source for the current repository
setup, keys, and package commands. Use its commands exactly rather than
copying installation commands from an old tutorial.

After installation, open a new terminal and run:

``` bash
source /opt/ros/jazzy/setup.bash
echo "$ROS_DISTRO"
ros2 --help
```

Expected check: - `echo "$ROS_DISTRO"` prints `jazzy`. - `ros2 --help`
displays ROS 2 command help.

If `source /opt/ros/jazzy/setup.bash` says the file does not exist, ROS
2 Jazzy has not been installed in the expected location or installation
did not complete.

## 5. Download PX4 Autopilot

Go to your home directory:

``` bash
cd ~
```

Clone PX4 with its submodules:

``` bash
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
```

If the folder already exists, do not clone it over the existing folder.
Enter it and inspect the current state:

``` bash
cd ~/PX4-Autopilot
git status
git describe --tags --always
```

### Install the PX4 development toolchain

For a **new, clean Ubuntu 24.04 development computer**, PX4 documents
this setup script:

``` bash
bash ~/PX4-Autopilot/Tools/setup/ubuntu.sh
```

Read the prompts before accepting changes. The PX4 documentation notes
that the setup script is intended for clean supported Ubuntu
installations and may not work correctly on top of a heavily modified
system. It can install development tools and simulation dependencies.

When it finishes, follow any restart instruction shown by the installer.
Official instructions:
https://docs.px4.io/main/en/dev_setup/dev_env_linux

Do not rerun this installer casually on an already working developer
computer just to fix one missing package.

## 6. Get the HCU Drone Project repository

If you are setting up a new computer:

``` bash
cd ~
git clone https://github.com/Karthikeya1304/HCU-Drone-Project.git
cd ~/HCU-Drone-Project
```

If the repository is already present, update it instead:

``` bash
cd ~/HCU-Drone-Project
git pull origin main
```

List the project files:

``` bash
find . -maxdepth 3 -type f | sort
```

The repository contains project-specific files such as: -
`scripts/survey_forest.py` -
`px4_custom/airframes/4022_gz_x500_lidar_3d` -
`px4_custom/gazebo/models/x500_lidar_3d/model.sdf` -
`px4_custom/gazebo/worlds/forest_lidar.sdf` - FAST-LIO configuration
files and ROS 2 utilities

**Important:** Downloading this repository does not automatically
install PX4, FAST-LIO2, ROS 2, or all their dependencies. It stores
project-specific source files and configurations.

## 7. Copy custom files into the PX4 tree

PX4 reads simulation models and airframe definitions from its own source
tree. The HCU repository stores copies of the project-specific files for
review and version control.

First, make sure the PX4 repository exists:

``` bash
test -d ~/PX4-Autopilot/.git && echo "PX4 repository found"
```

Copy the custom airframe:

``` bash
cp ~/HCU-Drone-Project/px4_custom/airframes/4022_gz_x500_lidar_3d \
~/PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/airframes/
```

Copy the custom Gazebo model:

``` bash
mkdir -p ~/PX4-Autopilot/Tools/simulation/gz/models/x500_lidar_3d
cp -a ~/HCU-Drone-Project/px4_custom/gazebo/models/x500_lidar_3d/. \
~/PX4-Autopilot/Tools/simulation/gz/models/x500_lidar_3d/
```

Copy the forest world:

``` bash
cp ~/HCU-Drone-Project/px4_custom/gazebo/worlds/forest_lidar.sdf \
~/PX4-Autopilot/Tools/simulation/gz/worlds/
```

The repository also includes other world files. Copy a world only when
you intend to use it.

Check that the files exist:

``` bash
ls -l ~/PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/airframes/4022_gz_x500_lidar_3d
ls -l ~/PX4-Autopilot/Tools/simulation/gz/models/x500_lidar_3d/
ls -l ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf
```

These copy commands overwrite same-named files in the PX4 tree. If you
already have custom edits in that tree, back them up or compare the
files first.

## 8. Build and verify PX4 SITL

Open a terminal:

``` bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_lidar_3d
```

This target must exist in the checked-out PX4 version and its simulation
configuration. If the build says the target is unknown, do not guess
another target: verify that the custom model and airframe are installed
in the expected locations and consult the PX4 version used by the
project.

The first build may take time. Keep the complete error output if it
fails.

## 9. Prepare the ROS 2 workspace

The developer setup uses two workspaces: - `~/px4_ros2_ws` -
`~/fastlio_ws`

A workspace is a folder containing ROS 2 packages. After building, ROS 2
creates an `install` directory with environment setup scripts.

### Check the PX4 ROS 2 workspace

``` bash
ls -la ~/px4_ros2_ws/src
```

If it does not exist, do not assume it should be created from the HCU
repository alone. The current workspace may contain PX4 message packages
and other dependencies. Follow the PX4 ROS 2 instructions that match the
PX4 version: https://docs.px4.io/main/en/ros2/

If the workspace already exists and contains packages, source ROS 2 and
build it according to its package dependencies:

``` bash
source /opt/ros/jazzy/setup.bash
cd ~/px4_ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

Only run the build step if this workspace is set up as a valid ROS 2
workspace and its dependencies are available. If `rosdep` or `colcon` is
missing, use the official ROS 2 setup instructions to install the
relevant tools.

After a successful build:

``` bash
source ~/px4_ros2_ws/install/setup.bash
```

### Check the FAST-LIO workspace

``` bash
ls -la ~/fastlio_ws/src
```

The developer setup includes `FAST_LIO_ROS2`, `livox_ros_driver2`, and a
project-specific `lidar_time_patch` package.

FAST-LIO forks and branches can differ in their dependency requirements
and launch arguments. Review the source README and package manifests
before installing or building: https://github.com/Ericsii/FAST_LIO_ROS2

If the workspace is already prepared:

``` bash
source /opt/ros/jazzy/setup.bash
cd ~/fastlio_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

If a build fails, read the first actual compiler or dependency error. Do
not repeatedly rebuild without resolving it. Some FAST-LIO variants
expect a particular Livox driver or point-cloud message format; the
project's `lidar_time_patch` exists to support its configured data path.

After a successful build:

``` bash
source ~/fastlio_ws/install/setup.bash
ros2 pkg list | grep -i fast
```

The exact package name shown depends on the FAST-LIO source version.

## 10. Verify Gazebo and sensor configuration

Before running the full survey, inspect the model and world files:

``` bash
grep -nE 'model name|sensor name|<topic>|min_angle|max_angle|<samples>' \
~/PX4-Autopilot/Tools/simulation/gz/models/x500_lidar_3d/model.sdf
```

Check the forest world:

``` bash
grep -nE '<world|<include|<uri>' \
~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf | head -n 60
```

These commands display relevant lines; they do not prove the simulation
will start. Actual topic names and message types must be checked after
Gazebo launches.

## 11. First simulation test

Follow the terminal-by-terminal startup sequence in
[`COMMANDS.md`](COMMANDS.md):

1.  Start Gazebo with `forest_lidar.sdf`.
2.  Start PX4 with `make px4_sitl gz_x500_lidar_3d`.
3.  Check Gazebo topics with `gz topic -l`.
4.  Inspect the LiDAR topic with `gz topic -i -t /lidar/points`.
5.  Confirm the ROS--Gazebo bridge and FAST-LIO input data are
    configured before starting mapping.
6.  Run the forest survey script only after its required connections are
    ready.

Do not assume Gazebo topics automatically appear in ROS 2. A bridge may
be required, and it must use a compatible message type.

## 12. Common installation problems

### `ros2: command not found`

Run:

``` bash
source /opt/ros/jazzy/setup.bash
```

If the file is missing, revisit the official ROS 2 installation
instructions.

### `colcon: command not found`

Install the build tools documented for ROS 2 Jazzy, then open a new
terminal and source ROS 2.

### `rosdep: command not found`

Install and initialize `rosdep` using the official ROS 2 instructions
for Jazzy.

### PX4 target is not found

Check the custom airframe and model paths, then check the PX4 version
and target configuration. The target name is version-dependent.

### Gazebo cannot find the model

Check the model path and resource-path variables. Follow the environment
setup and startup commands in `COMMANDS.md`.

### FAST-LIO cannot find a package or topic

Source the correct workspace, check `ros2 pkg list` and
`ros2 topic list`, and verify the actual launch arguments and message
types. The package name and required driver may vary by FAST-LIO fork.

### Build fails

Save the full terminal output, especially the first error that indicates
a missing dependency or compiler failure. Avoid deleting build
directories or reinstalling the entire system before identifying the
cause.

## 13. Reproducibility checklist

Before calling the installation complete, verify each item:

-   [ ] Ubuntu version is 24.04.
-   [ ] ROS 2 Jazzy commands work.
-   [ ] PX4 source and submodules are present.
-   [ ] The custom airframe file is in the PX4 tree.
-   [ ] The custom LiDAR model is in the Gazebo models tree.
-   [ ] The forest world file is present.
-   [ ] PX4 SITL builds and starts.
-   [ ] Gazebo topics appear.
-   [ ] The LiDAR topic exists and has the expected message type.
-   [ ] The ROS--Gazebo bridge and FAST-LIO input data work.
-   [ ] The survey script runs and produces the expected output.

## 14. Safety and scope

This guide covers a simulation development environment. It does not
certify the software for a physical aircraft. Real flights require
hardware validation, calibration, failsafe testing, suitable
supervision, and compliance with local aviation rules.
