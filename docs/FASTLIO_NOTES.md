# FAST-LIO simulation notes

## Where the files go
- px4_custom/gazebo/worlds/forest_lidar.sdf -> ~/PX4-Autopilot/Tools/simulation/gz/worlds/ (forest world with the 8 system plugins added; stock forest.sdf has none)
- px4_custom/gazebo/worlds/default_fastlio.sdf -> same folder (PX4 default world plus Imu, AirPressure, Magnetometer, NavSat plugins and four static walls/blocks; world name is still "default")
- fastlio/config/gz_x500.yaml and gz_x500_forest.yaml -> ~/fastlio_ws/src/FAST_LIO_ROS2/config/ (only the imu_topic world name differs)
- fastlio/lidar_time_patch -> ~/fastlio_ws/src/ then: colcon build --packages-select lidar_time_patch (subscribes /lidar/points/points, drops non-finite points)
- scripts/hop_test.py, loop_test.py -> run with ROS and ~/px4_ros2_ws sourced (needs px4_msgs)

## Launch order (each in its own terminal tab)
1. Gazebo: gz sim -v 4 -r <world file> (set GZ_CONFIG_PATH, GZ_SIM_RESOURCE_PATH, GZ_SIM_SYSTEM_PLUGIN_PATH as in the PX4 setup)
2. PX4: PX4_SIM_MODEL=x500_lidar_3d PX4_SYS_AUTOSTART=4022 ./px4 -s etc/init.d-posix/rcS -w <rootfs>   (forest: also PX4_GZ_WORLD=forest). Do not spawn the model manually.
3. MicroXRCEAgent udp4 -p 8888
4. IMU bridge: /world/<default|forest>/model/x500_lidar_3d_0/link/base_link/sensor/imu_sensor/imu@sensor_msgs/msg/Imu[gz.msgs.IMU
5. LiDAR bridge: /lidar/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked
6. ros2 run lidar_time_patch add_time_field
7. ros2 launch fast_lio mapping.launch.py config_path:=<config dir> config_file:=gz_x500.yaml (forest: gz_x500_forest.yaml)
8. Check: ros2 topic hz /Odometry (about 10 Hz)

## Results so far
- 4 m hop out and back: FAST-LIO y peak about 3.97 m (default world) and 4.00 m (forest), ends within a few cm of Gazebo truth.
- 4 m square in the forest: loop closes within about 4 cm. Mid-loop corner readings not yet captured.
- PX4 parameter NAV_DLL_ACT set to 0 (clears the no-GCS warning).
- Hop odometry log (forest): altitude about 2.45 m, y peak 4.03 m and 4.09 m on two runs, back within 3 to 7 cm of the start.
- Hop map (2026-10-12): 4,974,646 points, 22 of 30 trees seen, tree residual rms about 0.8 m after a best-fit shift and yaw.
- Survey map (2026-10-12, scripts/survey_forest.py): 7,194,699 points, about 230 MB, extents x -24.2 to 25.2, y -13.1 to 37.0, z -0.61 to 6.22 m. All 30 trees matched against forest_lidar.sdf. Best-fit alignment yaw -0.27 degrees, shift (-0.03, -0.07) m, residual rms 0.28 m (median 0.21 m). The residual includes a near-face trunk bias of roughly 0.2 to 0.3 m, so it is not a precise accuracy figure. Matching method: centroid of points at z 0.5 to 2.0 m near each tree, re-centred on the aligned position.
- The map ground footprint is an L-shape that matches the grasspatch layout in forest_lidar.sdf.

## Area survey
- scripts/survey_forest.py is a copy of hop_test.py with a 10-waypoint loop at 2.5 m altitude and SPEED = 0.5 m/s (about 106 m). Waypoints are NED (north, east) metres from the start: (-3.5, -12), (10, -12), (16, 3), (24, 2), (28, 9), (26, 14), (14, 14), (13, 6), (3, 4), (-4, 3), then home. Planned clearance from every tree centre was at least 5.4 m (canopy width not accounted for).
- Why low altitude: the LiDAR is 360 x 32 beams, -30 to +15 degrees vertical, 0.1 to 40 m range, 10 Hz. At 12 m the lowest beam leaves about a 21 m hole of unseen ground under the drone.
- Axis mapping: NED +x is world north (FAST-LIO +y), NED +y is world east (FAST-LIO +x). Checked with the hop and the tree fit.
- Abort: Ctrl+C in the script's tab sends a land command (from reading the code, not tested).

## Saving the map
- FAST_LIO_ROS2 is not tracked in git. In src/laserMapping.cpp the block that fills pcl_wait_save was commented out (/* on line 516, */ on line 543), so no .pcd was ever written. Removed those two lines and rebuilt fast_lio. Backups: src/laserMapping.cpp.bak_pcd and ~/fast_lio_install_backup (kept outside the workspace because colcon rejects duplicate package names).
- Stop FAST-LIO once with Ctrl+C or kill -INT <pid>, wait for it to exit, and the map is written to ~/fastlio_ws/src/FAST_LIO_ROS2/PCD/scans.pcd. The next run overwrites it, so copy it first. Saved copies: scans_hop_2026-10-12.pcd and scans_survey_2026-10-12.pcd.
- Every scan's points are kept until shutdown (about 230 MB for the survey), so keep flights short.
- Viewing: pcl_viewer and CloudCompare are not installed. Open3D and matplotlib are in the venv ~/venvs/o3d.

## Next
Record FAST-LIO position at each corner of the square, fly the square with yaw turns, and try a faster or higher survey.
