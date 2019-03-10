# cimport c_numpy
# c_numpy.import_array()
include "base.pxi"

from pyproj.crs import CRS
from pyproj.compat import cstrencode, pystrdecode
from pyproj.datadir import get_data_dir
from pyproj.exceptions import ProjError


# # version number strings for proj.4 and Geod
proj_version_str = "{0}.{1}.{2}".format(
    PROJ_VERSION_MAJOR,
    PROJ_VERSION_MINOR,
    PROJ_VERSION_PATCH
)

cdef class Proj:
    def __cinit__(self):
        self.projctx = NULL
        self.projpj = NULL

    def __init__(self, const char *projstring):
        self.srs = pystrdecode(projstring)
        # setup the context
        self.projctx = proj_context_create()
        py_data_dir = cstrencode(get_data_dir())
        cdef const char* data_dir = py_data_dir
        proj_context_set_search_paths(self.projctx, 1, &data_dir)
        proj_context_use_proj4_init_rules(self.projctx, 1)
        # initialize projection
        self.projpj = proj_create(self.projctx, projstring)
        if self.projpj is NULL:
            raise ProjError("Invalid projection {}.".format(projstring))
        self.projpj_info = proj_pj_info(self.projpj)
        self.proj_version = PROJ_VERSION_MAJOR

    def __dealloc__(self):
        """destroy projection definition"""
        if self.projpj is not NULL:
            proj_destroy(self.projpj)
        if self.projctx is not NULL:
            proj_context_destroy(self.projctx)

    @property
    def definition(self):
        return self.projpj_info.definition

    @property
    def has_inverse(self):
        """Returns true if this projection has an inverse"""
        return self.projpj_info.has_inverse == 1

    def __reduce__(self):
        """special method that allows pyproj.Proj instance to be pickled"""
        return self.__class__,(self.crs.srs,)

    def _fwd(self, object lons, object lats, errcheck=False):
        """
        forward transformation - lons,lats to x,y (done in place).
        if errcheck=True, an exception is raised if the forward transformation is invalid.
        if errcheck=False and the forward transformation is invalid, no exception is
        raised and 1.e30 is returned.
        """
        cdef PJ_COORD projxyout
        cdef PJ_COORD projlonlatin
        cdef Py_ssize_t buflenx, bufleny, ndim, i
        cdef double *lonsdata
        cdef double *latsdata
        cdef void *londata
        cdef void *latdata
        cdef int err
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(lons, &londata, &buflenx) <> 0:
            raise ProjError
        if PyObject_AsWriteBuffer(lats, &latdata, &bufleny) <> 0:
            raise ProjError
        # process data in buffer
        if buflenx != bufleny:
            raise ProjError("Buffer lengths not the same")
        ndim = buflenx//_DOUBLESIZE
        lonsdata = <double *>londata
        latsdata = <double *>latdata
        for i from 0 <= i < ndim:
            # if inputs are nan's, return big number.
            if lonsdata[i] != lonsdata[i] or latsdata[i] != latsdata[i]:
                lonsdata[i]=1.e30; latsdata[i]=1.e30
                if errcheck:
                    raise ProjError('projection undefined')
                continue
            if proj_angular_input(self.projpj, PJ_FWD):
                projlonlatin.uv.u = _DG2RAD*lonsdata[i]
                projlonlatin.uv.v = _DG2RAD*latsdata[i]
            else:
                projlonlatin.uv.u = lonsdata[i]
                projlonlatin.uv.v = latsdata[i]
            projxyout = proj_trans(self.projpj, PJ_FWD, projlonlatin)
            if errcheck:
                err = proj_errno(self.projpj)
                if err != 0:
                     raise ProjError(proj_errno_string(err))
            # since HUGE_VAL can be 'inf',
            # change it to a real (but very large) number.
            # also check for NaNs.
            if projxyout.xy.x == HUGE_VAL or\
                    projxyout.xy.x != projxyout.xy.x or\
                    projxyout.xy.y == HUGE_VAL or\
                    projxyout.xy.x != projxyout.xy.x:
                if errcheck:
                    raise ProjError('projection undefined')
                lonsdata[i] = 1.e30
                latsdata[i] = 1.e30
            else:
                lonsdata[i] = projxyout.xy.x
                latsdata[i] = projxyout.xy.y

    def _inv(self, object x, object y, errcheck=False):
        """
        inverse transformation - x,y to lons,lats (done in place).
        if errcheck=True, an exception is raised if the inverse transformation is invalid.
        if errcheck=False and the inverse transformation is invalid, no exception is
        raised and 1.e30 is returned.
        """
        if not self.has_inverse:
            raise ProjError('inverse projection undefined')

        cdef PJ_COORD projxyin
        cdef PJ_COORD projlonlatout
        cdef Py_ssize_t buflenx, bufleny, ndim, i
        cdef void *xdata
        cdef void *ydata
        cdef double *xdatab
        cdef double *ydatab
        # if buffer api is supported, get pointer to data buffers.
        if PyObject_AsWriteBuffer(x, &xdata, &buflenx) <> 0:
            raise ProjError
        if PyObject_AsWriteBuffer(y, &ydata, &bufleny) <> 0:
            raise ProjError
        # process data in buffer
        # (for numpy/regular python arrays).
        if buflenx != bufleny:
            raise ProjError("Buffer lengths not the same")
        ndim = buflenx//_DOUBLESIZE
        xdatab = <double *>xdata
        ydatab = <double *>ydata
        for i from 0 <= i < ndim:
            # if inputs are nan's, return big number.
            if xdatab[i] != xdatab[i] or ydatab[i] != ydatab[i]:
                xdatab[i]=1.e30; ydatab[i]=1.e30
                if errcheck:
                    raise ProjError('projection undefined')
                continue
            projxyin.uv.u = xdatab[i]
            projxyin.uv.v = ydatab[i]
            projlonlatout = proj_trans(self.projpj, PJ_INV, projxyin)
            if errcheck:
                err = proj_errno(self.projpj)
                if err != 0:
                     raise ProjError(proj_errno_string(err))
            # since HUGE_VAL can be 'inf',
            # change it to a real (but very large) number.
            # also check for NaNs.
            if projlonlatout.uv.u == HUGE_VAL or \
                    projlonlatout.uv.u != projlonlatout.uv.u or \
                    projlonlatout.uv.v == HUGE_VAL or \
                    projlonlatout.uv.v != projlonlatout.uv.v:
                if errcheck:
                    raise ProjError('projection undefined')
                xdatab[i] = 1.e30
                ydatab[i] = 1.e30
            elif proj_angular_output(self.projpj, PJ_INV):
                xdatab[i] = _RAD2DG*projlonlatout.uv.u
                ydatab[i] = _RAD2DG*projlonlatout.uv.v
            else:
                xdatab[i] = projlonlatout.uv.u
                ydatab[i] = projlonlatout.uv.v

#     def _fwdn(self, c_numpy.ndarray lonlat, radians=False, errcheck=False):
#       """
# forward transformation - lons,lats to x,y (done in place).
# Uses ndarray of shape ...,2.
# if radians=True, lons/lats are radians instead of degrees.
# if errcheck=True, an exception is raised if the forward
#                transformation is invalid.
# if errcheck=False and the forward transformation is
#                invalid, no exception is
#                raised and 1.e30 is returned.
#       """
#       cdef PJ_UV projxyout, projlonlatin
#       cdef PJ_UV *llptr
#       cdef int err
#       cdef Py_ssize_t npts, i
#       npts = c_numpy.PyArray_SIZE(lonlat)//2
#       llptr = <PJ_UV *>lonlat.data
#       for i from 0 <= i < npts:
#           if radians:
#               projlonlatin = llptr[i]
#           else:
#               projlonlatin.u = _DG2RAD*llptr[i].u
#               projlonlatin.v = _DG2RAD*llptr[i].v
#           projxyout = pj_fwd(projlonlatin,self.projpj)
#
#           if errcheck:
#               err = proj_context_errno(self.projctx)
#               if err != 0:
#                    raise ProjError(proj_errno_string(err))
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
#
#     def _invn(self, c_numpy.ndarray xy, radians=False, errcheck=False):
#       """
# inverse transformation - x,y to lons,lats (done in place).
# Uses ndarray of shape ...,2.
# if radians=True, lons/lats are radians instead of degrees.
# if errcheck=True, an exception is raised if the inverse transformation is invalid.
# if errcheck=False and the inverse transformation is invalid, no exception is
# raised and 1.e30 is returned.
#       """
#       cdef PJ_UV projxyin, projlonlatout
#       cdef PJ_UV *llptr
#       cdef Py_ssize_t npts, i
#       npts = c_numpy.PyArray_SIZE(xy)//2
#       llptr = <PJ_UV *>xy.data
#
#       for i from 0 <= i < npts:
#           projxyin = llptr[i]
#           projlonlatout = pj_inv(projxyin, self.projpj)
#           if errcheck:
#               err = proj_context_errno(self.projctx)
#               if err != 0:
#                    raise ProjError(proj_errno_string(err))
#           # since HUGE_VAL can be 'inf',
#           # change it to a real (but very large) number.
#           if projlonlatout.u == HUGE_VAL:
#               llptr[i].u = 1.e30
#           elif radians:
#               llptr[i].u = projlonlatout.u
#           else:
#               llptr[i].u = _RAD2DG*projlonlatout.u
#           if projlonlatout.v == HUGE_VAL:
#               llptr[i].v = 1.e30
#           elif radians:
#               llptr[i].v = projlonlatout.v
#           else:
#               llptr[i].v = _RAD2DG*projlonlatout.v

    def __repr__(self):
        return "Proj('{srs}', preserve_units=True)".format(srs=self.srs)

cdef class TransProj:
    def __cinit__(self):
        self.projpj = NULL
        self.projctx = NULL

    def __init__(self, p1, p2):
        # set up the context
        self.projctx = proj_context_create()
        py_data_dir = cstrencode(get_data_dir())
        cdef const char* data_dir = py_data_dir
        proj_context_set_search_paths(self.projctx, 1, &data_dir)

        self.projpj = proj_create_crs_to_crs(
            self.projctx,
            TransProj.definition_from_object(p1),
            TransProj.definition_from_object(p2),
            NULL)
        if self.projpj is NULL:
            raise ProjError("Error creating CRS to CRS.")

    def __dealloc__(self):
        """destroy projection definition"""
        if self.projpj is not NULL:
            proj_destroy(self.projpj)
        if self.projctx is not NULL:
            proj_context_destroy(self.projctx)

    @staticmethod
    def definition_from_object(in_proj):
        """
        Parameters
        ----------
        in_proj: :obj:`pyproj.Proj` or :obj:`pyproj.CRS`

        Returns
        -------
        char*: Definition string for `proj_create_crs_to_crs`.

        """
        if isinstance(in_proj, Proj):
            return in_proj.definition
        return cstrencode(CRS.from_user_input(in_proj).to_wkt())

def _transform(p1, p2, inx, iny, inz):
    pj_trans =  TransProj(p1, p2)
    # private function to call pj_transform
    cdef void *xdata
    cdef void *ydata
    cdef void *zdata
    cdef double *xx
    cdef double *yy
    cdef double *zz
    cdef Py_ssize_t buflenx, bufleny, buflenz, npts, i
    cdef int err
    if PyObject_AsWriteBuffer(inx, &xdata, &buflenx) <> 0:
        raise ProjError
    if PyObject_AsWriteBuffer(iny, &ydata, &bufleny) <> 0:
        raise ProjError
    if inz is not None:
        if PyObject_AsWriteBuffer(inz, &zdata, &buflenz) <> 0:
            raise ProjError
    else:
        buflenz = bufleny
    if not (buflenx == bufleny == buflenz):
        raise ProjError('x,y and z must be same size')
    xx = <double *>xdata
    yy = <double *>ydata
    if inz is not None:
        zz = <double *>zdata
    else:
        zz = NULL
    npts = buflenx//8
    if proj_angular_input(pj_trans.projpj, PJ_FWD):
        for i from 0 <= i < npts:
            xx[i] = xx[i]*_DG2RAD
            yy[i] = yy[i]*_DG2RAD

    proj_trans_generic(
        pj_trans.projpj,
        PJ_FWD,
        xx, _DOUBLESIZE, npts,
        yy, _DOUBLESIZE, npts,
        zz, _DOUBLESIZE, npts,
        NULL, 0, 0,
    )
    cdef int errno = proj_errno(pj_trans.projpj)
    if errno:
        raise ProjError("proj_trans_generic error: {}".format(
            pystrdecode(proj_errno_string(errno))))
    if proj_angular_output(pj_trans.projpj, PJ_FWD):
        for i from 0 <= i < npts:
            xx[i] = xx[i]*_RAD2DG
            yy[i] = yy[i]*_RAD2DG


def _transform_sequence(p1, p2, Py_ssize_t stride, inseq, bint switch):
    pj_trans =  TransProj(p1, p2)
    # private function to itransform function
    cdef:
        void *buffer
        double *coords
        double *x
        double *y
        double *z
        Py_ssize_t buflen, npts, i, j
        int err

    if stride < 2:
        raise ProjError("coordinates must contain at least 2 values")
    if PyObject_AsWriteBuffer(inseq, &buffer, &buflen) <> 0:
        raise ProjError("object does not provide the python buffer writeable interface")

    coords = <double*>buffer
    npts = buflen // (stride * _DOUBLESIZE)

    if proj_angular_input(pj_trans.projpj, PJ_FWD):
        for i from 0 <= i < npts:
            j = stride*i
            coords[j] *= _DG2RAD
            coords[j+1] *= _DG2RAD

    if not switch:
        x = coords
        y = coords + 1
    else:
        x = coords + 1
        y = coords

    if stride == 2:
        z = NULL
    else:
        z = coords + 2

    proj_trans_generic (
        pj_trans.projpj,
        PJ_FWD,
        x, stride*_DOUBLESIZE, npts,
        y, stride*_DOUBLESIZE, npts,
        z, stride*_DOUBLESIZE, npts,
        NULL, 0, 0,
    )

    cdef int errno = proj_errno(pj_trans.projpj)
    if errno:
        raise ProjError("proj_trans_generic error: {}".format(
            proj_errno_string(errno)))

    if proj_angular_output(pj_trans.projpj, PJ_FWD):
        for i from 0 <= i < npts:
            j = stride*i
            coords[j] *= _RAD2DG
            coords[j+1] *= _RAD2DG
