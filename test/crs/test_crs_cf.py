from distutils.version import LooseVersion

import pytest
from numpy.testing import assert_almost_equal

from pyproj import CRS, __proj_version__
from pyproj.crs import ProjectedCRS
from pyproj.crs._cf1x8 import _try_list_if_string
from pyproj.crs.coordinate_operation import (
    LambertAzumuthalEqualAreaConversion,
    LambertCylindricalEqualAreaConversion,
    MercatorAConversion,
    OrthographicConversion,
    PolarStereographicAConversion,
    PolarStereographicBConversion,
    SinusoidalConversion,
    StereographicConversion,
    VerticalPerspectiveConversion,
)
from pyproj.exceptions import CRSError


def _to_dict(operation):
    param_dict = {}
    for param in operation.params:
        param_dict[param.name] = param.value
    return param_dict


def _test_roundtrip(expected_cf, wkt_startswith):
    crs = CRS.from_cf(expected_cf)
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith(wkt_startswith)
    assert_almost_equal(
        cf_dict.pop("semi_minor_axis"), expected_cf.pop("semi_minor_axis")
    )
    assert_almost_equal(
        cf_dict.pop("inverse_flattening"), expected_cf.pop("inverse_flattening")
    )
    if "towgs84" in expected_cf:
        assert_almost_equal(cf_dict.pop("towgs84"), expected_cf.pop("towgs84"))

    assert cf_dict == expected_cf


def test_to_cf_transverse_mercator():
    crs = CRS(
        proj="tmerc",
        lat_0=0,
        lon_0=15,
        k=0.9996,
        x_0=2520000,
        y_0=0,
        ellps="intl",
        units="m",
        towgs84="-122.74,-34.27,-22.83,-1.884,-3.400,-3.030,-15.62",
    )
    towgs84_test = [-122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62]
    expected_cf = {
        "semi_major_axis": 6378388.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": 297.0,
        "reference_ellipsoid_name": "International 1909 (Hayford)",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": (
            "Unknown based on International 1909 (Hayford) ellipsoid"
        ),
        "towgs84": towgs84_test,
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_central_meridian": 15.0,
        "false_easting": 2520000.0,
        "false_northing": 0.0,
        "scale_factor_at_central_meridian": 0.9996,
        "geographic_crs_name": "unknown",
        "projected_crs_name": "unknown",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("BOUNDCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "BOUNDCRS[")

    with pytest.warns(UserWarning):
        assert crs.to_dict() == {
            "proj": "tmerc",
            "lat_0": 0,
            "lon_0": 15,
            "k": 0.9996,
            "x_0": 2520000,
            "y_0": 0,
            "ellps": "intl",
            "towgs84": towgs84_test,
            "units": "m",
            "no_defs": None,
            "type": "crs",
        }


@pytest.mark.parametrize(
    "towgs84_test",
    [
        (-122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62),
        "-122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62",
    ],
)
def test_from_cf_transverse_mercator(towgs84_test):
    crs = CRS.from_cf(
        {
            "grid_mapping_name": "transverse_mercator",
            "latitude_of_projection_origin": 0,
            "longitude_of_central_meridian": 15,
            "false_easting": 2520000,
            "false_northing": 0,
            "reference_ellipsoid_name": "intl",
            "towgs84": towgs84_test,
            "unit": "m",
        }
    )
    expected_cf = {
        "semi_major_axis": 6378388.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": 297.0,
        "reference_ellipsoid_name": "International 1909 (Hayford)",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_central_meridian": 15.0,
        "false_easting": 2520000.0,
        "false_northing": 0.0,
        "scale_factor_at_central_meridian": 1.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
        "horizontal_datum_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("BOUNDCRS[")
    assert_almost_equal(cf_dict.pop("towgs84"), _try_list_if_string(towgs84_test))
    assert cf_dict == expected_cf
    # test roundtrip
    expected_cf["towgs84"] = _try_list_if_string(towgs84_test)
    _test_roundtrip(expected_cf, "BOUNDCRS[")


def test_cf_from_latlon():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="latitude_longitude",
            semi_major_axis=6378137.0,
            inverse_flattening=298.257223,
        )
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "grid_mapping_name": "latitude_longitude",
        "geographic_crs_name": "undefined",
        "reference_ellipsoid_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("GEOGCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "GEOGCRS[")


def test_cf_from_latlon__named():
    crs = CRS.from_cf(dict(spatial_ref="epsg:4326"))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "WGS 84",
        "grid_mapping_name": "latitude_longitude",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("GEOGCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "GEOGCRS[")


def test_cf_from_utm():
    crs = CRS.from_cf(dict(crs_wkt="epsg:32615"))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "WGS 84",
        "horizontal_datum_name": "World Geodetic System 1984",
        "projected_crs_name": "WGS 84 / UTM zone 15N",
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_central_meridian": -93.0,
        "false_easting": 500000.0,
        "false_northing": 0.0,
        "scale_factor_at_central_meridian": 0.9996,
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_cf_from_utm__nad83():
    crs = CRS("epsg:26917")
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "GRS 1980",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "NAD83",
        "horizontal_datum_name": "North American Datum 1983",
        "projected_crs_name": "NAD83 / UTM zone 17N",
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_central_meridian": -81.0,
        "false_easting": 500000.0,
        "false_northing": 0.0,
        "scale_factor_at_central_meridian": 0.9996,
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_cf_rotated_latlon():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="rotated_latitude_longitude",
            grid_north_pole_latitude=32.5,
            grid_north_pole_longitude=170.0,
        )
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "rotated_latitude_longitude",
        "grid_north_pole_latitude": 32.5,
        "grid_north_pole_longitude": 170.0,
        "north_pole_grid_longitude": 0.0,
        "geographic_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("GEOGCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "GEOGCRS[")
    with pytest.warns(UserWarning):
        proj_dict = crs.to_dict()
    if LooseVersion(__proj_version__) >= LooseVersion("6.3.0"):
        assert proj_dict == {
            "proj": "ob_tran",
            "o_proj": "longlat",
            "o_lat_p": 32.5,
            "o_lon_p": 170.0,
            "lon_0": 0,
            "datum": "WGS84",
            "no_defs": None,
            "type": "crs",
        }
    else:
        assert proj_dict == {}


def test_cf_rotated_latlon__grid():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="rotated_latitude_longitude",
            grid_north_pole_latitude=32.5,
            grid_north_pole_longitude=170.0,
            north_pole_grid_longitude=1.0,
        )
    )
    with pytest.warns(UserWarning):
        proj_dict = crs.to_dict()
    if LooseVersion(__proj_version__) >= LooseVersion("6.3.0"):
        assert proj_dict == {
            "proj": "ob_tran",
            "o_proj": "longlat",
            "o_lat_p": 32.5,
            "o_lon_p": 170.0,
            "lon_0": 1.0,
            "datum": "WGS84",
            "no_defs": None,
            "type": "crs",
        }
    else:
        assert proj_dict == {}


def test_cf_lambert_conformal_conic_1sp():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="lambert_conformal_conic",
            standard_parallel=25.0,
            longitude_of_central_meridian=265.0,
            latitude_of_projection_origin=25.0,
        )
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "lambert_conformal_conic",
        "longitude_of_central_meridian": 265.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
        "standard_parallel": 25.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")

    with pytest.warns(UserWarning):
        proj_dict = crs.to_dict()
    assert proj_dict == {
        "proj": "lcc",
        "lat_1": 25,
        "lat_0": 25,
        "lon_0": 265,
        "k_0": 1,
        "x_0": 0,
        "y_0": 0,
        "datum": "WGS84",
        "units": "m",
        "no_defs": None,
        "type": "crs",
    }


@pytest.mark.parametrize("standard_parallel", [[25.0, 30.0], "25., 30."])
def test_cf_lambert_conformal_conic_2sp(standard_parallel):
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="lambert_conformal_conic",
            standard_parallel=standard_parallel,
            longitude_of_central_meridian=265.0,
            latitude_of_projection_origin=25.0,
        )
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "lambert_conformal_conic",
        "standard_parallel": (25.0, 30.0),
        "latitude_of_projection_origin": 25.0,
        "longitude_of_central_meridian": 265.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")

    with pytest.warns(UserWarning):
        proj_dict = crs.to_dict()
    assert proj_dict == {
        "proj": "lcc",
        "lat_1": 25,
        "lat_2": 30,
        "lat_0": 25,
        "lon_0": 265,
        "x_0": 0,
        "y_0": 0,
        "datum": "WGS84",
        "units": "m",
        "no_defs": None,
        "type": "crs",
    }


def test_oblique_mercator():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="oblique_mercator",
            azimuth_of_central_line=0.35,
            latitude_of_projection_origin=10,
            longitude_of_projection_origin=15,
            reference_ellipsoid_name="WGS84",
            false_easting=0.0,
            false_northing=0.0,
        )
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "grid_mapping_name": "oblique_mercator",
        "latitude_of_projection_origin": 10.0,
        "longitude_of_projection_origin": 15.0,
        "azimuth_of_central_line": 0.35,
        "scale_factor_at_projection_origin": 1.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
        "horizontal_datum_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")
    with pytest.warns(UserWarning):
        assert crs.to_dict() == {
            "proj": "omerc",
            "lat_0": 10,
            "lonc": 15,
            "alpha": 0.35,
            "gamma": 0,
            "k": 1,
            "x_0": 0,
            "y_0": 0,
            "ellps": "WGS84",
            "units": "m",
            "no_defs": None,
            "type": "crs",
        }


def test_oblique_mercator_losing_gamma():
    crs = CRS(
        "+proj=omerc +lat_0=-36.10360962430914 +lonc=147.0632291727015 "
        "+alpha=-54.78622979612904 +k=1 +x_0=0 +y_0=0 +gamma=-54.78622979612904"
    )
    with pytest.warns(
        UserWarning,
        match="angle from rectified to skew grid parameter lost in conversion to CF",
    ):
        crs.to_cf()


def test_cf_from_invalid():
    with pytest.raises(CRSError):
        CRS.from_cf(
            dict(
                longitude_of_central_meridian=265.0, latitude_of_projection_origin=25.0
            )
        )

    with pytest.raises(CRSError):
        CRS.from_cf(
            dict(grid_mapping_name="invalid", latitude_of_projection_origin=25.0)
        )


def test_geos_crs_sweep():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="geostationary",
            perspective_point_height=1,
            sweep_angle_axis="x",
        )
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "geostationary",
        "sweep_angle_axis": "x",
        "perspective_point_height": 1.0,
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 0.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_geos_crs_fixed_angle_axis():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="geostationary",
            perspective_point_height=1,
            fixed_angle_axis="y",
        )
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "geostationary",
        "sweep_angle_axis": "x",
        "perspective_point_height": 1.0,
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 0.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_geos_proj_string():
    crs = CRS({"proj": "geos", "h": 35785831.0, "a": 6378169.0, "b": 6356583.8})
    expected_cf = {
        "semi_major_axis": 6378169.0,
        "semi_minor_axis": 6356583.8,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "grid_mapping_name": "geostationary",
        "sweep_angle_axis": "y",
        "perspective_point_height": 35785831.0,
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 0.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
        "geographic_crs_name": "unknown",
        "horizontal_datum_name": "unknown",
        "projected_crs_name": "unknown",
        "reference_ellipsoid_name": "unknown",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_ob_tran_not_rotated_latlon():
    crs = CRS("+proj=ob_tran +o_proj=moll +o_lat_p=45 +o_lon_p=-90 +lon_0=-90")
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == {}


def test_mercator_b():
    crs = CRS.from_cf(
        {
            "grid_mapping_name": "mercator",
            "longitude_of_projection_origin": 10,
            "standard_parallel": 21.354,
            "false_easting": 0,
            "false_northing": 0,
        }
    )
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "mercator",
        "standard_parallel": 21.354,
        "longitude_of_projection_origin": 10.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    with pytest.warns(UserWarning):
        assert crs.to_dict() == {
            "datum": "WGS84",
            "lat_ts": 21.354,
            "lon_0": 10,
            "no_defs": None,
            "proj": "merc",
            "type": "crs",
            "units": "m",
            "x_0": 0,
            "y_0": 0,
        }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_osgb_1936():
    crs = CRS("OSGB 1936 / British National Grid")
    param_dict = _to_dict(crs.coordinate_operation)
    expected_cf = {
        "semi_major_axis": crs.ellipsoid.semi_major_metre,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "Airy 1830",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "OSGB 1936",
        "horizontal_datum_name": "OSGB 1936",
        "projected_crs_name": "OSGB 1936 / British National Grid",
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": 49.0,
        "longitude_of_central_meridian": -2.0,
        "false_easting": 400000.0,
        "false_northing": -100000.0,
        "scale_factor_at_central_meridian": param_dict[
            "Scale factor at natural origin"
        ],
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_export_compound_crs():
    crs = CRS("urn:ogc:def:crs,crs:EPSG::2393,crs:EPSG::5717")
    expected_cf = {
        "semi_major_axis": 6378388.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": 297.0,
        "reference_ellipsoid_name": "International 1924",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "KKJ",
        "horizontal_datum_name": "Kartastokoordinaattijarjestelma (1966)",
        "projected_crs_name": "KKJ / Finland Uniform Coordinate System",
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_central_meridian": 27.0,
        "false_easting": 3500000.0,
        "false_northing": 0.0,
        "scale_factor_at_central_meridian": 1.0,
        "geopotential_datum_name": "Helsinki 1960",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("COMPOUNDCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "COMPOUNDCRS[")


@pytest.mark.skipif(
    LooseVersion(__proj_version__) < LooseVersion("6.3.0"),
    reason="geoid model does not work in PROJ < 6.3.0",
)
def test_geoid_model_name():
    wkt = (
        'COMPOUNDCRS["NAD83 / Pennsylvania South + NAVD88 height",\n'
        '    PROJCRS["NAD83 / Pennsylvania South",\n'
        '        BASEGEOGCRS["NAD83",\n'
        '            DATUM["North American Datum 1983",\n'
        '                ELLIPSOID["GRS 1980",6378137,298.257222101,\n'
        '                    LENGTHUNIT["metre",1]]],\n'
        '            PRIMEM["Greenwich",0,\n'
        '                ANGLEUNIT["degree",0.0174532925199433]]],\n'
        '        CONVERSION["SPCS83 Pennsylvania South zone (meters)",\n'
        '            METHOD["Lambert Conic Conformal (2SP)",\n'
        '                ID["EPSG",9802]],\n'
        '            PARAMETER["Latitude of false origin",39.3333333333333,\n'
        '                ANGLEUNIT["degree",0.0174532925199433],\n'
        '                ID["EPSG",8821]],\n'
        '            PARAMETER["Longitude of false origin",-77.75,\n'
        '                ANGLEUNIT["degree",0.0174532925199433],\n'
        '                ID["EPSG",8822]],\n'
        '            PARAMETER["Latitude of 1st standard '
        'parallel",40.9666666666667,\n'
        '                ANGLEUNIT["degree",0.0174532925199433],\n'
        '                ID["EPSG",8823]],\n'
        '            PARAMETER["Latitude of 2nd standard '
        'parallel",39.9333333333333,\n'
        '                ANGLEUNIT["degree",0.0174532925199433],\n'
        '                ID["EPSG",8824]],\n'
        '            PARAMETER["Easting at false origin",600000,\n'
        '                LENGTHUNIT["metre",1],\n'
        '                ID["EPSG",8826]],\n'
        '            PARAMETER["Northing at false origin",0,\n'
        '                LENGTHUNIT["metre",1],\n'
        '                ID["EPSG",8827]]],\n'
        "        CS[Cartesian,2],\n"
        '            AXIS["easting (X)",east,\n'
        "                ORDER[1],\n"
        '                LENGTHUNIT["metre",1]],\n'
        '            AXIS["northing (Y)",north,\n'
        "                ORDER[2],\n"
        '                LENGTHUNIT["metre",1]]],\n'
        '    VERTCRS["NAVD88 height",\n'
        '        VDATUM["North American Vertical Datum 1988"],\n'
        "        CS[vertical,1],\n"
        '            AXIS["gravity-related height (H)",up,\n'
        '                LENGTHUNIT["metre",1]],\n'
        '        GEOIDMODEL["GEOID12B"]]]'
    )
    crs = CRS(wkt)
    param_dict = _to_dict(crs.sub_crs_list[0].coordinate_operation)
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "GRS 1980",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "NAD83",
        "horizontal_datum_name": "North American Datum 1983",
        "projected_crs_name": "NAD83 / Pennsylvania South",
        "grid_mapping_name": "lambert_conformal_conic",
        "standard_parallel": (
            param_dict["Latitude of 1st standard parallel"],
            param_dict["Latitude of 2nd standard parallel"],
        ),
        "latitude_of_projection_origin": param_dict["Latitude of false origin"],
        "longitude_of_central_meridian": -77.75,
        "false_easting": 600000.0,
        "false_northing": 0.0,
        "geoid_name": "GEOID12B",
        "geopotential_datum_name": "North American Vertical Datum 1988",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("COMPOUNDCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "COMPOUNDCRS[")


def test_albers_conical_equal_area():
    crs = CRS("ESRI:102008")
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "GRS 1980",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "NAD83",
        "horizontal_datum_name": "North American Datum 1983",
        "projected_crs_name": "North_America_Albers_Equal_Area_Conic",
        "grid_mapping_name": "albers_conical_equal_area",
        "standard_parallel": (20.0, 60.0),
        "latitude_of_projection_origin": 40.0,
        "longitude_of_central_meridian": -96.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_azimuthal_equidistant():
    crs = CRS("ESRI:54032")
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "geographic_crs_name": "WGS 84",
        "horizontal_datum_name": "World Geodetic System 1984",
        "projected_crs_name": "World_Azimuthal_Equidistant",
        "grid_mapping_name": "azimuthal_equidistant",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 0.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_lambert_azimuthal_equal_area():
    crs = ProjectedCRS(conversion=LambertAzumuthalEqualAreaConversion(1, 2, 3, 4))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "lambert_azimuthal_equal_area",
        "latitude_of_projection_origin": 1.0,
        "longitude_of_projection_origin": 2.0,
        "false_easting": 3.0,
        "false_northing": 4.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_lambert_cylindrical_equal_area():
    crs = ProjectedCRS(conversion=LambertCylindricalEqualAreaConversion(1, 2, 3, 4))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "lambert_cylindrical_equal_area",
        "standard_parallel": 1.0,
        "longitude_of_central_meridian": 2.0,
        "false_easting": 3.0,
        "false_northing": 4.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_mercator_a():
    crs = ProjectedCRS(conversion=MercatorAConversion(1, 2, 3, 4))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "mercator",
        "standard_parallel": 1.0,
        "longitude_of_projection_origin": 2.0,
        "false_easting": 3.0,
        "false_northing": 4.0,
        "scale_factor_at_projection_origin": 1.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_orthographic():
    crs = ProjectedCRS(conversion=OrthographicConversion(1, 2, 3, 4))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "orthographic",
        "latitude_of_projection_origin": 1.0,
        "longitude_of_projection_origin": 2.0,
        "false_easting": 3.0,
        "false_northing": 4.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_polar_stereographic_a():
    crs = ProjectedCRS(conversion=PolarStereographicAConversion(90, 1, 2, 3))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "polar_stereographic",
        "latitude_of_projection_origin": 90.0,
        "straight_vertical_longitude_from_pole": 1.0,
        "false_easting": 2.0,
        "false_northing": 3.0,
        "scale_factor_at_projection_origin": 1.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_polar_stereographic_b():
    crs = ProjectedCRS(conversion=PolarStereographicBConversion(0, 1, 2, 3))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "polar_stereographic",
        "standard_parallel": 0.0,
        "straight_vertical_longitude_from_pole": 1.0,
        "false_easting": 2.0,
        "false_northing": 3.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_stereographic():
    crs = ProjectedCRS(conversion=StereographicConversion(0, 1, 2, 3))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "stereographic",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 1.0,
        "false_easting": 2.0,
        "false_northing": 3.0,
        "scale_factor_at_projection_origin": 1.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_sinusoidal():
    crs = ProjectedCRS(conversion=SinusoidalConversion(0, 1, 2))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "sinusoidal",
        "longitude_of_projection_origin": 0.0,
        "false_easting": 1.0,
        "false_northing": 2.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_vertical_perspective():
    crs = ProjectedCRS(conversion=VerticalPerspectiveConversion(50, 0, 1, 0, 2, 3))
    expected_cf = {
        "semi_major_axis": 6378137.0,
        "semi_minor_axis": crs.ellipsoid.semi_minor_metre,
        "inverse_flattening": crs.ellipsoid.inverse_flattening,
        "reference_ellipsoid_name": "WGS 84",
        "longitude_of_prime_meridian": 0.0,
        "prime_meridian_name": "Greenwich",
        "horizontal_datum_name": "World Geodetic System 1984",
        "grid_mapping_name": "vertical_perspective",
        "perspective_point_height": 50.0,
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 1.0,
        "false_easting": 2.0,
        "false_northing": 3.0,
        "geographic_crs_name": "undefined",
        "projected_crs_name": "undefined",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == expected_cf
    # test roundtrip
    _test_roundtrip(expected_cf, "PROJCRS[")


def test_build_custom_datum():
    cf_dict = {
        "semi_major_axis": 6370997.0,
        "semi_minor_axis": 6370997.0,
        "inverse_flattening": 0.0,
        "reference_ellipsoid_name": "Normal Sphere (r=6370997)",
        "longitude_of_prime_meridian": 1.0,
        "grid_mapping_name": "oblique_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 13.809602948622212,
        "azimuth_of_central_line": 8.998112717187938,
        "scale_factor_at_projection_origin": 1.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
    }
    crs = CRS.from_cf(cf_dict)
    assert crs.datum.name == "undefined"
    assert crs.ellipsoid.name == "Normal Sphere (r=6370997)"
    assert crs.prime_meridian.name == "undefined"
    assert crs.prime_meridian.longitude == 1


def test_build_custom_datum__default_prime_meridian():
    cf_dict = {
        "semi_major_axis": 6370997.0,
        "semi_minor_axis": 6370997.0,
        "inverse_flattening": 0.0,
        "grid_mapping_name": "oblique_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 13.809602948622212,
        "azimuth_of_central_line": 8.998112717187938,
        "scale_factor_at_projection_origin": 1.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
    }
    crs = CRS.from_cf(cf_dict)
    assert crs.datum.name == "undefined"
    assert crs.ellipsoid.name == "undefined"
    assert crs.prime_meridian.name == "Greenwich"
    assert crs.prime_meridian.longitude == 0


def test_build_custom_datum__default_ellipsoid():
    cf_dict = {
        "prime_meridian_name": "Paris",
        "grid_mapping_name": "oblique_mercator",
        "latitude_of_projection_origin": 0.0,
        "longitude_of_projection_origin": 13.809602948622212,
        "azimuth_of_central_line": 8.998112717187938,
        "scale_factor_at_projection_origin": 1.0,
        "false_easting": 0.0,
        "false_northing": 0.0,
    }
    crs = CRS.from_cf(cf_dict)
    assert crs.datum.name == "undefined"
    assert crs.ellipsoid.name == "WGS 84"
    assert crs.prime_meridian.name == "Paris"
    assert str(crs.prime_meridian.longitude).startswith("2.")
