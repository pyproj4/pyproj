import pytest
from numpy.testing import assert_almost_equal

from pyproj import CRS
from pyproj.exceptions import CRSError


def test_to_cf_transverse_mercator():
    crs = CRS(
        init="epsg:3004", towgs84="-122.74,-34.27,-22.83,-1.884,-3.400,-3.030,-15.62"
    )
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    towgs84_test = [-122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62]
    assert cf_dict.pop("crs_wkt").startswith("BOUNDCRS[")
    assert cf_dict == {
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": 0,
        "longitude_of_central_meridian": 15,
        "fase_easting": 2520000,
        "fase_northing": 0,
        "reference_ellipsoid_name": "intl",
        "towgs84": towgs84_test,
        "unit": "m",
    }
    assert crs.to_proj4_dict() == {
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


def test_from_cf_transverse_mercator():
    towgs84_test = [-122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62]
    crs = CRS.from_cf(
        {
            "grid_mapping_name": "transverse_mercator",
            "latitude_of_projection_origin": 0,
            "longitude_of_central_meridian": 15,
            "fase_easting": 2520000,
            "fase_northing": 0,
            "reference_ellipsoid_name": "intl",
            "towgs84": towgs84_test,
            "unit": "m",
        }
    )
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert len(cf_dict) == 9
    assert cf_dict["crs_wkt"].startswith("BOUNDCRS[")
    assert cf_dict["grid_mapping_name"] == "transverse_mercator"
    assert cf_dict["latitude_of_projection_origin"] == 0
    assert cf_dict["longitude_of_central_meridian"] == 15
    assert cf_dict["fase_easting"] == 2520000
    assert cf_dict["fase_northing"] == 0
    assert cf_dict["reference_ellipsoid_name"] == "intl"
    assert cf_dict["unit"] == "m"
    assert_almost_equal(cf_dict["towgs84"], towgs84_test)


def test_cf_from_latlon():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="latitude_longitude",
            semi_major_axis=6378137.0,
            inverse_flattening=298.257223,
        )
    )
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert len(cf_dict) == 4
    assert cf_dict["crs_wkt"].startswith("GEOGCRS[")
    assert cf_dict["grid_mapping_name"] == "latitude_longitude"
    assert cf_dict["semi_major_axis"] == 6378137.0
    assert cf_dict["inverse_flattening"] == 298.257223


def test_cf_from_latlon__named():
    crs = CRS.from_cf(dict(spatial_ref="epsg:4326"))
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert cf_dict.pop("crs_wkt").startswith("GEOGCRS[")
    assert cf_dict == {
        "geographic_crs_name": "WGS 84",
        "grid_mapping_name": "latitude_longitude",
        "horizontal_datum_name": "WGS84",
    }


def test_cf_from_utm():
    crs = CRS.from_cf(dict(crs_wkt="epsg:32615"))
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == {
        "projected_crs_name": "WGS 84 / UTM zone 15N",
        "grid_mapping_name": "unknown",
        "horizontal_datum_name": "WGS84",
        "unit": "m",
    }


def test_cf_rotated_latlon():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="rotated_latitude_longitude",
            grid_north_pole_latitude=32.5,
            grid_north_pole_longitude=170.0,
        )
    )
    assert crs.to_proj4_dict() == {
        "proj": "ob_tran",
        "o_proj": "latlon",
        "o_lat_p": 32.5,
        "o_lon_p": 170.0,
        "type": "crs",
    }
    cf_dict = crs.to_cf()
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == dict(
        grid_mapping_name="rotated_latitude_longitude",
        grid_north_pole_latitude=32.5,
        grid_north_pole_longitude=170.0,
    )


def test_cf_rotated_latlon__grid():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="rotated_latitude_longitude",
            grid_north_pole_latitude=32.5,
            grid_north_pole_longitude=170.0,
            north_pole_grid_longitude=0,
        )
    )
    assert crs.to_proj4_dict() == {
        "proj": "ob_tran",
        "o_proj": "latlon",
        "o_lat_p": 32.5,
        "o_lon_p": 170.0,
        "lon_0": 0,
        "type": "crs",
    }


def test_cf_lambert_conformal_conic():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="lambert_conformal_conic",
            standard_parallel=25.0,
            longitude_of_central_meridian=265.0,
            latitude_of_projection_origin=25.0,
        )
    )
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == {
        "grid_mapping_name": "lambert_conformal_conic",
        "longitude_of_central_meridian": 265,
        "scale_factor_at_projection_origin": 1,
        "standard_parallel": 25,
        "latitude_of_projection_origin": 25,
        "fase_easting": 0,
        "fase_northing": 0,
        "horizontal_datum_name": "WGS84",
        "unit": "m",
    }


def test_cf_lambert_conformal_conic_1sp():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="lambert_conformal_conic",
            standard_parallel=25.0,
            longitude_of_central_meridian=265.0,
            latitude_of_projection_origin=25.0,
        )
    )
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == {
        "grid_mapping_name": "lambert_conformal_conic",
        "longitude_of_central_meridian": 265,
        "scale_factor_at_projection_origin": 1,
        "standard_parallel": 25,
        "latitude_of_projection_origin": 25,
        "fase_easting": 0,
        "fase_northing": 0,
        "horizontal_datum_name": "WGS84",
        "unit": "m",
    }
    proj_dict = crs.to_proj4_dict()
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


def test_cf_lambert_conformal_conic_2sp():
    crs = CRS.from_cf(
        dict(
            grid_mapping_name="lambert_conformal_conic",
            standard_parallel=[25.0, 30.0],
            longitude_of_central_meridian=265.0,
            latitude_of_projection_origin=25.0,
        )
    )
    with pytest.warns(UserWarning):
        cf_dict = crs.to_cf(errcheck=True)
    assert cf_dict.pop("crs_wkt").startswith("PROJCRS[")
    assert cf_dict == {
        "grid_mapping_name": "lambert_conformal_conic",
        "longitude_of_central_meridian": 265,
        "standard_parallel": [25, 30],
        "latitude_of_projection_origin": 25,
        "fase_easting": 0,
        "fase_northing": 0,
        "horizontal_datum_name": "WGS84",
        "unit": "m",
    }
    proj_dict = crs.to_proj4_dict()
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
