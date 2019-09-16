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
from pyproj.enums import PJTypes


def test_units_map():
    units_map = get_units_map()
    assert isinstance(units_map["m"], Unit)
    assert units_map["m"].id == "m"
    assert units_map["m"].name == "Meter"


def test_angular_units_map():
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
        ("IGNF", PJTypes.ELLIPSOID, False),
        ("EPSG", PJTypes.CRS, False),
        ("EPSG", PJTypes.CRS, True),
        ("PROJ", PJTypes.ELLIPSOID, False),
    ],
)
def test_get_codes(auth, pj_type, deprecated):
    assert get_codes(auth, pj_type, deprecated)


@pytest.mark.parametrize(
    "auth, pj_type",
    [("blob", 123), ("PROJ", PJTypes.BOUND_CRS), ("ITRF", PJTypes.BOUND_CRS)],
)
def test_get_codes__empty(auth, pj_type):
    assert not get_codes(auth, pj_type)


@pytest.mark.parametrize("auth, pj_type", [(123, 123), ("ITRF", "frank")])
def test_get_codes__invalid_input(auth, pj_type):
    with pytest.raises(TypeError):
        get_codes(auth, pj_type)
