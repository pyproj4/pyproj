import concurrent.futures
import json
import platform
from unittest.mock import patch

import numpy
import pytest

import pyproj
from pyproj import CRS
from pyproj._crs import AuthorityMatchInfo
from pyproj.crs import (
    CoordinateOperation,
    CoordinateSystem,
    Datum,
    Ellipsoid,
    PrimeMeridian,
)
from pyproj.crs.enums import CoordinateOperationType, DatumType
from pyproj.enums import ProjVersion, WktVersion
from pyproj.exceptions import CRSError
from pyproj.transformer import TransformerGroup
from test.conftest import (
    PROJ_GTE_91,
    PROJ_GTE_901,
    PROJ_GTE_911,
    assert_can_pickle,
    grids_available,
)


class CustomCRS(object):
    def to_wkt(self):
        return CRS.from_epsg(4326).to_wkt()


def test_from_proj4_json():
    json_str = '{"proj": "longlat", "ellps": "WGS84", "datum": "WGS84"}'
    proj = CRS.from_string(json_str)
    with pytest.warns(UserWarning):
        assert proj.to_proj4(4) == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
        assert proj.to_proj4(5) == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
    # Test with invalid JSON code
    with pytest.raises(CRSError):
        assert CRS.from_string("{foo: bar}")


def test_from_proj4():
    proj = CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs +type=crs")
    with pytest.warns(UserWarning):
        assert proj.to_proj4() == "+proj=longlat +datum=WGS84 +no_defs +type=crs"


def test_from_proj4__invalid():
    # Test with invalid JSON code
    with pytest.raises(CRSError):
        assert CRS.from_proj4(CRS(3857).to_wkt())


def test_from_epsg():
    proj = CRS.from_epsg(4326)
    assert proj.to_epsg() == 4326

    # Test with invalid EPSG code
    with pytest.raises(CRSError):
        assert CRS.from_epsg(0)


def test_from_epsg_string():
    proj = CRS.from_string("epsg:4326")
    assert proj.to_epsg() == 4326

    # Test with invalid EPSG code
    with pytest.raises(CRSError):
        assert CRS.from_string("epsg:xyz")


def test_from_epsg_int_like_string():
    proj = CRS.from_string("4326")
    assert proj.to_epsg() == 4326

    # Test with invalid EPSG code
    with pytest.raises(CRSError):
        assert CRS.from_string("0")


def test_from_string():
    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    with pytest.warns(UserWarning):
        assert wgs84_crs.to_proj4() == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
    # Make sure this doesn't get handled using the from_epsg()
    # even though 'epsg' is in the string
    with pytest.warns(FutureWarning):
        epsg_init_crs = CRS.from_string("+init=epsg:26911 +units=m +no_defs=True")
    with pytest.warns(UserWarning):
        assert (
            epsg_init_crs.to_proj4()
            == "+proj=utm +zone=11 +datum=NAD83 +units=m +no_defs +type=crs"
        )


def test_from_numpy():
    crs_numpy = numpy.array([4326])[0]
    proj = CRS.from_user_input(crs_numpy)
    assert proj.to_epsg() == 4326

    # Test with invalid EPSG code
    with pytest.raises(CRSError):
        crs_numpy = numpy.array([0])[0]
        assert CRS.from_epsg(crs_numpy)


def test_from_string__invalid():
    with pytest.raises(CRSError, match="CRS input is not a string"):
        CRS.from_string(4326)


def test_initialize_projparams_with_kwargs():
    crs_mixed_args = CRS("+proj=utm +zone=10", ellps="WGS84")
    crs_positional = CRS("+proj=utm +zone=10 +ellps=WGS84")
    assert crs_mixed_args.is_exact_same(crs_positional)


def test_bare_parameters():
    """Make sure that bare parameters (e.g., no_defs) are handled properly,
    even if they come in with key=True.  This covers interaction with pyproj,
    which makes presents bare parameters as key=<bool>."""

    # Example produced by pyproj
    proj = CRS.from_string(
        "+proj=lcc +lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True "
        "+x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    with pytest.warns(UserWarning):
        assert "+no_defs" in proj.to_proj4(4)

    # TODO: THIS DOES NOT WORK
    proj = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +proj=lcc +y_0=0 +no_defs=False "
        "+x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    # assert "+no_defs" not in proj.to_proj4(4)


def test_is_geographic():
    assert CRS("EPSG:4326").is_geographic is True
    assert CRS("EPSG:3857").is_geographic is False

    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    assert wgs84_crs.is_geographic is True

    nad27_crs = CRS.from_string("+proj=longlat +ellps=clrk66 +datum=NAD27 +no_defs")
    assert nad27_crs.is_geographic is True

    lcc_crs = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc +x_0=0 "
        "+units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    assert lcc_crs.is_geographic is False


def test_is_projected():
    assert CRS("EPSG:3857").is_projected is True

    lcc_crs = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc +x_0=0 "
        "+units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    assert CRS.from_user_input(lcc_crs).is_projected is True

    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    assert CRS.from_user_input(wgs84_crs).is_projected is False


def test_is_compound():
    assert CRS("EPSG:4326+5773").is_compound
    assert not CRS("EPSG:4326").is_compound


def test_is_same_crs():
    crs1 = CRS("urn:ogc:def:crs:OGC::CRS84")
    crs2 = CRS("EPSG:3857")

    assert crs1 == crs1
    assert crs1 != crs2

    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84")
    assert crs1 == wgs84_crs

    # Make sure that same projection with different parameter are not equal
    lcc_crs1 = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc "
        "+x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    lcc_crs2 = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc "
        "+x_0=0 +units=m +lat_2=77 +lat_1=45 +lat_0=0"
    )
    assert lcc_crs1 != lcc_crs2


def test_to_proj4():
    with pytest.warns(UserWarning):
        assert (
            CRS("EPSG:4326").to_proj4(4)
            == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
        )


def test_empty_json():
    with pytest.raises(CRSError):
        CRS.from_string("{}")
    with pytest.raises(CRSError):
        CRS.from_string("[]")
    with pytest.raises(CRSError):
        CRS.from_string("")


def test_has_wkt_property():
    with pytest.warns(FutureWarning):
        assert (
            CRS({"init": "EPSG:4326"})
            .to_wkt("WKT1_GDAL")
            .startswith('GEOGCS["WGS 84",DATUM')
        )


def test_to_wkt_pretty():
    crs = CRS.from_epsg(4326)
    assert "\n" in crs.to_wkt(pretty=True)
    assert "\n" not in crs.to_wkt()


def test_repr():
    with pytest.warns(FutureWarning):
        assert repr(CRS({"init": "EPSG:4326"})) == (
            "<Geographic 2D CRS: +init=epsg:4326 +type=crs>\n"
            "Name: WGS 84\n"
            "Axis Info [ellipsoidal]:\n"
            "- lon[east]: Longitude (degree)\n"
            "- lat[north]: Latitude (degree)\n"
            "Area of Use:\n"
            "- name: World.\n"
            "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
            "Datum: World Geodetic System 1984 ensemble\n"
            "- Ellipsoid: WGS 84\n"
            "- Prime Meridian: Greenwich\n"
        )


def test_repr__long():
    with pytest.warns(FutureWarning):
        wkt_str = 'GEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1'
        assert repr(CRS(CRS({"init": "EPSG:4326"}).to_wkt())) == (
            f"<Geographic 2D CRS: {wkt_str} ...>\n"
            "Name: WGS 84\n"
            "Axis Info [ellipsoidal]:\n"
            "- lon[east]: Longitude (degree)\n"
            "- lat[north]: Latitude (degree)\n"
            "Area of Use:\n"
            "- name: World.\n"
            "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
            "Datum: World Geodetic System 1984 ensemble\n"
            "- Ellipsoid: WGS 84\n"
            "- Prime Meridian: Greenwich\n"
        )


def test_repr_epsg():
    assert repr(CRS(CRS("EPSG:4326").to_wkt())) == (
        "<Geographic 2D CRS: EPSG:4326>\n"
        "Name: WGS 84\n"
        "Axis Info [ellipsoidal]:\n"
        "- Lat[north]: Geodetic latitude (degree)\n"
        "- Lon[east]: Geodetic longitude (degree)\n"
        "Area of Use:\n"
        "- name: World.\n"
        "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
        "Datum: World Geodetic System 1984 ensemble\n"
        "- Ellipsoid: WGS 84\n"
        "- Prime Meridian: Greenwich\n"
    )


def test_repr__undefined():
    datum_name = "unknown"
    if PROJ_GTE_901:
        datum_name = f"{datum_name} using nadgrids=@null"
    assert repr(
        CRS(
            "+proj=merc +a=6378137.0 +b=6378137.0 +nadgrids=@null"
            " +lon_0=0.0 +x_0=0.0 +y_0=0.0 +units=m +no_defs"
        )
    ) == (
        "<Bound CRS: +proj=merc +a=6378137.0 +b=6378137.0 +nadgrids=@nu ...>\n"
        "Name: unknown\n"
        "Axis Info [cartesian]:\n"
        "- E[east]: Easting (metre)\n"
        "- N[north]: Northing (metre)\n"
        "Area of Use:\n"
        "- undefined\n"
        "Coordinate Operation:\n"
        "- name: unknown to WGS84\n"
        "- method: NTv2\n"
        f"Datum: {datum_name}\n"
        "- Ellipsoid: unknown\n"
        "- Prime Meridian: Greenwich\n"
        "Source CRS: unknown\n"
    )


def test_repr_compound():
    assert repr(CRS.from_epsg(3901)) == (
        "<Compound CRS: EPSG:3901>\n"
        "Name: KKJ / Finland Uniform Coordinate System + N60 height\n"
        "Axis Info [cartesian|vertical]:\n"
        "- X[north]: Northing (metre)\n"
        "- Y[east]: Easting (metre)\n"
        "- H[up]: Gravity-related height (metre)\n"
        "Area of Use:\n"
        "- name: Finland - onshore.\n"
        "- bounds: (19.24, 59.75, 31.59, 70.09)\n"
        "Datum: Kartastokoordinaattijarjestelma (1966)\n"
        "- Ellipsoid: International 1924\n"
        "- Prime Meridian: Greenwich\n"
        "Sub CRS:\n"
        "- KKJ / Finland Uniform Coordinate System\n"
        "- N60 height\n"
    )


def test_axis_info_compound():
    assert [axis.direction for axis in CRS.from_epsg(3901).axis_info] == [
        "north",
        "east",
        "up",
    ]


def test_dunder_str():
    with pytest.warns(FutureWarning):
        assert str(CRS({"init": "EPSG:4326"})) == CRS({"init": "EPSG:4326"}).srs


def test_epsg():
    with pytest.warns(FutureWarning):
        assert CRS({"init": "EPSG:4326"}).to_epsg(20) == 4326
        assert CRS({"init": "EPSG:4326"}).to_epsg() is None
    assert CRS.from_user_input(4326).to_epsg() == 4326
    assert CRS.from_epsg(4326).to_epsg() == 4326
    assert CRS.from_user_input("epsg:4326").to_epsg() == 4326


def test_datum():
    datum = CRS.from_epsg(4326).datum
    assert "\n" in repr(datum)
    datum_wkt = 'ENSEMBLE["World Geodetic System 1984 ensemble"'
    assert repr(datum).startswith(datum_wkt)
    assert datum.to_wkt().startswith(datum_wkt)
    assert datum == datum
    assert datum.is_exact_same(datum)


def test_datum_horizontal():
    assert CRS.from_epsg(5972).datum == CRS.from_epsg(25832).datum


def test_datum_unknown():
    crs = CRS(
        "+proj=omerc +lat_0=-36.10360962430914 "
        "+lonc=147.06322917270154 +alpha=-54.786229796129035 "
        "+k=1 +x_0=0 +y_0=0 +gamma=0 +ellps=WGS84 "
        "+towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
    )
    datum_name = "Unknown based on WGS84 ellipsoid"
    if PROJ_GTE_901:
        datum_name = f"{datum_name} using towgs84=0,0,0,0,0,0,0"
    assert crs.datum.name == datum_name


def test_epsg__not_found():
    assert CRS("+proj=longlat +datum=WGS84 +no_defs +towgs84=0,0,0").to_epsg(0) is None
    assert (
        CRS.from_string("+proj=longlat +datum=WGS84 +no_defs +towgs84=0,0,0").to_epsg()
        is None
    )


def test_epsg__no_code_available():
    lcc_crs = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc "
        "+x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    assert lcc_crs.to_epsg() is None


def test_crs_OSR_equivalence():
    crs1 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs")
    crs2 = CRS.from_string("+proj=latlong +datum=WGS84 +no_defs")
    with pytest.warns(FutureWarning):
        crs3 = CRS({"init": "EPSG:4326"})
    assert crs1 == crs2
    # these are not equivalent in proj.4 now as one uses degrees and the other radians
    assert crs1 == crs3


def test_crs_OSR_no_equivalence():
    crs1 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs")
    crs2 = CRS.from_string("+proj=longlat +datum=NAD27 +no_defs")
    assert crs1 != crs2


def test_init_from_wkt():
    wgs84 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs")
    from_wkt = CRS(wgs84.to_wkt())
    assert wgs84.to_wkt() == from_wkt.to_wkt()


def test_init_from_wkt_invalid():
    with pytest.raises(CRSError):
        CRS("trash-54322")
    with pytest.raises(CRSError):
        CRS("")


def test_from_wkt():
    wgs84 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs")
    from_wkt = CRS.from_wkt(wgs84.to_wkt())
    assert wgs84.to_wkt() == from_wkt.to_wkt()


def test_from_wkt_invalid():
    with pytest.raises(CRSError), pytest.warns(UserWarning):
        CRS.from_wkt(CRS(4326).to_proj4())


def test_from_user_input_epsg():
    with pytest.warns(UserWarning):
        assert "+proj=longlat" in CRS.from_user_input("EPSG:4326").to_proj4(4)


def test_from_esri_wkt():
    projection_string = (
        'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic_USGS_version",'
        'GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",'
        'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
        'PRIMEM["Greenwich",0.0],'
        'UNIT["Degree",0.0174532925199433]],'
        'PROJECTION["Albers"],'
        'PARAMETER["false_easting",0.0],'
        'PARAMETER["false_northing",0.0],'
        'PARAMETER["central_meridian",-96.0],'
        'PARAMETER["standard_parallel_1",29.5],'
        'PARAMETER["standard_parallel_2",45.5],'
        'PARAMETER["latitude_of_origin",23.0],'
        'UNIT["Meter",1.0],'
        'VERTCS["NAVD_1988",'
        'VDATUM["North_American_Vertical_Datum_1988"],'
        'PARAMETER["Vertical_Shift",0.0],'
        'PARAMETER["Direction",1.0],UNIT["Centimeter",0.01]]]'
    )
    proj_crs_str = CRS.from_string(projection_string)
    proj_crs_wkt = CRS(projection_string)
    with pytest.warns(UserWarning):
        assert proj_crs_str.to_proj4() == proj_crs_wkt.to_proj4()
        assert proj_crs_str.to_proj4(4) == (
            "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 "
            "+lat_2=45.5 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs +type=crs"
        )


def test_compound_crs():
    wkt = """COMPD_CS["unknown",GEOGCS["WGS 84",DATUM["WGS_1984",
             SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],
             TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6326"]],
             PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],
             AUTHORITY["EPSG","4326"]],VERT_CS["unknown",
             VERT_DATUM["unknown",2005],UNIT["metre",1.0,
             AUTHORITY["EPSG","9001"]],AXIS["Up",UP]]]"""
    assert CRS(wkt).to_wkt("WKT1_GDAL").startswith('COMPD_CS["unknown",GEOGCS["WGS 84"')


def test_ellipsoid():
    crs1 = CRS.from_epsg(4326)
    assert f"{crs1.ellipsoid.inverse_flattening:.3f}" == "298.257"
    assert f"{crs1.ellipsoid.semi_major_metre:.3f}" == "6378137.000"
    assert f"{crs1.ellipsoid.semi_minor_metre:.3f}" == "6356752.314"


def test_ellipsoid__semi_minor_not_computed():
    cc = CRS("+proj=geos +lon_0=-89.5 +a=6378137.0 +b=6356752.31 h=12345")
    assert cc.datum.ellipsoid.semi_minor_metre == 6356752.31
    assert cc.datum.ellipsoid.semi_major_metre == 6378137.0
    assert not cc.datum.ellipsoid.is_semi_minor_computed


def test_area_of_use():
    crs1 = CRS.from_epsg(4326)
    assert crs1.area_of_use.bounds == (-180.0, -90.0, 180.0, 90.0)
    assert crs1.area_of_use.name == "World."


def test_from_user_input_custom_crs_class():
    assert CRS.from_user_input(CustomCRS()) == CRS.from_epsg(4326)


def test_non_crs_error():
    with pytest.raises(CRSError, match="Input is not a CRS"):
        CRS(
            "+proj=pipeline +ellps=GRS80 +step +proj=merc "
            "+step +proj=axisswap +order=2,1"
        )


def test_sub_crs():
    crs = CRS.from_epsg(5972)
    sub_crs_list = crs.sub_crs_list
    assert len(sub_crs_list) == 2
    assert sub_crs_list[0] == CRS.from_epsg(25832)
    assert sub_crs_list[1] == CRS.from_epsg(5941)
    assert crs.is_projected
    assert crs.is_vertical
    assert not crs.is_geographic


def test_sub_crs__none():
    assert CRS.from_epsg(4326).sub_crs_list == []


def test_coordinate_system():
    crs = CRS.from_epsg(26915)
    assert repr(crs.coordinate_system).startswith("CS[Cartesian")
    assert crs.coordinate_system.name == "cartesian"
    assert crs.coordinate_system.name == str(crs.coordinate_system)
    assert crs.coordinate_system.axis_list == crs.axis_info
    assert len(crs.coordinate_system.axis_list) == 2


def test_coordinate_system_geog():
    crs = CRS.from_epsg(4326)
    assert repr(crs.coordinate_system).startswith("CS[ellipsoidal")
    assert crs.coordinate_system.name == "ellipsoidal"
    assert crs.coordinate_system.name == str(crs.coordinate_system)
    assert crs.coordinate_system.axis_list == crs.axis_info
    assert repr(crs.coordinate_system.axis_list) == (
        "[Axis(name=Geodetic latitude, abbrev=Lat, direction=north, "
        "unit_auth_code=EPSG, unit_code=9122, unit_name=degree), "
        "Axis(name=Geodetic longitude, abbrev=Lon, direction=east, "
        "unit_auth_code=EPSG, unit_code=9122, unit_name=degree)]"
    )


def test_coordinate_operation():
    crs = CRS.from_epsg(26915)
    assert repr(crs.coordinate_operation) == (
        "<Coordinate Operation: Conversion>\n"
        "Name: UTM zone 15N\n"
        "Method: Transverse Mercator\n"
        "Area of Use:\n"
        "- name: Between 96°W and 90°W, northern hemisphere between equator and 84°N, "
        "onshore and offshore.\n"
        "- bounds: (-96.0, 0.0, -90.0, 84.0)"
    )
    assert crs.coordinate_operation.method_name == "Transverse Mercator"
    assert crs.coordinate_operation.name == str(crs.coordinate_operation)
    assert crs.coordinate_operation.method_auth_name == "EPSG"
    assert crs.coordinate_operation.method_code == "9807"
    assert crs.coordinate_operation.is_instantiable == 1
    assert crs.coordinate_operation.has_ballpark_transformation == 0
    assert crs.coordinate_operation.accuracy == -1.0
    assert repr(crs.coordinate_operation.params) == (
        "[Param(name=Latitude of natural origin, auth_name=EPSG, code=8801, "
        "value=0.0, unit_name=degree, unit_auth_name=EPSG, "
        "unit_code=9102, unit_category=angular), "
        "Param(name=Longitude of natural origin, auth_name=EPSG, code=8802, "
        "value=-93.0, unit_name=degree, unit_auth_name=EPSG, "
        "unit_code=9102, unit_category=angular), "
        "Param(name=Scale factor at natural origin, auth_name=EPSG, code=8805, "
        "value=0.9996, unit_name=unity, unit_auth_name=EPSG, "
        "unit_code=9201, unit_category=scale), "
        "Param(name=False easting, auth_name=EPSG, code=8806, value=500000.0, "
        "unit_name=metre, unit_auth_name=EPSG, unit_code=9001, unit_category=linear), "
        "Param(name=False northing, auth_name=EPSG, code=8807, value=0.0, "
        "unit_name=metre, unit_auth_name=EPSG, unit_code=9001, unit_category=linear)]"
    )
    assert crs.coordinate_operation.grids == []


def test_coordinate_operation_grids():
    cc = CoordinateOperation.from_epsg(1312)
    if not cc.grids[0].full_name:
        assert (
            repr(cc.grids)
            == "[Grid(short_name=NTv1_0.gsb, full_name=, package_name=, url=, "
            "direct_download=False, open_license=False, available=False)]"
        )
    else:
        assert (
            repr(cc.grids)
            == "[Grid(short_name=NTv1_0.gsb, full_name=NTv1_0.gsb, package_name=, "
            "url=, direct_download=False, open_license=False, available=False)]"
        )


@pytest.mark.grid
def test_coordinate_operation_grids__alternative_grid_name():
    cc = CoordinateOperation.from_epsg(1312, True)
    assert len(cc.grids) == 1
    grid = cc.grids[0]
    assert grid.direct_download is True
    assert grid.open_license is True
    assert grid.short_name == "ca_nrc_ntv1_can.tif"
    assert grid.package_name == ""
    assert grid.url == "https://cdn.proj.org/ca_nrc_ntv1_can.tif"
    if (PROJ_GTE_91 and grids_available(grid.short_name, check_network=False)) or (
        not PROJ_GTE_91 and grids_available(grid.short_name)
    ):
        assert grid.available is True
        assert grid.full_name.endswith(grid.short_name)
    elif PROJ_GTE_911 and pyproj.network.is_network_enabled():
        assert grid.available is True
        assert grid.full_name == grid.url
    elif PROJ_GTE_91 and pyproj.network.is_network_enabled():
        assert grid.available is True
        assert grid.full_name == ""
    else:
        assert grid.available is False
        assert grid.full_name == ""


def test_coordinate_operation__missing():
    crs = CRS.from_epsg(4326)
    assert crs.coordinate_operation is None


def test_coordinate_operation__from_epsg():
    cc = CoordinateOperation.from_epsg(16031)
    assert cc.method_auth_name == "EPSG"
    assert cc.method_code == "9807"


def test_coordinate_operation__from_authority():
    cc = CoordinateOperation.from_authority("EPSG", 16031)
    assert cc.method_auth_name == "EPSG"
    assert cc.method_code == "9807"


@pytest.mark.parametrize(
    "user_input",
    [
        1671,
        ("EPSG", 1671),
        "urn:ogc:def:coordinateOperation:EPSG::1671",
        CoordinateOperation.from_epsg(1671),
        CoordinateOperation.from_epsg(1671).to_json_dict(),
        "RGF93 v1 to WGS 84 (1)",
    ],
)
def test_coordinate_operation__from_user_input(user_input):
    assert CoordinateOperation.from_user_input(
        user_input
    ) == CoordinateOperation.from_epsg(1671)


def test_coordinate_operation__from_user_input__invalid():
    with pytest.raises(CRSError, match="Invalid coordinate operation"):
        CoordinateOperation.from_user_input({})


def test_coordinate_operation__from_epsg__empty():
    with pytest.raises(CRSError, match="Invalid authority"):
        CoordinateOperation.from_epsg(1)


def test_coordinate_operation__from_authority__empty():
    with pytest.raises(CRSError, match="Invalid authority"):
        CoordinateOperation.from_authority("BOB", 4326)


def test_datum__from_epsg():
    datum_wkt = (
        'ENSEMBLE["World Geodetic System 1984 ensemble",'
        'MEMBER["World Geodetic System 1984 (Transit)",ID["EPSG",1166]],'
        'MEMBER["World Geodetic System 1984 (G730)",ID["EPSG",1152]],'
        'MEMBER["World Geodetic System 1984 (G873)",ID["EPSG",1153]],'
        'MEMBER["World Geodetic System 1984 (G1150)",ID["EPSG",1154]],'
        'MEMBER["World Geodetic System 1984 (G1674)",ID["EPSG",1155]],'
        'MEMBER["World Geodetic System 1984 (G1762)",ID["EPSG",1156]],'
        'MEMBER["World Geodetic System 1984 (G2139)",ID["EPSG",1309]],'
        'ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1],'
        'ID["EPSG",7030]],ENSEMBLEACCURACY[2.0],ID["EPSG",6326]]'
    )
    assert Datum.from_epsg("6326").to_wkt() == datum_wkt


def test_datum__from_authority():
    dt = Datum.from_authority("EPSG", 6326)
    assert dt.name == "World Geodetic System 1984 ensemble"


def test_datum__from_epsg__invalid():
    with pytest.raises(CRSError, match="Invalid authority"):
        Datum.from_epsg(1)


def test_datum__from_authority__invalid():
    with pytest.raises(CRSError, match="Invalid authority"):
        Datum.from_authority("BOB", 1)


@pytest.mark.parametrize(
    "user_input",
    [
        6326,
        ("EPSG", 6326),
        "urn:ogc:def:ensemble:EPSG::6326",
        Datum.from_epsg(6326),
        Datum.from_epsg(6326).to_json_dict(),
        "World Geodetic System 1984",
    ],
)
def test_datum__from_user_input(user_input):
    assert Datum.from_user_input(user_input) == Datum.from_epsg(6326)


def test_datum__from_user_input__invalid():
    with pytest.raises(CRSError, match="Invalid datum"):
        Datum.from_user_input({})


def test_prime_meridian__from_epsg():
    assert PrimeMeridian.from_epsg(8903).to_wkt() == (
        'PRIMEM["Paris",2.5969213,ANGLEUNIT["grad",0.0157079632679489],ID["EPSG",8903]]'
    )


def test_prime_meridian__from_authority():
    assert PrimeMeridian.from_authority("EPSG", 8903).name == "Paris"


def test_prime_meridian__from_epsg__invalid():
    with pytest.raises(CRSError, match="Invalid authority"):
        PrimeMeridian.from_epsg(1)


def test_prime_meridian__from_authority__invalid():
    with pytest.raises(CRSError, match="Invalid authority"):
        PrimeMeridian.from_authority("Bob", 1)


@pytest.mark.parametrize(
    "user_input",
    [
        8901,
        ("EPSG", 8901),
        "urn:ogc:def:meridian:EPSG::8901",
        PrimeMeridian.from_epsg(8901),
        PrimeMeridian.from_epsg(8901).to_json_dict(),
        "Greenwich",
    ],
)
def test_prime_meridian__from_user_input(user_input):
    assert PrimeMeridian.from_user_input(user_input) == PrimeMeridian.from_epsg(8901)


def test_prime_meridian__from_user_input__invalid():
    with pytest.raises(CRSError, match="Invalid prime meridian"):
        PrimeMeridian.from_user_input({})


def test_ellipsoid__from_epsg():
    assert Ellipsoid.from_epsg(7030).to_wkt() == (
        'ELLIPSOID["WGS 84",6378137,298.257223563,'
        'LENGTHUNIT["metre",1],ID["EPSG",7030]]'
    )


def test_ellipsoid__from_authority():
    assert Ellipsoid.from_authority("EPSG", 7030).name == "WGS 84"


def test_ellipsoid__from_epsg__invalid():
    with pytest.raises(CRSError, match="Invalid authority"):
        Ellipsoid.from_epsg(1)


def test_ellipsoid__from_authority__invalid():
    with pytest.raises(CRSError, match="Invalid authority"):
        Ellipsoid.from_authority("BOB", 1)


@pytest.mark.parametrize(
    "user_input",
    [
        7001,
        ("EPSG", 7001),
        "urn:ogc:def:ellipsoid:EPSG::7001",
        Ellipsoid.from_epsg(7001),
        Ellipsoid.from_epsg(7001).to_json_dict(),
        "Airy 1830",
    ],
)
def test_ellipsoid__from_user_input(user_input):
    assert Ellipsoid.from_user_input(user_input) == Ellipsoid.from_epsg(7001)


def test_ellipsoid__from_user_input__invalid():
    with pytest.raises(CRSError, match="Invalid ellipsoid"):
        Ellipsoid.from_user_input({})


CS_JSON_DICT = {
    "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
    "type": "CoordinateSystem",
    "subtype": "Cartesian",
    "axis": [
        {"name": "Easting", "abbreviation": "E", "direction": "east", "unit": "metre"},
        {
            "name": "Northing",
            "abbreviation": "N",
            "direction": "north",
            "unit": "metre",
        },
    ],
}


@pytest.mark.parametrize(
    "user_input",
    [
        CS_JSON_DICT,
        json.dumps(CS_JSON_DICT),
        CoordinateSystem.from_json_dict(CS_JSON_DICT),
    ],
)
def test_coordinate_system__from_user_input(user_input):
    assert CoordinateSystem.from_user_input(
        user_input
    ) == CoordinateSystem.from_json_dict(CS_JSON_DICT)


@pytest.mark.parametrize(
    "user_input",
    [
        7001,
        ("EPSG", 7001),
        "urn:ogc:def:ellipsoid:EPSG::7001",
        Ellipsoid.from_epsg(7001),
        Ellipsoid.from_epsg(7001).to_json_dict(),
    ],
)
def test_coordinate_system__from_user_input__invalid(user_input):
    with pytest.raises(CRSError, match="Invalid"):
        CoordinateSystem.from_user_input(user_input)


def test_bound_crs_is_geographic():
    assert CRS(
        "proj=longlat datum=WGS84 no_defs ellps=WGS84 towgs84=0,0,0"
    ).is_geographic


def test_coordinate_operation_towgs84_three():
    crs = CRS("+proj=latlong +ellps=GRS80 +towgs84=-199.87,74.79,246.62")
    assert crs.coordinate_operation.towgs84 == [-199.87, 74.79, 246.62]


def test_coordinate_operation_towgs84_seven():
    crs = CRS(
        "+proj=tmerc +lat_0=0 +lon_0=15 +k=0.9996 +x_0=2520000 +y_0=0 "
        "+ellps=intl +towgs84=-122.74,-34.27,-22.83,-1.884,-3.400,-3.030,-15.62"
    )
    assert crs.coordinate_operation.towgs84 == [
        -122.74,
        -34.27,
        -22.83,
        -1.884,
        -3.4,
        -3.03,
        -15.62,
    ]


def test_axis_info_bound():
    crs = CRS(
        "+proj=tmerc +lat_0=0 +lon_0=15 +k=0.9996 +x_0=2520000 +y_0=0 "
        "+ellps=intl +towgs84=-122.74,-34.27,-22.83,-1.884,-3.400,-3.030,-15.62"
    )
    assert [axis.direction for axis in crs.axis_info] == ["east", "north"]


def test_coordinate_operation_towgs84_missing():
    crs = CRS("epsg:3004")
    assert crs.coordinate_operation.towgs84 == []


@pytest.mark.parametrize(
    "wkt_version_str, wkt_version_enum",
    [
        ("WKT1_GDAL", WktVersion.WKT1_GDAL),
        ("WKT2_2018", WktVersion.WKT2_2018),
        ("WKT2_2018_SIMPLIFIED", WktVersion.WKT2_2018_SIMPLIFIED),
        ("WKT2_2019", WktVersion.WKT2_2019),
        ("WKT2_2019_SIMPLIFIED", WktVersion.WKT2_2019_SIMPLIFIED),
        ("WKT2_2015", WktVersion.WKT2_2015),
        ("WKT2_2015_SIMPLIFIED", WktVersion.WKT2_2015_SIMPLIFIED),
    ],
)
def test_to_wkt_enum(wkt_version_str, wkt_version_enum):
    crs = CRS.from_epsg(4326)
    assert crs.to_wkt(wkt_version_str) == crs.to_wkt(wkt_version_enum)


def test_to_wkt_enum__invalid():
    crs = CRS.from_epsg(4326)
    with pytest.raises(ValueError, match="Invalid value"):
        crs.to_wkt("WKT_INVALID")


@pytest.mark.parametrize(
    "wkt_version",
    ["WKT2_2015", "WKT2_2015_SIMPLIFIED", "WKT1_GDAL", "WKT1_ESRI"],
)
def test_to_wkt_none_warning(wkt_version):
    wkt_string = (
        'PROJCRS["unknown",BASEGEOGCRS["unknown",DATUM["unknown",'
        'ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1,'
        'ID["EPSG",9001]]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199],'
        'ID["EPSG",8901]]],CONVERSION["unknown",METHOD["Equidistant Cylindrical",'
        'ID["EPSG",1028]],PARAMETER["Latitude of 1st standard parallel",0,'
        'ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],'
        'PARAMETER["Longitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199],'
        'ID["EPSG",8802]],PARAMETER["False easting",0,'
        'LENGTHUNIT["unknown",111319.490793274],ID["EPSG",8806]],'
        'PARAMETER["False northing",0,LENGTHUNIT["unknown",111319.490793274],'
        'ID["EPSG",8807]]],CS[Cartesian,3],AXIS["(E)",east,ORDER[1],'
        'LENGTHUNIT["unknown",111319.490793274]],AXIS["(N)",north,ORDER[2],'
        'LENGTHUNIT["unknown",111319.490793274]],AXIS["ellipsoidal height (h)",up,'
        'ORDER[3],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]'
    )
    crs = CRS.from_wkt(wkt_string)
    with pytest.raises(CRSError, match="CRS cannot be converted to a WKT string"):
        assert crs.to_wkt(version=wkt_version) is None


def test_to_proj4_none_warning():
    crs = CRS("EPSG:4326")
    with patch("pyproj.crs.crs.CRS._crs") as crs_mock, pytest.raises(
        CRSError, match="CRS cannot be converted to a PROJ string"
    ):
        crs_mock.to_proj4.return_value = None
        assert crs.to_proj4() is None


def test_to_json_none_warning():
    crs = CRS("EPSG:4326")
    with patch("pyproj.crs.crs.CRS._crs") as crs_mock, pytest.raises(
        CRSError, match="CRS cannot be converted to a PROJ JSON string"
    ):
        crs_mock.to_json.return_value = None
        assert crs.to_json() is None


def test_to_proj4_enum():
    crs = CRS.from_epsg(4326)
    with pytest.warns(UserWarning):
        assert crs.to_proj4(4) == crs.to_proj4(ProjVersion.PROJ_4)
        assert crs.to_proj4(5) == crs.to_proj4(ProjVersion.PROJ_5)


def test_datum_equals():
    datum = Datum.from_epsg(6326)
    assert datum == 6326
    assert not datum != 6326
    assert datum != "invalid"


@pytest.mark.parametrize(
    "input_str",
    [
        "urn:ogc:def:ensemble:EPSG::6326",
        "World Geodetic System 1984",
    ],
)
def test_datum__from_string(input_str):
    dd = Datum.from_string(input_str)
    assert dd.name == "World Geodetic System 1984 ensemble"
    assert dd.type_name == "Datum Ensemble"


@pytest.mark.parametrize(
    "input_str, type_name",
    [
        ('ENGINEERINGDATUM["Engineering datum"]', "Engineering Datum"),
        ('PDATUM["Mean Sea Level",ANCHOR["1013.25 hPa at 15°C"]]', "Parametric Datum"),
        (
            'TDATUM["Gregorian calendar",CALENDAR["proleptic Gregorian"],'
            "TIMEORIGIN[0000-01-01]]",
            "Temporal Datum",
        ),
    ],
)
def test_datum__from_string__type_name(input_str, type_name):
    dd = Datum.from_string(input_str)
    assert dd.type_name == type_name


@pytest.mark.parametrize(
    "input_name", ["World Geodetic System 1984", "WGS84", "WGS 84"]
)
def test_datum__from_name(input_name):
    dd = Datum.from_name(input_name)
    assert dd.name == "World Geodetic System 1984 ensemble"


@pytest.mark.parametrize("auth_name", [None, "ESRI"])
def test_datum_from_name__auth_type(auth_name):
    dd = Datum.from_name(
        "WGS_1984_Geoid",
        auth_name=auth_name,
        datum_type=DatumType.VERTICAL_REFERENCE_FRAME,
    )
    assert dd.name == "WGS_1984_Geoid"
    assert dd.type_name == "Vertical Reference Frame"


def test_datum_from_name__any_type():
    dd = Datum.from_name("WGS_1984_Geoid")
    assert dd.name == "WGS_1984_Geoid"
    assert dd.type_name == "Vertical Reference Frame"


@pytest.mark.parametrize(
    "invalid_str", ["3-598y5-98y", "urn:ogc:def:ellipsoid:EPSG::7001"]
)
def test_datum__from_name__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid datum name:"):
        Datum.from_name(invalid_str)


def test_datum__from_name__invalid_type():
    with pytest.raises(CRSError, match="Invalid datum name: WGS84"):
        Datum.from_name("WGS84", datum_type="VERTICAL_REFERENCE_FRAME")


@pytest.mark.parametrize(
    "invalid_str", ["3-598y5-98y", "urn:ogc:def:ellipsoid:EPSG::7001"]
)
def test_datum__from_string__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid datum string"):
        Datum.from_string(invalid_str)


def test_ellipsoid_equals():
    ellipsoid = Ellipsoid.from_epsg(7001)
    assert ellipsoid == 7001
    assert not ellipsoid != 7001
    assert ellipsoid != "invalid"


@pytest.mark.parametrize("input_str", ["urn:ogc:def:ellipsoid:EPSG::7001", "Airy 1830"])
def test_ellipsoid__from_string(input_str):
    ee = Ellipsoid.from_string(input_str)
    assert ee.name == "Airy 1830"


@pytest.mark.parametrize(
    "input_str,long_name",
    [
        ("Airy 1830", "Airy 1830"),
        ("intl", "International 1924 (Hayford 1909, 1910)"),
        (
            "International 1924 (Hayford 1909, 1910)",
            "International 1924 (Hayford 1909, 1910)",
        ),
    ],
)
def test_ellipsoid__from_name(input_str, long_name):
    ee = Ellipsoid.from_name(input_str)
    assert ee.name == long_name


@pytest.mark.parametrize("invalid_str", ["3-598y5-98y", "urn:ogc:def:datum:EPSG::6326"])
def test_ellipsoid__from_name__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid ellipsoid name"):
        Ellipsoid.from_name(invalid_str)


def test_ellipsoid__from_name__invalid__auth():
    with pytest.raises(CRSError, match="Invalid ellipsoid name"):
        Ellipsoid.from_name("intl", auth_name="ESRI")


@pytest.mark.parametrize("invalid_str", ["3-598y5-98y", "urn:ogc:def:datum:EPSG::6326"])
def test_ellipsoid__from_string__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid ellipsoid string"):
        Ellipsoid.from_string(invalid_str)


def test_prime_meridian_equals():
    pm = PrimeMeridian.from_epsg(8901)
    assert pm == 8901
    assert not pm != 8901
    assert pm != "invalid"


@pytest.mark.parametrize("input_str", ["urn:ogc:def:meridian:EPSG::8901", "Greenwich"])
def test_prime_meridian__from_string(input_str):
    pm = PrimeMeridian.from_string(input_str)
    assert pm.name == "Greenwich"


@pytest.mark.parametrize("invalid_str", ["3-598y5-98y", "urn:ogc:def:datum:EPSG::6326"])
def test_prime_meridian__from_string__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid prime meridian string"):
        PrimeMeridian.from_string(invalid_str)


def test_prime_meridian__from_name():
    pm = PrimeMeridian.from_name("Greenwich")
    assert pm.name == "Greenwich"


@pytest.mark.parametrize("invalid_str", ["3-598y5-98y", "urn:ogc:def:datum:EPSG::6326"])
def test_prime_meridian__from_name__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid prime meridian name"):
        PrimeMeridian.from_name(invalid_str)


def test_coordinate_operation_equals():
    co = CoordinateOperation.from_epsg(1671)
    assert co == 1671
    assert not co != 1671
    assert co != "invalid"


@pytest.mark.parametrize(
    "input_str",
    ["urn:ogc:def:coordinateOperation:EPSG::1671", "RGF93 v1 to WGS 84 (1)"],
)
def test_coordinate_operation__from_string(input_str):
    co = CoordinateOperation.from_string(input_str)
    assert co.name == "RGF93 v1 to WGS 84 (1)"


def test_coordinate_operation__from_name():
    co = CoordinateOperation.from_name("UTM zone 12N")
    assert co.name == "UTM zone 12N"


def test_coordinate_operation__from_name_auth_type():
    co = CoordinateOperation.from_name(
        "ITRF_2000_To_WGS_1984",
        auth_name="ESRI",
        coordinate_operation_type=CoordinateOperationType.TRANSFORMATION,
    )
    assert co.name == "ITRF_2000_To_WGS_1984"


@pytest.mark.parametrize("invalid_str", ["3-598y5-98y", "urn:ogc:def:datum:EPSG::6326"])
def test_coordinate_operation__from_name__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid coordinate operation name"):
        CoordinateOperation.from_name(invalid_str)


@pytest.mark.parametrize("invalid_str", ["3-598y5-98y", "urn:ogc:def:datum:EPSG::6326"])
def test_coordinate_operation__from_string__invalid(invalid_str):
    with pytest.raises(CRSError, match="Invalid coordinate operation string"):
        CoordinateOperation.from_string(invalid_str)


_COORDINATE_SYSTEM_STR = (
    '{"$schema":"https://proj.org/schemas/v0.2/projjson.schema.json",'
    '"type":"CoordinateSystem","subtype":"ellipsoidal",'
    '"axis":[{"name":"Geodetic latitude","abbreviation":"Lat",'
    '"direction":"north","unit":"degree"},'
    '{"name":"Geodetic longitude","abbreviation":"Lon",'
    '"direction":"east","unit":"degree"}],'
    '"id":{"authority":"EPSG","code":6422}}'
)


def test_coordinate_system__equals():
    cs = CoordinateSystem.from_string(_COORDINATE_SYSTEM_STR)
    assert cs == _COORDINATE_SYSTEM_STR
    assert not cs != _COORDINATE_SYSTEM_STR
    assert cs != "invalid"


def test_coordinate_system__from_string():
    cs = CoordinateSystem.from_string(_COORDINATE_SYSTEM_STR)
    assert cs.name == "ellipsoidal"


@pytest.mark.parametrize(
    "invalid_cs_string", ["3-598y5-98y", "urn:ogc:def:datum:EPSG::6326"]
)
def test_coordinate_system__from_string__invalid(invalid_cs_string):
    with pytest.raises(CRSError, match="Invalid coordinate system string"):
        CoordinateSystem.from_string(invalid_cs_string)


def test_to_proj4_enum__invalid():
    crs = CRS.from_epsg(4326)
    with pytest.raises(ValueError, match="Invalid value"), pytest.warns(UserWarning):
        crs.to_proj4(1)


def test_geodetic_crs():
    cc = CRS("epsg:3004")
    assert cc.geodetic_crs.to_epsg() == 4265


def test_itrf_init():
    crs = CRS("ITRF2000")
    assert crs.name == "ITRF2000"


def test_compound_crs_init():
    crs = CRS("EPSG:2393+5717")
    assert crs.name == "KKJ / Finland Uniform Coordinate System + N60 height"


def test_compound_crs_urn_init():
    crs = CRS("urn:ogc:def:crs,crs:EPSG::2393,crs:EPSG::5717")
    assert crs.name == "KKJ / Finland Uniform Coordinate System + N60 height"


def test_from_authority__ignf():
    cc = CRS.from_authority("IGNF", "ETRS89UTM28")
    assert cc.to_authority() == ("IGNF", "ETRS89UTM28")
    assert cc.to_authority("EPSG") == ("EPSG", "25828")
    assert cc.to_epsg() == 25828


def test_ignf_authority_repr():
    assert repr(CRS.from_authority("IGNF", "ETRS89UTM28")).startswith(
        "<Projected CRS: IGNF:ETRS89UTM28>"
    )


def test_crs_hash():
    """hashes of equivalent CRS are equal"""
    assert hash(CRS.from_epsg(3857)) == hash(CRS.from_epsg(3857))


def test_crs_hash_unequal():
    """hashes of non-equivalent CRS are not equal"""
    assert hash(CRS.from_epsg(3857)) != hash(CRS.from_epsg(4326))


def test_crs_init_user_input():
    assert CRS(("IGNF", "ETRS89UTM28")).to_authority() == ("IGNF", "ETRS89UTM28")
    assert CRS(4326).to_epsg() == 4326

    proj4_dict = {"proj": "longlat", "datum": "WGS84", "no_defs": None, "type": "crs"}
    with pytest.warns(UserWarning):
        assert CRS({"proj": "lonlat", "datum": "WGS84"}).to_dict() == proj4_dict
        assert CRS(proj="lonlat", datum="WGS84").to_dict() == proj4_dict
        assert (
            CRS('{"proj": "longlat", "ellps": "WGS84", "datum": "WGS84"}').to_dict()
            == proj4_dict
        )
    assert CRS(CRS(4326)).is_exact_same(CRS(CustomCRS()))


def test_crs_is_exact_same__non_crs_input():
    assert CRS(4326).is_exact_same("epsg:4326")
    with pytest.warns(FutureWarning):
        assert not CRS(4326).is_exact_same("+init=epsg:4326")


def test_derived_projected_crs():
    wkt = (
        'DERIVEDPROJCRS["derived projectedCRS",\n'
        '    BASEPROJCRS["WGS 84 / UTM zone 31N",\n'
        '        BASEGEOGCRS["WGS 84",\n'
        '            DATUM["World Geodetic System 1984",\n'
        '                ELLIPSOID["WGS 84",6378137,298.257223563,\n'
        '                    LENGTHUNIT["metre",1]]],\n'
        '            PRIMEM["Greenwich",0,\n'
        '                ANGLEUNIT["degree",0.0174532925199433]]],\n'
        '        CONVERSION["UTM zone 31N",\n'
        '            METHOD["Transverse Mercator",\n'
        '                ID["EPSG",9807]],\n'
        '            PARAMETER["Latitude of natural origin",0,\n'
        '                ANGLEUNIT["degree",0.0174532925199433],\n'
        '                ID["EPSG",8801]],\n'
        '            PARAMETER["Longitude of natural origin",3,\n'
        '                ANGLEUNIT["degree",0.0174532925199433],\n'
        '                ID["EPSG",8802]],\n'
        '            PARAMETER["Scale factor at natural origin",0.9996,\n'
        '                SCALEUNIT["unity",1],\n'
        '                ID["EPSG",8805]],\n'
        '            PARAMETER["False easting",500000,\n'
        '                LENGTHUNIT["metre",1],\n'
        '                ID["EPSG",8806]],\n'
        '            PARAMETER["False northing",0,\n'
        '                LENGTHUNIT["metre",1],\n'
        '                ID["EPSG",8807]]]],\n'
        '    DERIVINGCONVERSION["unnamed",\n'
        '        METHOD["PROJ unimplemented"],\n'
        '        PARAMETER["foo",1.0,UNIT["metre",1]]],\n'
        "    CS[Cartesian,2],\n"
        '        AXIS["(E)",east,\n'
        "            ORDER[1],\n"
        '            LENGTHUNIT["metre",1,\n'
        '                ID["EPSG",9001]]],\n'
        '        AXIS["(N)",north,\n'
        "            ORDER[2],\n"
        '            LENGTHUNIT["metre",1,\n'
        '                ID["EPSG",9001]]]]'
    )
    crs = CRS(wkt)
    assert crs.is_derived
    assert crs.type_name == "Derived Projected CRS"


def test_to_string__no_auth():
    proj = CRS("+proj=latlong +ellps=GRS80 +towgs84=-199.87,74.79,246.62")
    assert (
        proj.to_string()
        == "+proj=latlong +ellps=GRS80 +towgs84=-199.87,74.79,246.62 +type=crs"
    )


def test_to_string__auth():
    assert CRS(("IGNF", "ETRS89UTM28")).to_string() == "IGNF:ETRS89UTM28"


def test_srs__no_plus():
    assert (
        CRS("proj=longlat datum=WGS84 no_defs").srs
        == "proj=longlat datum=WGS84 no_defs type=crs"
    )


def test_equals_different_type():
    assert CRS("epsg:4326") != ""
    assert not CRS("epsg:4326") == ""

    assert CRS("epsg:4326") != 27700
    assert not CRS("epsg:4326") == 27700

    assert not CRS("epsg:4326") != 4326
    assert CRS("epsg:4326") == 4326


def test_is_exact_same_different_type():
    assert not CRS("epsg:4326").is_exact_same(None)


def test_compare_crs_non_crs():
    assert CRS.from_epsg(4326) != 4.2
    assert CRS.from_epsg(4326) == 4326
    with pytest.warns(FutureWarning):
        assert CRS.from_dict({"init": "epsg:4326"}) == {"init": "epsg:4326"}
        assert CRS.from_dict({"init": "epsg:4326"}) != "epsg:4326"
    assert CRS("epsg:4326") == CustomCRS()


def test_is_geocentric__bound():
    with pytest.warns(FutureWarning):
        ccs = CRS("+init=epsg:4328 +towgs84=0,0,0")
    assert ccs.is_geocentric


def test_is_geocentric():
    ccs = CRS.from_epsg(4328)
    assert ccs.is_geocentric


def test_is_vertical():
    cc = CRS.from_epsg(5717)
    assert cc.is_vertical


def test_is_engineering():
    eng_wkt = (
        'ENGCRS["A construction site CRS",\n'
        'EDATUM["P1",ANCHOR["Peg in south corner"]],\n'
        'CS[Cartesian,2],\nAXIS["site east",southWest,ORDER[1]],\n'
        'AXIS["site north",southEast,ORDER[2]],\n'
        'LENGTHUNIT["metre",1.0],\n'
        'TIMEEXTENT["date/time t1","date/time t2"]]'
    )
    assert CRS(eng_wkt).is_engineering


def test_source_crs__bound():
    with pytest.warns(FutureWarning):
        assert CRS("+init=epsg:4328 +towgs84=0,0,0").source_crs.name == "unknown"


def test_source_crs__missing():
    assert CRS("epsg:4326").source_crs is None


def test_target_crs__bound():
    with pytest.warns(FutureWarning):
        assert CRS("+init=epsg:4328 +towgs84=0,0,0").target_crs.name == "WGS 84"


def test_target_crs__missing():
    assert CRS("epsg:4326").target_crs is None


def test_whitepace_between_equals():
    crs = CRS(
        "+proj =lcc +lat_1= 30.0 +lat_2= 35.0 +lat_0=30.0 +lon_0=87.0 +x_0=0 +y_0=0"
    )
    assert crs.srs == (
        "+proj=lcc +lat_1=30.0 +lat_2=35.0 +lat_0=30.0 "
        "+lon_0=87.0 +x_0=0 +y_0=0 +type=crs"
    )


def test_to_dict_no_proj4():
    crs = CRS(
        {
            "a": 6371229.0,
            "b": 6371229.0,
            "lon_0": -10.0,
            "o_lat_p": 30.0,
            "o_lon_p": 0.0,
            "o_proj": "longlat",
            "proj": "ob_tran",
        }
    )
    with pytest.warns(UserWarning):
        assert crs.to_dict() == {
            "R": 6371229,
            "lon_0": -10,
            "no_defs": None,
            "o_lat_p": 30,
            "o_lon_p": 0,
            "o_proj": "longlat",
            "proj": "ob_tran",
            "type": "crs",
        }


def test_to_dict_from_dict():
    cc = CRS.from_epsg(4326)
    with pytest.warns(UserWarning):
        assert CRS.from_dict(cc.to_dict()).name == "unknown"


def test_from_dict__invalid():
    with pytest.raises(CRSError, match="CRS input is not a dict"):
        CRS.from_dict(4326)


@pytest.mark.parametrize(
    "class_type",
    [Datum, Ellipsoid, PrimeMeridian, CoordinateOperation, CoordinateSystem],
)
def test_incorrectly_initialized(class_type):
    with pytest.raises(RuntimeError):
        class_type()


def test_scope__remarks():
    co = CoordinateOperation.from_epsg("8048")
    assert "GDA94" in co.scope
    assert "Scale difference" in co.remarks


def test_crs__scope__remarks__missing():
    cc = CRS("+proj=latlon")
    assert cc.scope is None
    assert cc.remarks is None


def test_operations_missing():
    cc = CRS(("IGNF", "ETRS89UTM28"))
    assert cc.coordinate_operation.operations == ()


def test_operations():
    transformer = TransformerGroup(28356, 7856).transformers[0]
    coord_op = CoordinateOperation.from_string(transformer.to_wkt())
    assert coord_op.operations == transformer.operations


def test_operations__scope_remarks():
    operation = TransformerGroup(28356, 7856).transformers[0].operations[1]
    coord_op = CoordinateOperation.from_string(operation.to_wkt())
    assert coord_op == operation
    assert coord_op.remarks == operation.remarks
    assert coord_op.scope == operation.scope


def test_crs_equals():
    assert CRS(4326).equals("epsg:4326")


def test_crs_equals__ignore_axis_order():
    with pytest.warns(FutureWarning):
        assert CRS("epsg:4326").equals("+init=epsg:4326", ignore_axis_order=True)


@pytest.mark.parametrize(
    "crs_input",
    [
        "+proj=utm +zone=15",
        26915,
        "+proj=utm +zone=15 +towgs84=0,0,0",
        "EPSG:26915+5717",
    ],
)
def test_utm_zone(crs_input):
    assert CRS(crs_input).utm_zone == "15N"


@pytest.mark.parametrize("crs_input", ["+proj=tmerc", "epsg:4326"])
def test_utm_zone__none(crs_input):
    assert CRS(crs_input).utm_zone is None


def test_numpy_bool_kwarg_false():
    # Issue 564
    south = numpy.array(50) < 0
    crs = CRS(
        proj="utm", zone=32, ellipsis="WGS84", datum="WGS84", units="m", south=south
    )
    assert "south" not in crs.srs


def test_numpy_bool_kwarg_true():
    # Issue 564
    south = numpy.array(50) > 0
    crs = CRS(
        proj="utm", zone=32, ellipsis="WGS84", datum="WGS84", units="m", south=south
    )
    assert "+south " in crs.srs


@pytest.mark.skipif(
    pyproj._datadir._USE_GLOBAL_CONTEXT, reason="Global Context not Threadsafe."
)
def test_crs_multithread():
    # https://github.com/pyproj4/pyproj/issues/782
    crs = CRS(4326)

    def to_wkt(num):
        return crs.to_wkt()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for result in executor.map(to_wkt, range(10)):
            pass


@pytest.mark.skipif(
    platform.python_implementation() != "CPython", reason="pypy process unstable."
)
def test_crs_multiprocess():
    # https://github.com/pyproj4/pyproj/issues/933
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        for result in executor.map(CRS, [4326 for _ in range(10)]):
            pass


def test_coordinate_operation__to_proj4():
    operation = CoordinateOperation.from_string(
        "+proj=pipeline +step +proj=axisswap +order=2,1 +step "
        "+proj=unitconvert +xy_in=deg +xy_out=rad +step "
        "+proj=webmerc +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84"
    )
    proj_string = operation.to_proj4()
    assert "+proj=pipeline" in proj_string
    assert "\n" not in proj_string


def test_coordinate_operation__to_proj4__pretty():
    operation = CoordinateOperation.from_string(
        "+proj=pipeline +step +proj=axisswap +order=2,1 +step "
        "+proj=unitconvert +xy_in=deg +xy_out=rad +step "
        "+proj=webmerc +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84"
    )
    proj_string = operation.to_proj4(pretty=True)
    assert "+proj=pipeline" in proj_string
    assert "\n" in proj_string


@pytest.mark.parametrize(
    "crs_input",
    [
        "EPSG:4326",
        "EPSG:2056",
    ],
)
def test_to_3d(crs_input):
    crs = CRS(crs_input)
    assert len(crs.axis_info) == 2
    crs_3d = crs.to_3d()
    assert len(crs_3d.axis_info) == 3
    vert_axis = crs_3d.axis_info[-1]
    assert vert_axis.name == "Ellipsoidal height"
    assert vert_axis.unit_name == "metre"
    assert vert_axis.direction == "up"
    assert crs_3d.to_3d() == crs_3d
    assert crs_3d.name == crs.name


def test_to_3d__name():
    crs_3d = CRS("EPSG:2056").to_3d(name="TEST")
    assert crs_3d.name == "TEST"


def test_crs__pickle(tmp_path):
    assert_can_pickle(CRS("epsg:4326"), tmp_path)


def test_is_derived():
    assert CRS(
        "+proj=ob_tran +o_proj=longlat +o_lat_p=0 +o_lon_p=0 +lon_0=0"
    ).is_derived
    assert not CRS("+proj=latlon").is_derived


def test_inheritance__from_methods():
    class ChildCRS(CRS):
        def new_method(self):
            return 1

    def assert_inheritance_valid(new_crs):
        assert new_crs.new_method() == 1
        assert isinstance(new_crs, ChildCRS)
        assert isinstance(new_crs.geodetic_crs, ChildCRS)
        assert isinstance(new_crs.source_crs, (type(None), ChildCRS))
        assert isinstance(new_crs.target_crs, (type(None), ChildCRS))
        assert isinstance(new_crs.to_3d(), ChildCRS)
        for sub_crs in new_crs.sub_crs_list:
            assert isinstance(sub_crs, ChildCRS)

    assert_inheritance_valid(ChildCRS.from_epsg(4326))
    assert_inheritance_valid(ChildCRS.from_string("EPSG:2056"))
    with pytest.warns(FutureWarning):
        assert_inheritance_valid(ChildCRS.from_proj4("+init=epsg:4328 +towgs84=0,0,0"))
    assert_inheritance_valid(ChildCRS.from_user_input("EPSG:4326+5773"))
    assert_inheritance_valid(ChildCRS.from_json(CRS(4326).to_json()))
    assert_inheritance_valid(ChildCRS.from_json_dict(CRS(4326).to_json_dict()))
    assert_inheritance_valid(ChildCRS.from_wkt(CRS(4326).to_wkt()))


def test_list_authority():
    assert CRS("+proj=utm +zone=15").list_authority() == [
        AuthorityMatchInfo(auth_name="EPSG", code="32615", confidence=70)
    ]


def test_list_authority__multiple():
    auth_list = CRS("+proj=longlat").list_authority()
    assert AuthorityMatchInfo(auth_name="OGC", code="CRS84", confidence=70) in auth_list
    assert AuthorityMatchInfo(auth_name="EPSG", code="4326", confidence=70) in auth_list
