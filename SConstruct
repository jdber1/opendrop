import os


env = Environment(
    NAME='opendrop',

    PACKAGE_METADATA = {
        'Requires-Python': '>=3.6',
        'Provides-Extra': 'genicam',
        'Requires-Dist': File('requirements.txt').get_text_contents().splitlines(),
        'Home-page': 'https://github.com/jdber1/opendrop',
        'Classifier': [
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        ],
    },

    BUILDDIR='./build',
)


AddOption(
    '--build-dir',
    dest='build_dir',
    default=env.Dir('build'),
    metavar='DIR',
    help='Set DIR as the build directory.',
)


env['BUILDDIR'] = GetOption('build_dir')

env.Append(
    ENV={'PATH': os.environ['PATH']},
    CPPPATH=[env.Dir('include')],
    CCFLAGS=['-O3', '-std=c++14'],
#    CXXFLAGS=['-std=c++11'],
)

env.Tool('gitversion')
env.Tool('python')
env.Tool('pydist')


package_files = SConscript('opendrop/SConscript', exports='env')
wheel = env.WheelPackage(
    '$BUILDDIR',
    package_files,
    packages={'opendrop': './opendrop'},

    python_tag='cp%s%s' % tuple(env['PYTHONVERSION'].split('.')[:2]),
    abi_tag='abi3',
    platform_tag=env['PYTHON_DISTUTILS_PLATFORM'],
)
Alias('bdist_wheel', wheel)


c_tests = SConscript('tests/c/SConscript', exports='env')
Alias('tests', c_tests)
