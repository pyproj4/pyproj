# Make changes to this file, not the c-wrappers that Pyrex generates.

import math, array
from types import TupleType, ListType

cdef int _doublesize
cdef double _dg2rad, _rad2dg
_dg2rad = math.radians(1.)
_rad2dg = math.degrees(1.)
_doublesize = sizeof(double)
__version__ = "1.8.1"

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
    int PyObject_AsWriteBuffer(object, void **rbuf, Py_ssize_t *len)
    char *PyString_AsString(object)

cdef class Proj:
    cdef projPJ projpj
    cdef public object projparams
    cdef public object proj_version
    cdef char *pjinitstring

    def __new__(self, projparams=None, **kwargs):
        # if projparams is None, use kwargs.
        if projparams is None:
            if len(kwargs) == 0:
                raise RuntimeError('no projection control parameters specified')
            else:
                projparams = kwargs
        # set units to meters.
        if not projparams.has_key('units'):
            projparams['units']='m'
        elif projparams['units'] != 'm':
            print 'resetting units to meters ...'
            projparams['units']='m'
        # setup proj initialization string.
        pjargs = []
        for key,value in projparams.iteritems():
            pjargs.append('+'+key+"="+str(value)+' ')
        self.projparams = projparams
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
        """special method that allows pyproj.Proj instance to be pickled"""
        return (self.__class__,(self.projparams,))

    def _fwd(self, object lons, object lats, radians=False, errcheck=False):
        """
 forward transformation - lons,lats to x,y.
 if radians=True, lons/lats are radians instead of degrees.
 if errcheck=True, an exception is raised if the forward transformation is invalid.
 if errcheck=False and the forward transformation is invalid, no exception is
 raised and the platform dependent value HUGE_VAL is returned.
        """
        cdef projUV projxyout, projlonlatin
        cdef Py_ssize_t buflenx, bufleny
        cdef int ndim, i
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
            if radians:
                projlonlatin.u = lonsdata[i]
                projlonlatin.v = latsdata[i]
            else:
                projlonlatin.u = _dg2rad*lonsdata[i]
                projlonlatin.v = _dg2rad*latsdata[i]
            projxyout = pj_fwd(projlonlatin,self.projpj)
            if errcheck and pj_errno != 0:
                raise RuntimeError(pj_strerrno(pj_errno))
            lonsdata[i] = projxyout.u
            latsdata[i] = projxyout.v
        return lons, lats

    def _inv(self, object x, object y, radians=False, errcheck=False):
        """
 inverse transformation - x,y to lons,lats.
 if radians=True, lons/lats are radians instead of degrees.
 if errcheck=True, an exception is raised if the inverse transformation is invalid.
 if errcheck=False and the inverse transformation is invalid, no exception is
 raised and the platform dependent value HUGE_VAL is returned.
        """
        cdef projUV projxyin, projlonlatout
        cdef Py_ssize_t buflenx, bufleny
        cdef int ndim, i
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
            projxyin.u = xdatab[i]
            projxyin.v = ydatab[i]
            projlonlatout = pj_inv(projxyin,self.projpj)
            if errcheck and pj_errno != 0:
                raise RuntimeError(pj_strerrno(pj_errno))
            if radians:
                xdatab[i] = projlonlatout.u
                ydatab[i] = projlonlatout.v
            else:
                xdatab[i] = _rad2dg*projlonlatout.u
                ydatab[i] = _rad2dg*projlonlatout.v
        return x, y 

    def __call__(self,lon,lat,inverse=False,radians=False,errcheck=False):
        # if lon,lat support BufferAPI, must make sure they contain doubles.
        isfloat = False; islist = False; istuple = False
        # first, if it's a numpy array scalar convert to float
        # (array scalars don't support buffer API)
        if hasattr(lon,'shape') and lon.shape == (): lon = float(lon)
        if hasattr(lat,'shape') and lat.shape == (): lat = float(lat)
        try:
            # typecast numpy arrays to double.
            # (this makes a copy - which is crucial
            #  since buffer is modified in place)
            lon.dtype.char
            lat.dtype.char
            inx = lon.astype('d')
            iny = lat.astype('d')
        except:
            try: # perhaps they are Numeric/numarray arrays?
                lon.typecode()
                lat.typecode()
                inx = lon.astype('d')
                iny = lat.astype('d')
            except:
                # perhaps they are regular python arrays?
                try:
                    lon.typecode
                    lat.typecode
                    inx = array.array('d',lon)
                    iny = array.array('d',lat)
                except: 
                    # none of the above
                    # try to convert to python array
                    # a list.
                    if type(lon) is ListType and type(lon) is ListType:
                        inx = array.array('d',lon)
                        iny = array.array('d',lat)
                        islist = True
                    # a tuple.
                    elif type(lon) is TupleType and type(lon) is TupleType:
                        inx = array.array('d',lon)
                        iny = array.array('d',lat)
                        istuple = True
                    # a float.
                    else:
                        try:
                            lon = float(lon)
                            lat = float(lat)
                            inx = array.array('d',(lon,))
                            iny = array.array('d',(lat,))
                            isfloat = True
                        except:
                            raise TypeError, 'lon and lat must be arrays, lists/tuples or scalars (and they must all be of the same type)'
        # call proj4 functions.
        if inverse:
            outx, outy = self._inv(inx, iny, radians=radians, errcheck=errcheck)
        else:
            outx, outy = self._fwd(inx, iny, radians=radians, errcheck=errcheck)
        # all done.
        # if inputs were lists, tuples or floats, convert back.
        if isfloat:
            return outx[0],outy[0]
        elif islist:
            return outx.tolist(),outy.tolist()
        elif istuple:
            return tuple(outx),tuple(outy)
        else:
            return outx,outy

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

def transform(Proj p1, Proj p2, x, y, z=None, radians=False):
    # make sure x,y,z support Buffer API and contain doubles.
    isfloat = False; islist = False; istuple = False
    # first, if it's a numpy array scalar convert to float
    # (array scalars don't support buffer API)
    if hasattr(x,'shape') and x.shape == (): x = float(x)
    if hasattr(y,'shape') and y.shape == (): y = float(y)
    if hasattr(z,'shape') and z.shape == (): z = float(z)
    try:
        # typecast numpy arrays to double.
        # (this makes a copy - which is crucial
        #  since buffer is modified in place)
        x.dtype.char
        y.dtype.char
        if z is not None: z.dtype.char
        inx = x.astype('d')
        iny = y.astype('d')
        if z is not None:
            inz = z.astype('d')
    except:
        try: # perhaps they are Numeric/numarray arrays?
            x.typecode()
            y.typecode()
            if z is not None: z.typecode()
            inx = x.astype('d')
            iny = y.astype('d')
            if z is not None:
                inz = z.astype('d')
        except:
            # perhaps they are regular python arrays?
            try:
                x.typecode
                y.typecode
                if z is not None: z.typecode
                inx = array.array('d',x)
                iny = array.array('d',y)
                if z is not None:
                    inz = array.array('d',z)
            except: 
                # try to convert to python array
                # a list.
                if type(x) is ListType and type(y) is ListType and (type(z) is None or type(z) is ListType):
                    inx = array.array('d',x)
                    iny = array.array('d',y)
                    if z is not None:
                        inz = array.array('d',z)
                    islist = True
                # a tuple.
                elif type(x) is TupleType and type(y) is TupleType and (type(z) is None or type(z) is TupleType):
                    inx = array.array('d',x)
                    iny = array.array('d',y)
                    if z is not None:
                        inz = array.array('d',z)
                    istuple = True
                # a scalar?
                else:
                    try:
                        x = float(x)
                        y = float(y)
                        if z is not None: z = float(z)
                        inx = array.array('d',(x,))
                        iny = array.array('d',(y,))
                        if z is not None: inz = array.array('d',(z,))
                        isfloat = True
                    except:
                        raise TypeError, 'x, y and z must be arrays, lists/tuples or scalars (and they must all be of the same type)'
    ierr = _transform(p1,p2,inx,iny,inz,radians)
    if ierr != 0:
        raise RuntimeError(pj_strerrno(ierr))
    # if inputs were lists, tuples or floats, convert back.
    if inz is not None:
        if isfloat:
            return inx[0],iny[0],inz[0]
        elif islist:
            return inx.tolist(),iny.tolist(),inz.tolist()
        elif istuple:
            return tuple(inx),tuple(iny),tuple(inz)
        else:
            return inx,iny,inz
    else:
        if isfloat:
            return inx[0],iny[0]
        elif islist:
            return inx.tolist(),iny.tolist()
        elif istuple:
            return tuple(inx),tuple(iny)
        else:
            return inx,iny

cdef _transform(Proj p1, Proj p2, inx, iny, inz, radians):
    """private function to call pj_transform"""
    cdef void *xdata, *ydata, *zdata
    cdef double *xx, *yy, *zz
    cdef Py_ssize_t buflenx, bufleny, buflenz
    cdef int npts, i
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
    if not radians and p2.is_latlong():
        for i from 0 <= i < npts:
            xx[i] = xx[i]*_rad2dg
            yy[i] = yy[i]*_rad2dg
    return ierr
