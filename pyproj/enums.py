"""
This module contains enumerations used in pyproj.

"""
from enum import Enum, IntEnum


class WktVersion(Enum):
    """
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


class ProjVersion(IntEnum):
    """
    Supported CRS PROJ string versions
    """

    #: PROJ String version 4
    PROJ_4 = 4
    #: PROJ String version 5
    PROJ_5 = 5


class TransformDirection(IntEnum):
    """
    Supported transform directions
    """

    #: Forward direction
    FORWARD = 1
    #: Inverse direction
    INVERSE = -1
    #: Do nothing
    IDENT = 0
