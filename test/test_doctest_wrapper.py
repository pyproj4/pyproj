"""
This is a wrapper for the doctests in lib/pyproj/__init__.py so that
pytest can conveniently run all the tests in a single command line.
"""
import os
import platform

import pyproj


def test_doctests():
    failure_count = pyproj.test()

    # shapely wheels not on windows, so allow failures there
    expected_failure_count = 0
    try:
        import shapely  # noqa
    except ImportError:
        if os.name == "nt" or platform.uname()[4] != "x86_64":
            expected_failure_count = 6

    # if the below line fails, doctests have failed
    assert (
        failure_count == expected_failure_count
    ), "{0} of the doctests in " "lib/pyproj/__init__.py failed".format(failure_count)
