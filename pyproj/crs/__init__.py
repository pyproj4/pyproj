"""
This module interfaces with PROJ to produce a pythonic interface
to the coordinate reference system (CRS) information through the CRS
class.
"""

from pyproj._crs import (  # noqa: F401  pylint: disable=unused-import
    CoordinateOperation,
    CoordinateSystem,
    Datum,
    Ellipsoid,
    PrimeMeridian,
    guess_wkt_version,
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
from pyproj.exceptions import CRSError  # noqa: F401  pylint: disable=unused-import

__all__ = [
    "CRS",
    "BoundCRS",
    "CompoundCRS",
    "CustomConstructorCRS",
    "DerivedGeographicCRS",
    "GeocentricCRS",
    "GeographicCRS",
    "ProjectedCRS",
    "VerticalCRS",
    "guess_wkt_version",
    "is_proj",
    "is_wkt",
]
