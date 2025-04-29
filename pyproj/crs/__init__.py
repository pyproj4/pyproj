"""
This module interfaces with PROJ to produce a pythonic interface
to the coordinate reference system (CRS) information through the CRS
class.
"""

from pyproj._crs import (
    CoordinateOperation,
    CoordinateSystem,
    Datum,
    Ellipsoid,
    PrimeMeridian,
    is_proj,
    is_wkt,
)
from pyproj.crs.crs import (
    CRS,
    BoundCRS,
    CompoundCRS,
    CustomConstructorCRS,
    DerivedGeographicCRS,
    GeocentricCRS,
    GeographicCRS,
    ProjectedCRS,
    VerticalCRS,
)
from pyproj.exceptions import CRSError

__all__ = [
    "CoordinateOperation",
    "CoordinateSystem",
    "Datum",
    "Ellipsoid",
    "PrimeMeridian",
    "is_proj",
    "is_wkt",
    "CRS",
    "BoundCRS",
    "CompoundCRS",
    "CustomConstructorCRS",
    "DerivedGeographicCRS",
    "GeocentricCRS",
    "GeographicCRS",
    "ProjectedCRS",
    "VerticalCRS",
    "CRSError",
]
