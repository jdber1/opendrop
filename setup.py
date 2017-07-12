from setuptools import find_packages, setup

setup(
    name = "opendrop",
    version = "2.0dev",
    packages = find_packages(exclude = ["opendrop.bin"]),
    include_package_data = True,
    entry_points = {"console_scripts": [
        "opendrop = opendrop.lib.opendrop_ui:main"
    ]},
)
