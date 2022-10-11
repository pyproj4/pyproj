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
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            "You will likely lose important projection information when",
            UserWarning,
        )

        failure_count_proj, test_count = doctest.testmod(pyproj.proj, verbose=True)
        failure_count_crs, test_count_crs = doctest.testmod(pyproj.crs, verbose=True)
        failure_count_geod, test_count_geod = doctest.testmod(pyproj.geod, verbose=True)

    failure_count = failure_count_proj + failure_count_crs + failure_count_geod
    expected_failure_count = 0
    try:
        import shapely.geometry  # noqa: F401 pylint: disable=unused-import
    except (ImportError, OSError):
        # missing shapely
        expected_failure_count = 6

    # if the below line fails, doctests have failed
    assert (
        failure_count == expected_failure_count
    ), f"{failure_count} of the doctests failed"


@pytest.mark.network
def test_doctests__network():
    """run the examples in the docstrings using the doctest module
    that require the network
    """
    with proj_network_env():
        pyproj.network.set_network_enabled(active=True)
        with pytest.warns(FutureWarning):
            failure_count, _ = doctest.testmod(pyproj.transformer, verbose=True)

    assert failure_count == 0, f"{failure_count} of the doctests failed"
