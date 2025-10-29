"""
This module contains enumerations used in pyproj.
"""

from enum import Enum, IntFlag


class BaseEnum(Enum):
    """
    Base enumeration class that handles
    input as strings ignoring case.
    """

    @classmethod
    def create(cls, item):
        """
        Handles finding the enumeration
        ignoring case if provided as a string.
        """
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
            f"Invalid value supplied '{item}'. "
            f"Only {tuple(version.value for version in cls)} are supported."
        )


class WktVersion(BaseEnum):
    """
     .. versionadded:: 2.2.0

    Supported CRS WKT string versions

    See: :c:enum:`PJ_WKT_TYPE`
    """

    #: WKT Version 2 from 2015
    WKT2_2015 = "WKT2_2015"
    #: WKT Version 2 from 2015 Simplified
    WKT2_2015_SIMPLIFIED = "WKT2_2015_SIMPLIFIED"
    #: Deprecated alias for WKT Version 2 from 2019
    WKT2_2018 = "WKT2_2018"
    #: Deprecated alias for WKT Version 2 from 2019 Simplified
    WKT2_2018_SIMPLIFIED = "WKT2_2018_SIMPLIFIED"
    #: WKT Version 2 from 2019
    WKT2_2019 = "WKT2_2019"
    #: WKT Version 2 from 2019 Simplified
    WKT2_2019_SIMPLIFIED = "WKT2_2019_SIMPLIFIED"
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

    PJ Types for listing codes with :func:`pyproj.get_codes`

    See: :c:enum:`PJ_TYPE`

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
    DERIVED_PROJECTED_CRS = "DERIVED_PROJECTED_CRS"
    COMPOUND_CRS = "COMPOUND_CRS"
    TEMPORAL_CRS = "TEMPORAL_CRS"
    ENGINEERING_CRS = "ENGINEERING_CRS"
    BOUND_CRS = "BOUND_CRS"
    OTHER_CRS = "OTHER_CRS"
    CONVERSION = "CONVERSION"
    TRANSFORMATION = "TRANSFORMATION"
    CONCATENATED_OPERATION = "CONCATENATED_OPERATION"
    OTHER_COORDINATE_OPERATION = "OTHER_COORDINATE_OPERATION"


class GeodIntermediateFlag(IntFlag):
    """
    .. versionadded:: 3.1.0

    Flags to be used in Geod.[inv|fwd]_intermediate()
    """

    DEFAULT = 0x0

    NPTS_ROUND = 0x0
    NPTS_CEIL = 0x1
    NPTS_TRUNC = 0x2

    DEL_S_RECALC = 0x00
    DEL_S_NO_RECALC = 0x10

    AZIS_DISCARD = 0x000
    AZIS_KEEP = 0x100


class CRSExtentUse(BaseEnum):
    """
    .. versionadded:: 3.8.0

     See: :c:enum:`PROJ_CRS_EXTENT_USE`

    Controls how CRS extents are used when building candidate coordinate
    operations in :class:`pyproj.transformer.TransformerGroup`.

    Mirrors the PROJ CLI option ``--crs-extent-use``.

    Values
    ------
    NONE
        Ignore CRS areas of use.
    BOTH
        Require both source & target CRS extents to intersect operation area.
    INTERSECTION
        Use intersection of source & target CRS extents.
    SMALLEST
        Use the smallest of source or target CRS extent.
    """

    NONE = "NONE"
    BOTH = "BOTH"
    INTERSECTION = "INTERSECTION"
    SMALLEST = "SMALLEST"
