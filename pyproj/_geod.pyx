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
    def __init__(self, a, f, sphere, b, es):
        geod_init(&self._geod_geodesic, <double> a, <double> f)
        self.a = a
        self.f = f
        if isinstance(a, float) and a.is_integer():
            # convert 'a' only for initstring
            a = int(a)
        if f == 0.0:
            f = 0
        self.initstring = pystrdecode(cstrencode("+a=%s +f=%s" % (a, f)))
        self.sphere = sphere
        self.b = b
        self.es = es

    def __reduce__(self):
        """special method that allows pyproj.Geod instance to be pickled"""
        return self.__class__,(self.initstring,)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _fwd(self, object lons, object lats, object az, object dist, bint radians=False):
        """
        forward transformation - determine longitude, latitude and back azimuth
        of a terminus point given an initial point longitude and latitude, plus
        forward azimuth and distance.
        if radians=True, lons/lats are radians instead of degrees.
        """
        cdef Py_ssize_t buflenlons, buflenlats, buflenaz, buflend, ndim, iii
        cdef double lat1,lon1,az1,s12,plon2,plat2,pazi2
        cdef double *lonsdata
        cdef double *latsdata
        cdef double *azdata
        cdef double *distdata
        cdef void *londata
        cdef void *latdata
        cdef void *azdat
        cdef void *distdat
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenlons) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(lats, &latdata, &buflenlats) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(az, &azdat, &buflenaz) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(dist, &distdat, &buflend) <> 0:
            raise GeodError
        # process data in buffer
        if not buflenlons == buflenlats == buflenaz == buflend:
            raise GeodError("Buffer lengths not the same")
        ndim = buflenlons//_DOUBLESIZE
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        azdata = <double *>azdat
        distdata = <double *>distdat
        with nogil:
            for iii in range(ndim):
                if not radians:
                    lon1 = lonsdata[iii]
                    lat1 = latsdata[iii]
                    az1 = azdata[iii]
                    s12 = distdata[iii]
                else:
                    lon1 = _RAD2DG * lonsdata[iii]
                    lat1 = _RAD2DG * latsdata[iii]
                    az1 = _RAD2DG * azdata[iii]
                    s12 = distdata[iii]
                geod_direct(&self._geod_geodesic, lat1, lon1, az1, s12,\
                    &plat2, &plon2, &pazi2)
                # back azimuth needs to be flipped 180 degrees
                # to match what proj4 geod utility produces.
                if pazi2 > 0:
                    pazi2 = pazi2 - 180.
                elif pazi2 <= 0:
                    pazi2 = pazi2 + 180.
                if not radians:
                    lonsdata[iii] = plon2
                    latsdata[iii] = plat2
                    azdata[iii] = pazi2
                else:
                    lonsdata[iii] = _DG2RAD * plon2
                    latsdata[iii] = _DG2RAD * plat2
                    azdata[iii] = _DG2RAD * pazi2

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _inv(self, object lons1, object lats1, object lons2, object lats2, bint radians=False):
        """
        inverse transformation - return forward and back azimuths, plus distance
        between an initial and terminus lat/lon pair.
        if radians=True, lons/lats are radians instead of degree
        """
        cdef double lat1,lon1,lat2,lon2,pazi1,pazi2,ps12
        cdef Py_ssize_t buflenlons, buflenlats, buflenaz, buflend, ndim, iii
        cdef double *lonsdata
        cdef double *latsdata
        cdef double *azdata
        cdef double *distdata
        cdef void *londata
        cdef void *latdata
        cdef void *azdat
        cdef void *distdat
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons1, &londata, &buflenlons) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(lats1, &latdata, &buflenlats) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(lons2, &azdat, &buflenaz) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(lats2, &distdat, &buflend) <> 0:
            raise GeodError
        # process data in buffer
        if not buflenlons == buflenlats == buflenaz == buflend:
            raise GeodError("Buffer lengths not the same")
        ndim = buflenlons//_DOUBLESIZE
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        azdata = <double *>azdat
        distdata = <double *>distdat
        with nogil:
            for iii in range(ndim):
                if radians:
                    lon1 = _RAD2DG * lonsdata[iii]
                    lat1 = _RAD2DG * latsdata[iii]
                    lon2 = _RAD2DG * azdata[iii]
                    lat2 = _RAD2DG * distdata[iii]
                else:
                    lon1 = lonsdata[iii]
                    lat1 = latsdata[iii]
                    lon2 = azdata[iii]
                    lat2 = distdata[iii]
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
                    lonsdata[iii] = _DG2RAD * pazi1
                    latsdata[iii] = _DG2RAD * pazi2
                else:
                    lonsdata[iii] = pazi1
                    latsdata[iii] = pazi2
                azdata[iii] = ps12

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _npts(self, double lon1, double lat1, double lon2, double lat2, int npts, bint radians=False):
        """
        given initial and terminus lat/lon, find npts intermediate points.
        """
        cdef Py_ssize_t iii
        cdef double del_s,ps12,pazi1,pazi2,s12,plon2,plat2
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
        float: The total distance.
    
        """
        cdef double lat1,lon1,lat2,lon2,pazi1,pazi2,ps12
        cdef double total_distance = 0.0
        cdef Py_ssize_t buflenlons, buflenlats, ndim, iii
        cdef double *lonsdata
        cdef double *latsdata
        cdef void *londata
        cdef void *latdata
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenlons) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(lats, &latdata, &buflenlats) <> 0:
            raise GeodError
        # process data in buffer
        if buflenlons != buflenlats:
            raise GeodError("Buffer lengths not the same")
        ndim = buflenlons//_DOUBLESIZE
        lonsdata = <double *>londata
        latsdata = <double *>latdata

        if ndim == 1:
            lonsdata[0] = 0
            return 0.0
        with nogil:
            for iii in range(ndim - 1):
                if radians:
                    lon1 = _RAD2DG * lonsdata[iii]
                    lat1 = _RAD2DG * latsdata[iii]
                    lon2 = _RAD2DG * lonsdata[iii + 1]
                    lat2 = _RAD2DG * latsdata[iii + 1]
                else:
                    lon1 = lonsdata[iii]
                    lat1 = latsdata[iii]
                    lon2 = lonsdata[iii + 1]
                    lat2 = latsdata[iii + 1]
                geod_inverse(
                    &self._geod_geodesic,
                    lat1, lon1, lat2, lon2,
                    &ps12, &pazi1, &pazi2,
                )
                lonsdata[iii] = ps12
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
        (float, float): The area (meter^2) and permimeter (meters) of the polygon.

        """
        cdef Py_ssize_t buflenlons, buflenlats, ndim, iii
        cdef void *londata
        cdef void *latdata
        cdef double *lonsdata
        cdef double *latsdata
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenlons) <> 0:
            raise GeodError
        if PyObject_AsWriteBuffer(lats, &latdata, &buflenlats) <> 0:
            raise GeodError
        # process data in buffer
        if not buflenlons == buflenlats:
            raise GeodError("Buffer lengths not the same")

        cdef double polygon_area
        cdef double polygon_perimeter
        ndim = buflenlons//_DOUBLESIZE

        lonsdata = <double *>londata
        latsdata = <double *>latdata
        with nogil:
            if radians:
                for iii in range(ndim):
                    lonsdata[iii] *= _RAD2DG
                    latsdata[iii] *= _RAD2DG

            geod_polygonarea(
                &self._geod_geodesic,
                latsdata, lonsdata, ndim, 
                &polygon_area, &polygon_perimeter
            )
        return (polygon_area, polygon_perimeter)


    def __repr__(self):
        return "{classname}({init!r})".format(
            classname=self.__class__.__name__,
            init=self.initstring,
        )
