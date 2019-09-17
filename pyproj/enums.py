"""
This module contains enumerations used in pyproj.
"""
from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def create(cls, item):
        try:
            return cls(item)
        except ValueError:
            pass
        if isinstance(item, str):
            item = item.upper()
        for member in cls:
            if member.value == item:
                return member
        raise ValueError(
            "Invalid value supplied '{}'. "
            "Only {} are supported.".format(
                item, tuple(version.value for version in cls)
            )
        )


class WktVersion(BaseEnum):
    """
     .. versionadded:: 2.2.0

    Supported CRS WKT string versions
    """

    #: WKT Version 2 from 2015
    WKT2_2015 = "WKT2_2015"
    #: WKT Version 2 from 2015 Simplified
    WKT2_2015_SIMPLIFIED = "WKT2_2015_SIMPLIFIED"
    #: WKT Version 2 from 2018
    WKT2_2018 = "WKT2_2018"
    #: WKT Version 2 from 2018 Simplified
    WKT2_2018_SIMPLIFIED = "WKT2_2018_SIMPLIFIED"
    #: WKT Version 1 GDAL Style
    WKT1_GDAL = "WKT1_GDAL"
    #: WKT Version 1 ESRI Style
    WKT1_ESRI = "WKT1_ESRI"


class ProjVersion(BaseEnum):
    """
    .. versionadded:: 2.2.0

    Supported CRS PROJ string versions
    """

    #: PROJ String version 4
    PROJ_4 = 4
    #: PROJ String version 5
    PROJ_5 = 5


class TransformDirection(BaseEnum):
    """
    .. versionadded:: 2.2.0

    Supported transform directions
    """

    #: Forward direction
    FORWARD = "FORWARD"
    #: Inverse direction
    INVERSE = "INVERSE"
    #: Do nothing
    IDENT = "IDENT"


class PJType(BaseEnum):
    """
    .. versionadded:: 2.4.0

    PJ Types for listing codes with :func:`~pyproj.get_codes`

    Attributes
    ----------
    UNKNOWN
    ELLIPSOID
    PRIME_MERIDIAN
    GEODETIC_REFERENCE_FRAME
    DYNAMIC_GEODETIC_REFERENCE_FRAME
    VERTICAL_REFERENCE_FRAME
    DYNAMIC_VERTICAL_REFERENCE_FRAME
    DATUM_ENSEMBLE
    CRS
    GEODETIC_CRS
    GEOCENTRIC_CRS
    GEOGRAPHIC_CRS
    GEOGRAPHIC_2D_CRS
    GEOGRAPHIC_3D_CRS
    VERTICAL_CRS
    PROJECTED_CRS
    COMPOUND_CRS
    TEMPORAL_CRS
    ENGINEERING_CRS
    BOUND_CRS
    OTHER_CRS
    CONVERSION
    TRANSFORMATION
    CONCATENATED_OPERATION
    OTHER_COORDINATE_OPERATION

    """

    UNKNOWN = "UNKNOWN"
    ELLIPSOID = "ELLIPSOID"
    PRIME_MERIDIAN = "PRIME_MERIDIAN"
    GEODETIC_REFERENCE_FRAME = "GEODETIC_REFERENCE_FRAME"
    DYNAMIC_GEODETIC_REFERENCE_FRAME = "DYNAMIC_GEODETIC_REFERENCE_FRAME"
    VERTICAL_REFERENCE_FRAME = "VERTICAL_REFERENCE_FRAME"
    DYNAMIC_VERTICAL_REFERENCE_FRAME = "DYNAMIC_VERTICAL_REFERENCE_FRAME"
    DATUM_ENSEMBLE = "DATUM_ENSEMBLE"
    CRS = "CRS"
    GEODETIC_CRS = "GEODETIC_CRS"
    GEOCENTRIC_CRS = "GEOCENTRIC_CRS"
    GEOGRAPHIC_CRS = "GEOGRAPHIC_CRS"
    GEOGRAPHIC_2D_CRS = "GEOGRAPHIC_2D_CRS"
    GEOGRAPHIC_3D_CRS = "GEOGRAPHIC_3D_CRS"
    VERTICAL_CRS = "VERTICAL_CRS"
    PROJECTED_CRS = "PROJECTED_CRS"
    COMPOUND_CRS = "COMPOUND_CRS"
    TEMPORAL_CRS = "TEMPORAL_CRS"
    ENGINEERING_CRS = "ENGINEERING_CRS"
    BOUND_CRS = "BOUND_CRS"
    OTHER_CRS = "OTHER_CRS"
    CONVERSION = "CONVERSION"
    TRANSFORMATION = "TRANSFORMATION"
    CONCATENATED_OPERATION = "CONCATENATED_OPERATION"
    OTHER_COORDINATE_OPERATION = "OTHER_COORDINATE_OPERATION"
