include "base.pxi"

cimport cython
from cpython cimport array
from libc.math cimport ceil, isnan, round

import array
from collections import namedtuple

from pyproj.compat import cstrencode, pystrdecode
from pyproj.enums import GeodIntermediateFlag
from pyproj.exceptions import GeodError

geodesic_version_str = (
    f"{GEODESIC_VERSION_MAJOR}.{GEODESIC_VERSION_MINOR}.{GEODESIC_VERSION_PATCH}"
)

GeodIntermediateReturn = namedtuple(
    "GeodIntermediateReturn", ["npts", "del_s", "dist", "lons", "lats", "azis"]
)

GeodIntermediateReturn.__doc__ = """
.. versionadded:: 3.1.0

Geod Intermediate Return value (Named Tuple)

Parameters
----------

npts: int
    number of points
del_s: float
    delimiter distance between two successive points
dist: float
    distance between the initial and terminus points
out_lons: Any
    array of the output lons
out_lats: Any
    array of the output lats
out_azis: Any
    array of the output azis
"""


cdef int GEOD_INTER_FLAG_DEFAULT = GeodIntermediateFlag.DEFAULT

cdef int GEOD_INTER_FLAG_NPTS_MASK = GeodIntermediateFlag.NPTS_MASK
cdef int GEOD_INTER_FLAG_NPTS_ROUND = GeodIntermediateFlag.NPTS_ROUND
cdef int GEOD_INTER_FLAG_NPTS_CEIL = GeodIntermediateFlag.NPTS_CEIL
cdef int GEOD_INTER_FLAG_NPTS_TRUNC = GeodIntermediateFlag.NPTS_TRUNC

cdef int GEOD_INTER_FLAG_DEL_S_MASK = GeodIntermediateFlag.DEL_S_MASK
cdef int GEOD_INTER_FLAG_DEL_S_RECALC = GeodIntermediateFlag.DEL_S_RECALC
cdef int GEOD_INTER_FLAG_DEL_S_NO_RECALC = GeodIntermediateFlag.DEL_S_NO_RECALC

cdef int GEOD_INTER_FLAG_AZIS_MASK = GeodIntermediateFlag.AZIS_MASK
cdef int GEOD_INTER_FLAG_AZIS_DISCARD = GeodIntermediateFlag.AZIS_DISCARD
cdef int GEOD_INTER_FLAG_AZIS_KEEP = GeodIntermediateFlag.AZIS_KEEP


cdef class Geod:
    def __init__(self, double a, double f, bint sphere, double b, double es):
        geod_init(&self._geod_geodesic, <double> a, <double> f)
        self.a = a
        self.f = f
        # convert 'a' only for initstring
        a_str = int(a) if a.is_integer() else a
        f_str = int(f) if f.is_integer() else f
        self.initstring = pystrdecode(cstrencode(f"+a={a_str} +f={f_str}"))
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
    def _inv_or_fwd_intermediate(
        self,
        double lon1,
        double lat1,
        double lon2_or_azi1,
        double lat2_or_nan,
        int npts,
        double del_s,
        bint radians,
        int initial_idx,
        int terminus_idx,
        int flags,
        object out_lons,
        object out_lats,
        object out_azis,
    ) -> GeodIntermediateReturn:
        """
        .. versionadded:: 3.1.0

        given initial and terminus lat/lon, find npts intermediate points.
        using given lons, lats buffers
        """
        cdef Py_ssize_t iii
        cdef double pazi2
        cdef double s12
        cdef double plon2
        cdef double plat2
        cdef geod_geodesicline line

        cdef bint store_az = \
            out_azis is not None \
            or (flags & GEOD_INTER_FLAG_AZIS_MASK) == GEOD_INTER_FLAG_AZIS_KEEP

        cdef array.array array_template = array.array("d", [])
        cdef PyBuffWriteManager lons_buff
        cdef PyBuffWriteManager lats_buff
        cdef PyBuffWriteManager azis_buff

        cdef bint is_fwd = isnan(lat2_or_nan)

        if not is_fwd and (del_s == 0) == (npts == 0):
            raise GeodError("inv_intermediate: "
                            "npts and del_s are mutually exclusive, "
                            "only one of them must be != 0.")
        with nogil:
            if radians:
                lon1 *= _RAD2DG
                lat1 *= _RAD2DG
                lon2_or_azi1 *= _RAD2DG
                if not is_fwd:
                    lat2_or_nan *= _RAD2DG

            if is_fwd:
                # do fwd computation to set azimuths, distance.
                geod_lineinit(&line, &self._geod_geodesic, lat1, lon1, lon2_or_azi1, 0u)
                line.s13 = del_s * (npts + initial_idx + terminus_idx - 1)
            else:
                # do inverse computation to set azimuths, distance.
                geod_inverseline(&line, &self._geod_geodesic, lat1, lon1,
                                 lat2_or_nan, lon2_or_azi1, 0u)

                if npts == 0:
                    # calc the number of required points by the distance increment
                    # s12 holds a temporary float value of npts (just reusing this var)
                    s12 = line.s13 / del_s - initial_idx - terminus_idx + 1
                    if (flags & GEOD_INTER_FLAG_NPTS_MASK) == \
                            GEOD_INTER_FLAG_NPTS_ROUND:
                        s12 = round(s12)
                    elif (flags & GEOD_INTER_FLAG_NPTS_MASK) == \
                            GEOD_INTER_FLAG_NPTS_CEIL:
                        s12 = ceil(s12)
                    npts = int(s12)
                if (flags & GEOD_INTER_FLAG_DEL_S_MASK) == GEOD_INTER_FLAG_DEL_S_RECALC:
                    # calc the distance increment by the number of required points
                    del_s = line.s13 / (npts + initial_idx + terminus_idx - 1)

            with gil:
                if out_lons is None:
                    out_lons = array.clone(array_template, npts, zero=False)
                if out_lats is None:
                    out_lats = array.clone(array_template, npts, zero=False)
                if out_azis is None and store_az:
                    out_azis = array.clone(array_template, npts, zero=False)

                lons_buff = PyBuffWriteManager(out_lons)
                lats_buff = PyBuffWriteManager(out_lats)
                if store_az:
                    azis_buff = PyBuffWriteManager(out_azis)

                if lons_buff.len < npts \
                        or lats_buff.len < npts \
                        or (store_az and azis_buff.len < npts):
                    raise GeodError(
                        "Arrays are not long enough ("
                        f"{lons_buff.len}, {lats_buff.len}, "
                        f"{azis_buff.len if store_az else -1}) < {npts}.")

            # loop over intermediate points, compute lat/lons.
            for iii in range(0, npts):
                s12 = (iii + initial_idx) * del_s
                geod_position(&line, s12, &plat2, &plon2, &pazi2)
                if radians:
                    plat2 *= _DG2RAD
                    plon2 *= _DG2RAD
                lats_buff.data[iii] = plat2
                lons_buff.data[iii] = plon2
                if store_az:
                    azis_buff.data[iii] = pazi2

        return GeodIntermediateReturn(
            npts, del_s, line.s13, out_lons, out_lats, out_azis)

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
        return f"{self.__class__.__name__}({self.initstring!r})"
