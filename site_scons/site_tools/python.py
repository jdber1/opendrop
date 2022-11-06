import os
import platform
import subprocess

from msys import native_path as _


def exists(env):
    return env.Detect('python3') or env.Detect('python')


def generate(env):
    python = os.environ.get('PYTHON', None) or env.Detect('python3') or env.Detect('python')
    env.SetDefault(PYTHON=python)

    if env['PYTHON'] is None:
        print("Could not find python executable")
        env.Exit(1)


    env['PYTHONVERSION'] = \
        subprocess.check_output([
            env.subst('$PYTHON'),
            '-Ic',
            "import sys; print('%d.%d.%d' % sys.version_info[:3])"
        ]) \
        .decode() \
        .strip()

    env['PYTHONPLATFORM'] = \
        subprocess.check_output([
            env.subst('$PYTHON'),
            '-Ic',
            "import sysconfig; print(sysconfig.get_platform())"
        ]) \
        .decode() \
        .strip()

    env['PYTHONINCLUDES'] = env.Dir(
        _(subprocess.check_output([
            env.subst('$PYTHON'),
            '-Ic',
            "import sysconfig; print(sysconfig.get_path('include'))"
        ])
        .decode()
        .strip())
    )

    env['PYTHONLIBPATH'] = env.Dir(
        _(subprocess.check_output([
            env.subst('$PYTHON'),
            '-Ic',
            "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))"
        ])
        .decode()
        .strip())
    )

    abiflags = \
        subprocess.check_output([
            env.subst('$PYTHON'),
            '-Ic',
            "import sys; print(sys.abiflags)"
        ]) \
        .decode() \
        .strip()

    if platform.system() == 'Windows':
        env['PYTHONLIB'] = 'python%s.%s%s' % (*env['PYTHONVERSION'].split('.')[:2], abiflags)
    else:
        env['PYTHONLIB'] = ''

    env['PYTHON_EXT_SUFFIX'] = \
        subprocess.check_output([
            env.subst('$PYTHON'),
            '-Ic',
            "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
        ]) \
        .decode() \
        .strip()

    paths = \
        subprocess.check_output([
            env.subst('$PYTHON'),
            '-Ic',
            "import sys; print('\\n'.join(sys.path))"
        ]) \
        .decode() \
        .strip() \
        .split('\n')
    
    env['PYTHONPATH'] = env.Dir([_(p) for p in paths if os.path.isdir(p)])
