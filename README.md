To install:

* clone github repo or download source release at http://python.org/pypi/pyproj.
* python setup.py build
* python setup.py install (with sudo if necessary).

To test, run `python -c "import pyproj; pyproj.test()"`

For new unit tests, run:
* `python unittest/test.py`
* OR this `py.test -v unittest/test.py`
* OR under the unittests folder this `nosetests -v`

To use installed proj lib (and data files), use setup-proj.py instead
and set PROJ_DIR env var to point to location of proj installation.

Docs at http://jswhit.github.io/pyproj.

Report bugs/ask questions at https://github.com/jswhit/pyproj/issues.
