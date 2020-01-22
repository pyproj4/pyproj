import pytest

from pyproj.crs import (
    CRS,
    CoordinateOperation,
    CoordinateSystem,
    Datum,
    Ellipsoid,
    PrimeMeridian,
)


def test_crs_to_json_dict():
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    json_dict = aeqd_crs.to_json_dict()
    assert json_dict["type"] == "ProjectedCRS"


def test_crs_to_json():
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    json_data = aeqd_crs.to_json()
    assert "ProjectedCRS" in json_data
    assert "\n" not in json_data


def test_crs_to_json__pretty():
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    json_data = aeqd_crs.to_json(pretty=True)
    assert "ProjectedCRS" in json_data
    assert json_data.startswith('{\n  "')


def test_crs_to_json__pretty__indenation():
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    json_data = aeqd_crs.to_json(pretty=True, indentation=4)
    assert "ProjectedCRS" in json_data
    assert json_data.startswith('{\n    "')


def test_crs_from_json():
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    assert CRS.from_json(aeqd_crs.to_json()) == aeqd_crs


def test_crs_from_json_dict():
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    assert CRS.from_json_dict(aeqd_crs.to_json_dict()) == aeqd_crs


@pytest.mark.parametrize(
    "property_name, expected_type",
    [
        ("coordinate_operation", "Conversion"),
        ("datum", "GeodeticReferenceFrame"),
        ("ellipsoid", "Ellipsoid"),
        ("prime_meridian", "PrimeMeridian"),
        ("coordinate_system", "CoordinateSystem"),
    ],
)
def test_properties_to_json(property_name, expected_type):
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    json_data = getattr(aeqd_crs, property_name).to_json()
    assert expected_type in json_data
    assert "\n" not in json_data


@pytest.mark.parametrize(
    "property_name, expected_type",
    [
        ("coordinate_operation", "Conversion"),
        ("datum", "GeodeticReferenceFrame"),
        ("ellipsoid", "Ellipsoid"),
        ("prime_meridian", "PrimeMeridian"),
        ("coordinate_system", "CoordinateSystem"),
    ],
)
def test_properties_to_json__pretty(property_name, expected_type):
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    json_data = getattr(aeqd_crs, property_name).to_json(pretty=True)
    assert expected_type in json_data
    assert json_data.startswith('{\n  "')


@pytest.mark.parametrize(
    "property_name, expected_type",
    [
        ("coordinate_operation", "Conversion"),
        ("datum", "GeodeticReferenceFrame"),
        ("ellipsoid", "Ellipsoid"),
        ("prime_meridian", "PrimeMeridian"),
        ("coordinate_system", "CoordinateSystem"),
    ],
)
def test_properties_to_json__pretty__indentation(property_name, expected_type):
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    json_data = getattr(aeqd_crs, property_name).to_json(pretty=True, indentation=4)
    assert expected_type in json_data
    assert json_data.startswith('{\n    "')


@pytest.mark.parametrize(
    "property_name, expected_type",
    [
        ("coordinate_operation", "Conversion"),
        ("datum", "GeodeticReferenceFrame"),
        ("ellipsoid", "Ellipsoid"),
        ("prime_meridian", "PrimeMeridian"),
    ],
)
def test_properties_to_json_dict(property_name, expected_type):
    aeqd_crs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5)
    assert getattr(aeqd_crs, property_name).to_json_dict()["type"] == expected_type


@pytest.mark.parametrize(
    "property_name, init_class",
    [
        ("coordinate_operation", CoordinateOperation),
        ("datum", Datum),
        ("ellipsoid", Ellipsoid),
        ("prime_meridian", PrimeMeridian),
    ],
)
def test_properties_from_json_dict(property_name, init_class):
    prop = getattr(CRS.from_epsg(26915), property_name)
    assert init_class.from_json_dict(prop.to_json_dict()) == prop


def test_coordinate_system_from_json_dict():
    # separate test from other properties due to
    # https://github.com/OSGeo/PROJ/issues/1818
    aeqd_cs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5).coordinate_system
    assert CoordinateSystem.from_json_dict(aeqd_cs.to_json_dict()) == aeqd_cs


def test_coordinate_system_from_json():
    # separate test from other properties due to
    # https://github.com/OSGeo/PROJ/issues/1818
    aeqd_cs = CRS(proj="aeqd", lon_0=-80, lat_0=40.5).coordinate_system
    assert CoordinateSystem.from_json(aeqd_cs.to_json()) == aeqd_cs
