import subprocess


def exists(env):
    return True


def generate(env):
    env.Tool('python')

    env['NUMPYINCLUDES'] = env.Dir(
        subprocess.check_output([
            env.subst('$PYTHON'),
            '-c',
            "import numpy; print(numpy.get_include())"
        ])
        .decode()
        .strip()
    )
