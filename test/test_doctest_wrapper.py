"""
This is a wrapper for the doctests in pyproj
"""
import doctest
import warnings

import pytest

import pyproj
from test.conftest import proj_network_env


def test_doctests():
    """run the examples in the docstrings using the doctest module"""

    with warnings.catch_warnings(), proj_network_env():
        pyproj.network.set_network_enabled(active=True)
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
    ), f"{failure_count} of the doctests failed"
