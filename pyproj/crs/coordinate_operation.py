"""
This module is for building operations to be used when
building a CRS.

https://proj.org/operations/
"""
import warnings
from distutils.version import LooseVersion
from typing import Any

from pyproj._crs import CoordinateOperation
from pyproj._proj import proj_version_str
from pyproj.exceptions import CRSError


class AlbersEqualAreaConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Albers Equal Area Conversion.

    https://proj.org/operations/projections/aea.html
    """

    def __new__(
        cls,
        latitude_first_parallel: float,
        latitude_second_parallel: float,
        latitude_false_origin: float = 0.0,
        longitude_false_origin: float = 0.0,
        easting_false_origin: float = 0.0,
        northing_false_origin: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_first_parallel: float
            First standard parallel (lat_1).
        latitude_second_parallel: float
            Second standard parallel (lat_2).
        latitude_false_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_false_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        easting_false_origin: float, optional
            False easting (x_0). Defaults to 0.0.
        northing_false_origin: float, optional
            False northing (y_0). Defaults to 0.0.
        """
        aea_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Albers Equal Area",
                "id": {"authority": "EPSG", "code": 9822},
            },
            "parameters": [
                {
                    "name": "Latitude of false origin",
                    "value": latitude_false_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8821},
                },
                {
                    "name": "Longitude of false origin",
                    "value": longitude_false_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8822},
                },
                {
                    "name": "Latitude of 1st standard parallel",
                    "value": latitude_first_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8823},
                },
                {
                    "name": "Latitude of 2nd standard parallel",
                    "value": latitude_second_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8824},
                },
                {
                    "name": "Easting at false origin",
                    "value": easting_false_origin,
                    "unit": {
                        "type": "LinearUnit",
                        "name": "Metre",
                        "conversion_factor": 1,
                    },
                    "id": {"authority": "EPSG", "code": 8826},
                },
                {
                    "name": "Northing at false origin",
                    "value": northing_false_origin,
                    "unit": {
                        "type": "LinearUnit",
                        "name": "Metre",
                        "conversion_factor": 1,
                    },
                    "id": {"authority": "EPSG", "code": 8827},
                },
            ],
        }
        return cls.from_json_dict(aea_json)


class AzumuthalEquidistantConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Modified Azimuthal Equidistant conversion.

    https://proj.org/operations/projections/aeqd.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_natural_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        aeqd_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Modified Azimuthal Equidistant",
                "id": {"authority": "EPSG", "code": 9832},
            },
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(aeqd_json)


class GeostationarySatelliteConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Geostationary Satellite conversion.

    https://proj.org/operations/projections/geos.html
    """

    def __new__(
        cls,
        sweep_angle_axis: str,
        satellite_height: float,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        sweep_angle_axis: str
            Sweep angle axis of the viewing instrument. Valid options are “X” and “Y”.
        satellite_height: float
            Satellite height.
        latitude_natural_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        sweep_angle_axis = sweep_angle_axis.strip().upper()
        valid_sweep_axis = ("X", "Y")
        if sweep_angle_axis not in valid_sweep_axis:
            raise CRSError("sweep_angle_axis only supports {}".format(valid_sweep_axis))

        if latitude_natural_origin != 0:
            warnings.warn(
                "The latitude of natural origin (lat_0) is not used "
                "within PROJ. It is only supported for exporting to "
                "the WKT or PROJ JSON formats."
            )

        geos_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Geostationary Satellite (Sweep {})".format(sweep_angle_axis)
            },
            "parameters": [
                {
                    "name": "Satellite height",
                    "value": satellite_height,
                    "unit": "metre",
                },
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(geos_json)


class LambertAzumuthalEqualAreaConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Lambert Azimuthal Equal Area conversion.

    https://proj.org/operations/projections/laea.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_natural_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        laea_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Lambert Azimuthal Equal Area",
                "id": {"authority": "EPSG", "code": 9820},
            },
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(laea_json)


class LambertConformalConic2SPConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Lambert Conformal Conic 2SP conversion.

    https://proj.org/operations/projections/lcc.html
    """

    def __new__(
        cls,
        latitude_first_parallel: float,
        latitude_second_parallel: float,
        latitude_false_origin: float = 0.0,
        longitude_false_origin: float = 0.0,
        easting_false_origin: float = 0.0,
        northing_false_origin: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_first_parallel: float
            Latitude of 1st standard parallel (lat_1).
        latitude_second_parallel: float
            Latitude of 2nd standard parallel (lat_2).
        latitude_false_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_false_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        easting_false_origin: float, optional
            False easting (x_0). Defaults to 0.0.
        northing_false_origin: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        lcc_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Lambert Conic Conformal (2SP)",
                "id": {"authority": "EPSG", "code": 9802},
            },
            "parameters": [
                {
                    "name": "Latitude of 1st standard parallel",
                    "value": latitude_first_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8823},
                },
                {
                    "name": "Latitude of 2nd standard parallel",
                    "value": latitude_second_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8824},
                },
                {
                    "name": "Latitude of false origin",
                    "value": latitude_false_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8821},
                },
                {
                    "name": "Longitude of false origin",
                    "value": longitude_false_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8822},
                },
                {
                    "name": "Easting at false origin",
                    "value": easting_false_origin,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8826},
                },
                {
                    "name": "Northing at false origin",
                    "value": northing_false_origin,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8827},
                },
            ],
        }
        return cls.from_json_dict(lcc_json)


class LambertConformalConic1SPConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Lambert Conformal Conic 1SP conversion.

    https://proj.org/operations/projections/lcc.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
        scale_factor_natural_origin: float = 1.0,
    ):
        """
        Parameters
        ----------
        latitude_natural_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.
        scale_factor_natural_origin: float, optional
            Scale factor at natural origin (k_0). Defaults to 1.0.

        """
        lcc_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Lambert Conic Conformal (1SP)",
                "id": {"authority": "EPSG", "code": 9801},
            },
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "Scale factor at natural origin",
                    "value": scale_factor_natural_origin,
                    "unit": "unity",
                    "id": {"authority": "EPSG", "code": 8805},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(lcc_json)


class LambertCylindricalEqualAreaConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Lambert Cylindrical Equal Area conversion.

    https://proj.org/operations/projections/cea.html
    """

    def __new__(
        cls,
        latitude_first_parallel: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_first_parallel: float, optional
            Latitude of 1st standard parallel (lat_ts). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        cea_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Lambert Cylindrical Equal Area",
                "id": {"authority": "EPSG", "code": 9835},
            },
            "parameters": [
                {
                    "name": "Latitude of 1st standard parallel",
                    "value": latitude_first_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8823},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(cea_json)


class LambertCylindricalEqualAreaScaleConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Lambert Cylindrical Equal Area conversion.

    This version uses the scale factor and differs from the official version.

    The scale factor will be converted to the Latitude of 1st standard parallel (lat_ts)
    when exporting to WKT in PROJ>=7.0.0. Previous version will export it as a
    PROJ-based coordinate operation in the WKT.

    https://proj.org/operations/projections/cea.html
    """

    def __new__(
        cls,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
        scale_factor_natural_origin: float = 1.0,
    ):
        """
        Parameters
        ----------
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.
        scale_factor_natural_origin: float, optional
            Scale factor at natural origin (k or k_0). Defaults to 1.0

        """
        from pyproj.crs import CRS

        # hack due to: https://github.com/OSGeo/PROJ/issues/1881
        # https://proj.org/operations/projections/cea.html
        proj_string = (
            "+proj=cea "
            "+lon_0={longitude_natural_origin} "
            "+x_0={false_easting} "
            "+y_0={false_northing} "
            "+k_0={scale_factor_natural_origin}".format(
                longitude_natural_origin=longitude_natural_origin,
                false_easting=false_easting,
                false_northing=false_northing,
                scale_factor_natural_origin=scale_factor_natural_origin,
            )
        )
        if LooseVersion(proj_version_str) >= LooseVersion("6.3.1"):
            return cls.from_json(
                CRS(proj_string).coordinate_operation.to_json()  # type: ignore
            )
        return cls.from_string(proj_string)


class MercatorAConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Mercator (variant A) conversion.

    https://proj.org/operations/projections/merc.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
        scale_factor_natural_origin: float = 1.0,
    ):
        """
        Parameters
        ----------
        longitude_natural_origin: float, optional
            Latitude of natural origin (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of natural origin (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.
        scale_factor_natural_origin: float, optional
            Scale factor at natural origin (k or k_0). Defaults to 1.0

        """
        merc_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Mercator (variant A)",
                "id": {"authority": "EPSG", "code": 9804},
            },
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "Scale factor at natural origin",
                    "value": scale_factor_natural_origin,
                    "unit": "unity",
                    "id": {"authority": "EPSG", "code": 8805},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(merc_json)


class MercatorBConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Mercator (variant B) conversion.

    https://proj.org/operations/projections/merc.html
    """

    def __new__(
        cls,
        latitude_first_parallel: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_first_parallel: float, optional
            Latitude of 1st standard parallel (lat_ts). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        merc_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Mercator (variant B)",
                "id": {"authority": "EPSG", "code": 9805},
            },
            "parameters": [
                {
                    "name": "Latitude of 1st standard parallel",
                    "value": latitude_first_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8823},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(merc_json)


class HotineObliqueMercatorBConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Hotine Oblique Mercator (variant B) conversion.

    https://proj.org/operations/projections/omerc.html
    """

    def __new__(
        cls,
        latitude_projection_centre: float,
        longitude_projection_centre: float,
        azimuth_initial_line: float,
        angle_from_rectified_to_skew_grid: float,
        scale_factor_on_initial_line: float = 1.0,
        easting_projection_centre: float = 0.0,
        northing_projection_centre: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_projection_centre: float
            Latitude of projection centre (lat_0).
        longitude_projection_centre: float
            Longitude of projection centre (lonc).
        azimuth_initial_line: float
            Azimuth of initial line (azimuth).
        angle_from_rectified_to_skew_grid: float
            Angle from Rectified to Skew Grid (gamma).
        scale_factor_on_initial_line: float, optional
            Scale factor on initial line (k or k_0). Default is 1.0.
        easting_projection_centre: float, optional
            Easting at projection centre (x_0). Default is 0.
        northing_projection_centre: float, optional
            Northing at projection centre (y_0). Default is 0.
        """
        omerc_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Hotine Oblique Mercator (variant B)",
                "id": {"authority": "EPSG", "code": 9815},
            },
            "parameters": [
                {
                    "name": "Latitude of projection centre",
                    "value": latitude_projection_centre,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8811},
                },
                {
                    "name": "Longitude of projection centre",
                    "value": longitude_projection_centre,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8812},
                },
                {
                    "name": "Azimuth of initial line",
                    "value": azimuth_initial_line,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8813},
                },
                {
                    "name": "Angle from Rectified to Skew Grid",
                    "value": angle_from_rectified_to_skew_grid,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8814},
                },
                {
                    "name": "Scale factor on initial line",
                    "value": scale_factor_on_initial_line,
                    "unit": "unity",
                    "id": {"authority": "EPSG", "code": 8815},
                },
                {
                    "name": "Easting at projection centre",
                    "value": easting_projection_centre,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8816},
                },
                {
                    "name": "Northing at projection centre",
                    "value": northing_projection_centre,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8817},
                },
            ],
        }
        return cls.from_json_dict(omerc_json)


class OrthographicConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Orthographic conversion.

    https://proj.org/operations/projections/ortho.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_natural_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        ortho_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Orthographic",
                "id": {"authority": "EPSG", "code": 9840},
            },
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(ortho_json)


class PolarStereographicAConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Polar Stereographic A conversion.

    https://proj.org/operations/projections/stere.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
        scale_factor_natural_origin: float = 1.0,
    ):
        """
        Parameters
        ----------
        latitude_natural_origin: float, optional
            Latitude of natural origin (lat_0). Either +90 or -90.
        longitude_natural_origin: float, optional
            Longitude of natural origin (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.
        scale_factor_natural_origin: float, optional
            Scale factor at natural origin (k or k_0). Defaults to 1.0

        """

        stere_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Polar Stereographic (variant A)",
                "id": {"authority": "EPSG", "code": 9810},
            },
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "Scale factor at natural origin",
                    "value": scale_factor_natural_origin,
                    "unit": "unity",
                    "id": {"authority": "EPSG", "code": 8805},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(stere_json)


class PolarStereographicBConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Polar Stereographic B conversion.

    https://proj.org/operations/projections/stere.html
    """

    def __new__(
        cls,
        latitude_standard_parallel: float = 0.0,
        longitude_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_standard_parallel: float, optional
            Latitude of standard parallel (lat_ts). Defaults to 0.0.
        longitude_origin: float, optional
            Longitude of origin (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        stere_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Polar Stereographic (variant B)",
                "id": {"authority": "EPSG", "code": 9829},
            },
            "parameters": [
                {
                    "name": "Latitude of standard parallel",
                    "value": latitude_standard_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8832},
                },
                {
                    "name": "Longitude of origin",
                    "value": longitude_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8833},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(stere_json)


class SinusoidalConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Sinusoidal conversion.

    https://proj.org/operations/projections/sinu.html
    """

    def __new__(
        cls,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        sinu_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {"name": "Sinusoidal"},
            "parameters": [
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(sinu_json)


class StereographicConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Stereographic conversion.

    https://proj.org/operations/projections/stere.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
        scale_factor_natural_origin: float = 1.0,
    ):
        """
        Parameters
        ----------
        latitude_natural_origin: float, optional
            Latitude of natural origin (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of natural origin (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.
        scale_factor_natural_origin: float, optional
            Scale factor at natural origin (k or k_0). Defaults to 1.0

        """

        stere_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {"name": "Stereographic"},
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "Scale factor at natural origin",
                    "value": scale_factor_natural_origin,
                    "unit": "unity",
                    "id": {"authority": "EPSG", "code": 8805},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(stere_json)


class UTMConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the UTM conversion.

    https://proj.org/operations/projections/utm.html
    """

    def __new__(cls, zone: str, hemisphere: str = "N"):
        """
        Parameters
        ----------
        zone: int
            UTM Zone between 1-60.
        hemisphere: str, optional
            Either N for North or S for South. Default is N.
        """
        return cls.from_name(
            "UTM zone {zone}{hemisphere}".format(zone=zone, hemisphere=hemisphere)
        )


class TransverseMercatorConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Transverse Mercator conversion.

    https://proj.org/operations/projections/tmerc.html
    """

    def __new__(
        cls,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
        scale_factor_natural_origin: float = 1.0,
    ):
        """
        Parameters
        ----------
        latitude_natural_origin: float, optional
            Latitude of projection center (lat_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.
        scale_factor_natural_origin: float, optional
            Scale factor at natural origin (k or k_0). Defaults to 1.0

        """
        tmerc_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Transverse Mercator",
                "id": {"authority": "EPSG", "code": 9807},
            },
            "parameters": [
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "Scale factor at natural origin",
                    "value": scale_factor_natural_origin,
                    "unit": "unity",
                    "id": {"authority": "EPSG", "code": 8805},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(tmerc_json)


class VerticalPerspectiveConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Vetical Perspective conversion.

    https://proj.org/operations/projections/nsper.html
    """

    def __new__(
        cls,
        viewpoint_height: float,
        latitude_topocentric_origin: float = 0.0,
        longitude_topocentric_origin: float = 0.0,
        ellipsoidal_height_topocentric_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        viewpoint_height: float
            Viewpoint height (h).
        latitude_topocentric_origin: float, optional
            Latitude of topocentric origin (lat_0). Defaults to 0.0.
        longitude_topocentric_origin: float, optional
            Longitude of topocentric origin (lon_0). Defaults to 0.0.
        ellipsoidal_height_topocentric_origin: float, optional
            Ellipsoidal height of topocentric origin. Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.

        """
        nsper_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Vertical Perspective",
                "id": {"authority": "EPSG", "code": 9838},
            },
            "parameters": [
                {
                    "name": "Latitude of topocentric origin",
                    "value": latitude_topocentric_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8834},
                },
                {
                    "name": "Longitude of topocentric origin",
                    "value": longitude_topocentric_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8835},
                },
                {
                    "name": "Ellipsoidal height of topocentric origin",
                    "value": ellipsoidal_height_topocentric_origin,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8836},
                },
                {
                    "name": "Viewpoint height",
                    "value": viewpoint_height,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8840},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(nsper_json)


class RotatedLatitudeLongitudeConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Rotated Latitude Longitude conversion.

    https://proj.org/operations/projections/ob_tran.html
    """

    def __new__(cls, o_lat_p: float, o_lon_p: float, lon_0: float = 0.0):
        """
        Parameters
        ----------
        o_lat_p: float
            Latitude of the North pole of the unrotated source CRS,
            expressed in the rotated geographic CRS.
        o_lon_p: float
            Longitude of the North pole of the unrotated source CRS,
            expressed in the rotated geographic CRS.
        lon_0: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.

        """
        rot_latlon_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {"name": "PROJ ob_tran o_proj=longlat"},
            "parameters": [
                {"name": "o_lat_p", "value": o_lat_p, "unit": "degree"},
                {"name": "o_lon_p", "value": o_lon_p, "unit": "degree"},
                {"name": "lon_0", "value": lon_0, "unit": "degree"},
            ],
        }
        return cls.from_json_dict(rot_latlon_json)


class EquidistantCylindricalConversion(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the Equidistant Cylintrical (Plate Carrée) conversion.

    https://proj.org/operations/projections/eqc.html
    """

    def __new__(
        cls,
        latitude_first_parallel: float = 0.0,
        latitude_natural_origin: float = 0.0,
        longitude_natural_origin: float = 0.0,
        false_easting: float = 0.0,
        false_northing: float = 0.0,
    ):
        """
        Parameters
        ----------
        latitude_first_parallel: float, optional
            Latitude of 1st standard parallel (lat_ts). Defaults to 0.0.
        latitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        longitude_natural_origin: float, optional
            Longitude of projection center (lon_0). Defaults to 0.0.
        false_easting: float, optional
            False easting (x_0). Defaults to 0.0.
        false_northing: float, optional
            False northing (y_0). Defaults to 0.0.
        """
        eqc_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Conversion",
            "name": "unknown",
            "method": {
                "name": "Equidistant Cylindrical",
                "id": {"authority": "EPSG", "code": 1028},
            },
            "parameters": [
                {
                    "name": "Latitude of 1st standard parallel",
                    "value": latitude_first_parallel,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8823},
                },
                {
                    "name": "Latitude of natural origin",
                    "value": latitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8801},
                },
                {
                    "name": "Longitude of natural origin",
                    "value": longitude_natural_origin,
                    "unit": "degree",
                    "id": {"authority": "EPSG", "code": 8802},
                },
                {
                    "name": "False easting",
                    "value": false_easting,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8806},
                },
                {
                    "name": "False northing",
                    "value": false_northing,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8807},
                },
            ],
        }
        return cls.from_json_dict(eqc_json)


# Add an alias for PlateCarree
PlateCarreeConversion = EquidistantCylindricalConversion


class ToWGS84Transformation(CoordinateOperation):
    """
    .. versionadded:: 2.5.0

    Class for constructing the ToWGS84 Transformation.
    """

    def __new__(
        cls,
        source_crs: Any,
        x_axis_translation: float = 0,
        y_axis_translation: float = 0,
        z_axis_translation: float = 0,
        x_axis_rotation: float = 0,
        y_axis_rotation: float = 0,
        z_axis_rotation: float = 0,
        scale_difference: float = 0,
    ):
        """
        Parameters
        ----------
        source_crs: Any
            Input to create the Source CRS.
        x_axis_translation: float, optional
            X-axis translation. Defaults to 0.0.
        y_axis_translation: float, optional
            Y-axis translation. Defaults to 0.0.
        z_axis_translation: float, optional
            Z-axis translation. Defaults to 0.0.
        x_axis_rotation: float, optional
            X-axis rotation. Defaults to 0.0.
        y_axis_rotation: float, optional
            Y-axis rotation. Defaults to 0.0.
        z_axis_rotation: float, optional
            Z-axis rotation. Defaults to 0.0.
        scale_difference: float, optional
            Scale difference. Defaults to 0.0.
        """
        from pyproj.crs import CRS

        towgs84_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "Transformation",
            "name": "Transformation from unknown to WGS84",
            "source_crs": CRS.from_user_input(source_crs).to_json_dict(),
            "target_crs": {
                "type": "GeographicCRS",
                "name": "WGS 84",
                "datum": {
                    "type": "GeodeticReferenceFrame",
                    "name": "World Geodetic System 1984",
                    "ellipsoid": {
                        "name": "WGS 84",
                        "semi_major_axis": 6378137,
                        "inverse_flattening": 298.257223563,
                    },
                },
                "coordinate_system": {
                    "subtype": "ellipsoidal",
                    "axis": [
                        {
                            "name": "Latitude",
                            "abbreviation": "lat",
                            "direction": "north",
                            "unit": "degree",
                        },
                        {
                            "name": "Longitude",
                            "abbreviation": "lon",
                            "direction": "east",
                            "unit": "degree",
                        },
                    ],
                },
                "id": {"authority": "EPSG", "code": 4326},
            },
            "method": {
                "name": "Position Vector transformation (geog2D domain)",
                "id": {"authority": "EPSG", "code": 9606},
            },
            "parameters": [
                {
                    "name": "X-axis translation",
                    "value": x_axis_translation,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8605},
                },
                {
                    "name": "Y-axis translation",
                    "value": y_axis_translation,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8606},
                },
                {
                    "name": "Z-axis translation",
                    "value": z_axis_translation,
                    "unit": "metre",
                    "id": {"authority": "EPSG", "code": 8607},
                },
                {
                    "name": "X-axis rotation",
                    "value": x_axis_rotation,
                    "unit": {
                        "type": "AngularUnit",
                        "name": "arc-second",
                        "conversion_factor": 4.84813681109536e-06,
                    },
                    "id": {"authority": "EPSG", "code": 8608},
                },
                {
                    "name": "Y-axis rotation",
                    "value": y_axis_rotation,
                    "unit": {
                        "type": "AngularUnit",
                        "name": "arc-second",
                        "conversion_factor": 4.84813681109536e-06,
                    },
                    "id": {"authority": "EPSG", "code": 8609},
                },
                {
                    "name": "Z-axis rotation",
                    "value": z_axis_rotation,
                    "unit": {
                        "type": "AngularUnit",
                        "name": "arc-second",
                        "conversion_factor": 4.84813681109536e-06,
                    },
                    "id": {"authority": "EPSG", "code": 8610},
                },
                {
                    "name": "Scale difference",
                    "value": scale_difference,
                    "unit": {
                        "type": "ScaleUnit",
                        "name": "parts per million",
                        "conversion_factor": 1e-06,
                    },
                    "id": {"authority": "EPSG", "code": 8611},
                },
            ],
        }

        return cls.from_json_dict(towgs84_json)
