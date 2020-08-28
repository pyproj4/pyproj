import pytest
from numpy.testing import assert_almost_equal

from pyproj import (
    get_authorities,
    get_codes,
    get_ellps_map,
    get_prime_meridians_map,
    get_proj_operations_map,
    get_units_map,
)
from pyproj._list import Unit
from pyproj.enums import PJType


def test_units_map__default():
    units_map = get_units_map()
    assert isinstance(units_map["metre"], Unit)
    assert units_map["metre"].name == "metre"
    assert units_map["metre"].auth_name == "EPSG"
    assert units_map["metre"].code == "9001"
    assert units_map["metre"].category == "linear"
    assert units_map["metre"].conv_factor == 1
    assert units_map["metre"].proj_short_name == "m"
    assert not units_map["metre"].deprecated
    any_deprecated = False
    for item in units_map.values():
        any_deprecated = any_deprecated or item.deprecated
    assert not any_deprecated


@pytest.mark.parametrize(
    "category",
    [
        "linear",
        "linear_per_time",
        "angular",
        "angular_per_time",
        "scale",
        "scale_per_time",
        "time",
    ],
)
def test_units_map__category(category):
    units_map = get_units_map(category=category)
    assert len(units_map) > 1
    for item in units_map.values():
        assert item.category == category


@pytest.mark.parametrize("auth_name", ["EPSG", "PROJ"])
def test_units_map__auth_name(auth_name):
    units_map = get_units_map(auth_name=auth_name)
    assert len(units_map) > 1
    for item in units_map.values():
        assert item.auth_name == auth_name


@pytest.mark.parametrize("deprecated", ["zzz", "True", True])
def test_units_map__deprecated(deprecated):
    units_map = get_units_map(allow_deprecated=deprecated)
    assert len(units_map) > 1
    any_deprecated = False
    for item in units_map.values():
        any_deprecated = any_deprecated or item.deprecated
    assert any_deprecated


@pytest.mark.parametrize("auth_name, category", [(None, 1), (1, None)])
def test_units_map__invalid(auth_name, category):
    with pytest.raises(TypeError):
        get_units_map(auth_name=auth_name, category=category)


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
