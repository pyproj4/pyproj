"""
Cython wrapper to provide python interfaces to
PROJ (https://proj.org) functions.

Performs geodetic computations.

The Geod class can perform forward and inverse geodetic, or
Great Circle, computations.  The forward computation involves
determining latitude, longitude and back azimuth of a terminus
point given the latitude and longitude of an initial point, plus
azimuth and distance. The inverse computation involves
determining the forward and back azimuths and distance given the
latitudes and longitudes of an initial and terminus point.

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

__all__ = ["Geod", "pj_ellps", "geodesic_version_str"]

import math

from pyproj._geod import Geod as _Geod
from pyproj._geod import geodesic_version_str
from pyproj._list import get_ellps_map
from pyproj.exceptions import GeodError
from pyproj.utils import _convertback, _copytobuffer

pj_ellps = get_ellps_map()


class Geod(_Geod):
    """
    performs forward and inverse geodetic, or Great Circle,
    computations.  The forward computation (using the 'fwd' method)
    involves determining latitude, longitude and back azimuth of a
    computations.  The forward computation (using the 'fwd' method)
    involves determining latitude, longitude and back azimuth of a
    terminus point given the latitude and longitude of an initial
    point, plus azimuth and distance. The inverse computation (using
    the 'inv' method) involves determining the forward and back
    azimuths and distance given the latitudes and longitudes of an
    initial and terminus point.

    Attributes
    ----------
    initstring: str
        The string form of the user input used to create the Geod.
    sphere: bool
        If True, it is a sphere.
    a: float
        The ellipsoid equatorial radius, or semi-major axis.
    b: float
        The ellipsoid polar radius, or semi-minor axis.
    es: float
        The 'eccentricity' of the ellipse, squared (1-b2/a2).
    f: float
        The ellipsoid 'flattening' parameter ( (a-b)/a ).

    """

    def __init__(self, initstring=None, **kwargs):
        """
        initialize a Geod class instance.

        Geodetic parameters for specifying the ellipsoid
        can be given in a dictionary 'initparams', as keyword arguments,
        or as as proj geod initialization string.

        You can get a dictionary of ellipsoids using :func:`~pyproj.get_ellps_map`
        or with the variable `pyproj.pj_ellps`.

        The parameters of the ellipsoid may also be set directly using
        the 'a' (semi-major or equatorial axis radius) keyword, and
        any one of the following keywords: 'b' (semi-minor,
        or polar axis radius), 'e' (eccentricity), 'es' (eccentricity
        squared), 'f' (flattening), or 'rf' (reciprocal flattening).

        See the proj documentation (https://proj.org) for more
        information about specifying ellipsoid parameters.

        Example usage:

        >>> from pyproj import Geod
        >>> g = Geod(ellps='clrk66') # Use Clarke 1866 ellipsoid.
        >>> # specify the lat/lons of some cities.
        >>> boston_lat = 42.+(15./60.); boston_lon = -71.-(7./60.)
        >>> portland_lat = 45.+(31./60.); portland_lon = -123.-(41./60.)
        >>> newyork_lat = 40.+(47./60.); newyork_lon = -73.-(58./60.)
        >>> london_lat = 51.+(32./60.); london_lon = -(5./60.)
        >>> # compute forward and back azimuths, plus distance
        >>> # between Boston and Portland.
        >>> az12,az21,dist = g.inv(boston_lon,boston_lat,portland_lon,portland_lat)
        >>> "%7.3f %6.3f %12.3f" % (az12,az21,dist)
        '-66.531 75.654  4164192.708'
        >>> # compute latitude, longitude and back azimuth of Portland,
        >>> # given Boston lat/lon, forward azimuth and distance to Portland.
        >>> endlon, endlat, backaz = g.fwd(boston_lon, boston_lat, az12, dist)
        >>> "%6.3f  %6.3f %13.3f" % (endlat,endlon,backaz)
        '45.517  -123.683        75.654'
        >>> # compute the azimuths, distances from New York to several
        >>> # cities (pass a list)
        >>> lons1 = 3*[newyork_lon]; lats1 = 3*[newyork_lat]
        >>> lons2 = [boston_lon, portland_lon, london_lon]
        >>> lats2 = [boston_lat, portland_lat, london_lat]
        >>> az12,az21,dist = g.inv(lons1,lats1,lons2,lats2)
        >>> for faz, baz, d in list(zip(az12,az21,dist)):
        ...     "%7.3f %7.3f %9.3f" % (faz, baz, d)
        ' 54.663 -123.448 288303.720'
        '-65.463  79.342 4013037.318'
        ' 51.254 -71.576 5579916.651'
        >>> g2 = Geod('+ellps=clrk66') # use proj4 style initialization string
        >>> az12,az21,dist = g2.inv(boston_lon,boston_lat,portland_lon,portland_lat)
        >>> "%7.3f %6.3f %12.3f" % (az12,az21,dist)
        '-66.531 75.654  4164192.708'
        """
        # if initparams is a proj-type init string,
        # convert to dict.
        ellpsd = {}
        if initstring is not None:
            for kvpair in initstring.split():
                # Actually only +a and +b are needed
                # We can ignore safely any parameter that doesn't have a value
                if kvpair.find("=") == -1:
                    continue
                k, v = kvpair.split("=")
                k = k.lstrip("+")
                if k in ["a", "b", "rf", "f", "es", "e"]:
                    v = float(v)
                ellpsd[k] = v
        # merge this dict with kwargs dict.
        kwargs = dict(list(kwargs.items()) + list(ellpsd.items()))
        sphere = False
        if "ellps" in kwargs:
            # ellipse name given, look up in pj_ellps dict
            ellps_dict = pj_ellps[kwargs["ellps"]]
            a = ellps_dict["a"]
            if ellps_dict["description"] == "Normal Sphere":
                sphere = True
            if "b" in ellps_dict:
                b = ellps_dict["b"]
                es = 1.0 - (b * b) / (a * a)
                f = (a - b) / a
            elif "rf" in ellps_dict:
                f = 1.0 / ellps_dict["rf"]
                b = a * (1.0 - f)
                es = 1.0 - (b * b) / (a * a)
        else:
            # a (semi-major axis) and one of
            # b the semi-minor axis
            # rf the reciprocal flattening
            # f flattening
            # es eccentricity squared
            # must be given.
            a = kwargs["a"]
            if "b" in kwargs:
                b = kwargs["b"]
                es = 1.0 - (b * b) / (a * a)
                f = (a - b) / a
            elif "rf" in kwargs:
                f = 1.0 / kwargs["rf"]
                b = a * (1.0 - f)
                es = 1.0 - (b * b) / (a * a)
            elif "f" in kwargs:
                f = kwargs["f"]
                b = a * (1.0 - f)
                es = 1.0 - (b / a) ** 2
            elif "es" in kwargs:
                es = kwargs["es"]
                b = math.sqrt(a ** 2 - es * a ** 2)
                f = (a - b) / a
            elif "e" in kwargs:
                es = kwargs["e"] ** 2
                b = math.sqrt(a ** 2 - es * a ** 2)
                f = (a - b) / a
            else:
                b = a
                f = 0.0
                es = 0.0
                # msg='ellipse name or a, plus one of f,es,b must be given'
                # raise ValueError(msg)
        if math.fabs(f) < 1.0e-8:
            sphere = True

        super(Geod, self).__init__(a, f, sphere, b, es)

    def fwd(self, lons, lats, az, dist, radians=False):
        """
        forward transformation - Returns longitudes, latitudes and back
        azimuths of terminus points given longitudes (lons) and
        latitudes (lats) of initial points, plus forward azimuths (az)
        and distances (dist).
        latitudes (lats) of initial points, plus forward azimuths (az)
        and distances (dist).

        Works with numpy and regular python array objects, python
        sequences and scalars.

        if radians=True, lons/lats and azimuths are radians instead of
        degrees. Distances are in meters.
        """
        # process inputs, making copies that support buffer API.
        inx, xisfloat, xislist, xistuple = _copytobuffer(lons)
        iny, yisfloat, yislist, yistuple = _copytobuffer(lats)
        inz, zisfloat, zislist, zistuple = _copytobuffer(az)
        ind, disfloat, dislist, distuple = _copytobuffer(dist)
        self._fwd(inx, iny, inz, ind, radians=radians)
        # if inputs were lists, tuples or floats, convert back.
        outx = _convertback(xisfloat, xislist, xistuple, inx)
        outy = _convertback(yisfloat, yislist, xistuple, iny)
        outz = _convertback(zisfloat, zislist, zistuple, inz)
        return outx, outy, outz

    def inv(self, lons1, lats1, lons2, lats2, radians=False):
        """
        inverse transformation - Returns forward and back azimuths, plus
        distances between initial points (specified by lons1, lats1) and
        terminus points (specified by lons2, lats2).

        Works with numpy and regular python array objects, python
        sequences and scalars.

        if radians=True, lons/lats and azimuths are radians instead of
        degrees. Distances are in meters.
        """
        # process inputs, making copies that support buffer API.
        inx, xisfloat, xislist, xistuple = _copytobuffer(lons1)
        iny, yisfloat, yislist, yistuple = _copytobuffer(lats1)
        inz, zisfloat, zislist, zistuple = _copytobuffer(lons2)
        ind, disfloat, dislist, distuple = _copytobuffer(lats2)
        self._inv(inx, iny, inz, ind, radians=radians)
        # if inputs were lists, tuples or floats, convert back.
        outx = _convertback(xisfloat, xislist, xistuple, inx)
        outy = _convertback(yisfloat, yislist, xistuple, iny)
        outz = _convertback(zisfloat, zislist, zistuple, inz)
        return outx, outy, outz

    def npts(self, lon1, lat1, lon2, lat2, npts, radians=False):
        """
        Given a single initial point and terminus point (specified by
        python floats lon1,lat1 and lon2,lat2), returns a list of
        longitude/latitude pairs describing npts equally spaced
        intermediate points along the geodesic between the initial and
        terminus points.

        if radians=True, lons/lats are radians instead of degrees.

        Example usage:

        >>> from pyproj import Geod
        >>> g = Geod(ellps='clrk66') # Use Clarke 1866 ellipsoid.
        >>> # specify the lat/lons of Boston and Portland.
        >>> boston_lat = 42.+(15./60.); boston_lon = -71.-(7./60.)
        >>> portland_lat = 45.+(31./60.); portland_lon = -123.-(41./60.)
        >>> # find ten equally spaced points between Boston and Portland.
        >>> lonlats = g.npts(boston_lon,boston_lat,portland_lon,portland_lat,10)
        >>> for lon,lat in lonlats: '%6.3f  %7.3f' % (lat, lon)
        '43.528  -75.414'
        '44.637  -79.883'
        '45.565  -84.512'
        '46.299  -89.279'
        '46.830  -94.156'
        '47.149  -99.112'
        '47.251  -104.106'
        '47.136  -109.100'
        '46.805  -114.051'
        '46.262  -118.924'
        >>> # test with radians=True (inputs/outputs in radians, not degrees)
        >>> import math
        >>> dg2rad = math.radians(1.)
        >>> rad2dg = math.degrees(1.)
        >>> lonlats = g.npts(
        ...    dg2rad*boston_lon,
        ...    dg2rad*boston_lat,
        ...    dg2rad*portland_lon,
        ...    dg2rad*portland_lat,
        ...    10,
        ...    radians=True
        ... )
        >>> for lon,lat in lonlats: '%6.3f  %7.3f' % (rad2dg*lat, rad2dg*lon)
        '43.528  -75.414'
        '44.637  -79.883'
        '45.565  -84.512'
        '46.299  -89.279'
        '46.830  -94.156'
        '47.149  -99.112'
        '47.251  -104.106'
        '47.136  -109.100'
        '46.805  -114.051'
        '46.262  -118.924'
        """
        lons, lats = super(Geod, self)._npts(
            lon1, lat1, lon2, lat2, npts, radians=radians
        )
        return list(zip(lons, lats))

    def line_length(self, lons, lats, radians=False):
        """
        .. versionadded:: 2.3.0

        Calculate the total distance between points along a line.

        >>> from pyproj import Geod
        >>> geod = Geod('+a=6378137 +f=0.0033528106647475126')
        >>> lats = [-72.9, -71.9, -74.9, -74.3, -77.5, -77.4, -71.7, -65.9, -65.7,
        ...         -66.6, -66.9, -69.8, -70.0, -71.0, -77.3, -77.9, -74.7]
        >>> lons = [-74, -102, -102, -131, -163, 163, 172, 140, 113,
        ...         88, 59, 25, -4, -14, -33, -46, -61]
        >>> total_length = geod.line_length(lons, lats)
        >>> "{:.3f}".format(total_length)
        '14259605.611'


        Parameters
        ----------
        lons: array, :class:`numpy.ndarray`, list, tuple, or scalar
            The longitude points along a line.
        lats: array, :class:`numpy.ndarray`, list, tuple, or scalar
            The latitude points along a line.
        radians: bool, optional
            If True, the input data is assumed to be in radians.

        Returns
        -------
        float: The total length of the line.
        """
        # process inputs, making copies that support buffer API.
        inx, xisfloat, xislist, xistuple = _copytobuffer(lons)
        iny, yisfloat, yislist, yistuple = _copytobuffer(lats)
        return self._line_length(inx, iny, radians=radians)

    def line_lengths(self, lons, lats, radians=False):
        """
        .. versionadded:: 2.3.0

        Calculate the distances between points along a line.

        >>> from pyproj import Geod
        >>> geod = Geod(ellps="WGS84")
        >>> lats = [-72.9, -71.9, -74.9]
        >>> lons = [-74, -102, -102]
        >>> for line_length in geod.line_lengths(lons, lats):
        ...     "{:.3f}".format(line_length)
        '943065.744'
        '334805.010'

        Parameters
        ----------
        lons: array, :class:`numpy.ndarray`, list, tuple, or scalar
            The longitude points along a line.
        lats: array, :class:`numpy.ndarray`, list, tuple, or scalar
            The latitude points along a line.
        radians: bool, optional
            If True, the input data is assumed to be in radians.

        Returns
        -------
        array, :class:`numpy.ndarray`, list, tuple, or scalar:
            The total length of the line.
        """
        # process inputs, making copies that support buffer API.
        inx, xisfloat, xislist, xistuple = _copytobuffer(lons)
        iny, yisfloat, yislist, yistuple = _copytobuffer(lats)
        self._line_length(inx, iny, radians=radians)
        line_lengths = _convertback(xisfloat, xislist, xistuple, inx)
        return line_lengths if xisfloat else line_lengths[:-1]

    def polygon_area_perimeter(self, lons, lats, radians=False):
        """
        .. versionadded:: 2.3.0

        A simple interface for computing the area (meters^2) and perimeter (meters)
        of a geodesic polygon.

        .. warning:: Only simple polygons (which are not self-intersecting) are allowed.

        .. note:: lats should be in the range [-90 deg, 90 deg].

        There's no need to "close" the polygon by repeating the first vertex.
        The area returned is signed with counter-clockwise traversal being treated as
        positive.

        Example usage:

        >>> from pyproj import Geod
        >>> geod = Geod('+a=6378137 +f=0.0033528106647475126')
        >>> lats = [-72.9, -71.9, -74.9, -74.3, -77.5, -77.4, -71.7, -65.9, -65.7,
        ...         -66.6, -66.9, -69.8, -70.0, -71.0, -77.3, -77.9, -74.7]
        >>> lons = [-74, -102, -102, -131, -163, 163, 172, 140, 113,
        ...         88, 59, 25, -4, -14, -33, -46, -61]
        >>> poly_area, poly_perimeter = geod.polygon_area_perimeter(lons, lats)
        >>> "{:.1f} {:.1f}".format(poly_area, poly_perimeter)
        '13376856682207.4 14710425.4'


        Parameters
        ----------
        lons: array, :class:`numpy.ndarray`, list, tuple, or scalar
            An array of longitude values.
        lats: array, :class:`numpy.ndarray`, list, tuple, or scalar
            An array of latitude values.
        radians: bool, optional
            If True, the input data is assumed to be in radians.

        Returns
        -------
        (float, float):
            The geodesic area (meters^2) and permimeter (meters) of the polygon.
        """
        return self._polygon_area_perimeter(
            _copytobuffer(lons)[0], _copytobuffer(lats)[0], radians=radians
        )

    def geometry_length(self, geometry, radians=False):
        """
        .. versionadded:: 2.3.0

        Returns the geodesic length (meters) of the shapely geometry.

        If it is a Polygon, it will return the sum of the
        lengths along the perimeter.
        If it is a MultiPolygon or MultiLine, it will return
        the sum of the lengths.

        Example usage:

        >>> from pyproj import Geod
        >>> from shapely.geometry import Point, LineString
        >>> line_string = LineString([Point(1, 2), Point(3, 4)])
        >>> geod = Geod(ellps="WGS84")
        >>> "{:.3f}".format(geod.geometry_length(line_string))
        '313588.397'

        Parameters
        ----------
        geometry: :class:`shapely.geometry.BaseGeometry`
            The geometry to calculate the length from.
        radians: bool, optional
            If True, the input data is assumed to be in radians.

        Returns
        -------
        float: The total geodesic length of the geometry (meters).

        """
        try:
            return self.line_length(*geometry.xy, radians=radians)
        except (AttributeError, NotImplementedError):
            pass
        if hasattr(geometry, "exterior"):
            return self.geometry_length(geometry.exterior, radians=radians)
        elif hasattr(geometry, "geoms"):
            total_length = 0.0
            for geom in geometry.geoms:
                total_length += self.geometry_length(geom, radians=radians)
            return total_length
        raise GeodError("Invalid geometry provided.")

    def geometry_area_perimeter(self, geometry, radians=False):
        """
        .. versionadded:: 2.3.0

        A simple interface for computing the area (meters^2) and perimeter (meters)
        of a geodesic polygon as a shapely geometry.

        .. warning:: Only simple polygons (which are not self-intersecting) are allowed.

        .. note:: lats should be in the range [-90 deg, 90 deg].

        There's no need to "close" the polygon by repeating the first vertex.
        The area returned is signed with counter-clockwise traversal being treated as
        positive.

        If it is a Polygon, it will return the area and exterior perimeter.
        It will subtract the area of the interior holes.
        If it is a MultiPolygon or MultiLine, it will return
        the sum of the areas and perimeters of all geometries.


        Example usage:

        >>> from pyproj import Geod
        >>> from shapely.geometry import LineString, Point, Polygon
        >>> geod = Geod(ellps="WGS84")
        >>> poly_area, poly_perimeter = geod.geometry_area_perimeter(
        ...     Polygon(
        ...         LineString([
        ...             Point(1, 1), Point(1, 10), Point(10, 10), Point(10, 1)
        ...         ]),
        ...         holes=[LineString([Point(1, 2), Point(3, 4), Point(5, 2)])],
        ...     )
        ... )
        >>> "{:.3f} {:.3f}".format(poly_area, poly_perimeter)
        '-944373881400.339 3979008.036'


        Parameters
        ----------
        geometry: :class:`shapely.geometry.BaseGeometry`
            The geometry to calculate the area and perimeter from.
        radians: bool, optional
            If True, the input data is assumed to be in radians.

         Returns
        -------
        (float, float):
            The geodesic area (meters^2) and permimeter (meters) of the polygon.
       """
        try:
            return self.polygon_area_perimeter(*geometry.xy, radians=radians)
        except (AttributeError, NotImplementedError):
            pass
        # polygon
        if hasattr(geometry, "exterior"):
            total_area, total_perimeter = self.geometry_area_perimeter(
                geometry.exterior, radians=radians
            )
            # subtract area of holes
            for hole in geometry.interiors:
                area, _ = self.geometry_area_perimeter(hole, radians=radians)
                total_area -= area
            return total_area, total_perimeter
        # multi geometries
        elif hasattr(geometry, "geoms"):
            total_area = 0.0
            total_perimeter = 0.0
            for geom in geometry.geoms:
                area, perimeter = self.geometry_area_perimeter(geom, radians=radians)
                total_area += area
                total_perimeter += perimeter
            return total_area, total_perimeter
        raise GeodError("Invalid geometry provided.")

    def __repr__(self):
        # search for ellipse name
        for (ellps, vals) in pj_ellps.items():
            if self.a == vals["a"]:
                b = vals.get("b", None)
                rf = vals.get("rf", None)
                # self.sphere is True when self.f is zero or very close to
                # zero (0), so prevent divide by zero.
                if self.b == b or (not self.sphere and (1.0 / self.f) == rf):
                    return "{classname}(ellps={ellps!r})" "".format(
                        classname=self.__class__.__name__, ellps=ellps
                    )

        # no ellipse name found, call super class
        return super(Geod, self).__repr__()

    def __eq__(self, other):
        """
        equality operator == for Geod objects

        Example usage:

        >>> from pyproj import Geod
        >>> # Use Clarke 1866 ellipsoid.
        >>> gclrk1 = Geod(ellps='clrk66')
        >>> # Define Clarke 1866 using parameters
        >>> gclrk2 = Geod(a=6378206.4, b=6356583.8)
        >>> gclrk1 == gclrk2
        True
        >>> # WGS 66 ellipsoid, PROJ style
        >>> gwgs66 = Geod('+ellps=WGS66')
        >>> # Naval Weapons Lab., 1965 ellipsoid
        >>> gnwl9d = Geod('+ellps=NWL9D')
        >>> # these ellipsoids are the same
        >>> gnwl9d == gwgs66
        True
        >>> gclrk1 != gnwl9d  # Clarke 1866 is unlike NWL9D
        True
        """
        if not isinstance(other, _Geod):
            return False

        return self.__repr__() == other.__repr__()
