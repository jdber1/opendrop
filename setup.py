#!/usr/bin/env python
#coding=utf-8

"""
Usage:
    python setup.py py2app

"""

from setuptools import setup

APP = ['opendrop.py']
DATA_FILES = [('', ['modules']), ('', ['data'])]
OPTIONS = {'iconfile':'opendrop.icns',}

setup(
    app = APP,
    data_files = DATA_FILES,
    options = {'py2app': OPTIONS},
    setup_requires = ['py2app'],
)


"""
config = {
    'name': 'Open Drop',

    'version': '0.1',

    'description': ( 'A python routine that implements the pendant'
        'drop method to determine the interfacial tension based on'
        'the shape of a deformed pendant drop' ),

    'url': 'http://opencolloids.com/',

    'author': 'Michael J Neeson, Joe D. Berry, Rico F Tabor',
    
    'download_url': 'http://opencolloids.com/',

    'install_requires': ['cv, cv2'],
    # 'packages': ['NAME'],
    # 'scripts': [],
}
"""
