from setuptools import setup
setup(
    name='lidar_time_patch',
    version='0.0.1',
    packages=['lidar_time_patch'],
    install_requires=['setuptools'],
    entry_points={'console_scripts': [
        'add_time_field = lidar_time_patch.add_time_field:main']},
)
