import pytest
from numpy.testing import assert_almost_equal

from pyproj import (
    get_angular_units_map,
    get_authorities,
    get_codes,
    get_ellps_map,
    get_prime_meridians_map,
    get_proj_operations_map,
    get_units_map,
)
from pyproj._list import Unit
from pyproj.enums import PJType


def test_units_map():
    with pytest.warns(DeprecationWarning):
        units_map = get_units_map()
    assert isinstance(units_map["m"], Unit)
    assert units_map["m"].id == "m"
    assert units_map["m"].name == "Meter"


def test_angular_units_map():
    with pytest.warns(DeprecationWarning):
        ang_map = get_angular_units_map()
    assert isinstance(ang_map["deg"], Unit)
    assert ang_map["deg"].id == "deg"
    assert ang_map["deg"].name == "Degree"


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


def test_get_authorities():
    assert "EPSG" in get_authorities()


@pytest.mark.parametrize(
    "auth, pj_type, deprecated",
    [
        ("IGNF", PJType.ELLIPSOID, False),
        ("EPSG", PJType.CRS, False),
        ("EPSG", PJType.CRS, True),
        ("PROJ", PJType.ELLIPSOID, False),
        ("IGNF", "ELLIPSOID", False),
        ("EPSG", "CRS", False),
        ("EPSG", "crs", True),
        ("PROJ", "ellipsoid", False),
    ],
)
def test_get_codes(auth, pj_type, deprecated):
    assert get_codes(auth, pj_type, deprecated)


@pytest.mark.parametrize(
    "auth, pj_type",
    [("blob", "BOUND_CRS"), ("PROJ", PJType.BOUND_CRS), ("ITRF", PJType.BOUND_CRS)],
)
def test_get_codes__empty(auth, pj_type):
    assert not get_codes(auth, pj_type)


def test_get_codes__invalid_auth():
    with pytest.raises(TypeError):
        get_codes(123, PJType.BOUND_CRS)


def test_get_codes__invalid_code():
    with pytest.raises(ValueError):
        get_codes("ITRF", "frank")
