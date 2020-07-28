from pathlib import Path
import subprocess


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    subprocess.run(['scons', '-Q', 'bdist_wheel', '--build-dir=' + wheel_directory], check=True)

    try:
        fp, = Path(wheel_directory).glob('*.whl')
    except ValueError:
        raise RuntimeError('No .whl file found in build directory')

    return fp


def build_sdist(sdist_directory, config_settings=None):
    raise NotImplementedError
