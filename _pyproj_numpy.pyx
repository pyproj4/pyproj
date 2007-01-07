# Make changes to this file, not the c-wrappers that Pyrex generates.

import math
import numpy
import_array()

cdef double _dg2rad, _rad2dg
_dg2rad = math.radians(1.)
_rad2dg = math.degrees(1.)
__version__ = "1.8.1"

cdef extern from "numpy/arrayobject.h":
    ctypedef extern class numpy.ndarray [object PyArrayObject]:
        cdef char *data
    void import_array()

cdef extern from "proj_api.h":
    ctypedef double *projPJ
    ctypedef struct projUV:
        double u
        double v
    projPJ pj_init_plus(char *)
    projUV pj_fwd(projUV, projPJ)
    projUV pj_inv(projUV, projPJ)
    int pj_transform(projPJ src, projPJ dst, long point_count, int point_offset,
                  double *x, double *y, double *z)
    int pj_is_latlong(projPJ)
    int pj_is_geocent(projPJ)
    char *pj_strerrno(int)
    void pj_free(projPJ)
    cdef extern int pj_errno
    cdef enum:
        PJ_VERSION

cdef extern from "Python.h":
    char *PyString_AsString(object)

cdef class Proj:
    cdef projPJ projpj
    cdef public object projparams
    cdef public object proj_version
    cdef char *pjinitstring

    def __new__(self, projparams):
        self.projparams = projparams
        # setup proj initialization string.
        pjargs = []
        for key,value in projparams.iteritems():
            pjargs.append('+'+key+"="+str(value)+' ')
        self.pjinitstring = PyString_AsString(''.join(pjargs))
        # initialize projection
        self.projpj = pj_init_plus(self.pjinitstring)
        if pj_errno != 0:
            raise RuntimeError(pj_strerrno(pj_errno))
        self.proj_version = PJ_VERSION/100.

    def __dealloc__(self):
        """destroy projection definition"""
        pj_free(self.projpj)

    def __reduce__(self):
        """special method that allows Proj instance to be pickled"""
        return (self.__class__,(self.projparams,))

    def _fwd(self, ndarray lons, ndarray lats, radians=False, errcheck=False):
        """
 forward transformation - lons,lats to x,y (done in place).
 if radians=True, lons/lats are radians instead of degrees.
 if errcheck=True, an exception is raised if the forward transformation is invalid.
 if errcheck=False and the forward transformation is invalid, no exception is
 raised and the platform dependent value HUGE_VAL is returned.
        """
        cdef projUV projxyout, projlonlatin
        cdef int i
        cdef Py_ssize_t npts
        cdef double u, v
        cdef double *lonsdata, *latsdata, *xdata, *ydata
        cdef ndarray x,y
        # make sure data is contiguous.
        # if not, make a local copy.
        if not lons.flags['C_CONTIGUOUS']:
            lons = lons.copy()
        if not lats.flags['C_CONTIGUOUS']:
            lats = lats.copy()
        npts = lons.size
        lonsdata = <double *>lons.data
        latsdata = <double *>lats.data
        x = numpy.empty(lons.shape,numpy.float64)
        y = numpy.empty(lats.shape,numpy.float64)
        xdata = <double *>x.data
        ydata = <double *>y.data
        for i from 0 <= i < npts:
            if radians:
                projlonlatin.u = lonsdata[i]
                projlonlatin.v = latsdata[i]
            else:
                projlonlatin.u = _dg2rad*lonsdata[i]
                projlonlatin.v = _dg2rad*latsdata[i]
            projxyout = pj_fwd(projlonlatin,self.projpj)
            if errcheck and pj_errno != 0:
                raise RuntimeError(pj_strerrno(pj_errno))
            xdata[i] = projxyout.u
            ydata[i] = projxyout.v
        return x,y

    def _inv(self, ndarray x, ndarray y, radians=False, errcheck=False):
        """
 inverse transformation - x,y to lons,lats (done in place).
 if radians=True, lons/lats are radians instead of degrees.
 if errcheck=True, an exception is raised if the inverse transformation is invalid.
 if errcheck=False and the inverse transformation is invalid, no exception is
 raised and the platform dependent value HUGE_VAL is returned.
        """
        cdef projUV projxyin, projlonlatout
        cdef int i
        cdef Py_ssize_t npts
        cdef double u, v
        cdef double *xdata, *ydata, *lonsdata, *latsdata
        cdef ndarray lons, lats
        # make sure data is contiguous.
        # if not, make a local copy.
        if not x.flags['C_CONTIGUOUS']:
            x = x.copy()
        if not y.flags['C_CONTIGUOUS']:
            y = y.copy()
        npts = x.size
        xdata = <double *>x.data
        ydata = <double *>y.data
        lons = numpy.empty(x.shape,numpy.float64)
        lats = numpy.empty(y.shape,numpy.float64)
        lonsdata = <double *>lons.data
        latsdata = <double *>lats.data
        for i from 0 <= i < npts:
            projxyin.u = xdata[i]
            projxyin.v = ydata[i]
            projlonlatout = pj_inv(projxyin,self.projpj)
            if errcheck and pj_errno != 0:
                raise RuntimeError(pj_strerrno(pj_errno))
            if radians:
                lonsdata[i] = projlonlatout.u
                latsdata[i] = projlonlatout.v
            else:
                lonsdata[i] = _rad2dg*projlonlatout.u
                latsdata[i] = _rad2dg*projlonlatout.v
        return lons, lats

    def is_latlong(self):
        # returns True if projection in geographic (lon/lat) coordinates
        cdef int i
        i = pj_is_latlong(self.projpj)
        if i:
            return True
        else:
            return False

    def is_geocent(self):
        # returns True if projection in geocentric (x/y) coordinates
        cdef int i
        i = pj_is_geocent(self.projpj)
        if i:
            return True
        else:
            return False

def _transform(Proj p1, Proj p2, ndarray inx, ndarray iny, ndarray inz, radians):
    # private function to call pj_transform
    cdef double *xx, *yy, *zz
    cdef int i
    cdef Py_ssize_t npts
    npts = inx.size
    xx = <double *>inx.data
    yy = <double *>iny.data
    if inz.dtype != numpy.dtype('bool'):
        zz = <double *>inz.data
    if not radians and p1.is_latlong():
        for i from 0 <= i < npts:
            xx[i] = xx[i]*_dg2rad
            yy[i] = yy[i]*_dg2rad
    if inz.dtype != numpy.dtype('bool'):
        ierr = pj_transform(p1.projpj, p2.projpj, npts, 0, xx, yy, zz)
    else:
        ierr = pj_transform(p1.projpj, p2.projpj, npts, 0, xx, yy, NULL)
    if ierr != 0:
        raise RuntimeError(pj_strerrno(ierr))
    if not radians and p2.is_latlong():
        for i from 0 <= i < npts:
            xx[i] = xx[i]*_rad2dg
            yy[i] = yy[i]*_rad2dg
