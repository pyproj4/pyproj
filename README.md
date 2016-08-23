pyproj
======

Installation
------------
* clone github repo or download source release at http://python.org/pypi/pyproj.
  * If you clone the github repo, [Cython](http://cython.org/) is a dependency.
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
[nose2](https://github.com/nose-devs/nose2) is required to run some tests.
There are two testing suites: doctests and unittests. Doctests are located in
lib/pyproj/\__init\__.py.  Unittests are located in unittest/.

To run all tests  (add `-v` option to add verbose output):
```
    nose2 [-v]
```

To run only the doctest:
```
    python -c "import pyproj; pyproj.test()"
```

To run only the unittests:
```
    python unittest/test.py [-v]
OR:
    nose2 unittest/test.py [-v]
```

Code Coverage
-------------
nose2 will automatically produce coverage for python files.  In order to
get coverage for the Cython code there are a couple extra steps needed.
Travis-CI should be set up to measure this automatically.

* Download pyproj source.
* Install Cython, and all  other testing requirements
```
  pip install -r requirements-dev.txt
```

* Add this line to top of _proj.pyx
```
  # cython: linetrace=True
```

* Set the environment variable PYPROJ_FULL_COVERAGE to any value.  This
  is only needed for installation. Most platforms `$ export PYPROJ_FULL_COVERGAGE=1`.
  Windows: `C:...> set PYPROJ_FULL_COVERGAGE=1`,

* Install in editable/development mode (python setup.py uses the `--inplace` flag)
  * Using pip, use `--upgrade` flag if pyproj is already installed.
```
    pip install [--upgrade] --editable .
```
  * Using python setup.py (this isn't well tested)
```
    python setup.py build_ext --inplace
    python setup.py install
```

Documentation
-------------
Docs are at http://jswhit.github.io/pyproj.

Bugs/Questions
--------------
Report bugs/ask questions at https://github.com/jswhit/pyproj/issues.
