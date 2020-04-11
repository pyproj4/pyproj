from distutils.version import LooseVersion

import pytest
from numpy.testing import assert_almost_equal

from pyproj import __proj_version__
from pyproj.crs import GeographicCRS
from pyproj.crs.coordinate_operation import (
    AlbersEqualAreaConversion,
    AzumuthalEquidistantConversion,
    EquidistantCylindricalConversion,
    GeostationarySatelliteConversion,
    HotineObliqueMercatorBConversion,
    LambertAzumuthalEqualAreaConversion,
    LambertConformalConic1SPConversion,
    LambertConformalConic2SPConversion,
    LambertCylindricalEqualAreaConversion,
    LambertCylindricalEqualAreaScaleConversion,
    MercatorAConversion,
    MercatorBConversion,
    OrthographicConversion,
    PlateCarreeConversion,
    PolarStereographicAConversion,
    PolarStereographicBConversion,
    RotatedLatitudeLongitudeConversion,
    SinusoidalConversion,
    StereographicConversion,
    ToWGS84Transformation,
    TransverseMercatorConversion,
    UTMConversion,
    VerticalPerspectiveConversion,
)
from pyproj.exceptions import CRSError


def _to_dict(operation):
    param_dict = {}
    for param in operation.params:
        param_dict[param.name] = param.value
    return param_dict


def test_albers_equal_area_operation__defaults():
    aeaop = AlbersEqualAreaConversion(
        latitude_first_parallel=1, latitude_second_parallel=2
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Albers Equal Area"
    assert _to_dict(aeaop) == {
        "Easting at false origin": 0.0,
        "Latitude of 1st standard parallel": 1.0,
        "Latitude of 2nd standard parallel": 2.0,
        "Latitude of false origin": 0.0,
        "Longitude of false origin": 0.0,
        "Northing at false origin": 0.0,
    }


def test_albers_equal_area_operation():
    aeaop = AlbersEqualAreaConversion(
        latitude_first_parallel=1,
        latitude_second_parallel=2,
        latitude_false_origin=3,
        longitude_false_origin=4,
        easting_false_origin=5,
        northing_false_origin=6,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Albers Equal Area"
    assert _to_dict(aeaop) == {
        "Easting at false origin": 5.0,
        "Latitude of 1st standard parallel": 1.0,
        "Latitude of 2nd standard parallel": 2.0,
        "Latitude of false origin": 3.0,
        "Longitude of false origin": 4.0,
        "Northing at false origin": 6.0,
    }


def test_azimuthal_equidistant_operation__defaults():
    aeop = AzumuthalEquidistantConversion()
    assert aeop.name == "unknown"
    assert aeop.method_name == "Modified Azimuthal Equidistant"
    assert _to_dict(aeop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_azimuthal_equidistant_operation():
    aeop = AzumuthalEquidistantConversion(
        latitude_natural_origin=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
    )
    assert aeop.name == "unknown"
    assert aeop.method_name == "Modified Azimuthal Equidistant"
    assert _to_dict(aeop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_geostationary_operation__defaults():
    geop = GeostationarySatelliteConversion(sweep_angle_axis="x", satellite_height=10)
    assert geop.name == "unknown"
    assert geop.method_name == "Geostationary Satellite (Sweep X)"
    assert _to_dict(geop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
        "Satellite height": 10.0,
    }


def test_geostationary_operation():
    with pytest.warns(UserWarning):
        geop = GeostationarySatelliteConversion(
            sweep_angle_axis="y",
            satellite_height=11,
            latitude_natural_origin=1,
            longitude_natural_origin=2,
            false_easting=3,
            false_northing=4,
        )
    assert geop.name == "unknown"
    assert geop.method_name == "Geostationary Satellite (Sweep Y)"
    assert _to_dict(geop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
        "Satellite height": 11.0,
    }


def test_geostationary_operation__invalid_sweep():
    with pytest.raises(CRSError):
        GeostationarySatelliteConversion(sweep_angle_axis="P", satellite_height=10)


def test_lambert_azimuthal_equal_area_operation__defaults():
    aeop = LambertAzumuthalEqualAreaConversion()
    assert aeop.name == "unknown"
    assert aeop.method_name == "Lambert Azimuthal Equal Area"
    assert _to_dict(aeop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_lambert_azimuthal_equal_area_operation():
    aeop = LambertAzumuthalEqualAreaConversion(
        latitude_natural_origin=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
    )
    assert aeop.name == "unknown"
    assert aeop.method_name == "Lambert Azimuthal Equal Area"
    assert _to_dict(aeop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_lambert_conformat_conic_2sp_operation__defaults():
    aeaop = LambertConformalConic2SPConversion(
        latitude_first_parallel=1, latitude_second_parallel=2
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Lambert Conic Conformal (2SP)"
    assert _to_dict(aeaop) == {
        "Easting at false origin": 0.0,
        "Latitude of 1st standard parallel": 1.0,
        "Latitude of 2nd standard parallel": 2.0,
        "Latitude of false origin": 0.0,
        "Longitude of false origin": 0.0,
        "Northing at false origin": 0.0,
    }


def test_lambert_conformat_conic_2sp_operation():
    aeaop = LambertConformalConic2SPConversion(
        latitude_first_parallel=1,
        latitude_second_parallel=2,
        latitude_false_origin=3,
        longitude_false_origin=4,
        easting_false_origin=5,
        northing_false_origin=6,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Lambert Conic Conformal (2SP)"
    assert _to_dict(aeaop) == {
        "Easting at false origin": 5.0,
        "Latitude of 1st standard parallel": 1.0,
        "Latitude of 2nd standard parallel": 2.0,
        "Latitude of false origin": 3.0,
        "Longitude of false origin": 4.0,
        "Northing at false origin": 6.0,
    }


def test_lambert_conformat_conic_1sp_operation__defaults():
    aeaop = LambertConformalConic1SPConversion()
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Lambert Conic Conformal (1SP)"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
        "Scale factor at natural origin": 1.0,
    }


def test_lambert_conformat_conic_1sp_operation():
    aeaop = LambertConformalConic1SPConversion(
        latitude_natural_origin=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
        scale_factor_natural_origin=0.5,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Lambert Conic Conformal (1SP)"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
        "Scale factor at natural origin": 0.5,
    }


def test_lambert_cylindrical_area_operation__defaults():
    lceaop = LambertCylindricalEqualAreaConversion()
    assert lceaop.name == "unknown"
    assert lceaop.method_name == "Lambert Cylindrical Equal Area"
    assert _to_dict(lceaop) == {
        "Latitude of 1st standard parallel": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_lambert_cylindrical_equal_area_operation():
    lceaop = LambertCylindricalEqualAreaConversion(
        latitude_first_parallel=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
    )
    assert lceaop.name == "unknown"
    assert lceaop.method_name == "Lambert Cylindrical Equal Area"
    assert _to_dict(lceaop) == {
        "Latitude of 1st standard parallel": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_mercator_a_operation__defaults():
    aeaop = MercatorAConversion()
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Mercator (variant A)"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
        "Scale factor at natural origin": 1.0,
    }


def test_mercator_a_operation():
    aeaop = MercatorAConversion(
        latitude_natural_origin=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
        scale_factor_natural_origin=0.5,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Mercator (variant A)"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
        "Scale factor at natural origin": 0.5,
    }


def test_mercator_b_operation__defaults():
    lceaop = MercatorBConversion()
    assert lceaop.name == "unknown"
    assert lceaop.method_name == "Mercator (variant B)"
    assert _to_dict(lceaop) == {
        "Latitude of 1st standard parallel": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_mercator_b_operation():
    lceaop = MercatorBConversion(
        latitude_first_parallel=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
    )
    assert lceaop.name == "unknown"
    assert lceaop.method_name == "Mercator (variant B)"
    assert _to_dict(lceaop) == {
        "Latitude of 1st standard parallel": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_hotline_oblique_mercator_b_operation__defaults():
    hop = HotineObliqueMercatorBConversion(
        latitude_projection_centre=0,
        longitude_projection_centre=0,
        azimuth_initial_line=0,
        angle_from_rectified_to_skew_grid=0,
    )
    assert hop.name == "unknown"
    assert hop.method_name == "Hotine Oblique Mercator (variant B)"
    assert _to_dict(hop) == {
        "Latitude of projection centre": 0.0,
        "Longitude of projection centre": 0.0,
        "Azimuth of initial line": 0.0,
        "Angle from Rectified to Skew Grid": 0.0,
        "Scale factor on initial line": 1.0,
        "Easting at projection centre": 0.0,
        "Northing at projection centre": 0.0,
    }


def test_hotline_oblique_mercator_b_operation():
    hop = HotineObliqueMercatorBConversion(
        latitude_projection_centre=1,
        longitude_projection_centre=2,
        azimuth_initial_line=3,
        angle_from_rectified_to_skew_grid=4,
        scale_factor_on_initial_line=0.5,
        easting_projection_centre=6,
        northing_projection_centre=7,
    )
    assert hop.name == "unknown"
    assert hop.method_name == "Hotine Oblique Mercator (variant B)"
    assert _to_dict(hop) == {
        "Latitude of projection centre": 1.0,
        "Longitude of projection centre": 2.0,
        "Azimuth of initial line": 3.0,
        "Angle from Rectified to Skew Grid": 4.0,
        "Scale factor on initial line": 0.5,
        "Easting at projection centre": 6.0,
        "Northing at projection centre": 7.0,
    }


def test_orthographic_operation__defaults():
    aeop = OrthographicConversion()
    assert aeop.name == "unknown"
    assert aeop.method_name == "Orthographic"
    assert _to_dict(aeop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_orthographic_operation():
    aeop = OrthographicConversion(
        latitude_natural_origin=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
    )
    assert aeop.name == "unknown"
    assert aeop.method_name == "Orthographic"
    assert _to_dict(aeop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_polar_stereographic_a_operation__defaults():
    aeaop = PolarStereographicAConversion(90)
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Polar Stereographic (variant A)"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 90.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
        "Scale factor at natural origin": 1.0,
    }


def test_polar_stereographic_a_operation():
    aeaop = PolarStereographicAConversion(
        latitude_natural_origin=-90,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
        scale_factor_natural_origin=0.5,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Polar Stereographic (variant A)"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": -90.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
        "Scale factor at natural origin": 0.5,
    }


def test_polar_stereographic_b_operation__defaults():
    aeop = PolarStereographicBConversion()
    assert aeop.name == "unknown"
    assert aeop.method_name == "Polar Stereographic (variant B)"
    assert _to_dict(aeop) == {
        "Latitude of standard parallel": 0.0,
        "Longitude of origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_polar_stereographic_b_operation():
    aeop = PolarStereographicBConversion(
        latitude_standard_parallel=1,
        longitude_origin=2,
        false_easting=3,
        false_northing=4,
    )
    assert aeop.name == "unknown"
    assert aeop.method_name == "Polar Stereographic (variant B)"
    assert _to_dict(aeop) == {
        "Latitude of standard parallel": 1.0,
        "Longitude of origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_sinusoidal_operation__defaults():
    aeop = SinusoidalConversion()
    assert aeop.name == "unknown"
    assert aeop.method_name == "Sinusoidal"
    assert _to_dict(aeop) == {
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_sinusoidal_operation():
    aeop = SinusoidalConversion(
        longitude_natural_origin=2, false_easting=3, false_northing=4
    )
    assert aeop.name == "unknown"
    assert aeop.method_name == "Sinusoidal"
    assert _to_dict(aeop) == {
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_stereographic_operation__defaults():
    aeaop = StereographicConversion()
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Stereographic"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
        "Scale factor at natural origin": 1.0,
    }


def test_stereographic_operation():
    aeaop = StereographicConversion(
        latitude_natural_origin=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
        scale_factor_natural_origin=0.5,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Stereographic"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
        "Scale factor at natural origin": 0.5,
    }


def test_utm_operation__defaults():
    aeop = UTMConversion(zone=2)
    assert aeop.name == "UTM zone 2N"
    assert aeop.method_name == "Transverse Mercator"


def test_utm_operation():
    aeop = UTMConversion(zone=2, hemisphere="s")
    assert aeop.name == "UTM zone 2S"
    assert aeop.method_name == "Transverse Mercator"


def test_transverse_mercator_operation__defaults():
    aeaop = TransverseMercatorConversion()
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Transverse Mercator"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
        "Scale factor at natural origin": 1.0,
    }


def test_transverse_mercator_operation():
    aeaop = TransverseMercatorConversion(
        latitude_natural_origin=1,
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
        scale_factor_natural_origin=0.5,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Transverse Mercator"
    assert _to_dict(aeaop) == {
        "Latitude of natural origin": 1.0,
        "Longitude of natural origin": 2.0,
        "False easting": 3.0,
        "False northing": 4.0,
        "Scale factor at natural origin": 0.5,
    }


def test_vertical_perspective_operation__defaults():
    aeaop = VerticalPerspectiveConversion(viewpoint_height=10)
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Vertical Perspective"
    assert _to_dict(aeaop) == {
        "Latitude of topocentric origin": 0.0,
        "Longitude of topocentric origin": 0.0,
        "Ellipsoidal height of topocentric origin": 0.0,
        "Viewpoint height": 10.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


def test_vertical_perspective_operation():
    aeaop = VerticalPerspectiveConversion(
        viewpoint_height=10,
        latitude_topocentric_origin=1,
        longitude_topocentric_origin=2,
        false_easting=3,
        false_northing=4,
        ellipsoidal_height_topocentric_origin=5,
    )
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "Vertical Perspective"
    assert _to_dict(aeaop) == {
        "Latitude of topocentric origin": 1.0,
        "Longitude of topocentric origin": 2.0,
        "Ellipsoidal height of topocentric origin": 5.0,
        "Viewpoint height": 10.0,
        "False easting": 3.0,
        "False northing": 4.0,
    }


def test_rotated_latitude_longitude_operation__defaults():
    aeaop = RotatedLatitudeLongitudeConversion(o_lat_p=1, o_lon_p=2)
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "PROJ ob_tran o_proj=longlat"
    assert _to_dict(aeaop) == {"o_lat_p": 1.0, "o_lon_p": 2.0, "lon_0": 0.0}


def test_rotated_latitude_longitude_operation():
    aeaop = RotatedLatitudeLongitudeConversion(o_lat_p=1, o_lon_p=2, lon_0=3)
    assert aeaop.name == "unknown"
    assert aeaop.method_name == "PROJ ob_tran o_proj=longlat"
    assert _to_dict(aeaop) == {"o_lat_p": 1.0, "o_lon_p": 2.0, "lon_0": 3.0}


def test_lambert_cylindrical_equal_area_scale_operation__defaults():
    lceaop = LambertCylindricalEqualAreaScaleConversion()
    if LooseVersion(__proj_version__) >= LooseVersion("6.3.1"):
        assert lceaop.name == "unknown"
        assert lceaop.method_name == "Lambert Cylindrical Equal Area"
        assert _to_dict(lceaop) == {
            "Latitude of 1st standard parallel": 0.0,
            "Longitude of natural origin": 0.0,
            "False easting": 0.0,
            "False northing": 0.0,
        }
    else:
        assert lceaop.name == "PROJ-based coordinate operation"
        assert lceaop.method_name == (
            "PROJ-based operation method: +proj=cea +lon_0=0.0 "
            "+x_0=0.0 +y_0=0.0 +k_0=1.0"
        )
        assert _to_dict(lceaop) == {}


def test_lambert_cylindrical_equal_area_scale_operation():
    lceaop = LambertCylindricalEqualAreaScaleConversion(
        longitude_natural_origin=2,
        false_easting=3,
        false_northing=4,
        scale_factor_natural_origin=0.999,
    )
    if LooseVersion(__proj_version__) >= LooseVersion("6.3.1"):
        assert lceaop.name == "unknown"
        assert lceaop.method_name == "Lambert Cylindrical Equal Area"
        op_dict = _to_dict(lceaop)
        assert_almost_equal(
            op_dict.pop("Latitude of 1st standard parallel"), 2.57, decimal=2
        )
        assert op_dict == {
            "Longitude of natural origin": 2.0,
            "False easting": 3.0,
            "False northing": 4.0,
        }
    else:
        assert lceaop.name == "PROJ-based coordinate operation"
        assert lceaop.method_name == (
            "PROJ-based operation method: +proj=cea +lon_0=2 +x_0=3 +y_0=4 +k_0=0.999"
        )
        assert _to_dict(lceaop) == {}


@pytest.mark.parametrize(
    "eqc_class", [EquidistantCylindricalConversion, PlateCarreeConversion]
)
def test_equidistant_cylindrical_conversion__defaults(eqc_class):
    eqc = eqc_class()
    assert eqc.name == "unknown"
    assert eqc.method_name == "Equidistant Cylindrical"
    assert _to_dict(eqc) == {
        "Latitude of 1st standard parallel": 0.0,
        "Latitude of natural origin": 0.0,
        "Longitude of natural origin": 0.0,
        "False easting": 0.0,
        "False northing": 0.0,
    }


@pytest.mark.parametrize(
    "eqc_class", [EquidistantCylindricalConversion, PlateCarreeConversion]
)
def test_equidistant_cylindrical_conversion(eqc_class):
    eqc = eqc_class(
        latitude_first_parallel=1.0,
        latitude_natural_origin=2.0,
        longitude_natural_origin=3.0,
        false_easting=4.0,
        false_northing=5.0,
    )
    assert eqc.name == "unknown"
    assert eqc.method_name == "Equidistant Cylindrical"
    assert _to_dict(eqc) == {
        "Latitude of 1st standard parallel": 1.0,
        "Latitude of natural origin": 2.0,
        "Longitude of natural origin": 3.0,
        "False easting": 4.0,
        "False northing": 5.0,
    }


def test_towgs84_transformation():
    transformation = ToWGS84Transformation(GeographicCRS(), 1, 2, 3, 4, 5, 6, 7)
    assert transformation.towgs84 == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert _to_dict(transformation) == {
        "Scale difference": 7.0,
        "X-axis rotation": 4.0,
        "X-axis translation": 1.0,
        "Y-axis rotation": 5.0,
        "Y-axis translation": 2.0,
        "Z-axis rotation": 6.0,
        "Z-axis translation": 3.0,
    }


def test_towgs84_transformation__defaults():
    transformation = ToWGS84Transformation(GeographicCRS())
    assert transformation.towgs84 == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert _to_dict(transformation) == {
        "Scale difference": 0.0,
        "X-axis rotation": 0.0,
        "X-axis translation": 0.0,
        "Y-axis rotation": 0.0,
        "Y-axis translation": 0.0,
        "Z-axis rotation": 0.0,
        "Z-axis translation": 0.0,
    }
