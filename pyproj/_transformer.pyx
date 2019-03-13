include "base.pxi"

from pyproj.crs import CRS
from pyproj.proj import Proj
from pyproj.compat import cstrencode, pystrdecode
from pyproj.datadir import get_data_dir
from pyproj.exceptions import ProjError

cdef class _Transformer:
    def __cinit__(self):
        self.projpj = NULL
        self.projctx = NULL
        self.from_geographic = False
        self.to_geographic = False

    def __init__(self):
        # set up the context
        self.projctx = proj_context_create()
        py_data_dir = cstrencode(get_data_dir())
        cdef const char* data_dir = py_data_dir
        proj_context_set_search_paths(self.projctx, 1, &data_dir)

    def __dealloc__(self):
        """destroy projection definition"""
        if self.projpj is not NULL:
            proj_destroy(self.projpj)
        if self.projctx is not NULL:
            proj_context_destroy(self.projctx)

    @staticmethod
    def _init_crs_to_crs(proj_from, proj_to):
        cdef _Transformer transformer = _Transformer()
        transformer.projpj = proj_create_crs_to_crs(
            transformer.projctx,
            _Transformer._definition_from_object(proj_from),
            _Transformer._definition_from_object(proj_to),
            NULL)
        if transformer.projpj is NULL:
            raise ProjError("Error creating CRS to CRS.")
        transformer.from_geographic = _Transformer._is_geographic(proj_from)
        transformer.to_geographic = _Transformer._is_geographic(proj_to)
        return transformer

    @staticmethod
    def _is_geographic(proj):
        if hasattr(proj, "crs"):
            return proj.crs.is_geographic
        return proj.is_geographic

    @staticmethod
    def from_proj(proj_from, proj_to):
        if not isinstance(proj_from, Proj):
            proj_from = Proj(proj_from)
        if not isinstance(proj_to, Proj):
            proj_to = Proj(proj_to)
        return _Transformer._init_crs_to_crs(proj_from, proj_to)

    @staticmethod
    def from_crs(crs_from, crs_to):
        if not isinstance(crs_from, CRS):
            crs_from = CRS.from_user_input(crs_from)
        if not isinstance(crs_to, CRS):
            crs_to = CRS.from_user_input(crs_to)
        return _Transformer._init_crs_to_crs(crs_from, crs_to)

    @staticmethod
    def from_pipeline(const char *proj_pipeline):
        cdef _Transformer transformer = _Transformer()

        # initialize projection
        transformer.projpj = proj_create(transformer.projctx, proj_pipeline)
        if transformer.projpj is NULL:
            raise ProjError("Invalid projection {}.".format(proj_pipeline))

        # disable radians as it should be handled in the pipeline
        transformer.from_geographic = False
        transformer.to_geographic = False
        return transformer



    @staticmethod
    def _definition_from_object(in_proj):
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

    def _transform(self, inx, iny, inz, radians):
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

        if radians and self.from_geographic:
            for i from 0 <= i < npts:
                xx[i] = xx[i]*_RAD2DG
                yy[i] = yy[i]*_RAD2DG

        proj_trans_generic(
            self.projpj,
            PJ_FWD,
            xx, _DOUBLESIZE, npts,
            yy, _DOUBLESIZE, npts,
            zz, _DOUBLESIZE, npts,
            NULL, 0, 0,
        )
        cdef int errno = proj_errno(self.projpj)
        if errno:
            raise ProjError("proj_trans_generic error: {}".format(
                pystrdecode(proj_errno_string(errno))))

        if radians and self.to_geographic:
            for i from 0 <= i < npts:
                xx[i] = xx[i]*_DG2RAD
                yy[i] = yy[i]*_DG2RAD

    def _transform_sequence(self, Py_ssize_t stride, inseq, bint switch, radians):
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

        if radians and self.from_geographic:
            for i from 0 <= i < npts:
                j = stride*i
                coords[j] *= _RAD2DG
                coords[j+1] *= _RAD2DG

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
            self.projpj,
            PJ_FWD,
            x, stride*_DOUBLESIZE, npts,
            y, stride*_DOUBLESIZE, npts,
            z, stride*_DOUBLESIZE, npts,
            NULL, 0, 0,
        )

        cdef int errno = proj_errno(self.projpj)
        if errno:
            raise ProjError("proj_trans_generic error: {}".format(
                proj_errno_string(errno)))

        if radians and self.to_geographic:
            for i from 0 <= i < npts:
                j = stride*i
                coords[j] *= _DG2RAD
                coords[j+1] *= _DG2RAD
