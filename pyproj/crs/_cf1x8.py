"""
This module contains mappings necessary to convert from
a CRS to a CF-1.8 compliant projection.

http://cfconventions.org/cf-conventions/cf-conventions.html#appendix-grid-mappings

"""
from pyproj._crs import Datum, Ellipsoid, PrimeMeridian
from pyproj.crs.coordinate_operation import (
    AlbersEqualAreaConversion,
    AzumuthalEquidistantConversion,
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
    PolarStereographicAConversion,
    PolarStereographicBConversion,
    RotatedLatitudeLongitudeConversion,
    SinusoidalConversion,
    StereographicConversion,
    TransverseMercatorConversion,
    VerticalPerspectiveConversion,
)
from pyproj.crs.datum import CustomDatum, CustomEllipsoid, CustomPrimeMeridian
from pyproj.exceptions import CRSError


def _horizontal_datum_from_params(cf_params):
    # step 1: build ellipsoid
    ellipsoid = None
    ellipsoid_name = cf_params.get("reference_ellipsoid_name")
    try:
        ellipsoid = CustomEllipsoid(
            name=ellipsoid_name or "undefined",
            semi_major_axis=cf_params.get("semi_major_axis"),
            semi_minor_axis=cf_params.get("semi_minor_axis"),
            inverse_flattening=cf_params.get("inverse_flattening"),
            radius=cf_params.get("earth_radius"),
        )
    except CRSError:
        if ellipsoid_name:
            ellipsoid = Ellipsoid.from_name(ellipsoid_name)

    # step 2: build prime meridian
    prime_meridian = None
    prime_meridian_name = cf_params.get("prime_meridian_name")
    try:
        ellipsoid = CustomPrimeMeridian(
            name=prime_meridian_name or "undefined",
            longitude=cf_params["prime_meridian_longitude"],
        )
    except KeyError:
        if prime_meridian_name:
            prime_meridian = PrimeMeridian.from_name(prime_meridian_name)

    # step 3: build datum
    datum_name = cf_params.get("horizontal_datum_name")
    if ellipsoid or prime_meridian:
        return CustomDatum(
            name=datum_name or "undefined",
            ellipsoid=ellipsoid or "WGS 84",
            prime_meridian=prime_meridian or "Greenwich",
        )
    if datum_name:
        return Datum.from_name(datum_name)
    return None


def _get_standard_parallels(standard_parallel):
    try:
        first_parallel = float(standard_parallel)
        second_parallel = None
    except TypeError:
        first_parallel, second_parallel = standard_parallel
    return first_parallel, second_parallel


def _albers_conical_equal_area(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_albers_equal_area
    """
    first_parallel, second_parallel = _get_standard_parallels(
        cf_params["standard_parallel"]
    )
    return AlbersEqualAreaConversion(
        latitude_first_parallel=first_parallel,
        latitude_second_parallel=second_parallel or 0.0,
        latitude_false_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_false_origin=cf_params.get("longitude_of_central_meridian", 0.0),
        easting_false_origin=cf_params.get("false_easting", 0.0),
        northing_false_origin=cf_params.get("false_northing", 0.0),
    )


def _azimuthal_equidistant(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#azimuthal-equidistant
    """
    return AzumuthalEquidistantConversion(
        latitude_natural_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_projection_origin", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _geostationary(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_geostationary_projection
    """
    try:
        sweep_angle_axis = cf_params["sweep_angle_axis"]
    except KeyError:
        sweep_angle_axis = {"x": "y", "y": "x"}[cf_params["fixed_angle_axis"].lower()]
    return GeostationarySatelliteConversion(
        sweep_angle_axis=sweep_angle_axis,
        satellite_height=cf_params["perspective_point_height"],
        latitude_natural_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_projection_origin", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _lambert_azimuthal_equal_area(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#lambert-azimuthal-equal-area
    """
    return LambertAzumuthalEqualAreaConversion(
        latitude_natural_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_projection_origin", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _lambert_conformal_conic(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_lambert_conformal
    """
    first_parallel, second_parallel = _get_standard_parallels(
        cf_params["standard_parallel"]
    )
    if second_parallel is not None:
        return LambertConformalConic2SPConversion(
            latitude_first_parallel=first_parallel,
            latitude_second_parallel=second_parallel,
            latitude_false_origin=cf_params.get("latitude_of_projection_origin", 0.0),
            longitude_false_origin=cf_params.get("longitude_of_central_meridian", 0.0),
            easting_false_origin=cf_params.get("false_easting", 0.0),
            northing_false_origin=cf_params.get("false_northing", 0.0),
        )
    return LambertConformalConic1SPConversion(
        latitude_natural_origin=first_parallel,
        longitude_natural_origin=cf_params.get("longitude_of_central_meridian", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _lambert_cylindrical_equal_area(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_lambert_cylindrical_equal_area
    """
    if "scale_factor_at_projection_origin" in cf_params:
        return LambertCylindricalEqualAreaScaleConversion(
            scale_factor_natural_origin=cf_params["scale_factor_at_projection_origin"],
            longitude_natural_origin=cf_params.get(
                "longitude_of_central_meridian", 0.0
            ),
            false_easting=cf_params.get("false_easting", 0.0),
            false_northing=cf_params.get("false_northing", 0.0),
        )
    return LambertCylindricalEqualAreaConversion(
        latitude_first_parallel=cf_params.get("standard_parallel", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_central_meridian", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _mercator(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_mercator
    """
    if "scale_factor_at_projection_origin" in cf_params:
        return MercatorAConversion(
            latitude_natural_origin=cf_params.get("standard_parallel", 0.0),
            longitude_natural_origin=cf_params.get(
                "longitude_of_projection_origin", 0.0
            ),
            false_easting=cf_params.get("false_easting", 0.0),
            false_northing=cf_params.get("false_northing", 0.0),
            scale_factor_natural_origin=cf_params["scale_factor_at_projection_origin"],
        )
    return MercatorBConversion(
        latitude_first_parallel=cf_params.get("standard_parallel", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_projection_origin", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _oblique_mercator(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_oblique_mercator
    """
    return HotineObliqueMercatorBConversion(
        latitude_projection_centre=cf_params["latitude_of_projection_origin"],
        longitude_projection_centre=cf_params["longitude_of_projection_origin"],
        azimuth_initial_line=cf_params["azimuth_of_central_line"],
        angle_from_rectified_to_skew_grid=0.0,
        scale_factor_on_initial_line=cf_params.get(
            "scale_factor_at_projection_origin", 1.0
        ),
        easting_projection_centre=cf_params.get("false_easting", 0.0),
        northing_projection_centre=cf_params.get("false_northing", 0.0),
    )


def _orthographic(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_orthographic
    """
    return OrthographicConversion(
        latitude_natural_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_projection_origin", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _polar_stereographic(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#polar-stereographic
    """
    if "standard_parallel" in cf_params:
        return PolarStereographicBConversion(
            latitude_standard_parallel=cf_params["standard_parallel"],
            longitude_origin=cf_params["straight_vertical_longitude_from_pole"],
            false_easting=cf_params.get("false_easting", 0.0),
            false_northing=cf_params.get("false_northing", 0.0),
        )
    return PolarStereographicAConversion(
        latitude_natural_origin=cf_params["latitude_of_projection_origin"],
        longitude_natural_origin=cf_params["straight_vertical_longitude_from_pole"],
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
        scale_factor_natural_origin=cf_params.get(
            "scale_factor_at_projection_origin", 1.0
        ),
    )


def _sinusoidal(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_sinusoidal
    """
    return SinusoidalConversion(
        longitude_natural_origin=cf_params.get("longitude_of_projection_origin", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _stereographic(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_stereographic
    """
    return StereographicConversion(
        latitude_natural_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_projection_origin", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
        scale_factor_natural_origin=cf_params.get(
            "scale_factor_at_projection_origin", 1.0
        ),
    )


def _transverse_mercator(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_transverse_mercator
    """
    return TransverseMercatorConversion(
        latitude_natural_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_natural_origin=cf_params.get("longitude_of_central_meridian", 0.0),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
        scale_factor_natural_origin=cf_params.get(
            "scale_factor_at_central_meridian", 1.0
        ),
    )


def _vertical_perspective(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#vertical-perspective
    """
    return VerticalPerspectiveConversion(
        viewpoint_height=cf_params["perspective_point_height"],
        latitude_topocentric_origin=cf_params.get("latitude_of_projection_origin", 0.0),
        longitude_topocentric_origin=cf_params.get(
            "longitude_of_projection_origin", 0.0
        ),
        false_easting=cf_params.get("false_easting", 0.0),
        false_northing=cf_params.get("false_northing", 0.0),
    )


def _rotated_latitude_longitude(cf_params):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_rotated_pole
    """
    return RotatedLatitudeLongitudeConversion(
        o_lat_p=cf_params["grid_north_pole_latitude"],
        o_lon_p=cf_params["grid_north_pole_longitude"],
        lon_0=cf_params.get("north_pole_grid_longitude", 0.0),
    )


_GRID_MAPPING_NAME_MAP = {
    "albers_conical_equal_area": _albers_conical_equal_area,
    "azimuthal_equidistant": _azimuthal_equidistant,
    "geostationary": _geostationary,
    "lambert_azimuthal_equal_area": _lambert_azimuthal_equal_area,
    "lambert_conformal_conic": _lambert_conformal_conic,
    "lambert_cylindrical_equal_area": _lambert_cylindrical_equal_area,
    "mercator": _mercator,
    "oblique_mercator": _oblique_mercator,
    "orthographic": _orthographic,
    "polar_stereographic": _polar_stereographic,
    "sinusoidal": _sinusoidal,
    "stereographic": _stereographic,
    "transverse_mercator": _transverse_mercator,
    "vertical_perspective": _vertical_perspective,
}

_GEOGRAPHIC_GRID_MAPPING_NAME_MAP = {
    "rotated_latitude_longitude": _rotated_latitude_longitude,
}


def _to_dict(operation):
    param_dict = {}
    for param in operation.params:
        param_dict[param.name.lower()] = param.value
    return param_dict


def _albers_conical_equal_area__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_albers_equal_area

    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "albers_conical_equal_area",
        "standard_parallel": (
            params["latitude of 1st standard parallel"],
            params["latitude of 2nd standard parallel"],
        ),
        "latitude_of_projection_origin": params["latitude of false origin"],
        "longitude_of_central_meridian": params["longitude of false origin"],
        "false_easting": params["easting at false origin"],
        "false_northing": params["northing at false origin"],
    }


def _azimuthal_equidistant__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#azimuthal-equidistant
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "azimuthal_equidistant",
        "latitude_of_projection_origin": params["latitude of natural origin"],
        "longitude_of_projection_origin": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _geostationary__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_geostationary_projection
    """
    params = _to_dict(conversion)
    sweep_angle_axis = "y"
    if conversion.method_name.lower().endswith("(sweep x)"):
        sweep_angle_axis = "x"
    return {
        "grid_mapping_name": "geostationary",
        "sweep_angle_axis": sweep_angle_axis,
        "perspective_point_height": params["satellite height"],
        "latitude_of_projection_origin": params["latitude of natural origin"],
        "longitude_of_projection_origin": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _lambert_azimuthal_equal_area__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#lambert-azimuthal-equal-area
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "lambert_azimuthal_equal_area",
        "latitude_of_projection_origin": params["latitude of natural origin"],
        "longitude_of_projection_origin": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _lambert_conformal_conic__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_lambert_conformal
    """
    params = _to_dict(conversion)
    if conversion.method_name.lower().endswith("(2sp)"):
        return {
            "grid_mapping_name": "lambert_conformal_conic",
            "standard_parallel": (
                params["latitude of 1st standard parallel"],
                params["latitude of 2nd standard parallel"],
            ),
            "latitude_of_projection_origin": params["latitude of false origin"],
            "longitude_of_central_meridian": params["longitude of false origin"],
            "false_easting": params["easting at false origin"],
            "false_northing": params["northing at false origin"],
        }
    return {
        "grid_mapping_name": "lambert_conformal_conic",
        "standard_parallel": params["latitude of natural origin"],
        "longitude_of_central_meridian": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _lambert_cylindrical_equal_area__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_lambert_cylindrical_equal_area
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "lambert_cylindrical_equal_area",
        "standard_parallel": params["latitude of 1st standard parallel"],
        "longitude_of_central_meridian": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _mercator__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_mercator
    """
    params = _to_dict(conversion)
    if conversion.method_name.lower().endswith("(variant a)"):
        return {
            "grid_mapping_name": "mercator",
            "standard_parallel": params["latitude of natural origin"],
            "longitude_of_projection_origin": params["longitude of natural origin"],
            "false_easting": params["false easting"],
            "false_northing": params["false northing"],
            "scale_factor_at_projection_origin": params[
                "scale factor at natural origin"
            ],
        }
    return {
        "grid_mapping_name": "mercator",
        "standard_parallel": params["latitude of 1st standard parallel"],
        "longitude_of_projection_origin": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _oblique_mercator__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_oblique_mercator
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "oblique_mercator",
        "latitude_of_projection_origin": params["latitude of projection centre"],
        "longitude_of_projection_origin": params["longitude of projection centre"],
        "azimuth_of_central_line": params["azimuth of initial line"],
        "scale_factor_at_projection_origin": params["scale factor on initial line"],
        "false_easting": params["easting at projection centre"],
        "false_northing": params["northing at projection centre"],
    }


def _orthographic__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_orthographic
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "orthographic",
        "latitude_of_projection_origin": params["latitude of natural origin"],
        "longitude_of_projection_origin": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _polar_stereographic__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#polar-stereographic
    """
    params = _to_dict(conversion)
    if conversion.method_name.lower().endswith("(variant b)"):
        return {
            "grid_mapping_name": "polar_stereographic",
            "standard_parallel": params["latitude of standard parallel"],
            "straight_vertical_longitude_from_pole": params["longitude of origin"],
            "false_easting": params["false easting"],
            "false_northing": params["false northing"],
        }
    return {
        "grid_mapping_name": "polar_stereographic",
        "latitude_of_projection_origin": params["latitude of natural origin"],
        "straight_vertical_longitude_from_pole": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
        "scale_factor_at_projection_origin": params["scale factor at natural origin"],
    }


def _sinusoidal__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_sinusoidal
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "sinusoidal",
        "longitude_of_projection_origin": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _stereographic__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_stereographic
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "stereographic",
        "latitude_of_projection_origin": params["latitude of natural origin"],
        "longitude_of_projection_origin": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
        "scale_factor_at_projection_origin": params["scale factor at natural origin"],
    }


def _transverse_mercator__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_transverse_mercator
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "transverse_mercator",
        "latitude_of_projection_origin": params["latitude of natural origin"],
        "longitude_of_central_meridian": params["longitude of natural origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
        "scale_factor_at_central_meridian": params["scale factor at natural origin"],
    }


def _vertical_perspective__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#vertical-perspective
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "vertical_perspective",
        "perspective_point_height": params["viewpoint height"],
        "latitude_of_projection_origin": params["latitude of topocentric origin"],
        "longitude_of_projection_origin": params["longitude of topocentric origin"],
        "false_easting": params["false easting"],
        "false_northing": params["false northing"],
    }


def _rotated_latitude_longitude__to_cf(conversion):
    """
    http://cfconventions.org/cf-conventions/cf-conventions.html#_rotated_pole
    """
    params = _to_dict(conversion)
    return {
        "grid_mapping_name": "rotated_latitude_longitude",
        "grid_north_pole_latitude": params["o_lat_p"],
        "grid_north_pole_longitude": params["o_lon_p"],
        "north_pole_grid_longitude": params["lon_0"],
    }


_INVERSE_GRID_MAPPING_NAME_MAP = {
    "albers equal area": _albers_conical_equal_area__to_cf,
    "modified azimuthal equidistant": _azimuthal_equidistant__to_cf,
    "geostationary satellite (sweep x)": _geostationary__to_cf,
    "geostationary satellite (sweep y)": _geostationary__to_cf,
    "lambert azimuthal equal area": _lambert_azimuthal_equal_area__to_cf,
    "lambert conic conformal (2sp)": _lambert_conformal_conic__to_cf,
    "lambert conic conformal (1sp)": _lambert_conformal_conic__to_cf,
    "lambert cylindrical equal area": _lambert_cylindrical_equal_area__to_cf,
    "mercator (variant a)": _mercator__to_cf,
    "mercator (variant b)": _mercator__to_cf,
    "hotine oblique mercator (variant b)": _oblique_mercator__to_cf,
    "orthographic": _orthographic__to_cf,
    "polar stereographic (variant a)": _polar_stereographic__to_cf,
    "polar stereographic (variant b)": _polar_stereographic__to_cf,
    "sinusoidal": _sinusoidal__to_cf,
    "stereographic": _stereographic__to_cf,
    "transverse mercator": _transverse_mercator__to_cf,
    "vertical perspective": _vertical_perspective__to_cf,
}

_INVERSE_GEOGRAPHIC_GRID_MAPPING_NAME_MAP = {
    "proj ob_tran o_proj=longlat": _rotated_latitude_longitude__to_cf,
    "proj ob_tran o_proj=lonlat": _rotated_latitude_longitude__to_cf,
    "proj ob_tran o_proj=latlon": _rotated_latitude_longitude__to_cf,
    "proj ob_tran o_proj=latlong": _rotated_latitude_longitude__to_cf,
}
