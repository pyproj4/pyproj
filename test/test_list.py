from numpy.testing import assert_almost_equal

from pyproj.list import get_ellps_map, get_prime_meridians_map, get_proj_operations_map


def test_backwards_compatible_import_paths():
    from pyproj import (  # noqa: F401 pylint: disable=unused-import
        get_ellps_map,
        get_prime_meridians_map,
        get_proj_operations_map,
    )


def test_get_ellps_map():
    ellps_map = get_ellps_map()
    assert ellps_map["WGS84"]["description"] == "WGS 84"
    assert_almost_equal(ellps_map["WGS84"]["a"], 6378137.0, decimal=1)
    assert_almost_equal(ellps_map["WGS84"]["rf"], 298.257223563, decimal=1)


def test_get_prime_meridians_map():
    prime_meridians_map = get_prime_meridians_map()
    assert prime_meridians_map["greenwich"] == "0dE"


def test_get_proj_operations_map():
    proj_operations_map = get_proj_operations_map()
    assert proj_operations_map["aea"] == "Albers Equal Area"
