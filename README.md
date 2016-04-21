pyproj
======

Installation
------------
* clone github repo or download source release at http://python.org/pypi/pyproj.
* python setup.py build
* python setup.py install (with sudo if necessary).

To use proj4 lib (and data files) that are already installed on the system, 
set PROJ_DIR environment variable to point to location of proj4 installation
before running setup.py. If PROJ_DIR is not set, the bundled proj4
source code and data files are used.

Examples of how to set the PROJ_DIR environment variable:
* Windows - `C:\...> set PROJ_DIR=C:\OSGeo4W\`
* Linux/OS X on most shells- `$ export PROJ_DIR=/lib/`

Testing
-------
To test, run `python -c "import pyproj; pyproj.test()"`

For new unit tests, run `python unittest/test.py`

Documentation
-------------
Docs are at http://jswhit.github.io/pyproj.

Bugs/Questions
--------------
Report bugs/ask questions at https://github.com/jswhit/pyproj/issues.
