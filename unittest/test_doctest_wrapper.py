"""
This is a wrapper for the doctests in lib/pyproj/__init__.py so that
nose2 can conveniently run all the tests in a single command line.
"""

import pyproj


def test_doctests():
    failure_count = pyproj.test()
    # if the below line fails, doctests have failed
    assert (
        failure_count == 0
    ), "{0} of the doctests in " "lib/pyproj/__init__.py failed".format(failure_count)
