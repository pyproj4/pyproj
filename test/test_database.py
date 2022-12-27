import pytest

from pyproj.aoi import AreaOfInterest, BBox
from pyproj.database import (
    Unit,
    get_authorities,
    get_codes,
    get_database_metadata,
    get_units_map,
    query_crs_info,
    query_utm_crs_info,
)
from pyproj.enums import PJType
from test.conftest import PROJ_GTE_92


def test_backwards_compatible_import_paths():
    from pyproj import (  # noqa: F401 pylint: disable=unused-import
        get_authorities,
        get_codes,
        get_units_map,
    )


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


def test_get_codes__derived_projected_crs():
    if PROJ_GTE_92:
        assert not get_codes("EPSG", PJType.DERIVED_PROJECTED_CRS)
    else:
        with pytest.raises(
            NotImplementedError, match="DERIVED_PROJECTED_CRS requires PROJ 9.2+"
        ):
            get_codes("EPSG", PJType.DERIVED_PROJECTED_CRS)


def test_get_codes__invalid_auth():
    with pytest.raises(TypeError):
        get_codes(123, PJType.BOUND_CRS)


def test_get_codes__invalid_code():
    with pytest.raises(ValueError):
        get_codes("ITRF", "frank")


@pytest.mark.parametrize(
    "auth, pj_type, deprecated",
    [
        (None, None, False),
        ("EPSG", PJType.PROJECTED_CRS, False),
        ("EPSG", PJType.PROJECTED_CRS, True),
        ("IGNF", [PJType.GEOGRAPHIC_3D_CRS, PJType.GEOGRAPHIC_2D_CRS], False),
        ("EPSG", "PROJECTED_CRS", False),
        ("EPSG", "Projected_Crs", True),
    ],
)
def test_query_crs_info(auth, pj_type, deprecated):
    crs_info_list = query_crs_info(auth, pj_type, allow_deprecated=deprecated)
    assert crs_info_list
    any_deprecated = any(crs_info.deprecated for crs_info in crs_info_list)
    if deprecated:
        assert any_deprecated
    else:
        assert not any_deprecated


def test_query_crs_info__derived_projected_crs():
    if PROJ_GTE_92:
        assert not query_crs_info(pj_types=PJType.DERIVED_PROJECTED_CRS)
    else:
        with pytest.raises(
            NotImplementedError, match="DERIVED_PROJECTED_CRS requires PROJ 9.2+"
        ):
            query_crs_info(pj_types=PJType.DERIVED_PROJECTED_CRS)


@pytest.mark.parametrize(
    "auth, pj_type",
    [
        ("blob", "BOUND_CRS"),
        ("IGNF", PJType.ELLIPSOID),
        ("PROJ", PJType.BOUND_CRS),
        ("ITRF", PJType.BOUND_CRS),
    ],
)
def test_query_crs_info__empty(auth, pj_type):
    assert not query_crs_info(auth, pj_type)


def test_query_crs_info__invalid_auth():
    with pytest.raises(TypeError):
        query_crs_info(123, PJType.BOUND_CRS)


def test_query_crs_info__invalid_code():
    with pytest.raises(ValueError):
        query_crs_info("ITRF", "frank")


def test_query_crs_info__aoi():
    aoi = BBox(west=-40, south=50, east=-20, north=70)
    crs_info_list = query_crs_info(
        auth_name="ESRI",
        pj_types=PJType.PROJECTED_CRS,
        area_of_interest=AreaOfInterest(
            west_lon_degree=aoi.west,
            south_lat_degree=aoi.south,
            east_lon_degree=aoi.east,
            north_lat_degree=aoi.north,
        ),
    )
    assert crs_info_list
    not_contains_present = False
    for crs_info in crs_info_list:
        bbox = BBox(*crs_info.area_of_use.bounds)
        assert bbox.intersects(aoi)
        assert crs_info.auth_name == "ESRI"
        assert crs_info.type == PJType.PROJECTED_CRS
        assert not crs_info.deprecated
        if not bbox.contains(aoi):
            not_contains_present = True
    assert not_contains_present


def test_query_crs_info__aoi_contains():
    aoi = BBox(west=-40, south=50, east=-20, north=70)
    crs_info_list = query_crs_info(
        auth_name="IGNF",
        pj_types=[PJType.PROJECTED_CRS],
        area_of_interest=AreaOfInterest(
            west_lon_degree=aoi.west,
            south_lat_degree=aoi.south,
            east_lon_degree=aoi.east,
            north_lat_degree=aoi.north,
        ),
        contains=True,
    )
    assert crs_info_list
    for crs_info in crs_info_list:
        assert BBox(*crs_info.area_of_use.bounds).contains(aoi)
        assert crs_info.auth_name == "IGNF"
        assert crs_info.type == PJType.PROJECTED_CRS
        assert not crs_info.deprecated


@pytest.mark.parametrize("datum_name", ["WGS 84", "WGS84", "NAD27", "NAD83"])
def test_query_utm_crs_info__aoi_datum_name(datum_name):
    aoi = BBox(west=-93.581543, south=42.032974, east=-93.581543, north=42.032974)
    crs_info_list = query_utm_crs_info(
        datum_name=datum_name,
        area_of_interest=AreaOfInterest(
            west_lon_degree=aoi.west,
            south_lat_degree=aoi.south,
            east_lon_degree=aoi.east,
            north_lat_degree=aoi.north,
        ),
    )
    assert len(crs_info_list) == 1
    crs_info = crs_info_list[0]
    bbox = BBox(*crs_info.area_of_use.bounds)
    assert bbox.intersects(aoi)
    assert "UTM zone" in crs_info.name
    assert datum_name.replace(" ", "") in crs_info.name.replace(" ", "")
    assert crs_info.auth_name == "EPSG"
    assert crs_info.type == PJType.PROJECTED_CRS
    assert not crs_info.deprecated


def test_query_utm_crs_info__aoi_contains():
    aoi = BBox(west=41, south=50, east=42, north=51)
    crs_info_list = query_utm_crs_info(
        area_of_interest=AreaOfInterest(
            west_lon_degree=aoi.west,
            south_lat_degree=aoi.south,
            east_lon_degree=aoi.east,
            north_lat_degree=aoi.north,
        ),
        contains=True,
    )
    assert crs_info_list
    for crs_info in crs_info_list:
        assert BBox(*crs_info.area_of_use.bounds).contains(aoi)
        assert "UTM zone" in crs_info.name
        assert crs_info.auth_name == "EPSG"
        assert crs_info.type == PJType.PROJECTED_CRS
        assert not crs_info.deprecated


def test_get_database_metadata():
    epsg_version = get_database_metadata("EPSG.VERSION")
    assert epsg_version
    assert isinstance(epsg_version, str)


def test_get_database_metadata__invalid():
    assert get_database_metadata("doesnotexist") is None
