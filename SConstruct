from setuptools_scm import get_version


env = Environment(
    NAME='opendrop',
    VERSION=get_version(),

    PACKAGE_METADATA = {
        'Requires-Python': '>=3.5',
        'Requires-Dist': [
            'matplotlib',
            'numpy',
            'scipy',
            'pycairo',
            'pygobject',
            'pytest',
            'setuptools',
            "typing_extensions; python_version<'3.8'",
            'injector',
            "importlib_resources; python_version<'3.7'",
        ],
        'Home-page': 'https://github.com/jdber1/opendrop',
        'Classifier': [
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        ],
    },

    BUILDDIR='./build',
)


env.Tool('pydist')

package_files = SConscript('opendrop/SConscript', exports='env')
wheel = env.WheelPackage('$BUILDDIR', package_files, packages={'opendrop': './opendrop'})


Alias('bdist_wheel', wheel)
