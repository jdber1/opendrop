from setuptools_scm import get_version


env = Environment(
    NAME='opendrop',
    VERSION=get_version(),

    PACKAGE_METADATA = {
        'Requires-Python': '>=3.5',
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
    default='./build',
    metavar='DIR',
    help='Set DIR as the build directory.',
)

env['BUILDDIR'] = GetOption('build_dir')

env.Tool('pydist')


package_files = SConscript('opendrop/SConscript', exports='env')
wheel = env.WheelPackage('$BUILDDIR', package_files, packages={'opendrop': './opendrop'})


Alias('bdist_wheel', wheel)
