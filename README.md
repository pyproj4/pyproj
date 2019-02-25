pyproj
======

Installation
------------

#### Setup PROJ.4

Follow installation instructions at: https://github.com/OSGeo/proj.4

In the setup.py, the order for searching for PROJ.4 is:

    1. The PROJ_DIR environment variable
    2. The internal PROJ.4 directory (pyproj/proj_dir)
    3. The `proj` executable on the PATH.

For best results, set the PROJ_DIR environment variable to 
point to location of PROJ.4 installation before running setup.py.

Examples of how to set the PROJ_DIR environment variable:

* Windows - `C:\...> set PROJ_DIR=C:\OSGeo4W\`
* Linux/OS X on most shells- `$ export PROJ_DIR=/lib/`

If you have a previous version of PROJ.4 installed alongside the current
version of PROJ.4 (6.0.0), the best way to avoid conflicts is to:

    1. Remove the previous PROJ.4 from PATH & unset old PROJ_LIB environment variable (temporarily)
    2. Install PROJ.4 to the internal PROJ.4 directory (pyproj/proj_dir)
    3. Set the environment variable PROJ_DIR to point to the internal PROJ.4 directory
    4. Set the environment variable PROJ_WHEEL=true
    5. Build pyproj

#### Setup pyproj

##### The data directory

The order of preference for the data directory is:

1. The one set by pyproj.datadir.set_data_dir (if exists & valid)
2. The internal proj directory (if exists & valid)
3. The directory in the PROJ_LIB environment variable (if exists & valid)

##### Install pyproj

* [Cython](http://cython.org/) or pip>=10.0.1 is required for the installation.

Note: You may need to run pip with administrative privileges (e.g. `sudo pip`) or
perform a user only installation (e.g. `pip install --user`).


From pypi:

```
pip install pyproj
```

From GitHub with `pip`:

```
pip install git+https://github.com/jswhit/pyproj.git
```

From cloned GitHub repo for development:

```
pip install -e .
```


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
