# Contributing to OpenDrop

Thank you for taking the time to contribute.

We welcome all contributions such as:

* Bug reports
* Feature proposals
* Code patches

OpenDrop is licensed under [GNU GPLv3](https://github.com/jdber1/opendrop/blob/master/LICENSE).

## Bug reports and feature proposals

Please submit any bug reports and feature proposals by opening a new [GitHub issue](https://github.com/jdber1/opendrop/issues). Try to do a brief search of existing issues to see if the problem has already been raised to avoid duplicates. Include any information you think is relevant for replicating a bug, we will follow up for more details if needed.

Any other queries or help can be asked by creating a new issue as well.

## Contributing code

Code contributions are accepted via pull requests. Before making large changes however, please create a new issue so that we can discuss any proposed changes. Try to keep modifications focused and avoid correcting formatting changes in irrelevant code, this will make it easier to see what has actually changed.

We currently aim to support Python versions 3.5 and above.

### Preparing a development environment

Make sure your system has GTK+ 3 installed.

1. Clone the repository.
2. Create a new Python virtual environment (e.g. in the '.venv/' subdirectory of the project root).
3. Install the app's Python dependencies with `pip install -r requirements.txt` and manually install the OpenCV Python bindings to the virtual environment. Also install the build dependencies [setuptools_scm](https://pypi.org/project/setuptools-scm/) and [Scons](https://pypi.org/project/SCons/).
4. Add the project root to the Python path using a .pth [path configuration file](https://docs.python.org/3/library/site.html). This will let you test the app as you develop.

### Developing

OpenDrop makes use of some GLib compiled resource features. Whenever a .ui file or a file in the 'opendrop/assets/' directory is modified, the GLib resource bundle needs to be rebuilt. This is done by running `scons opendrop/data.gresource` in the project root.

Versioning is managed by setuptools_scm.

### Code style

There is no stringent coding style in place. Mainly just follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) conventions and maintain a column width of around 110 (not strict).

Please include type annotations that are "as descriptive as possible" unless exact type-safety is overly arduous.
