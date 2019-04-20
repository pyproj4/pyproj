import pytest

from pyproj import CRS
from pyproj.crs import CoordinateOperation, Datum, Ellipsoid, PrimeMeridian
from pyproj.exceptions import CRSError


def test_from_proj4_json():
    json_str = '{"proj": "longlat", "ellps": "WGS84", "datum": "WGS84"}'
    proj = CRS.from_string(json_str)
    assert proj.to_proj4(4) == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
    assert proj.to_proj4(5) == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
    # Test with invalid JSON code
    with pytest.raises(CRSError):
        assert CRS.from_string("{foo: bar}")


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
    with pytest.raises(ValueError):
        assert CRS.from_string("epsg:xyz")


def test_from_string():
    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    assert wgs84_crs.to_proj4() == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
    # Make sure this doesn't get handled using the from_epsg() even though 'epsg' is in the string
    epsg_init_crs = CRS.from_string("+init=epsg:26911 +units=m +no_defs=True")
    assert (
        epsg_init_crs.to_proj4()
        == "+proj=utm +zone=11 +datum=NAD83 +units=m +no_defs +type=crs"
    )


def test_bare_parameters():
    """ Make sure that bare parameters (e.g., no_defs) are handled properly,
    even if they come in with key=True.  This covers interaction with pyproj,
    which makes presents bare parameters as key=<bool>."""

    # Example produced by pyproj
    proj = CRS.from_string(
        "+proj=lcc +lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    assert "+no_defs" in proj.to_proj4(4)

    # TODO: THIS DOES NOT WORK
    proj = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +proj=lcc +y_0=0 +no_defs=False +x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    # assert "+no_defs" not in proj.to_proj4(4)


def test_is_geographic():
    assert CRS({"init": "EPSG:4326"}).is_geographic is True
    assert CRS({"init": "EPSG:3857"}).is_geographic is False

    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    assert wgs84_crs.is_geographic is True

    nad27_crs = CRS.from_string("+proj=longlat +ellps=clrk66 +datum=NAD27 +no_defs")
    assert nad27_crs.is_geographic is True

    lcc_crs = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc +x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    assert lcc_crs.is_geographic is False


def test_is_projected():
    assert CRS({"init": "EPSG:3857"}).is_projected is True

    lcc_crs = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc +x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    assert CRS.from_user_input(lcc_crs).is_projected is True

    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    assert CRS.from_user_input(wgs84_crs).is_projected is False


def test_is_same_crs():
    crs1 = CRS({"init": "EPSG:4326"})
    crs2 = CRS({"init": "EPSG:3857"})

    assert crs1 == crs1
    assert crs1 != crs2

    wgs84_crs = CRS.from_string("+proj=longlat +ellps=WGS84 +datum=WGS84")
    assert crs1 == wgs84_crs

    # Make sure that same projection with different parameter are not equal
    lcc_crs1 = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc +x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    lcc_crs2 = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc +x_0=0 +units=m +lat_2=77 +lat_1=45 +lat_0=0"
    )
    assert lcc_crs1 != lcc_crs2


def test_to_proj4():
    assert (
        CRS({"init": "EPSG:4326"}).to_proj4(4)
        == "+proj=longlat +datum=WGS84 +no_defs +type=crs"
    )


def test_is_valid_false():
    with pytest.raises(CRSError):
        CRS(init="EPSG:432600").is_valid


def test_is_valid():
    assert CRS(init="EPSG:4326").is_valid


def test_empty_json():
    with pytest.raises(CRSError):
        CRS.from_string("{}")
    with pytest.raises(CRSError):
        CRS.from_string("[]")
    with pytest.raises(CRSError):
        CRS.from_string("")


def test_has_wkt_property():
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
    assert repr(CRS({"init": "EPSG:4326"})) == (
        "<CRS: +init=epsg:4326 +type=crs>\n"
        "Name: WGS 84\n"
        "Axis Info:\n"
        "- east: Longitude [EPSG:9122] (degree)\n"
        "- north: Latitude [EPSG:9122] (degree)\n"
        "Area of Use:\n"
        "- name: World\n"
        "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
        "Coordinate System:\n"
        "- ellipsoidal\n"
        "Coordinate Operation:\n"
        "- undefined\n"
        "Datum:\n"
        "- World Geodetic System 1984\n"
        "Ellipsoid:\n"
        "- WGS 84\n"
        "Prime Meridian:\n"
        "- Greenwich\n"
    )


def test_repr__long():
    assert repr(CRS(CRS({"init": "EPSG:4326"}).to_wkt())) == (
        '<CRS: GEOGCRS["WGS 84",DATUM["World Geodetic System 1984 ...>\n'
        "Name: WGS 84\n"
        "Axis Info:\n"
        "- east: Longitude [EPSG:9122] (degree)\n"
        "- north: Latitude [EPSG:9122] (degree)\n"
        "Area of Use:\n"
        "- name: World\n"
        "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
        "Coordinate System:\n"
        "- ellipsoidal\n"
        "Coordinate Operation:\n"
        "- undefined\n"
        "Datum:\n"
        "- World Geodetic System 1984\n"
        "Ellipsoid:\n"
        "- WGS 84\n"
        "Prime Meridian:\n"
        "- Greenwich\n"
    )


def test_repr_epsg():
    assert repr(CRS(CRS("EPSG:4326").to_wkt())) == (
        "<CRS: epsg:4326>\n"
        "Name: WGS 84\n"
        "Axis Info:\n"
        "- north: Geodetic latitude [EPSG:9122] (degree)\n"
        "- east: Geodetic longitude [EPSG:9122] (degree)\n"
        "Area of Use:\n"
        "- name: World\n"
        "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
        "Coordinate System:\n"
        "- ellipsoidal\n"
        "Coordinate Operation:\n"
        "- undefined\n"
        "Datum:\n"
        "- World Geodetic System 1984\n"
        "Ellipsoid:\n"
        "- WGS 84\n"
        "Prime Meridian:\n"
        "- Greenwich\n"
    )


def test_repr__undefined():
    assert repr(
        CRS(
            "+proj=merc +a=6378137.0 +b=6378137.0 +nadgrids=@null"
            " +lon_0=0.0 +x_0=0.0 +y_0=0.0 +units=m +no_defs"
        )
    ) == (
        "<CRS: +proj=merc +a=6378137.0 +b=6378137.0 +nadgrids=@nu ...>\n"
        "Name: unknown\n"
        "Axis Info:\n"
        "- undefined\n"
        "Area of Use:\n"
        "- undefined\n"
        "Coordinate System:\n"
        "- undefined\n"
        "Coordinate Operation:\n"
        "- unknown to WGS84\n"
        "Datum:\n"
        "- unknown\n"
        "Ellipsoid:\n"
        "- unknown\n"
        "Prime Meridian:\n"
        "- Greenwich\n"
    )


def test_dunder_str():
    assert str(CRS({"init": "EPSG:4326"})) == CRS({"init": "EPSG:4326"}).srs


def test_epsg():
    assert CRS({"init": "EPSG:4326"}).to_epsg(20) == 4326
    assert CRS({"init": "EPSG:4326"}).to_epsg() is None
    assert CRS.from_user_input(4326).to_epsg() == 4326
    assert CRS.from_epsg(4326).to_epsg() == 4326
    assert CRS.from_user_input("epsg:4326").to_epsg() == 4326


def test_datum():
    datum = CRS.from_epsg(4326).datum
    assert repr(datum).startswith('DATUM["World Geodetic System 1984"')
    assert "\n" in repr(datum)
    assert datum.to_wkt().startswith('DATUM["World Geodetic System 1984"')
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
    assert crs.datum.name == "Unknown based on WGS84 ellipsoid"


def test_epsg__not_found():
    assert CRS("+proj=longlat +datum=WGS84 +no_defs").to_epsg(0) is None
    assert CRS.from_string("+proj=longlat +datum=WGS84 +no_defs").to_epsg() is None


def test_epsg__no_code_available():
    lcc_crs = CRS.from_string(
        "+lon_0=-95 +ellps=GRS80 +y_0=0 +no_defs=True +proj=lcc "
        "+x_0=0 +units=m +lat_2=77 +lat_1=49 +lat_0=0"
    )
    assert lcc_crs.to_epsg() is None


def test_crs_OSR_equivalence():
    crs1 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs")
    crs2 = CRS.from_string("+proj=latlong +datum=WGS84 +no_defs")
    crs3 = CRS({"init": "EPSG:4326"})
    assert crs1 == crs2
    # these are not equivalent in proj.4 now as one uses degrees and the othe radians
    assert crs1 == crs3


def test_crs_OSR_no_equivalence():
    crs1 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs")
    crs2 = CRS.from_string("+proj=longlat +datum=NAD27 +no_defs")
    assert crs1 != crs2


def test_from_wkt():
    wgs84 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs")
    from_wkt = CRS(wgs84.to_wkt())
    assert wgs84.to_wkt() == from_wkt.to_wkt()


def test_from_wkt_invalid():
    with pytest.raises(CRSError):
        CRS("trash-54322")
    with pytest.raises(CRSError):
        CRS("")


def test_from_user_input_epsg():
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
    assert proj_crs_str.to_proj4() == proj_crs_wkt.to_proj4()
    assert proj_crs_str.to_proj4(4) == (
        "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 "
        "+lat_2=45.5 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs +type=crs"
    )


def test_compound_crs():
    wkt = """COMPD_CS["unknown",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]],VERT_CS["unknown",VERT_DATUM["unknown",2005],UNIT["metre",1.0,AUTHORITY["EPSG","9001"]],AXIS["Up",UP]]]"""
    assert CRS(wkt).to_wkt("WKT1_GDAL").startswith('COMPD_CS["unknown",GEOGCS["WGS 84"')


def test_ellipsoid():
    crs1 = CRS.from_epsg(4326)
    assert "{:.3f}".format(crs1.ellipsoid.inverse_flattening) == "298.257"
    assert "{:.3f}".format(crs1.ellipsoid.semi_major_metre) == "6378137.000"
    assert "{:.3f}".format(crs1.ellipsoid.semi_minor_metre) == "6356752.314"


def test_area_of_use():
    crs1 = CRS.from_epsg(4326)
    assert crs1.area_of_use.bounds == (-180.0, -90.0, 180.0, 90.0)
    assert crs1.area_of_use.name == "World"


def test_from_user_input_custom_crs_class():
    class CustomCRS(object):
        def to_wkt(self):
            return CRS.from_epsg(4326).to_wkt()

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
    assert repr(crs.coordinate_operation).startswith('CONVERSION["UTM zone 15N"')
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
    assert (
        repr(cc.grids)
        == "[Grid(short_name=NTv1_0.gsb, full_name=, package_name=, url=, "
        "direct_download=False, open_license=False, available=False)]"
    )


def test_coordinate_operation_grids__alternative_grid_name():
    cc = CoordinateOperation.from_epsg(1312, True)
    assert len(cc.grids) == 1
    grid = cc.grids[0]
    assert grid.short_name == "ntv1_can.dat"
    assert grid.full_name.endswith(grid.short_name)
    assert grid.package_name == "proj-datumgrid"
    assert grid.url.startswith("https://download.osgeo.org/proj/proj-datumgrid")
    assert grid.direct_download is True
    assert grid.open_license is True
    assert grid.available is True


def test_coordinate_operation__missing():
    crs = CRS.from_epsg(4326)
    assert crs.coordinate_operation is None


def test_coordinate_operation__from_epsg():
    cc = CoordinateOperation.from_epsg(16031)
    assert cc.method_auth_name == "EPSG"
    assert cc.method_code == "9807"


def test_coordinate_operation__from_epsg__empty():
    CoordinateOperation.from_epsg(1) is None


def test_datum__from_epsg():
    assert Datum.from_epsg("6326").to_wkt() == (
        'DATUM["World Geodetic System 1984",'
        'ELLIPSOID["WGS 84",6378137,298.257223563,'
        'LENGTHUNIT["metre",1]],ID["EPSG",6326]]'
    )


def test_datum__from_epsg__empty():
    Datum.from_epsg(1) is None


def test_prime_meridian__from_epsg():
    assert PrimeMeridian.from_epsg(8903).to_wkt() == (
        'PRIMEM["Paris",2.5969213,ANGLEUNIT["grad",0.0157079632679489],ID["EPSG",8903]]'
    )


def test_prime_meridian__from_epsg__empty():
    PrimeMeridian.from_epsg(1) is None


def test_ellipsoid__from_epsg():
    assert Ellipsoid.from_epsg(7030).to_wkt() == (
        'ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1],ID["EPSG",7030]]'
    )


def test_ellipsoid__from_epsg__empty():
    assert Ellipsoid.from_epsg(1) is None


def test_bound_crs_is_geographic():
    assert CRS(
        "proj=longlat datum=WGS84 no_defs ellps=WGS84 towgs84=0,0,0"
    ).is_geographic


def test_coordinate_operation_towgs84_three():
    crs = CRS("+proj=latlong +ellps=GRS80 +towgs84=-199.87,74.79,246.62")
    assert crs.coordinate_operation.towgs84 == [-199.87, 74.79, 246.62]


def test_coordinate_operation_towgs84_seven():
    crs = CRS(
        init="epsg:3004", towgs84="-122.74,-34.27,-22.83,-1.884,-3.400,-3.030,-15.62"
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


def test_coordinate_operation_towgs84_missing():
    crs = CRS(init="epsg:3004")
    assert crs.coordinate_operation.towgs84 == []
