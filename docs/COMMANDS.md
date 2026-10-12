# HCU Drone Project: Beginner Command Guide

This guide explains the commands used to inspect and run the HCU Drone
Project. It assumes Ubuntu 24.04, ROS 2 Jazzy, PX4 Autopilot, Gazebo
Sim, and FAST-LIO2 are installed on the computer.

> **Important:** This is a simulation workflow, not instructions for
> flying a physical drone. Keep each running program in its own
> terminal. Do not disable PX4 safety checks to bypass errors.

## 1. Understand the terminal

-   A **terminal** is where you type commands.
-   `cd` changes the current folder.
-   `ls` lists files.
-   `source` loads a software environment into the current terminal.
-   `~` means your home folder, for example `/home/uoh`.
-   A command that starts a program may keep running. Leave that
    terminal open while the program is needed.

Open a new terminal with `Ctrl+Alt+T`.

## 2. Check the software environment

Run these commands separately:

``` bash
lsb_release -a
```

Shows the Ubuntu version.

``` bash
echo "$ROS_DISTRO"
```

Shows the ROS 2 distribution currently loaded. After sourcing ROS 2
Jazzy, it should print `jazzy`.

``` bash
gz sim --version
```

Shows the installed Gazebo Sim version.

``` bash
git --version
```

Shows the installed Git version.

Load ROS 2 Jazzy in any terminal where you need ROS 2 commands:

``` bash
source /opt/ros/jazzy/setup.bash
```

If you need packages built in the PX4 ROS 2 workspace, also run:

``` bash
source ~/px4_ros2_ws/install/setup.bash
```

If you need packages built in the FAST-LIO workspace, also run:

``` bash
source ~/fastlio_ws/install/setup.bash
```

Only source a workspace after it has been built and its
`install/setup.bash` file exists. These `source` commands apply to the
current terminal; repeat them in each new terminal that needs the
environment.

## 3. Check the project files

Open the project repository:

``` bash
cd ~/HCU-Drone-Project
```

List its files:

``` bash
ls -la
```

Check whether Git sees changes:

``` bash
git status
```

Inspect the survey script without running it:

``` bash
less ~/HCU-Drone-Project/scripts/survey_forest.py
```

Press `q` to exit `less`.

Check the Python syntax:

``` bash
python3 -m py_compile ~/HCU-Drone-Project/scripts/survey_forest.py
```

No output normally means the syntax check passed. This does not prove
that the script will run successfully with the live simulation.

## 4. Terminal 1 --- start the Gazebo forest world

Open a terminal and run:

``` bash
cd ~/PX4-Autopilot
```

Set the resource paths used by the project's Gazebo setup:

``` bash
export GZ_CONFIG_PATH=/usr/share/gz:$GZ_CONFIG_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/PX4-Autopilot/Tools/simulation/gz/models:$GZ_SIM_RESOURCE_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins:$GZ_SIM_SYSTEM_PLUGIN_PATH
```

Start the forest world:

``` bash
gz sim -v 4 -r ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf
```

What the options mean:

-   `gz sim`: starts Gazebo Sim.
-   `-v 4`: enables detailed logging.
-   `-r`: starts the simulation running.
-   The final path selects the forest world file.

Leave this terminal open. If Gazebo reports a missing model or plugin,
check the resource paths and the error message before continuing.

## 5. Terminal 2 --- start PX4 with the custom LiDAR drone

Open a second terminal:

``` bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_lidar_3d
```

This starts PX4 Software-in-the-Loop (SITL) with the `gz_x500_lidar_3d`
simulation target. SITL runs the autopilot software on the computer
rather than on a physical flight controller.

Leave this terminal open. Wait for PX4 and Gazebo to connect. If PX4
reports a preflight failure, read the reason and diagnose it; do not
disable safety checks simply to remove the warning.

## 6. Terminal 3 --- inspect Gazebo topics

Open a third terminal:

``` bash
gz topic -l
```

This lists topics published in Gazebo.

Inspect the configured LiDAR topic:

``` bash
gz topic -i -t /lidar/points
```

This shows information such as the message type and publishers. The
model configuration uses `/lidar/points`, but always trust the topic
list and message information from the running version.

To print messages:

``` bash
gz topic -e -t /lidar/points
```

**Caution:** LiDAR messages can be very large. The terminal may fill
rapidly. Stop printing with `Ctrl+C`.

## 7. Check ROS 2 topics

In a terminal that needs ROS 2, load the environment:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash
```

List ROS 2 topics:

``` bash
ros2 topic list
```

Gazebo topics and ROS 2 topics are not automatically identical. A
ROS--Gazebo bridge may be needed to pass sensor data between them. If
the LiDAR appears in Gazebo but not ROS 2, check whether the correct
bridge is running and whether its message types match.

Inspect a real topic copied from `ros2 topic list`:

``` bash
ros2 topic info /topic_name
```

Replace `/topic_name` with an actual topic. Do not copy the placeholder
literally.

## 8. FAST-LIO2 --- inspect before launching

The FAST-LIO source directory used in this setup is:

``` bash
ls ~/fastlio_ws/src/FAST_LIO_ROS2
```

List its launch files:

``` bash
ls ~/fastlio_ws/src/FAST_LIO_ROS2/launch
```

The project has a `mapping.launch.py` file. Before launching, inspect
its supported arguments:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/fastlio_ws/install/setup.bash
ros2 launch fast_lio mapping.launch.py --show-args
```

If ROS 2 says the package cannot be found, check that the workspace was
built and sourced, and confirm the package name in its `package.xml`.

Use the arguments shown by your installed launch file to select the
appropriate LiDAR configuration. Launch arguments can differ between
FAST-LIO versions, so do not assume an argument name that has not been
confirmed on this computer.

## 9. Run the forest survey script

Only run the survey after the required simulation, PX4 connection, ROS 2
packages, and data connections are ready.

In a terminal for the survey script, run:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash
python3 ~/HCU-Drone-Project/scripts/survey_forest.py
```

This loads the ROS 2 environments and runs the project's Python survey
script. Keep the simulation and required supporting processes running in
their own terminals.

If the script exits with an error, copy the full error text. Do not
repeatedly rerun it without checking the cause.

## 10. Find survey and map outputs

List point-cloud files generated by FAST-LIO:

``` bash
ls -lh ~/fastlio_ws/src/FAST_LIO_ROS2/PCD/
```

The `-l` option displays file details; `-h` displays file sizes in a
readable form.

Check the survey odometry log used in the previous recorded run:

``` bash
ls -lh ~/survey_odom_2026-10-12.txt
```

These are paths observed in the development setup. Future runs may
produce different names or locations depending on configuration.

A `.pcd` file contains point-cloud data. Point clouds may be hundreds of
megabytes and should not normally be committed directly to the main Git
repository.

## 11. GitHub --- save project changes

Always enter the repository first:

``` bash
cd ~/HCU-Drone-Project
```

Check changes:

``` bash
git status
```

Review the changed file names:

``` bash
git diff --stat
```

Stage one specific file:

``` bash
git add scripts/survey_forest.py
```

Replace the path with the file you actually changed. To stage all
changes inside this repository, use `git add .`, but review what is
staged before committing.

Review staged changes:

``` bash
git diff --cached --stat
git status
```

Commit the changes:

``` bash
git commit -m "Describe your changes"
```

Push to GitHub:

``` bash
git push origin main
```

Verify:

``` bash
git status
```

If the working tree is clean and the branch is up to date with
`origin/main`, the local repository is synchronized.

Do not commit passwords, tokens, private credentials, build folders, or
large generated maps. GitHub's standard Git upload rejects individual
files larger than 100 MB.

## 12. Common problems

### `No such file or directory`

Check the path with `ls -l /path/to/file`. Replace the example path with
the real path.

### `ros2: command not found` or ROS package missing

Run `source /opt/ros/jazzy/setup.bash`. If the package belongs to a
workspace, source that workspace's `install/setup.bash` too.

### Gazebo cannot find the model

Check the model directory and print the resource path:

``` bash
ls ~/PX4-Autopilot/Tools/simulation/gz/models/x500_lidar_3d
echo "$GZ_SIM_RESOURCE_PATH"
```

### LiDAR topic missing

Run `gz topic -l` and check that the custom drone model has spawned.
Then inspect the topic with `gz topic -i -t /lidar/points`.

### LiDAR is visible in Gazebo but not ROS 2

Check `ros2 topic list` and verify that the required bridge is running
and supports the message type.

### `fatal: not a git repository`

Enter the project folder before using Git:

``` bash
cd ~/HCU-Drone-Project
```

### `nothing to commit, working tree clean`

Git sees no uncommitted changes inside this repository. Changes made in
`~/PX4-Autopilot` or `~/fastlio_ws` are outside this repository until
the relevant project-specific files are copied into it.

## 13. Recommended startup order

1.  Start Gazebo with the forest world in Terminal 1.
2.  Start PX4 with `make px4_sitl gz_x500_lidar_3d` in Terminal 2.
3.  Check Gazebo topics in Terminal 3.
4.  Start or verify the required ROS 2 bridge and mapping processes
    using the configuration for this installation.
5.  Confirm the needed sensor data is available.
6.  Run `survey_forest.py` in another terminal.
7.  Inspect the generated point cloud and survey log.
8.  Save intentional source-code or documentation changes to GitHub.

The exact FAST-LIO launch command and bridge command should be added
here after confirming the installed package's launch arguments and the
actual topic/message types.

## 14. Safety note

These commands are for the simulation workflow. A successful simulated
flight does not prove a real drone is safe to fly. Physical flights
require hardware checks, calibration, failsafe testing, suitable
supervision, and compliance with applicable aviation rules.
