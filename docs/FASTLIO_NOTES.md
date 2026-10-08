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

## Next
Record FAST-LIO position during flights, fly the square with yaw turns, longer forest flights and map saving.
