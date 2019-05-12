include "base.pxi"

from pyproj._crs cimport _CRS
from pyproj._datadir cimport get_pyproj_context
from pyproj.compat import cstrencode, pystrdecode
from pyproj.enums import TransformDirection
from pyproj.exceptions import ProjError


cdef class _Transformer:
    def __cinit__(self):
        self.projpj = NULL
        self.projctx = NULL
        self.input_geographic = False
        self.output_geographic = False
        self._input_radians = {}
        self._output_radians = {}
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

    def _set_radians_io(self):
        self._input_radians.update({
            PJ_FWD: proj_angular_input(self.projpj, PJ_FWD),
            PJ_INV: proj_angular_input(self.projpj, PJ_INV),
            PJ_IDENT: proj_angular_input(self.projpj, PJ_IDENT),
        })
        self._output_radians.update({
            PJ_FWD: proj_angular_output(self.projpj, PJ_FWD),
            PJ_INV: proj_angular_output(self.projpj, PJ_INV),
            PJ_IDENT: proj_angular_output(self.projpj, PJ_IDENT),
        })

    @staticmethod
    def from_crs(_CRS crs_from, _CRS crs_to, skip_equivalent=False):
        cdef _Transformer transformer = _Transformer()
        transformer.projpj = proj_create_crs_to_crs(
            transformer.projctx,
            cstrencode(crs_from.srs),
            cstrencode(crs_to.srs),
            NULL)
        if transformer.projpj is NULL:
            raise ProjError("Error creating CRS to CRS.")

        transformer._set_radians_io()
        transformer.projections_exact_same = crs_from.is_exact_same(crs_to)
        transformer.projections_equivalent = crs_from == crs_to
        transformer.input_geographic = crs_from.is_geographic
        transformer.output_geographic = crs_to.is_geographic
        transformer.skip_equivalent = skip_equivalent
        transformer.is_pipeline = False
        return transformer

    @staticmethod
    def from_pipeline(const char *proj_pipeline):
        cdef _Transformer transformer = _Transformer()

        # initialize projection
        transformer.projpj = proj_create(transformer.projctx, proj_pipeline)
        if transformer.projpj is NULL:
            raise ProjError("Invalid projection {}.".format(proj_pipeline))
        transformer._set_radians_io()
        transformer.is_pipeline = True
        return transformer

    def _transform(self, inx, iny, inz, intime, direction, radians, errcheck):
        if self.projections_exact_same or (self.projections_equivalent and self.skip_equivalent):
            return
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>direction
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
        if not self.is_pipeline and not radians\
                and self._input_radians[pj_direction]:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_DG2RAD
                yy[iii] = yy[iii]*_DG2RAD
        # radians to degrees
        elif not self.is_pipeline and radians\
                and not self._input_radians[pj_direction]\
                and self.input_geographic:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_RAD2DG
                yy[iii] = yy[iii]*_RAD2DG

        ProjError.clear()
        proj_trans_generic(
            self.projpj,
            pj_direction,
            xx, _DOUBLESIZE, npts,
            yy, _DOUBLESIZE, npts,
            zz, _DOUBLESIZE, npts,
            tt, _DOUBLESIZE, npts,
        )
        cdef int errno = proj_errno(self.projpj)
        if errcheck and errno:
            raise ProjError("transform error: {}".format(
                pystrdecode(proj_errno_string(errno))))
        elif errcheck and ProjError.internal_proj_error is not None:
            raise ProjError("transform error")

        # radians to degrees
        if not self.is_pipeline and not radians\
                and self._output_radians[pj_direction]:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_RAD2DG
                yy[iii] = yy[iii]*_RAD2DG
        # degrees to radians
        elif not self.is_pipeline and radians\
                and not self._output_radians[pj_direction]\
                and self.output_geographic:
            for iii from 0 <= iii < npts:
                xx[iii] = xx[iii]*_DG2RAD
                yy[iii] = yy[iii]*_DG2RAD


    def _transform_sequence(
        self, Py_ssize_t stride, inseq, bint switch,
        direction, time_3rd, radians, errcheck
    ):
        if self.projections_exact_same or (self.projections_equivalent and self.skip_equivalent):
            return
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>direction
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
        if not self.is_pipeline and not radians\
                and self._input_radians[pj_direction]:
            for iii from 0 <= iii < npts:
                jjj = stride*iii
                coords[jjj] *= _DG2RAD
                coords[jjj+1] *= _DG2RAD
        # radians to degrees
        elif not self.is_pipeline and radians\
                and not self._input_radians[pj_direction]\
                and self.input_geographic:
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

        ProjError.clear()
        proj_trans_generic (
            self.projpj,
            pj_direction,
            x, stride*_DOUBLESIZE, npts,
            y, stride*_DOUBLESIZE, npts,
            z, stride*_DOUBLESIZE, npts,
            tt, stride*_DOUBLESIZE, npts,
        )
        cdef int errno = proj_errno(self.projpj)
        if errcheck and errno:
            raise ProjError("itransform error: {}".format(
                pystrdecode(proj_errno_string(errno))))
        elif errcheck and ProjError.internal_proj_error is not None:
            raise ProjError("itransform error")


        # radians to degrees
        if not self.is_pipeline and not radians\
                and self._output_radians[pj_direction]:
            for iii from 0 <= iii < npts:
                jjj = stride*iii
                coords[jjj] *= _RAD2DG
                coords[jjj+1] *= _RAD2DG
        # degrees to radians
        elif not self.is_pipeline and radians\
                and not self._output_radians[pj_direction]\
                and self.output_geographic:
            for iii from 0 <= iii < npts:
                jjj = stride*iii
                coords[jjj] *= _DG2RAD
                coords[jjj+1] *= _DG2RAD
