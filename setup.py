from setuptools import find_packages, setup

setup(
    name='opendrop',
    version='3.1.6dev0',
    packages=find_packages(exclude=['tests', 'manual_tests', 'docs']),
    package_data={
        'opendrop.res': ['images/*']
    },
    entry_points={
        'console_scripts': 'opendrop=opendrop.app:main'
    },
    install_requires=[
        'matplotlib',
        'numpy',
        'scipy',
        'pycairo',
        'pygobject',
        'pytest',
        'setuptools',
        'typing_extensions',
    ]
)
