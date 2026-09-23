from setuptools import find_packages, setup

package_name = 'drone_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='karthikeya-k',
    maintainer_email='karthikeya-k@todo.todo',
    description='ROS 2 package for PX4 X500 drone teleoperation and autonomous control',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'keyboard_control = drone_control.keyboard_control:main',
            'autonomous_control = drone_control.autonomous_control:main',
            'tf_broadcaster = drone_control.tf_broadcaster:main',
            'tf_broadcaster_lidar = drone_control.tf_broadcaster_lidar:main',
        ],
    },
)
