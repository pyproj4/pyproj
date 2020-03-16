cdef extern from "geodesic.h":
    struct geod_geodesic:
        pass
    struct geod_geodesicline:
        pass
    void geod_init(geod_geodesic* g, double a, double f)
    void geod_direct(
        geod_geodesic* g,
        double lat1,
        double lon1,
        double azi1,
        double s12,
        double* plat2,
        double* plon2,
        double* pazi2) nogil
    void geod_inverse(
        geod_geodesic* g,
        double lat1,
        double lon1,
        double lat2,
        double lon2,
        double* ps12,
        double* pazi1,
        double* pazi2) nogil
    void geod_lineinit(
        geod_geodesicline* l,
        geod_geodesic* g,
        double lat1,
        double lon1,
        double azi1,
        unsigned caps) nogil
    void geod_position(
        geod_geodesicline* l,
        double s12,
        double* plat2,
        double* plon2,
        double* pazi2) nogil
    void geod_polygonarea(
        geod_geodesic* g,
        double lats[],
        double lons[],
        int n,
        double* pA,
        double* pP) nogil

    cdef enum:
        GEODESIC_VERSION_MAJOR
        GEODESIC_VERSION_MINOR
        GEODESIC_VERSION_PATCH


cdef class Geod:
    cdef geod_geodesic _geod_geodesic
    cdef readonly object initstring
    cdef readonly double a
    cdef readonly double b
    cdef readonly double f
    cdef readonly double es
    cdef readonly bint sphere
