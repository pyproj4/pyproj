include "base.pxi"

cimport cython

from pyproj.compat import cstrencode, pystrdecode
from pyproj.exceptions import GeodError

geodesic_version_str = "{0}.{1}.{2}".format(
    GEODESIC_VERSION_MAJOR,
    GEODESIC_VERSION_MINOR,
    GEODESIC_VERSION_PATCH
)

cdef class Geod:
    def __init__(self, double a, double f, bint sphere, double b, double es):
        geod_init(&self._geod_geodesic, <double> a, <double> f)
        self.a = a
        self.f = f
        # convert 'a' only for initstring
        a_str = int(a) if a.is_integer() else a
        f_str = int(f) if f.is_integer() else f
        self.initstring = pystrdecode(cstrencode("+a=%s +f=%s" % (a_str, f_str)))
        self.sphere = sphere
        self.b = b
        self.es = es

    def __reduce__(self):
        """special method that allows pyproj.Geod instance to be pickled"""
        return self.__class__, (self.initstring,)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _fwd(
        self,
        object lons,
        object lats,
        object az,
        object dist,
        bint radians=False,
    ):
        """
        forward transformation - determine longitude, latitude and back azimuth
        of a terminus point given an initial point longitude and latitude, plus
        forward azimuth and distance.
        if radians=True, lons/lats are radians instead of degrees.
        """
        cdef PyBuffWriteManager lonbuff = PyBuffWriteManager(lons)
        cdef PyBuffWriteManager latbuff = PyBuffWriteManager(lats)
        cdef PyBuffWriteManager azbuff = PyBuffWriteManager(az)
        cdef PyBuffWriteManager distbuff = PyBuffWriteManager(dist)

        # process data in buffer
        if not lonbuff.len == latbuff.len == azbuff.len == distbuff.len:
            raise GeodError("Array lengths are not the same.")

        cdef double lat1, lon1, az1, s12, plon2, plat2, pazi2
        cdef Py_ssize_t iii
        with nogil:
            for iii in range(lonbuff.len):
                if not radians:
                    lon1 = lonbuff.data[iii]
                    lat1 = latbuff.data[iii]
                    az1 = azbuff.data[iii]
                    s12 = distbuff.data[iii]
                else:
                    lon1 = _RAD2DG * lonbuff.data[iii]
                    lat1 = _RAD2DG * latbuff.data[iii]
                    az1 = _RAD2DG * azbuff.data[iii]
                    s12 = distbuff.data[iii]
                geod_direct(
                    &self._geod_geodesic,
                    lat1,
                    lon1,
                    az1,
                    s12,
                    &plat2,
                    &plon2,
                    &pazi2,
                )
                # back azimuth needs to be flipped 180 degrees
                # to match what PROJ geod utility produces.
                if pazi2 > 0:
                    pazi2 = pazi2 - 180.
                elif pazi2 <= 0:
                    pazi2 = pazi2 + 180.
                if not radians:
                    lonbuff.data[iii] = plon2
                    latbuff.data[iii] = plat2
                    azbuff.data[iii] = pazi2
                else:
                    lonbuff.data[iii] = _DG2RAD * plon2
                    latbuff.data[iii] = _DG2RAD * plat2
                    azbuff.data[iii] = _DG2RAD * pazi2

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _inv(
        self,
        object lons1,
        object lats1,
        object lons2,
        object lats2,
        bint radians=False,
    ):
        """
        inverse transformation - return forward and back azimuths, plus distance
        between an initial and terminus lat/lon pair.
        if radians=True, lons/lats are radians instead of degree
        """
        cdef PyBuffWriteManager lon1buff = PyBuffWriteManager(lons1)
        cdef PyBuffWriteManager lat1buff = PyBuffWriteManager(lats1)
        cdef PyBuffWriteManager lon2buff = PyBuffWriteManager(lons2)
        cdef PyBuffWriteManager lat2buff = PyBuffWriteManager(lats2)

        # process data in buffer
        if not lon1buff.len == lat1buff.len == lon2buff.len == lat2buff.len:
            raise GeodError("Array lengths are not the same.")

        cdef double lat1, lon1, lat2, lon2, pazi1, pazi2, ps12
        cdef Py_ssize_t iii
        with nogil:
            for iii in range(lon1buff.len):
                if radians:
                    lon1 = _RAD2DG * lon1buff.data[iii]
                    lat1 = _RAD2DG * lat1buff.data[iii]
                    lon2 = _RAD2DG * lon2buff.data[iii]
                    lat2 = _RAD2DG * lat2buff.data[iii]
                else:
                    lon1 = lon1buff.data[iii]
                    lat1 = lat1buff.data[iii]
                    lon2 = lon2buff.data[iii]
                    lat2 = lat2buff.data[iii]
                geod_inverse(
                    &self._geod_geodesic,
                    lat1, lon1, lat2, lon2,
                    &ps12, &pazi1, &pazi2,
                )
                # back azimuth needs to be flipped 180 degrees
                # to match what proj4 geod utility produces.
                if pazi2 > 0:
                    pazi2 = pazi2-180.
                elif pazi2 <= 0:
                    pazi2 = pazi2+180.
                if radians:
                    lon1buff.data[iii] = _DG2RAD * pazi1
                    lat1buff.data[iii] = _DG2RAD * pazi2
                else:
                    lon1buff.data[iii] = pazi1
                    lat1buff.data[iii] = pazi2
                # write azimuth data into lon2 buffer
                lon2buff.data[iii] = ps12

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _npts(
        self,
        double lon1,
        double lat1,
        double lon2,
        double lat2,
        int npts,
        bint radians=False,
    ):
        """
        given initial and terminus lat/lon, find npts intermediate points.
        """
        cdef Py_ssize_t iii
        cdef double del_s
        cdef double ps12
        cdef double pazi1
        cdef double pazi2
        cdef double s12
        cdef double plon2
        cdef double plat2
        cdef geod_geodesicline line

        if radians:
            lon1 = _RAD2DG * lon1
            lat1 = _RAD2DG * lat1
            lon2 = _RAD2DG * lon2
            lat2 = _RAD2DG * lat2
        # do inverse computation to set azimuths, distance.
        # in proj 4.9.3 and later the next two steps can be replace by a call
        # to geod_inverseline with del_s = line.s13/(npts+1)
        with nogil:
            geod_inverse(
                &self._geod_geodesic,
                lat1, lon1, lat2, lon2,
                &ps12, &pazi1, &pazi2,
            )
            geod_lineinit(&line, &self._geod_geodesic, lat1, lon1, pazi1, 0u)
        # distance increment.
        del_s = ps12 / (npts + 1)
        # initialize output tuples.
        lats = ()
        lons = ()
        # loop over intermediate points, compute lat/lons.
        for iii in range(1, npts + 1):
            s12 = iii * del_s
            geod_position(&line, s12, &plat2, &plon2, &pazi2);
            if radians:
                lats = lats + (_DG2RAD * plat2,)
                lons = lons + (_DG2RAD * plon2,)
            else:
                lats = lats + (plat2,)
                lons = lons + (plon2,)
        return lons, lats

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _line_length(self, object lons, object lats, bint radians=False):
        """
        Calculate the distance between points along a line.


        Parameters
        ----------
        lons: array
            The longitude points along a line.
        lats: array
            The latitude points along a line.
        radians: bool, optional
            If True, the input data is assumed to be in radians.

        Returns
        -------
        float:
            The total distance.

        """
        cdef PyBuffWriteManager lonbuff = PyBuffWriteManager(lons)
        cdef PyBuffWriteManager latbuff = PyBuffWriteManager(lats)

        # process data in buffer
        if lonbuff.len != latbuff.len:
            raise GeodError("Array lengths are not the same.")

        if lonbuff.len == 1:
            lonbuff.data[0] = 0
            return 0.0

        cdef double lat1, lon1, lat2, lon2, pazi1, pazi2, ps12
        cdef double total_distance = 0.0
        cdef Py_ssize_t iii
        with nogil:
            for iii in range(lonbuff.len - 1):
                if radians:
                    lon1 = _RAD2DG * lonbuff.data[iii]
                    lat1 = _RAD2DG * latbuff.data[iii]
                    lon2 = _RAD2DG * lonbuff.data[iii + 1]
                    lat2 = _RAD2DG * latbuff.data[iii + 1]
                else:
                    lon1 = lonbuff.data[iii]
                    lat1 = latbuff.data[iii]
                    lon2 = lonbuff.data[iii + 1]
                    lat2 = latbuff.data[iii + 1]
                geod_inverse(
                    &self._geod_geodesic,
                    lat1, lon1, lat2, lon2,
                    &ps12, &pazi1, &pazi2,
                )
                lonbuff.data[iii] = ps12
                total_distance += ps12
        return total_distance

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _polygon_area_perimeter(self, object lons, object lats, bint radians=False):
        """
        A simple interface for computing the area of a geodesic polygon.

        lats should be in the range [-90 deg, 90 deg].

        Only simple polygons (which are not self-intersecting) are allowed.
        There's no need to "close" the polygon by repeating the first vertex.
        The area returned is signed with counter-clockwise traversal being treated as
        positive.

        Parameters
        ----------
        lons: array
            An array of longitude values.
        lats: array
            An array of latitude values.
        radians: bool, optional
            If True, the input data is assumed to be in radians.

        Returns
        -------
        (float, float):
            The area (meter^2) and permimeter (meters) of the polygon.

        """
        cdef PyBuffWriteManager lonbuff = PyBuffWriteManager(lons)
        cdef PyBuffWriteManager latbuff = PyBuffWriteManager(lats)

        # process data in buffer
        if not lonbuff.len == latbuff.len:
            raise GeodError("Array lengths are not the same.")

        cdef double polygon_area
        cdef double polygon_perimeter
        cdef Py_ssize_t iii

        with nogil:
            if radians:
                for iii in range(lonbuff.len):
                    lonbuff.data[iii] *= _RAD2DG
                    latbuff.data[iii] *= _RAD2DG

            geod_polygonarea(
                &self._geod_geodesic,
                latbuff.data, lonbuff.data, lonbuff.len,
                &polygon_area, &polygon_perimeter
            )
        return (polygon_area, polygon_perimeter)

    def __repr__(self):
        return "{classname}({init!r})".format(
            classname=self.__class__.__name__,
            init=self.initstring,
        )
