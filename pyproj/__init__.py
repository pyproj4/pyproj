"""
Python interface to PROJ (https://proj.org),
cartographic projections and coordinate transformations library.

Download: http://python.org/pypi/pyproj

Requirements: Python 3.5+.

Contact:  Jeffrey Whitaker <jeffrey.s.whitaker@noaa.gov>

Copyright (c) 2006-2018, Jeffrey Whitaker.
Copyright (c) 2019-2020, Open source contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
__version__ = "2.6.0"
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
