# WARNING: cartopy uses pyproj to import PROJ geodesic routines.
# Check what cartopy uses before removing any definitions.


cdef extern from "geodesic.h":
    struct geod_geodesic:
        pass
    struct geod_geodesicline:
        double lat1
        double lon1
        double azi1
        double a
        double f
        double salp1
        double calp1
        double a13
        double s13
        unsigned caps

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
        const geod_geodesic* g,
        double lat1,
        double lon1,
        double azi1,
        unsigned caps) nogil
    void geod_inverseline(
        geod_geodesicline* l,
        const geod_geodesic* g,
        double lat1,
        double lon1,
        double lat2,
        double lon2,
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

    # FOR CARTOPY ONLY
    cdef int GEOD_ARCMODE
    cdef int GEOD_LATITUDE
    cdef int GEOD_LONGITUDE

    double geod_geninverse(geod_geodesic*, double, double, double, double,
                           double*, double*, double*, double*, double*,
                           double*, double*) nogil
    void geod_genposition(geod_geodesicline*, int, double, double*,
                          double*, double*, double*, double*, double*,
                          double*, double*) nogil


cdef class Geod:
    cdef geod_geodesic _geod_geodesic
    cdef readonly object initstring
    cdef readonly double a
    cdef readonly double b
    cdef readonly double f
    cdef readonly double es
    cdef readonly bint sphere
