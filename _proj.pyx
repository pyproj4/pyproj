# Make changes to this file, not the c-wrappers that Pyrex generates.

include "_pyproj.pxi"
#cimport c_numpy
#c_numpy.import_array()

def set_datapath(datapath):
    cdef char *searchpath
    bytestr = _strencode(datapath)
    searchparth = bytestr
    pj_set_searchpath(1, &searchpath)
    
cdef class Proj:
    cdef projPJ projpj
    cdef public object proj_version
    cdef char *pjinitstring
    cdef public object srs

    def __cinit__(self, projstring):
        # setup proj initialization string.
        self.srs = projstring
        bytestr = _strencode(projstring)
        self.pjinitstring = bytestr
        # initialize projection
        self.projpj = pj_init_plus(self.pjinitstring)
        if pj_errno != 0:
            raise RuntimeError(pj_strerrno(pj_errno))
        self.proj_version = PJ_VERSION/100.

    def __dealloc__(self):
        """destroy projection definition"""
        pj_free(self.projpj)

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
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenx) <> 0:
            raise RuntimeError
        if PyObject_AsWriteBuffer(lats, &latdata, &bufleny) <> 0:
            raise RuntimeError
        # process data in buffer
        if buflenx != bufleny:
            raise RuntimeError("Buffer lengths not the same")
        ndim = buflenx/_doublesize
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
            if errcheck and pj_errno != 0:
                raise RuntimeError(pj_strerrno(pj_errno))
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
        ndim = buflenx/_doublesize
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
            if errcheck and pj_errno != 0:
                raise RuntimeError(pj_strerrno(pj_errno))
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

#           if errcheck and pj_errno != 0:
#               raise RuntimeError(pj_strerrno(pj_errno))
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
#           if errcheck and pj_errno != 0:
#               raise RuntimeError(pj_strerrno(pj_errno))
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
        ierr = pj_transform(p1.projpj, p2.projpj, npts, 0, xx, yy, zz)
    else:
        ierr = pj_transform(p1.projpj, p2.projpj, npts, 0, xx, yy, NULL)
    if ierr != 0:
        raise RuntimeError(pj_strerrno(ierr))
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
