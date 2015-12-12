To install:

* clone github repo or download source release at http://python.org/pypi/pyproj.
* python setup.py build
* python setup.py install (with sudo if necessary).

To test, run `python -c "import pyproj; pyproj.test()"`

For new unit tests, run `python unittest/test.py`

To use installed proj lib (and data files), 
set PROJ_DIR env var to point to location of proj installation.
before running setup.py. If PROJ_DIR is not set, bundled proj4
source code and data files are used.

Docs at http://jswhit.github.io/pyproj.

Report bugs/ask questions at https://github.com/jswhit/pyproj/issues.
