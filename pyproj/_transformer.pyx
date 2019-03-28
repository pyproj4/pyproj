include "base.pxi"

from pyproj.crs import CRS
from pyproj.proj import Proj
from pyproj.compat import cstrencode, pystrdecode
from pyproj._datadir cimport get_pyproj_context
from pyproj.exceptions import ProjError

cdef class _Transformer:
    def __cinit__(self):
        self.projpj = NULL
        self.projctx = NULL
        self.input_geographic = False
        self.output_geographic = False
        self.input_radians = False
        self.output_radians = False
        self.is_pipeline = False
        self.skip_equivalent = False
        self.projections_equivalent = False
        self.projections_exact_same = False

    def __init__(self):
        # set up the context
        self.projctx = get_pyproj_context()

    def __dealloc__(self):
        """destroy projection definition"""
        if self.projpj is not NULL:
            proj_destroy(self.projpj)
        if self.projctx is not NULL:
            proj_context_destroy(self.projctx)

    def set_radians_io(self):
        self.input_radians = proj_angular_input(self.projpj, PJ_FWD)
        self.output_radians = proj_angular_output(self.projpj, PJ_FWD)

    @staticmethod
    def _init_crs_to_crs(proj_from, proj_to, skip_equivalent=False):
        cdef _Transformer transformer = _Transformer()
        transformer.projpj = proj_create_crs_to_crs(
            transformer.projctx,
            cstrencode(proj_from.crs.srs),
            cstrencode(proj_to.crs.srs),
            NULL)
        if transformer.projpj is NULL:
            raise ProjError("Error creating CRS to CRS.")
        transformer.set_radians_io()
        transformer.projections_exact_same = proj_from.crs.is_exact_same(proj_to.crs)
        transformer.projections_equivalent = proj_from.crs == proj_to.crs
        transformer.skip_equivalent = skip_equivalent
        transformer.is_pipeline = False
        return transformer

    @staticmethod
    def from_proj(proj_from, proj_to, skip_equivalent=False):
        if not isinstance(proj_from, Proj):
            proj_from = Proj(proj_from)
        if not isinstance(proj_to, Proj):
            proj_to = Proj(proj_to)
        transformer = _Transformer._init_crs_to_crs(proj_from, proj_to, skip_equivalent=skip_equivalent)
        transformer.input_geographic = proj_from.crs.is_geographic
        transformer.output_geographic = proj_to.crs.is_geographic
        return transformer

    @staticmethod
    def from_pipeline(const char *proj_pipeline):
        cdef _Transformer transformer = _Transformer()

        # initialize projection
        transformer.projpj = proj_create(transformer.projctx, proj_pipeline)
        if transformer.projpj is NULL:
            raise ProjError("Invalid projection {}.".format(proj_pipeline))
        transformer.set_radians_io()
        transformer.is_pipeline = True
        return transformer

    def _transform(self, inx, iny, inz, intime, radians, errcheck=False):
        if self.projections_exact_same or (self.projections_equivalent and self.skip_equivalent):
            return
        # private function to call pj_transform
        cdef void *xdata
        cdef void *ydata
        cdef void *zdata
        cdef void *tdata
        cdef double *xx
        cdef double *yy
        cdef double *zz
        cdef double *tt
        cdef Py_ssize_t buflenx, bufleny, buflenz, buflent, npts, iii
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
        if intime is not None:
            if PyObject_AsWriteBuffer(intime, &tdata, &buflent) <> 0:
                raise ProjError
        else:
            buflent = bufleny

        if not buflenx or not (buflenx == bufleny == buflenz == buflent):
            raise ProjError('x,y,z, and time must be same size')
        xx = <double *>xdata
        yy = <double *>ydata
        if inz is not None:
            zz = <double *>zdata
        else:
            zz = NULL
        if intime is not None:
            tt = <double *>tdata
        else:
            tt = NULL
        npts = buflenx//8

        # degrees to radians
        if not self.is_pipeline and not radians and self.input_radians:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_DG2RAD
                yy[iii] = yy[iii]*_DG2RAD
        # radians to degrees
        elif not self.is_pipeline and radians and not self.input_radians and self.input_geographic:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_RAD2DG
                yy[iii] = yy[iii]*_RAD2DG

        cdef int err_count = proj_trans_generic(
            self.projpj,
            PJ_FWD,
            xx, _DOUBLESIZE, npts,
            yy, _DOUBLESIZE, npts,
            zz, _DOUBLESIZE, npts,
            tt, _DOUBLESIZE, npts,
        )
        cdef int errno = proj_errno(self.projpj)
        if errno and errcheck:
            raise ProjError("proj_trans_generic error: {}".format(
                pystrdecode(proj_errno_string(errno))))
        elif err_count and errcheck:
            raise ProjError("{} proj_trans_generic error(s)".format(err_count))

        # radians to degrees
        if not self.is_pipeline and not radians and self.output_radians:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_RAD2DG
                yy[iii] = yy[iii]*_RAD2DG
        # degrees to radians
        elif not self.is_pipeline and radians and not self.output_radians and self.output_geographic:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_DG2RAD
                yy[iii] = yy[iii]*_DG2RAD


    def _transform_sequence(self, Py_ssize_t stride, inseq, bint switch,
            time_3rd, radians, errcheck=False):
        if self.projections_exact_same or (self.projections_equivalent and self.skip_equivalent):
            return
        # private function to itransform function
        cdef:
            void *buffer
            double *coords
            double *x
            double *y
            double *z
            double *tt
            Py_ssize_t buflen, npts, iii, jjj
            int err

        if stride < 2:
            raise ProjError("coordinates must contain at least 2 values")
        if PyObject_AsWriteBuffer(inseq, &buffer, &buflen) <> 0:
            raise ProjError("object does not provide the python buffer writeable interface")

        coords = <double*>buffer
        npts = buflen // (stride * _DOUBLESIZE)

        # degrees to radians
        if not self.is_pipeline and not radians and self.input_radians:
            for iii from 0 <= iii < npts:
                jjj = stride*iii
                coords[jjj] *= _DG2RAD
                coords[jjj+1] *= _DG2RAD
        # radians to degrees
        elif not self.is_pipeline and radians and not self.input_radians and self.input_geographic:
            for iii from 0 <= iii < npts:
                jjj = stride*iii
                coords[jjj] *= _RAD2DG
                coords[jjj+1] *= _RAD2DG

        if not switch:
            x = coords
            y = coords + 1
        else:
            x = coords + 1
            y = coords

        # z coordinate
        if stride == 4 or (stride == 3 and not time_3rd):
            z = coords + 2
        else:
            z = NULL
        # time
        if stride == 3 and time_3rd:
            tt = coords + 2
        elif stride == 4:
            tt = coords + 3
        else:
            tt = NULL

        cdef int err_count = proj_trans_generic (
            self.projpj,
            PJ_FWD,
            x, stride*_DOUBLESIZE, npts,
            y, stride*_DOUBLESIZE, npts,
            z, stride*_DOUBLESIZE, npts,
            tt, stride*_DOUBLESIZE, npts,
        )
        cdef int errno = proj_errno(self.projpj)
        if errno and errcheck:
            raise ProjError("proj_trans_generic error: {}".format(
                pystrdecode(proj_errno_string(errno))))
        elif err_count and errcheck:
            raise ProjError("{} proj_trans_generic error(s)".format(err_count))


        # radians to degrees
        if not self.is_pipeline and not radians and self.output_radians:
            for iii from 0 <= iii < npts:
                jjj = stride*iii
                coords[jjj] *= _RAD2DG
                coords[jjj+1] *= _RAD2DG
        # degrees to radians
        elif not self.is_pipeline and radians and not self.output_radians and self.output_geographic:
            for iii from 0 <= iii < npts:
                jjj = stride*iii
                coords[jjj] *= _DG2RAD
                coords[jjj+1] *= _DG2RAD
