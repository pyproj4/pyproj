import pytest

from pyproj import CRS
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


def test_repr():
    assert repr(CRS({"init": "EPSG:4326"})) == (
        "<CRS: +init=epsg:4326 +type=crs>\n"
        "Name: WGS 84\n"
        "Ellipsoid:\n"
        "- semi_major_metre: 6378137.00\n"
        "- semi_minor_metre: 6356752.31\n"
        "- inverse_flattening: 298.26\n"
        "Area of Use:\n"
        "- name: World\n"
        "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
        "Prime Meridian:\n"
        "- longitude: 0.0000\n"
        "- unit_name: degree\n"
        "- unit_conversion_factor: 0.01745329\n"
        "Axis Info:\n"
        "- Longitude[lon] (east) EPSG:9122 (degree)\n"
        "- Latitude[lat] (north) EPSG:9122 (degree)\n"
    )


def test_repr__long():
    assert repr(CRS(CRS({"init": "EPSG:4326"}).to_wkt())) == (
        '<CRS: GEOGCRS["WGS 84",DATUM["World Geodetic System 1984 ...>\n'
        "Name: WGS 84\n"
        "Ellipsoid:\n"
        "- semi_major_metre: 6378137.00\n"
        "- semi_minor_metre: 6356752.31\n"
        "- inverse_flattening: 298.26\n"
        "Area of Use:\n"
        "- name: World\n"
        "- bounds: (-180.0, -90.0, 180.0, 90.0)\n"
        "Prime Meridian:\n"
        "- longitude: 0.0000\n"
        "- unit_name: degree\n"
        "- unit_conversion_factor: 0.01745329\n"
        "Axis Info:\n"
        "- Longitude[lon] (east) EPSG:9122 (degree)\n"
        "- Latitude[lat] (north) EPSG:9122 (degree)\n"
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
        "Ellipsoid:\n"
        "- semi_major_metre: 6378137.00\n"
        "- semi_minor_metre: nan\n"
        "- inverse_flattening: 0.00\n"
        "Area of Use:\n"
        "- UNDEFINED\n"
        "Prime Meridian:\n"
        "- longitude: 0.0000\n"
        "- unit_name: degree\n"
        "- unit_conversion_factor: 0.01745329\n"
        "Axis Info:\n"
        "- UNDEFINED"
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
    assert CRS.from_epsg(4326).datum == CRS(
        'DATUM["World Geodetic System 1984",'
        'ELLIPSOID["WGS 84",6378137,298.257223563,'
        'LENGTHUNIT["metre",1]],ID["EPSG",6326]]'
    )


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
