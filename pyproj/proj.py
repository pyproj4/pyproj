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

Input coordinates can be given as python arrays, lists/tuples,
scalars or numpy/Numeric/numarray arrays. Optimized for objects
that support the Python buffer protocol (regular python and
numpy array objects).

Download: http://python.org/pypi/pyproj

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
import re
import warnings

from pyproj import _proj
from pyproj.compat import cstrencode, pystrdecode
from pyproj.crs import CRS
from pyproj.utils import _convertback, _copytobuffer

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
        if not preserve_units and "foot" in self.crs.axis_info[0].unit_name:
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
