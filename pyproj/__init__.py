# -*- coding: utf-8 -*-
"""
Cython wrapper to provide python interfaces to
PROJ (https://proj.org) functions.

Performs cartographic transformations and geodetic computations.

The Proj class can convert from geographic (longitude,latitude)
to native map projection (x,y) coordinates and vice versa, or
from one map projection coordinate system directly to another.
The module variable pj_list is a dictionary containing all the
available projections and their descriptions.

The Geod class can perform forward and inverse geodetic, or
Great Circle, computations.  The forward computation involves
determining latitude, longitude and back azimuth of a terminus
point given the latitude and longitude of an initial point, plus
azimuth and distance. The inverse computation involves
determining the forward and back azimuths and distance given the
latitudes and longitudes of an initial and terminus point.

Input coordinates can be given as python arrays, lists/tuples,
scalars or numpy/Numeric/numarray arrays. Optimized for objects
that support the Python buffer protocol (regular python and
numpy array objects).

Download: http://python.org/pypi/pyproj

Requirements: Python 3.5+.

Example scripts are in 'test' subdirectory of source distribution.
The 'test()' function will run the examples in the docstrings.

Contact:  Jeffrey Whitaker <jeffrey.s.whitaker@noaa.gov

copyright (c) 2006 by Jeffrey Whitaker.

Permission to use, copy, modify, and distribute this software
and its documentation for any purpose and without fee is hereby
granted, provided that the above copyright notice appear in all
copies and that both the copyright notice and this permission
notice appear in supporting documentation. THE AUTHOR DISCLAIMS
ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT
SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE. """
__version__ = "2.4.2.post1"
__all__ = [
    "Proj",
    "Geod",
    "CRS",
    "Transformer",
    "transform",
    "itransform",
    "pj_ellps",
    "pj_list",
    "get_angular_units_map",
    "get_ellps_map",
    "get_prime_meridians_map",
    "get_proj_operations_map",
    "get_units_map",
    "show_versions",
]

import warnings

from pyproj import _datadir
from pyproj._list import (  # noqa: F401
    get_angular_units_map,
    get_authorities,
    get_codes,
    get_ellps_map,
    get_prime_meridians_map,
    get_proj_operations_map,
    get_units_map,
)
from pyproj._show_versions import show_versions  # noqa: F401
from pyproj.crs import CRS  # noqa: F401
from pyproj.exceptions import DataDirError, ProjError  # noqa: F401
from pyproj.geod import Geod, geodesic_version_str, pj_ellps  # noqa: F401
from pyproj.proj import Proj, pj_list, proj_version_str  # noqa: F401
from pyproj.transformer import Transformer, itransform, transform  # noqa: F401

try:
    _datadir.pyproj_global_context_initialize()
except DataDirError as err:
    warnings.warn(str(err))
