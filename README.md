pyproj
======

Installation
------------

* clone github repo or download source release at http://python.org/pypi/pyproj.
  * [Cython](http://cython.org/) is required for the installation.

#### Setup PROJ.4

Follow installation instructions at: https://github.com/OSGeo/proj.4

Next, set the PROJ_DIR environment variable to point to location of proj4 installation before running setup.py if it is not already on the PATH.

Examples of how to set the PROJ_DIR environment variable:

* Windows - `C:\...> set PROJ_DIR=C:\OSGeo4W\`
* Linux/OS X on most shells- `$ export PROJ_DIR=/lib/`

#### Setup pyproj

##### The data directory

The order of preference for the data directory is:

1. The one set by pyproj.datadir.set_data_dir (if exists & valid)
2. The internal proj directory (if exists & valid)
3. The directory in PROJ_LIB

##### Install pyproj

From pypi:

```
pip install pyproj
```

From github:

```
pip install cython
python setup.py build
python setup.py install
```

You may need to run `sudo python setup.py install` if you have permissions issues.

From GitHub with `pip`:

```
pip install cython
pip install git+https://github.com/jswhit/pyproj.git
```

You may need to run pip with administrative privileges (e.g. `sudo pip`) or
perform a user only installation (e.g. `pip install --user`).

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
