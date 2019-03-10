# -*- coding: utf-8 -*-
"""
Cython wrapper to provide python interfaces to
PROJ.4 (https://github.com/OSGeo/proj.4/wiki) functions.

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

Requirements: Python 2.6, 2.7, 3.2 or higher version.

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
__version__ = "2.0.1"
__all__ = ["Proj", "Geod", "CRS", "transform", "itransform", "pj_ellps", "pj_list"]

import re
import sys
import warnings
from array import array
from itertools import chain, islice

from pyproj import _proj
from pyproj.compat import cstrencode, pystrdecode
from pyproj.crs import CRS
from pyproj.exceptions import ProjError
from pyproj.geod import Geod, geodesic_version_str, pj_ellps
from pyproj.utils import _convertback, _copytobuffer

try:
    from future_builtins import zip  # python 2.6+
except ImportError:
    pass  # python 3.x


# import numpy as np
proj_version_str = _proj.proj_version_str

pj_list = {
    "aea": "Albers Equal Area",
    "aeqd": "Azimuthal Equidistant",
    "affine": "Affine transformation",
    "airy": "Airy",
    "aitoff": "Aitoff",
    "alsk": "Mod. Stererographics of Alaska",
    "apian": "Apian Globular I",
    "august": "August Epicycloidal",
    "bacon": "Bacon Globular",
    "bertin1953": "Bertin 1953",
    "bipc": "Bipolar conic of western hemisphere",
    "boggs": "Boggs Eumorphic",
    "bonne": "Bonne (Werner lat_1=90)",
    "calcofi": "Cal Coop Ocean Fish Invest Lines/Stations",
    "cart": "Geodetic/cartesian conversions",
    "cass": "Cassini",
    "cc": "Central Cylindrical",
    "ccon": "Central Conic",
    "cea": "Equal Area Cylindrical",
    "chamb": "Chamberlin Trimetric",
    "collg": "Collignon",
    "comill": "Compact Miller",
    "crast": "Craster Parabolic (Putnins P4)",
    "deformation": "Kinematic grid shift",
    "denoy": "Denoyer Semi-Elliptical",
    "eck1": "Eckert I",
    "eck2": "Eckert II",
    "eck3": "Eckert III",
    "eck4": "Eckert IV",
    "eck5": "Eckert V",
    "eck6": "Eckert VI",
    "eqc": "Equidistant Cylindrical (Plate Caree)",
    "eqdc": "Equidistant Conic",
    "euler": "Euler",
    "etmerc": "Extended Transverse Mercator",
    "fahey": "Fahey",
    "fouc": "Foucaut",
    "fouc_s": "Foucaut Sinusoidal",
    "gall": "Gall (Gall Stereographic)",
    "geoc": "Geocentric Latitude",
    "geocent": "Geocentric",
    "geogoffset": "Geographic Offset",
    "geos": "Geostationary Satellite View",
    "gins8": "Ginsburg VIII (TsNIIGAiK)",
    "gn_sinu": "General Sinusoidal Series",
    "gnom": "Gnomonic",
    "goode": "Goode Homolosine",
    "gs48": "Mod. Stererographics of 48 U.S.",
    "gs50": "Mod. Stererographics of 50 U.S.",
    "hammer": "Hammer & Eckert-Greifendorff",
    "hatano": "Hatano Asymmetrical Equal Area",
    "healpix": "HEALPix",
    "rhealpix": "rHEALPix",
    "helmert": "3- and 7-parameter Helmert shift",
    "hgridshift": "Horizontal grid shift",
    "horner": "Horner polynomial evaluation",
    "igh": "Interrupted Goode Homolosine",
    "imw_p": "International Map of the World Polyconic",
    "isea": "Icosahedral Snyder Equal Area",
    "kav5": "Kavraisky V",
    "kav7": "Kavraisky VII",
    "krovak": "Krovak",
    "labrd": "Laborde",
    "laea": "Lambert Azimuthal Equal Area",
    "lagrng": "Lagrange",
    "larr": "Larrivee",
    "lask": "Laskowski",
    "lonlat": "Lat/long (Geodetic)",
    "latlon": "Lat/long (Geodetic alias)",
    "latlong": "Lat/long (Geodetic alias)",
    "longlat": "Lat/long (Geodetic alias)",
    "lcc": "Lambert Conformal Conic",
    "lcca": "Lambert Conformal Conic Alternative",
    "leac": "Lambert Equal Area Conic",
    "lee_os": "Lee Oblated Stereographic",
    "loxim": "Loximuthal",
    "lsat": "Space oblique for LANDSAT",
    "mbt_s": "McBryde-Thomas Flat-Polar Sine",
    "mbt_fps": "McBryde-Thomas Flat-Pole Sine (No. 2)",
    "mbtfpp": "McBride-Thomas Flat-Polar Parabolic",
    "mbtfpq": "McBryde-Thomas Flat-Polar Quartic",
    "mbtfps": "McBryde-Thomas Flat-Polar Sinusoidal",
    "merc": "Mercator",
    "mil_os": "Miller Oblated Stereographic",
    "mill": "Miller Cylindrical",
    "misrsom": "Space oblique for MISR",
    "moll": "Mollweide",
    "molobadekas": "Molodensky-Badekas transform",
    "molodensky": "Molodensky transform",
    "murd1": "Murdoch I",
    "murd2": "Murdoch II",
    "murd3": "Murdoch III",
    "natearth": "Natural Earth",
    "natearth2": "Natural Earth 2",
    "nell": "Nell",
    "nell_h": "Nell-Hammer",
    "nicol": "Nicolosi Globular",
    "nsper": "Near-sided perspective",
    "nzmg": "New Zealand Map Grid",
    "ob_tran": "General Oblique Transformation",
    "ocea": "Oblique Cylindrical Equal Area",
    "oea": "Oblated Equal Area",
    "omerc": "Oblique Mercator",
    "ortel": "Ortelius Oval",
    "ortho": "Orthographic",
    "patterson": "Patterson Cylindrical",
    "pconic": "Perspective Conic",
    "pipeline": "Transformation pipeline manager",
    "poly": "Polyconic (American)",
    "pop": "Retrieve coordinate value from pipeline stack",
    "putp1": "Putnins P1",
    "putp2": "Putnins P2",
    "putp3": "Putnins P3",
    "putp3p": "Putnins P3'",
    "putp4p": "Putnins P4'",
    "putp5": "Putnins P5",
    "putp5p": "Putnins P5'",
    "putp6": "Putnins P6",
    "putp6p": "Putnins P6'",
    "qua_aut": "Quartic Authalic",
    "robin": "Robinson",
    "rouss": "Roussilhe Stereographic",
    "rpoly": "Rectangular Polyconic",
    "sch": "Spherical Cross-track Height",
    "sinu": "Sinusoidal (Sanson-Flamsteed)",
    "somerc": "Swiss. Obl. Mercator",
    "stere": "Stereographic",
    "sterea": "Oblique Stereographic Alternative",
    "gstmerc": "Gauss-Schreiber Transverse Mercator (aka Gauss-Laborde Reunion)",
    "tcc": "Transverse Central Cylindrical",
    "tcea": "Transverse Cylindrical Equal Area",
    "times": "Times",
    "tissot": "Tissot Conic",
    "tmerc": "Transverse Mercator",
    "tpeqd": "Two Point Equidistant",
    "tpers": "Tilted perspective",
    "ups": "Universal Polar Stereographic",
    "urm5": "Urmaev V",
    "urmfps": "Urmaev Flat-Polar Sinusoidal",
    "utm": "Universal Transverse Mercator (UTM)",
    "vandg": "van der Grinten (I)",
    "vandg2": "van der Grinten II",
    "vandg3": "van der Grinten III",
    "vandg4": "van der Grinten IV",
    "vitk1": "Vitkovsky I",
    "wag1": "Wagner I (Kavraisky VI)",
    "wag2": "Wagner II",
    "wag3": "Wagner III",
    "wag4": "Wagner IV",
    "wag5": "Wagner V",
    "wag6": "Wagner VI",
    "wag7": "Wagner VII",
    "webmerc": "Web Mercator / Pseudo Mercator",
    "weren": "Werenskiold I",
    "wink1": "Winkel I",
    "wink2": "Winkel II",
    "wintri": "Winkel Tripel",
}


class Proj(_proj.Proj):
    """
    performs cartographic transformations (converts from
    longitude,latitude to native map projection x,y coordinates and
    vice versa) using proj (https://github.com/OSGeo/proj.4/wiki).

    A Proj class instance is initialized with proj map projection
    control parameter key/value pairs. The key/value pairs can
    either be passed in a dictionary, or as keyword arguments,
    or as a proj4 string (compatible with the proj command). See
    http://www.remotesensing.org/geotiff/proj_list for examples of
    key/value pairs defining different map projections.

    Calling a Proj class instance with the arguments lon, lat will
    convert lon/lat (in degrees) to x/y native map projection
    coordinates (in meters).  If optional keyword 'inverse' is True
    (default is False), the inverse transformation from x/y to
    lon/lat is performed. If optional keyword 'errcheck' is True (default is
    False) an exception is raised if the transformation is invalid.
    If errcheck=False and the transformation is invalid, no
    exception is raised and 1.e30 is returned. If the optional keyword
    'preserve_units' is True, the units in map projection coordinates
    are not forced to be meters.

    Works with numpy and regular python array objects, python
    sequences and scalars.
    """

    def __init__(self, projparams=None, preserve_units=True, **kwargs):
        """
        initialize a Proj class instance.

        See the proj documentation (https://github.com/OSGeo/proj.4/wiki)
        for more information about projection parameters.

        Parameters
        ----------
        projparams: int, str, dict, pyproj.CRS
            A proj.4 or WKT string, proj.4 dict, EPSG integer, or a pyproj.CRS instnace.
        preserve_units: bool
            If false, will ensure +units=m.
        **kwargs:
            proj.4 projection parameters.

 
        Example usage:

        >>> from pyproj import Proj
        >>> p = Proj(proj='utm',zone=10,ellps='WGS84', preserve_units=False) # use kwargs
        >>> x,y = p(-120.108, 34.36116666)
        >>> 'x=%9.3f y=%11.3f' % (x,y)
        'x=765975.641 y=3805993.134'
        >>> 'lon=%8.3f lat=%5.3f' % p(x,y,inverse=True)
        'lon=-120.108 lat=34.361'
        >>> # do 3 cities at a time in a tuple (Fresno, LA, SF)
        >>> lons = (-119.72,-118.40,-122.38)
        >>> lats = (36.77, 33.93, 37.62 )
        >>> x,y = p(lons, lats)
        >>> 'x: %9.3f %9.3f %9.3f' % x
        'x: 792763.863 925321.537 554714.301'
        >>> 'y: %9.3f %9.3f %9.3f' % y
        'y: 4074377.617 3763936.941 4163835.303'
        >>> lons, lats = p(x, y, inverse=True) # inverse transform
        >>> 'lons: %8.3f %8.3f %8.3f' % lons
        'lons: -119.720 -118.400 -122.380'
        >>> 'lats: %8.3f %8.3f %8.3f' % lats
        'lats:   36.770   33.930   37.620'
        >>> p2 = Proj('+proj=utm +zone=10 +ellps=WGS84', preserve_units=False) # use proj4 string
        >>> x,y = p2(-120.108, 34.36116666)
        >>> 'x=%9.3f y=%11.3f' % (x,y)
        'x=765975.641 y=3805993.134'
        >>> p = Proj(init="epsg:32667", preserve_units=False)
        >>> 'x=%12.3f y=%12.3f (meters)' % p(-114.057222, 51.045)
        'x=-1783506.250 y= 6193827.033 (meters)'
        >>> p = Proj("+init=epsg:32667")
        >>> 'x=%12.3f y=%12.3f (feet)' % p(-114.057222, 51.045)
        'x=-5851386.754 y=20320914.191 (feet)'
        >>> # test data with radian inputs
        >>> p1 = Proj(init="epsg:4214")
        >>> x1, y1 = p1(116.366, 39.867)
        >>> '{:.3f} {:.3f}'.format(x1, y1)
        '2.031 0.696'
        >>> x2, y2 = p1(x1, y1, inverse=True)
        >>> '{:.3f} {:.3f}'.format(x2, y2)
        '116.366 39.867'
        """
        self.crs = CRS.from_user_input(projparams if projparams is not None else kwargs)
        # make sure units are meters if preserve_units is False.
        if not preserve_units and self.crs.is_projected:
            projstring = self.crs.to_proj4(4)
            projstring = re.sub(r"\s\+units=[\w-]+", "", projstring)
            projstring += " +units=m"
            self.crs = CRS(projstring)
        super(Proj, self).__init__(
            cstrencode(self.crs.to_proj4().replace("+type=crs", "").strip())
        )

    def __call__(self, *args, **kw):
        # ,lon,lat,inverse=False,errcheck=False):
        """
        Calling a Proj class instance with the arguments lon, lat will
        convert lon/lat (in degrees) to x/y native map projection
        coordinates (in meters).  If optional keyword 'inverse' is True
        (default is False), the inverse transformation from x/y to
        lon/lat is performed. If optional keyword 'errcheck' is True (default is
        False) an exception is raised if the transformation is invalid.
        If errcheck=False and the transformation is invalid, no
        exception is raised and 1.e30 is returned.

        Inputs should be doubles (they will be cast to doubles if they
        are not, causing a slight performance hit).

        Works with numpy and regular python array objects, python
        sequences and scalars, but is fastest for array objects.
        """
        inverse = kw.get("inverse", False)
        errcheck = kw.get("errcheck", False)
        # if len(args) == 1:
        #    latlon = np.array(args[0], copy=True,
        #                      order='C', dtype=float, ndmin=2)
        #    if inverse:
        #        _proj.Proj._invn(self, latlon, radians=radians, errcheck=errcheck)
        #    else:
        #        _proj.Proj._fwdn(self, latlon, radians=radians, errcheck=errcheck)
        #    return latlon
        lon, lat = args
        # process inputs, making copies that support buffer API.
        inx, xisfloat, xislist, xistuple = _copytobuffer(lon)
        iny, yisfloat, yislist, yistuple = _copytobuffer(lat)
        # call proj4 functions. inx and iny modified in place.
        if inverse:
            self._inv(inx, iny, errcheck=errcheck)
        else:
            self._fwd(inx, iny, errcheck=errcheck)
        # if inputs were lists, tuples or floats, convert back.
        outx = _convertback(xisfloat, xislist, xistuple, inx)
        outy = _convertback(yisfloat, yislist, xistuple, iny)
        return outx, outy

    def is_latlong(self):
        """
        Returns
        -------
        bool: True if projection in geographic (lon/lat) coordinates.
        """
        warnings.warn("'is_latlong()' is deprecated. Please use 'crs.is_geographic'.")
        return self.crs.is_geographic

    def is_geocent(self):
        """
        Returns
        -------
        bool: True if projection in geocentric (x/y) coordinates
        """
        warnings.warn("'is_geocent()' is deprecated. Please use 'crs.is_geocent'.")
        return self.is_geocent

    def definition_string(self):
        """Returns formal definition string for projection

        >>> Proj('+init=epsg:4326').definition_string()
        'proj=longlat datum=WGS84 no_defs ellps=WGS84 towgs84=0,0,0'
        >>>
        """
        return pystrdecode(self.definition)

    def to_latlong_def(self):
        """return the definition string of the geographic (lat/lon)
        coordinate version of the current projection"""
        # This is a little hacky way of getting a latlong proj object
        # Maybe instead of this function the __cinit__ function can take a
        # Proj object and a type (where type = "geographic") as the libproj
        # java wrapper
        return self.crs.to_geodetic().to_proj4(4)

    # deprecated : using in transform raised a TypeError in release 1.9.5.1
    # reported in issue #53, resolved in #73.
    def to_latlong(self):
        """return a new Proj instance which is the geographic (lat/lon)
        coordinate version of the current projection"""
        return Proj(self.crs.to_geodetic())


def transform(p1, p2, x, y, z=None):
    """
    x2, y2, z2 = transform(p1, p2, x1, y1, z1)

    Transform points between two coordinate systems defined by the
    Proj instances p1 and p2.

    The points x1,y1,z1 in the coordinate system defined by p1 are
    transformed to x2,y2,z2 in the coordinate system defined by p2.

    z1 is optional, if it is not set it is assumed to be zero (and
    only x2 and y2 are returned).

    In addition to converting between cartographic and geographic
    projection coordinates, this function can take care of datum
    shifts (which cannot be done using the __call__ method of the
    Proj instances). It also allows for one of the coordinate
    systems to be geographic (proj = 'latlong').

    x,y and z can be numpy or regular python arrays, python
    lists/tuples or scalars. Arrays are fastest.  For projections in
    geocentric coordinates, values of x and y are given in meters.
    z is always meters.

    Example usage:

    >>> # projection 1: UTM zone 15, grs80 ellipse, NAD83 datum
    >>> # (defined by epsg code 26915)
    >>> p1 = Proj(init='epsg:26915', preserve_units=False)
    >>> # projection 2: UTM zone 15, clrk66 ellipse, NAD27 datum
    >>> p2 = Proj(init='epsg:26715', preserve_units=False)
    >>> # find x,y of Jefferson City, MO.
    >>> x1, y1 = p1(-92.199881,38.56694)
    >>> # transform this point to projection 2 coordinates.
    >>> x2, y2 = transform(p1,p2,x1,y1)
    >>> '%9.3f %11.3f' % (x1,y1)
    '569704.566 4269024.671'
    >>> '%9.3f %11.3f' % (x2,y2)
    '569722.342 4268814.028'
    >>> '%8.3f %5.3f' % p2(x2,y2,inverse=True)
    ' -92.200 38.567'
    >>> # process 3 points at a time in a tuple
    >>> lats = (38.83,39.32,38.75) # Columbia, KC and StL Missouri
    >>> lons = (-92.22,-94.72,-90.37)
    >>> x1, y1 = p1(lons,lats)
    >>> x2, y2 = transform(p1,p2,x1,y1)
    >>> xy = x1+y1
    >>> '%9.3f %9.3f %9.3f %11.3f %11.3f %11.3f' % xy
    '567703.344 351730.944 728553.093 4298200.739 4353698.725 4292319.005'
    >>> xy = x2+y2
    >>> '%9.3f %9.3f %9.3f %11.3f %11.3f %11.3f' % xy
    '567721.149 351747.558 728569.133 4297989.112 4353489.645 4292106.305'
    >>> lons, lats = p2(x2,y2,inverse=True)
    >>> xy = lons+lats
    >>> '%8.3f %8.3f %8.3f %5.3f %5.3f %5.3f' % xy
    ' -92.220  -94.720  -90.370 38.830 39.320 38.750'
    >>> # test datum shifting, installation of extra datum grid files.
    >>> p1 = Proj(proj='latlong',datum='WGS84')
    >>> x1 = -111.5; y1 = 45.25919444444
    >>> p2 = Proj(proj="utm",zone=10,datum='NAD27', preserve_units=False)
    >>> x2, y2 = transform(p1, p2, x1, y1)
    >>> "%s  %s" % (str(x2)[:9],str(y2)[:9])
    '1402285.9  5076292.4'
    >>> from pyproj import CRS
    >>> c1 = CRS(proj='latlong',datum='WGS84')
    >>> x1 = -111.5; y1 = 45.25919444444
    >>> c2 = CRS(proj="utm",zone=10,datum='NAD27')
    >>> x2, y2 = transform(c1, c2, x1, y1)
    >>> "%s  %s" % (str(x2)[:9],str(y2)[:9])
    '1402291.0  5076289.5'
    >>> x3, y3 = transform("epsg:4326", "epsg:3857", 33, 98)
    >>> "%.3f  %.3f" % (x3, y3)
    '10909310.098  3895303.963'
    """
    # check that p1 and p2 are valid
    if not isinstance(p1, Proj):
        p1 = CRS.from_user_input(p1)
    if not isinstance(p2, Proj):
        p2 = CRS.from_user_input(p2)

    # process inputs, making copies that support buffer API.
    inx, xisfloat, xislist, xistuple = _copytobuffer(x)
    iny, yisfloat, yislist, yistuple = _copytobuffer(y)
    if z is not None:
        inz, zisfloat, zislist, zistuple = _copytobuffer(z)
    else:
        inz = None
    # call pj_transform.  inx,iny,inz buffers modified in place.
    _proj._transform(p1, p2, inx, iny, inz)
    # if inputs were lists, tuples or floats, convert back.
    outx = _convertback(xisfloat, xislist, xistuple, inx)
    outy = _convertback(yisfloat, yislist, xistuple, iny)
    if inz is not None:
        outz = _convertback(zisfloat, zislist, zistuple, inz)
        return outx, outy, outz
    else:
        return outx, outy


def itransform(p1, p2, points, switch=False):
    """
    points2 = transform(p1, p2, points1)
    Iterator/generator version of the function pyproj.transform.
    Transform points between two coordinate systems defined by the
    Proj instances p1 and p2. This function can be used as an alternative
    to pyproj.transform when there is a need to transform a big number of
    coordinates lazily, for example when reading and processing from a file.
    Points1 is an iterable/generator of coordinates x1,y1(,z1) or lon1,lat1(,z1)
    in the coordinate system defined by p1. Points2 is an iterator that returns tuples
    of x2,y2(,z2) or lon2,lat2(,z2) coordinates in the coordinate system defined by p2.
    z are provided optionally.

    Points1 can be:
        - a tuple/list of tuples/lists i.e. for 2d points: [(xi,yi),(xj,yj),....(xn,yn)]
        - a Nx3 or Nx2 2d numpy array where N is the point number
        - a generator of coordinates (xi,yi) for 2d points or (xi,yi,zi) for 3d

    If optional keyword 'switch' is True (default is False) then x, y or lon,lat coordinates
    of points are switched to y, x or lat, lon.


    Example usage:

    >>> # projection 1: WGS84
    >>> # (defined by epsg code 4326)
    >>> p1 = Proj(init='epsg:4326', preserve_units=False)
    >>> # projection 2: GGRS87 / Greek Grid
    >>> p2 = Proj(init='epsg:2100', preserve_units=False)
    >>> # Three points with coordinates lon, lat in p1
    >>> points = [(22.95, 40.63), (22.81, 40.53), (23.51, 40.86)]
    >>> # transform this point to projection 2 coordinates.
    >>> for pt in itransform(p1,p2,points): '%6.3f %7.3f' % pt
    '411200.657 4498214.742'
    '399210.500 4487264.963'
    '458703.102 4523331.451'
    >>> for pt in itransform(4326, 2100, points): '{:.3f} {:.3f}'.format(*pt)
    '2221638.801 2637034.372'
    '2212924.125 2619851.898'
    '2238294.779 2703763.736'
    """
    if not isinstance(p1, Proj):
        p1 = CRS.from_user_input(p1)
    if not isinstance(p2, Proj):
        p2 = CRS.from_user_input(p2)

    it = iter(points)  # point iterator
    # get first point to check stride
    try:
        fst_pt = next(it)
    except StopIteration:
        raise ValueError("iterable must contain at least one point")

    stride = len(fst_pt)
    if stride not in (2, 3):
        raise ValueError("points can contain up to 3 coordinates")

    # create a coordinate sequence generator etc. x1,y1,z1,x2,y2,z2,....
    # chain so the generator returns the first point that was already acquired
    coord_gen = chain(fst_pt, (coords[c] for coords in it for c in range(stride)))

    while True:
        # create a temporary buffer storage for the next 64 points (64*stride*8 bytes)
        buff = array("d", islice(coord_gen, 0, 64 * stride))
        if len(buff) == 0:
            break

        _proj._transform_sequence(p1, p2, stride, buff, switch)

        for pt in zip(*([iter(buff)] * stride)):
            yield pt


def test(**kwargs):
    """run the examples in the docstrings using the doctest module"""
    import doctest
    import pyproj

    verbose = kwargs.get("verbose")
    failure_count, test_count = doctest.testmod(pyproj, verbose=verbose)
    failure_count_crs, test_count_crs = doctest.testmod(pyproj.crs, verbose=verbose)
    failure_count_geod, test_count_geod = doctest.testmod(pyproj.geod, verbose=verbose)

    return failure_count + failure_count_crs + failure_count_geod


if __name__ == "__main__":
    sys.exit(test(verbose=True))
