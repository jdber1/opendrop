from setuptools import find_packages, setup

setup(
    name='opendrop',
    version='2.0.0dev3',
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
