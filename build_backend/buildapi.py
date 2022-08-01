import os
from pathlib import Path
import subprocess
import sys


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    env = os.environ.copy()
    if sys.executable is not None:
        env['PYTHON'] = sys.executable

    subprocess.run(['scons', '-Q', 'bdist_wheel', '--build-dir=' + wheel_directory], check=True, env=env)

    try:
        fp, = Path(wheel_directory).glob('*.whl')
    except ValueError:
        raise RuntimeError('No .whl file found in build directory')

    return fp


def build_sdist(sdist_directory, config_settings=None):
    raise NotImplementedError
