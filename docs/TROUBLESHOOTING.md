# HCU Drone Project --- Troubleshooting Guide

This guide covers common checks for the HCU Drone Project on Ubuntu with
ROS 2 Jazzy, PX4 SITL, Gazebo Sim, and FAST-LIO2. Commands are
diagnostic starting points. Exact fixes can depend on the installed
software versions and the error message, so inspect the output before
changing files.

## 1. Before troubleshooting

Run Git checks from the project folder:

``` bash
cd ~/HCU-Drone-Project
git status
git log -1 --oneline
```

Confirm the working tree and latest commit before making changes. If a
command fails, save the complete error output.

## 2. Gazebo does not start or cannot find a world

### Check the world file

``` bash
ls -l ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf
```

If the file is missing, check the actual path in your PX4 checkout and
the project repository. Do not create a replacement file until you have
confirmed the intended location.

### Start the known forest simulation

``` bash
cd ~/PX4-Autopilot
export GZ_CONFIG_PATH=/usr/share/gz:$GZ_CONFIG_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/PX4-Autopilot/Tools/simulation/gz/models:$GZ_SIM_RESOURCE_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins:$GZ_SIM_SYSTEM_PLUGIN_PATH
gz sim -v 4 -r ~/PX4-Autopilot/Tools/simulation/gz/worlds/forest_lidar.sdf
```

Keep this terminal open while the simulation is running. If Gazebo
reports a missing model or plugin, read the exact name in the error and
check the corresponding resource or plugin path.

## 3. PX4 SITL fails to start

### Check the repository and build directory

``` bash
cd ~/PX4-Autopilot
git status
ls -ld build/px4_sitl_default
```

### Start the custom LiDAR vehicle

``` bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_lidar_3d
```

If PX4 says the target is unknown, verify that the custom airframe and
model setup were installed as described in `docs/INSTALLATION.md`. Also
confirm that the target name matches the model and airframe
configuration in your current checkout.

Do not delete the build directory as a first troubleshooting step. It
can be large and rebuilding may take time.

## 4. Gazebo does not show the expected LiDAR topic

List active Gazebo topics:

``` bash
gz topic -l
```

Inspect the expected topic:

``` bash
gz topic -i -t /lidar/points
```

The model configuration in this project uses `/lidar/points`, but the
live topic name and message type must be confirmed from the running
simulation.

If the topic is absent: 1. Confirm that the LiDAR-equipped vehicle is
running. 2. Check the model file
`px4_custom/gazebo/models/x500_lidar_3d/model.sdf` in the project
repository. 3. Look at Gazebo's terminal output for sensor or model
errors. 4. Re-run `gz topic -l` after the model has fully spawned.

Do not assume that a topic name containing `points` necessarily uses a
point-cloud message type. Use `gz topic -i` to inspect it.

## 5. ROS 2 cannot see topics

Source the ROS 2 environment in the terminal where you are running ROS
commands:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash
ros2 topic list
```

If the workspace setup file does not exist, check whether the workspace
has been built and whether the path is correct.

If a Gazebo topic exists but the corresponding ROS 2 topic does not, a
bridge may be needed. Gazebo and ROS 2 topics are not automatically
interchangeable. Confirm that the appropriate bridge is installed,
running, and configured for the actual Gazebo message type and ROS
message type. Do not copy a bridge command from another setup without
checking compatibility.

To inspect a topic that is visible to ROS 2:

``` bash
ros2 topic info /topic_name
```

Replace `/topic_name` with a real topic name from `ros2 topic list`.

## 6. FAST-LIO2 does not launch or produces no map

First confirm the workspace and source directory:

``` bash
ls -ld ~/fastlio_ws/src/FAST_LIO_ROS2
ls -l ~/fastlio_ws/src/FAST_LIO_ROS2/PCD
```

Source the workspace only if its setup file exists:

``` bash
source ~/fastlio_ws/install/setup.bash
```

If this file is missing, the workspace may not have been built
successfully or the path may differ.

Check the following before changing FAST-LIO configuration: - The LiDAR
topic configured in the FAST-LIO YAML matches the actual input topic. -
The input message type is supported by the driver and FAST-LIO
configuration. - The IMU input topic exists and publishes data if the
selected configuration requires it. - The LiDAR and IMU timestamps are
usable and consistent. - The configured frame names match the sensor
messages and transforms. - The launch command and parameters match the
version of FAST-LIO installed.

The project has configuration files `fastlio/config/gz_x500.yaml` and
`fastlio/config/gz_x500_forest.yaml`. Compare them with the actual
running topics before editing. Exact launch commands are
version-dependent; use the package's available launch files and help
output rather than guessing an executable name.

## 7. The point cloud looks empty, sparse, or incorrect

Check whether the sensor is publishing and whether the environment is in
range:

``` bash
gz topic -i -t /lidar/points
```

Then check the ROS 2 input topic, if the data is bridged:

``` bash
ros2 topic list
ros2 topic info /topic_name
```

Possible causes to investigate: - The drone is not close enough to
objects for the selected sensor range or configuration. - The sensor
scan angle or direction does not cover the intended area. - The mapping
program is subscribed to a different topic. - Timestamps or frame names
are incorrect. - The drone is not moving as expected, or the input
stream has gaps. - The viewer is displaying a different coordinate frame
or a stale output file.

Check the SDF and YAML configuration before changing sensor angles,
timing, or frames. Change one setting at a time and record the result.

## 8. A script cannot be found or run

From the project root:

``` bash
cd ~/HCU-Drone-Project
ls -l scripts/
```

Run the survey script using the known workspace setup:

``` bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/install/setup.bash
python3 ~/HCU-Drone-Project/scripts/survey_forest.py
```

If Python reports a missing module, note the exact module name and check
which Python environment is active. Install dependencies only after
confirming which environment the project expects; system Python and a
virtual environment can have different packages.

If the script reports a missing file, check the path in the error and
confirm the file exists. Avoid moving files simply to silence a path
error.

## 9. Git says "not a git repository"

Git commands must be run inside the repository:

``` bash
cd ~/HCU-Drone-Project
git status
```

If that directory does not exist, check the folder where you cloned the
project:

``` bash
ls ~
```

Do not run `git init` inside an arbitrary folder to fix this error; that
can create a separate repository unrelated to your GitHub project.

## 10. Git push fails

Check the current branch and remote:

``` bash
cd ~/HCU-Drone-Project
git branch --show-current
git remote -v
git status
```

If the branch is `main` and the remote is `origin`, the normal push
command is:

``` bash
git push origin main
```

If Git reports rejected updates, authentication problems, or conflicts,
read the exact message before trying a fix. Do not force-push as a first
response, because it can overwrite remote history.

## 11. Large point-cloud files should not be committed casually

Point-cloud `.pcd` files can be hundreds of megabytes. Check repository
status before staging:

``` bash
cd ~/HCU-Drone-Project
git status --short
```

Avoid using `git add .` when large generated data files are present. Add
only the intended source or documentation files, for example:

``` bash
git add docs/TROUBLESHOOTING.md
```

If large files were staged accidentally, inspect `git status` and
unstage only the unintended path before committing. Do not delete the
original data unless you have a separate backup.

## 12. A safe debugging routine

1.  Copy the full error message.
2.  Record which terminal and command produced it.
3.  Check that the correct world, vehicle, workspace, and topic are
    running.
4.  Inspect live topics and message types instead of guessing.
5.  Change one setting at a time.
6.  Re-test and record what changed.
7.  If changing tracked files, inspect the diff before committing:

``` bash
cd ~/HCU-Drone-Project
git diff
git status
```

## 13. When asking for help, include

-   Ubuntu version and ROS 2 distribution.
-   PX4 and Gazebo versions, if known.
-   The exact command you ran.
-   The complete error output, not just the last line.
-   Output of relevant checks such as `gz topic -l`, `ros2 topic list`,
    or `git status`.
-   The file you changed and the reason for changing it.

Remove passwords, access tokens, and other secrets before sharing
terminal output.

## Related documentation

-   `README.md` --- project overview.
-   `docs/INSTALLATION.md` --- setup and installation.
-   `docs/COMMANDS.md` --- run commands and workflow.
-   `docs/PROJECT_ARCHITECTURE.md` --- component roles and data flow.
-   `docs/FASTLIO_NOTES.md` --- FAST-LIO project notes.

This guide is a diagnostic checklist, not a claim that every error has
one universal fix. Always use the actual error and installed versions to
choose the next step.
