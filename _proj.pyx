#cimport c_numpy
#c_numpy.import_array()

import math

cdef double _dg2rad, _rad2dg 

_dg2rad = math.radians(1.)
_rad2dg = math.degrees(1.)
_doublesize = sizeof(double)
__version__ = "1.9.4"

cdef extern from "math.h":
    cdef enum:
        HUGE_VAL
        FP_NAN

cdef extern from "geodesic.h":
  struct geod_geodesic:
        pass
  void geod_init(geod_geodesic* g, double a, double f)
  void geod_direct(geod_geodesic* g,\
              double lat1, double lon1, double azi1, double s12,\
              double* plat2, double* plon2, double* pazi2)
  void geod_inverse(geod_geodesic* g,\
               double lat1, double lon1, double lat2, double lon2,\
               double* ps12, double* pazi1, double* pazi2)

cdef extern from "proj_api.h":
    ctypedef struct projUV:
        double u
        double v
    ctypedef void *projPJ
    ctypedef void *projCtx
    projPJ pj_init_plus(char *)
    projPJ pj_init_plus_ctx(projCtx, char *)
    projUV pj_fwd(projUV, projPJ)
    projUV pj_inv(projUV, projPJ)
    projPJ pj_latlong_from_proj(projPJ) 
    int pj_transform(projPJ src, projPJ dst, long point_count, int point_offset,
                     double *x, double *y, double *z)
    int pj_is_latlong(projPJ)
    char *pj_get_def( projPJ pj, int options)
    int pj_is_geocent(projPJ)
    char *pj_strerrno(int)
    void pj_ctx_free( projCtx )
    int pj_ctx_get_errno( projCtx )
    projCtx pj_ctx_alloc()
    projCtx pj_get_default_ctx()
    void pj_free(projPJ)
    void pj_set_searchpath ( int count, char **path )
    cdef enum:
        PJ_VERSION

cdef extern from "Python.h":
    int PyObject_AsWriteBuffer(object, void **rbuf, Py_ssize_t *len)

def set_datapath(datapath):
    cdef char *searchpath
    bytestr = _strencode(datapath)
    searchpath = bytestr
    pj_set_searchpath(1, &searchpath)

def _createproj(projstring):
    return Proj(projstring)

cdef class Proj:
    cdef projPJ projpj
    cdef projCtx projctx
    cdef public object proj_version
    cdef char *pjinitstring
    cdef public object srs

    def __cinit__(self, projstring):
        # setup proj initialization string.
        cdef int err
        self.srs = projstring
        bytestr = _strencode(projstring)
        self.pjinitstring = bytestr
        # initialize projection
        self.projctx = pj_ctx_alloc()
        self.projpj = pj_init_plus_ctx(self.projctx, self.pjinitstring)
        err = pj_ctx_get_errno(self.projctx)
        if err != 0:
             raise RuntimeError(pj_strerrno(err))
        self.proj_version = PJ_VERSION/100.

    def __dealloc__(self):
        """destroy projection definition"""
        pj_free(self.projpj)
        pj_ctx_free(self.projctx)

    def to_latlong(self):
        """return a new Proj instance which is the geographic (lat/lon)
        coordinate version of the current projection"""
        cdef projPJ llpj
        llpj = pj_latlong_from_proj(self.projpj)
        initstring = pj_get_def(llpj, 0)
        pj_free(llpj)
        return _createproj(initstring)

    def __reduce__(self):
        """special method that allows pyproj.Proj instance to be pickled"""
        return (self.__class__,(self.srs,))

    def _fwd(self, object lons, object lats, radians=False, errcheck=False):
        """
 forward transformation - lons,lats to x,y (done in place).
 if radians=True, lons/lats are radians instead of degrees.
 if errcheck=True, an exception is raised if the forward transformation is invalid.
 if errcheck=False and the forward transformation is invalid, no exception is
 raised and 1.e30 is returned.
        """
        cdef projUV projxyout, projlonlatin
        cdef Py_ssize_t buflenx, bufleny, ndim, i
        cdef double u, v
        cdef double *lonsdata, *latsdata
        cdef void *londata, *latdata
        cdef int err
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenx) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats, &latdata, &bufleny) <> 0:
            raise RuntimeError
        # process data in buffer
        if buflenx != bufleny:
            raise RuntimeError("Buffer lengths not the same")
        ndim = buflenx//_doublesize
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        for i from 0 <= i < ndim:
            # if inputs are nan's, return big number.
            if lonsdata[i] != lonsdata[i] or latsdata[i] != latsdata[i]:
                lonsdata[i]=1.e30; latsdata[i]=1.e30
                if errcheck:
                    raise RuntimeError('projection undefined')
                continue
            if radians:
                projlonlatin.u = lonsdata[i]
                projlonlatin.v = latsdata[i]
            else:
                projlonlatin.u = _dg2rad*lonsdata[i]
                projlonlatin.v = _dg2rad*latsdata[i]
            projxyout = pj_fwd(projlonlatin,self.projpj)
            if errcheck:
                err = pj_ctx_get_errno(self.projctx)
                if err != 0:
                     raise RuntimeError(pj_strerrno(err))
            # since HUGE_VAL can be 'inf',
            # change it to a real (but very large) number.
            # also check for NaNs.
            if projxyout.u == HUGE_VAL or\
               projxyout.u != projxyout.u:
                if errcheck:
                    raise RuntimeError('projection undefined')
                lonsdata[i] = 1.e30
            else:
                lonsdata[i] = projxyout.u
            if projxyout.v == HUGE_VAL or\
               projxyout.u != projxyout.u:
                if errcheck:
                    raise RuntimeError('projection undefined')
                latsdata[i] = 1.e30
            else:     
                latsdata[i] = projxyout.v

    def _inv(self, object x, object y, radians=False, errcheck=False):
        """
 inverse transformation - x,y to lons,lats (done in place).
 if radians=True, lons/lats are radians instead of degrees.
 if errcheck=True, an exception is raised if the inverse transformation is invalid.
 if errcheck=False and the inverse transformation is invalid, no exception is
 raised and 1.e30 is returned.
        """
        cdef projUV projxyin, projlonlatout
        cdef Py_ssize_t buflenx, bufleny, ndim, i
        cdef double u, v
        cdef void *xdata, *ydata
        cdef double *xdatab, *ydatab
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(x, &xdata, &buflenx) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(y, &ydata, &bufleny) <> 0:
            raise RuntimeError
        # process data in buffer 
        # (for numpy/regular python arrays).
        if buflenx != bufleny:
            raise RuntimeError("Buffer lengths not the same")
        ndim = buflenx//_doublesize
        xdatab = <double *>xdata
        ydatab = <double *>ydata
        for i from 0 <= i < ndim:
            # if inputs are nan's, return big number.
            if xdatab[i] != xdatab[i] or ydatab[i] != ydatab[i]:
                xdatab[i]=1.e30; ydatab[i]=1.e30
                if errcheck:
                    raise RuntimeError('projection undefined')
                continue
            projxyin.u = xdatab[i]
            projxyin.v = ydatab[i]
            projlonlatout = pj_inv(projxyin,self.projpj)
            if errcheck:
                err = pj_ctx_get_errno(self.projctx)
                if err != 0:
                     raise RuntimeError(pj_strerrno(err))
            # since HUGE_VAL can be 'inf',
            # change it to a real (but very large) number.
            # also check for NaNs.
            if projlonlatout.u == HUGE_VAL or \
               projlonlatout.u != projlonlatout.u:
                if errcheck:
                    raise RuntimeError('projection undefined')
                xdatab[i] = 1.e30
            elif radians:
                xdatab[i] = projlonlatout.u
            else:
                xdatab[i] = _rad2dg*projlonlatout.u
            if projlonlatout.v == HUGE_VAL or \
               projlonlatout.v != projlonlatout.v:
                if errcheck:
                    raise RuntimeError('projection undefined')
                ydatab[i] = 1.e30
            elif radians:
                ydatab[i] = projlonlatout.v
            else:
                ydatab[i] = _rad2dg*projlonlatout.v

#   def _fwdn(self, c_numpy.ndarray lonlat, radians=False, errcheck=False):
#       """
#forward transformation - lons,lats to x,y (done in place).
#Uses ndarray of shape ...,2.
#if radians=True, lons/lats are radians instead of degrees.
#if errcheck=True, an exception is raised if the forward
#                transformation is invalid.
#if errcheck=False and the forward transformation is
#                invalid, no exception is
#                raised and 1.e30 is returned.
#       """
#       cdef projUV projxyout, projlonlatin
#       cdef projUV *llptr
#       cdef int err
#       cdef Py_ssize_t npts, i
#       npts = c_numpy.PyArray_SIZE(lonlat)//2
#       llptr = <projUV *>lonlat.data
#       for i from 0 <= i < npts:
#           if radians:
#               projlonlatin = llptr[i]
#           else:
#               projlonlatin.u = _dg2rad*llptr[i].u
#               projlonlatin.v = _dg2rad*llptr[i].v
#           projxyout = pj_fwd(projlonlatin,self.projpj)

#           if errcheck:
#               err = pj_ctx_get_errno(self.projctx)
#               if err != 0:
#                    raise RuntimeError(pj_strerrno(err))
#           # since HUGE_VAL can be 'inf',
#           # change it to a real (but very large) number.
#           if projxyout.u == HUGE_VAL:
#               llptr[i].u = 1.e30
#           else:
#               llptr[i].u = projxyout.u
#           if projxyout.v == HUGE_VAL:
#               llptr[i].u = 1.e30
#           else:
#               llptr[i].v = projxyout.v

#   def _invn(self, c_numpy.ndarray xy, radians=False, errcheck=False):
#       """
#inverse transformation - x,y to lons,lats (done in place).
#Uses ndarray of shape ...,2.
#if radians=True, lons/lats are radians instead of degrees.
#if errcheck=True, an exception is raised if the inverse transformation is invalid.
#if errcheck=False and the inverse transformation is invalid, no exception is
#raised and 1.e30 is returned.
#       """
#       cdef projUV projxyin, projlonlatout
#       cdef projUV *llptr
#       cdef Py_ssize_t npts, i
#       npts = c_numpy.PyArray_SIZE(xy)//2
#       llptr = <projUV *>xy.data

#       for i from 0 <= i < npts:
#           projxyin = llptr[i]
#           projlonlatout = pj_inv(projxyin, self.projpj)
#           if errcheck:
#               err = pj_ctx_get_errno(self.projctx)
#               if err != 0:
#                    raise RuntimeError(pj_strerrno(err))
#           # since HUGE_VAL can be 'inf',
#           # change it to a real (but very large) number.
#           if projlonlatout.u == HUGE_VAL:
#               llptr[i].u = 1.e30
#           elif radians:
#               llptr[i].u = projlonlatout.u
#           else:
#               llptr[i].u = _rad2dg*projlonlatout.u
#           if projlonlatout.v == HUGE_VAL:
#               llptr[i].v = 1.e30
#           elif radians:
#               llptr[i].v = projlonlatout.v
#           else:
#               llptr[i].v = _rad2dg*projlonlatout.v

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

def _transform(Proj p1, Proj p2, inx, iny, inz, radians):
    # private function to call pj_transform
    cdef void *xdata, *ydata, *zdata
    cdef double *xx, *yy, *zz
    cdef Py_ssize_t buflenx, bufleny, buflenz, npts, i
    cdef int err
    if PyObject_AsWriteBuffer(inx, &xdata, &buflenx) <> 0:
        raise RuntimeError
    if PyObject_AsWriteBuffer(iny, &ydata, &bufleny) <> 0:
        raise RuntimeError
    if inz is not None:
        if PyObject_AsWriteBuffer(inz, &zdata, &buflenz) <> 0:
            raise RuntimeError
    else:
        buflenz = bufleny
    if not (buflenx == bufleny == buflenz):
        raise RuntimeError('x,y and z must be same size')
    xx = <double *>xdata
    yy = <double *>ydata
    if inz is not None:
        zz = <double *>zdata
    npts = buflenx/8
    if not radians and p1.is_latlong():
        for i from 0 <= i < npts:
            xx[i] = xx[i]*_dg2rad
            yy[i] = yy[i]*_dg2rad
    if inz is not None:
        err = pj_transform(p1.projpj, p2.projpj, npts, 0, xx, yy, zz)
    else:
        err = pj_transform(p1.projpj, p2.projpj, npts, 0, xx, yy, NULL)
    if err != 0:
        raise RuntimeError(pj_strerrno(err))
    if not radians and p2.is_latlong():
        for i from 0 <= i < npts:
            xx[i] = xx[i]*_rad2dg
            yy[i] = yy[i]*_rad2dg

cdef _strencode(pystr,encoding='ascii'):
    # encode a string into bytes.  If already bytes, do nothing.
    try:
        return pystr.encode(encoding)
    except AttributeError:
        return pystr # already bytes?

cdef class Geod:
    cdef geod_geodesic _geod_geodesic
    cdef public object initstring

    def __cinit__(self, a, f):
        self.initstring = '+a=%s +f=%s' % (a, f)
        geod_init(&self._geod_geodesic, <double> a, <double> f)

    def __reduce__(self):
        """special method that allows pyproj.Geod instance to be pickled"""
        return (self.__class__,(self.initstring,))

    def _fwd(self, object lons, object lats, object az, object dist, radians=False):
        """
 forward transformation - determine longitude, latitude and back azimuth 
 of a terminus point given an initial point longitude and latitude, plus
 forward azimuth and distance.
 if radians=True, lons/lats are radians instead of degrees.
        """
        cdef Py_ssize_t buflenlons, buflenlats, buflenaz, buflend, ndim, i
        cdef double lat1,lon1,az1,s12,plon2,plat2,pazi2
        cdef double *lonsdata, *latsdata, *azdata, *distdata
        cdef void *londata, *latdata, *azdat, *distdat
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenlons) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats, &latdata, &buflenlats) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(az, &azdat, &buflenaz) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(dist, &distdat, &buflend) <> 0:
            raise RuntimeError
        # process data in buffer
        if not buflenlons == buflenlats == buflenaz == buflend:
            raise RuntimeError("Buffer lengths not the same")
        ndim = buflenlons//_doublesize
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        azdata = <double *>azdat
        distdata = <double *>distdat
        for i from 0 <= i < ndim:
            if not radians:
                lon1 = lonsdata[i]
                lat1 = latsdata[i]
                az1 = azdata[i]
                s12 = distdata[i]
            else:
                lon1 = _dg2rad*lonsdata[i]
                lat1 = _dg2rad*latsdata[i]
                az1 = _dg2rad*azdata[i]
                s12 = distdata[i]
            geod_direct(&self._geod_geodesic, lat1, lon1, az1, s12,\
                   &plat2, &plon2, &pazi2)
            # back azimuth needs to be flipped 180 degrees
            # to match what proj4 geod utility produces.
            if pazi2 > 0:
                pazi2 = pazi2-180.
            elif pazi2 <= 0:
                pazi2 = pazi2+180.
            # check for NaN.
            if pazi2 != pazi2:
                raise ValueError('undefined inverse geodesic (may be an antipodal point)')
            if not radians:
                lonsdata[i] = plon2
                latsdata[i] = plat2
                azdata[i] = pazi2
            else:
                lonsdata[i] = _rad2dg*plon2
                latsdata[i] = _rad2dg*plat2
                azdata[i] = _rad2dg*pazi2

    def _inv(self, object lons1, object lats1, object lons2, object lats2, radians=False):
        """
 inverse transformation - return forward and back azimuths, plus distance
 between an initial and terminus lat/lon pair.
 if radians=True, lons/lats are radians instead of degrees.
        """
        cdef double lat1,lon1,lat2,lon2,pazi1,pazi2,ps12
        cdef Py_ssize_t buflenlons, buflenlats, buflenaz, buflend, ndim, i
        cdef double *lonsdata, *latsdata, *azdata, *distdata
        cdef void *londata, *latdata, *azdat, *distdat
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons1, &londata, &buflenlons) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats1, &latdata, &buflenlats) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lons2, &azdat, &buflenaz) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats2, &distdat, &buflend) <> 0:
            raise RuntimeError
        # process data in buffer
        if not buflenlons == buflenlats == buflenaz == buflend:
            raise RuntimeError("Buffer lengths not the same")
        ndim = buflenlons//_doublesize
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        azdata = <double *>azdat
        distdata = <double *>distdat
        errmsg = 'undefined inverse geodesic (may be an antipodal point)'
        for i from 0 <= i < ndim:
            if radians:
                lon1 = _rad2dg*lonsdata[i]
                lat1 = _rad2dg*latsdata[i]
                lon2 = _rad2dg*azdata[i]
                lat2 = _rad2dg*distdata[i]
            else:
                lon1 = lonsdata[i]
                lat1 = latsdata[i]
                lon2 = azdata[i]
                lat2 = distdata[i]
            geod_inverse(&self._geod_geodesic, lat1, lon1, lat2, lon2,
                    &ps12, &pazi1, &pazi2)
            # back azimuth needs to be flipped 180 degrees
            # to match what proj4 geod utility produces.
            if pazi2 > 0:
                pazi2 = pazi2-180.
            elif pazi2 <= 0:
                pazi2 = pazi2+180.
            if ps12 != ps12: # check for NaN
                raise ValueError('undefined inverse geodesic (may be an antipodal point)')
            if radians:
                lonsdata[i] = _rad2dg*pazi1
                latsdata[i] = _rad2dg*pazi2
            else:
                lonsdata[i] = pazi1
                latsdata[i] = pazi2
            azdata[i] = ps12

    def _npts(self, double lon1, double lat1, double lon2, double lat2, int npts, radians=False):
        """
 given initial and terminus lat/lon, find npts intermediate points."""
        cdef int i
        cdef double del_s,ps12,pazi1,pazi2,s12,plon2,plat2
        if radians:
            lon1 = _rad2dg*lon1
            lat1 = _rad2dg*lat1
            lon2 = _rad2dg*lon2
            lat2 = _rad2dg*lat2
        # do inverse computation to set azimuths, distance.
        geod_inverse(&self._geod_geodesic, lat1, lon1,  lat2, lon2,
                &ps12, &pazi1, &pazi2)
        # distance increment.
        del_s = ps12/(npts+1)
        # initialize output tuples.
        lats = ()
        lons = ()
        # loop over intermediate points, compute lat/lons.
        for i from 1 <= i < npts+1:
            s12 = i*del_s
            geod_direct(&self._geod_geodesic, lat1, lon1, pazi1, s12,\
                   &plat2, &plon2, &pazi2)
            if radians:
                lats = lats + (_dg2rad*plat2,)
                lons = lons + (_dg2rad*plon2,)
            else:
                lats = lats + (plat2,)
                lons = lons + (plon2,)
        return lons, lats
