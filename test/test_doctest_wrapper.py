"""
This is a wrapper for the doctests in pyproj
"""
import doctest
import warnings

import pytest

import pyproj


def test_doctests():
    """run the examples in the docstrings using the doctest module"""

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            "You will likely lose important projection information when",
            UserWarning,
        )

        failure_count_proj, test_count = doctest.testmod(pyproj.proj, verbose=True)
        failure_count_crs, test_count_crs = doctest.testmod(pyproj.crs, verbose=True)
        failure_count_geod, test_count_geod = doctest.testmod(pyproj.geod, verbose=True)
        with pytest.warns(DeprecationWarning):
            failure_count_transform, test_count_transform = doctest.testmod(
                pyproj.transformer, verbose=True
            )

    failure_count = (
        failure_count_proj
        + failure_count_crs
        + failure_count_geod
        + failure_count_transform
    )
    expected_failure_count = 0
    try:
        import shapely  # noqa
    except ImportError:
        # missing shapely
        expected_failure_count = 6

    # if the below line fails, doctests have failed
    assert (
        failure_count == expected_failure_count
    ), "{0} of the doctests in " "lib/pyproj/__init__.py failed".format(failure_count)
