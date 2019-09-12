"""
This is a wrapper for the doctests in lib/pyproj/__init__.py so that
pytest can conveniently run all the tests in a single command line.
"""
import doctest
import os
import platform

import pyproj


def test_doctests():
    """run the examples in the docstrings using the doctest module"""

    failure_count_proj, test_count = doctest.testmod(pyproj.proj, verbose=True)
    failure_count_crs, test_count_crs = doctest.testmod(pyproj.crs, verbose=True)
    failure_count_geod, test_count_geod = doctest.testmod(pyproj.geod, verbose=True)
    failure_count_transform, test_count_transform = doctest.testmod(
        pyproj.transformer, verbose=True
    )

    failure_count = (
        failure_count_proj
        + failure_count_crs
        + failure_count_geod
        + failure_count_transform
    )
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
