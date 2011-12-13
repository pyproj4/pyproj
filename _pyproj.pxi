import math

_dg2rad = math.radians(1.)
_rad2dg = math.degrees(1.)
_doublesize = sizeof(double)
__version__ = "1.9.0"

cdef extern from "stdlib.h":
    ctypedef long size_t
    void *malloc(size_t size)
    void free(void *ptr)

cdef extern from "math.h":
    cdef enum:
        HUGE_VAL
        FP_NAN

cdef extern from "geodesic.h":
    ctypedef struct projUV:
        double u
        double v
    ctypedef struct GEODESIC_T:
        double A
        projUV p1, p2
        double ALPHA12
        double ALPHA21
        double DIST
        double ONEF, FLAT, FLAT2, FLAT4, FLAT64
        int ELLIPSE
        double FR_METER, TO_METER, del_alpha
        int n_alpha, n_S
        double th1,costh1,sinth1,sina12,cosa12,M,N,c1,c2,D,P,s1
        int merid, signS
    GEODESIC_T *GEOD_init_plus(char *args, GEODESIC_T *g)
    void geod_for(GEODESIC_T *g)
    void geod_pre(GEODESIC_T *g)
    int geod_inv(GEODESIC_T *g)

cdef extern from "proj_api.h":
    ctypedef double *projPJ
    projPJ pj_init_plus(char *)
    projUV pj_fwd(projUV, projPJ)
    projUV pj_inv(projUV, projPJ)
    int pj_transform(projPJ src, projPJ dst, long point_count, int point_offset,
                     double *x, double *y, double *z)
    int pj_is_latlong(projPJ)
    int pj_is_geocent(projPJ)
    char *pj_strerrno(int)
    void pj_free(projPJ)
    void pj_set_searchpath ( int count, char **path )
    cdef extern int pj_errno
    cdef enum:
        PJ_VERSION

#cdef extern from "pycompat.h":
#    ctypedef int Py_ssize_t

cdef extern from "Python.h":
    int PyObject_AsWriteBuffer(object, void **rbuf, Py_ssize_t *len)
