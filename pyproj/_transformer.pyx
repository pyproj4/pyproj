include "base.pxi"

cimport cython

import warnings
from collections import namedtuple

from pyproj._crs cimport AreaOfUse, Base, _CRS, CoordinateOperation
from pyproj._datadir cimport pyproj_context_initialize
from pyproj.compat import cstrencode, pystrdecode
from pyproj.enums import ProjVersion, TransformDirection
from pyproj.exceptions import ProjError


_PJ_DIRECTION_MAP = {
    TransformDirection.FORWARD: PJ_FWD,
    TransformDirection.INVERSE: PJ_INV,
    TransformDirection.IDENT: PJ_IDENT,
}

_TRANSFORMER_TYPE_MAP = {
    PJ_TYPE_UNKNOWN: "Unknown Transformer",
    PJ_TYPE_CONVERSION: "Conversion Transformer",
    PJ_TYPE_TRANSFORMATION: "Transformation Transformer",
    PJ_TYPE_CONCATENATED_OPERATION: "Concatenated Operation Transformer",
    PJ_TYPE_OTHER_COORDINATE_OPERATION: "Other Coordinate Operation Transformer",
}


AreaOfInterest = namedtuple("AreaOfInterest",
    ["west_lon_degree", "south_lat_degree", "east_lon_degree", "north_lat_degree"]
)
AreaOfInterest.__doc__ = """
.. versionadded:: 2.3.0

This is the area of interest for the transformation.

Parameters
----------
west_lon_degree: float
    The west bound in degrees of the area of interest.
south_lat_degree: float
    The south bound in degrees of the area of interest.
east_lon_degree: float
    The east bound in degrees of the area of interest.
north_lat_degree: float
    The north bound in degrees of the area of interest.
"""

cdef class _TransformerGroup:
    def __cinit__(self):
        self.context = NULL
        self._transformers = []
        self._unavailable_operations = []
        self._best_available = True

    def __dealloc__(self):
        """destroy projection definition"""
        if self.context != NULL:
            proj_context_destroy(self.context)

    def __init__(
        self,
        _CRS crs_from,
        _CRS crs_to,
        skip_equivalent=False,
        always_xy=False,
        area_of_interest=None,
    ):
        """
        From PROJ docs:

        The operations are sorted with the most relevant ones first: by
        descending area (intersection of the transformation area with the
        area of interest, or intersection of the transformation with the
        area of use of the CRS), and by increasing accuracy. Operations
        with unknown accuracy are sorted last, whatever their area.
        """
        self.context = proj_context_create()
        pyproj_context_initialize(self.context, False)
        cdef PJ_OPERATION_FACTORY_CONTEXT* operation_factory_context = NULL
        cdef PJ_OBJ_LIST * pj_operations = NULL
        cdef PJ* pj_transform = NULL
        cdef PJ_CONTEXT* context = NULL
        cdef int num_operations = 0
        cdef int is_instantiable = 0
        cdef double west_lon_degree, south_lat_degree, east_lon_degree, north_lat_degree
        try:
            operation_factory_context = proj_create_operation_factory_context(
                self.context,
                NULL,
            )
            if area_of_interest is not None:
                if not isinstance(area_of_interest, AreaOfInterest):
                    raise ProjError(
                        "Area of interest must be of the type pyproj.transformer.AreaOfInterest."
                    )
                west_lon_degree = area_of_interest.west_lon_degree
                south_lat_degree = area_of_interest.south_lat_degree
                east_lon_degree = area_of_interest.east_lon_degree
                north_lat_degree = area_of_interest.north_lat_degree
                proj_operation_factory_context_set_area_of_interest(
                    self.context,
                    operation_factory_context,
                    west_lon_degree,
                    south_lat_degree,
                    east_lon_degree,
                    north_lat_degree,
                )

            proj_operation_factory_context_set_grid_availability_use(
                self.context,
                operation_factory_context,
                PROJ_GRID_AVAILABILITY_IGNORED,
            )
            proj_operation_factory_context_set_spatial_criterion(
                self.context,
                operation_factory_context,
                PROJ_SPATIAL_CRITERION_PARTIAL_INTERSECTION
            )
            pj_operations = proj_create_operations(
                self.context,
                get_transform_crs(crs_from).projobj,
                get_transform_crs(crs_to).projobj,
                operation_factory_context,
            )
            num_operations = proj_list_get_count(pj_operations)
            for iii in range(num_operations):
                context = proj_context_create()
                pyproj_context_initialize(context, True)
                pj_transform = proj_list_get(
                    context,
                    pj_operations,
                    iii,
                )
                is_instantiable = proj_coordoperation_is_instantiable(
                    context,
                    pj_transform,
                )
                if is_instantiable:
                    self._transformers.append(
                        _Transformer._from_pj(
                            context,
                            pj_transform,
                            crs_from,
                            crs_to,
                            skip_equivalent,
                            always_xy,
                        )
                    )
                else:
                    coordinate_operation = CoordinateOperation.create(
                        context,
                        pj_transform,
                    )
                    self._unavailable_operations.append(coordinate_operation)
                    if iii == 0:
                        self._best_available = False
                        warnings.warn(
                            "Best transformation is not available due to missing "
                            "{!r}".format(coordinate_operation.grids[0])
                        )
        finally:
            if operation_factory_context != NULL:
                proj_operation_factory_context_destroy(operation_factory_context)
            if pj_operations != NULL:
                proj_list_destroy(pj_operations)
            ProjError.clear()
 

cdef _CRS get_transform_crs(_CRS in_crs):
    for sub_crs in in_crs.sub_crs_list:
        if (
            not sub_crs.type_name.startswith("Temporal") and
            not sub_crs.type_name.startswith("Temporal")
        ):
            return sub_crs.source_crs if sub_crs.is_bound else sub_crs
    return in_crs.source_crs if in_crs.is_bound else in_crs


cdef class _Transformer(Base):
    def __cinit__(self):
        self.input_geographic = False
        self.output_geographic = False
        self._input_radians = {}
        self._output_radians = {}
        self._area_of_use = None
        self.is_pipeline = False
        self.skip_equivalent = False
        self.projections_equivalent = False
        self.projections_exact_same = False
        self.type_name = "Unknown Transformer"

    def _set_radians_io(self):
        self._input_radians.update({
            PJ_FWD: proj_angular_input(self.projobj, PJ_FWD),
            PJ_INV: proj_angular_input(self.projobj, PJ_INV),
            PJ_IDENT: proj_angular_input(self.projobj, PJ_IDENT),
        })
        self._output_radians.update({
            PJ_FWD: proj_angular_output(self.projobj, PJ_FWD),
            PJ_INV: proj_angular_output(self.projobj, PJ_INV),
            PJ_IDENT: proj_angular_output(self.projobj, PJ_IDENT),
        })

    def _initialize_from_projobj(self):
        self.proj_info = proj_pj_info(self.projobj)
        if self.proj_info.id == NULL:
             raise ProjError("Input is not a transformation.")
        cdef PJ_TYPE transformer_type = proj_get_type(self.projobj)
        self.type_name = _TRANSFORMER_TYPE_MAP[transformer_type]
        ProjError.clear()

    @property
    def id(self):
        return pystrdecode(self.proj_info.id)

    @property
    def description(self):
        return pystrdecode(self.proj_info.description)

    @property
    def definition(self):
        return pystrdecode(self.proj_info.definition)

    @property
    def has_inverse(self):
        return self.proj_info.has_inverse == 1

    @property
    def accuracy(self):
        return self.proj_info.accuracy
    
    @property
    def area_of_use(self):
        """
        Returns
        -------
        AreaOfUse: The area of use object with associated attributes.
        """
        if self._area_of_use is not None:
            return self._area_of_use
        self._area_of_use = AreaOfUse.create(self.context, self.projobj)
        return self._area_of_use

    @staticmethod
    def from_crs(
        _CRS crs_from,
        _CRS crs_to,
        skip_equivalent=False,
        always_xy=False,
        area_of_interest=None,
    ):
        """
        Create a transformer from CRS objects
        """
        cdef PJ_AREA *pj_area_of_interest = NULL
        cdef double west_lon_degree, south_lat_degree, east_lon_degree, north_lat_degree
        cdef _Transformer transformer = _Transformer()
        try:
            if area_of_interest is not None:
                if not isinstance(area_of_interest, AreaOfInterest):
                    raise ProjError(
                        "Area of interest must be of the type pyproj.transformer.AreaOfInterest."
                    )
                pj_area_of_interest = proj_area_create()
                west_lon_degree = area_of_interest.west_lon_degree
                south_lat_degree = area_of_interest.south_lat_degree
                east_lon_degree = area_of_interest.east_lon_degree
                north_lat_degree = area_of_interest.north_lat_degree
                proj_area_set_bbox(
                    pj_area_of_interest,
                    west_lon_degree,
                    south_lat_degree,
                    east_lon_degree,
                    north_lat_degree,
                )
            transformer.context = proj_context_create()
            pyproj_context_initialize(transformer.context, False)
            transformer.projobj = proj_create_crs_to_crs(
                transformer.context,
                cstrencode(crs_from.srs),
                cstrencode(crs_to.srs),
                pj_area_of_interest,
            )
        finally:
            if pj_area_of_interest != NULL:
                proj_area_destroy(pj_area_of_interest)

        if transformer.projobj == NULL:
            raise ProjError("Error creating Transformer from CRS.")

        transformer._init_from_crs(
            crs_from=crs_from,
            crs_to=crs_to,
            skip_equivalent=skip_equivalent,
            always_xy=always_xy,
        )
        return transformer

    @staticmethod
    cdef _Transformer _from_pj(
        PJ_CONTEXT* context,
        PJ *transform_pj,
        _CRS crs_from,
        _CRS crs_to,
        skip_equivalent,
        always_xy,
    ):
        """
        Create a Transformer from a PJ* object
        """
        cdef _Transformer transformer = _Transformer()
        transformer.context = context
        transformer.projobj = transform_pj

        if transformer.projobj == NULL:
            raise ProjError("Error creating Transformer.")

        transformer._init_from_crs(
            crs_from=crs_from,
            crs_to=crs_to,
            skip_equivalent=skip_equivalent,
            always_xy=always_xy,
        )
        return transformer

    @staticmethod
    def from_pipeline(const char *proj_pipeline):
        """
        Create Transformer from a PROJ pipeline string.
        """
        cdef _Transformer transformer = _Transformer()
        transformer.context = proj_context_create()
        pyproj_context_initialize(transformer.context, False)
        # initialize projection
        transformer.projobj = proj_create(
            transformer.context,
            proj_pipeline,
        )
        if transformer.projobj is NULL:
            raise ProjError("Invalid projection {}.".format(proj_pipeline))
        transformer._initialize_from_projobj()
        transformer._set_radians_io()
        transformer.is_pipeline = True
        return transformer

    def _set_always_xy(self):
        """
        Setup the transformer so it has the axis order always in xy order.
        """
        cdef PJ* always_xy_pj = proj_normalize_for_visualization(
            self.context,
            self.projobj,
        )
        proj_destroy(self.projobj)
        self.projobj = always_xy_pj

    def _init_from_crs(
        self,
        _CRS crs_from,
        _CRS crs_to,
        skip_equivalent,
        always_xy,
    ):
        """
        Finish initializing transformer properties from CRS objects
        """
        if always_xy:
            self._set_always_xy()
        self._initialize_from_projobj()
        self._set_radians_io()
        self.projections_exact_same = crs_from.is_exact_same(crs_to)
        self.projections_equivalent = crs_from == crs_to
        self.input_geographic = crs_from.is_geographic
        self.output_geographic = crs_to.is_geographic
        self.skip_equivalent = skip_equivalent
        self.is_pipeline = False

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _transform(self, inx, iny, inz, intime, direction, radians, errcheck):
        if self.projections_exact_same or (self.projections_equivalent and self.skip_equivalent):
            return
        tmp_pj_direction = _PJ_DIRECTION_MAP[TransformDirection.create(direction)]
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>tmp_pj_direction
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
            raise ProjError("object does not provide the python buffer writeable interface")
        if PyObject_AsWriteBuffer(iny, &ydata, &bufleny) <> 0:
            raise ProjError("object does not provide the python buffer writeable interface")
        if inz is not None and PyObject_AsWriteBuffer(inz, &zdata, &buflenz) <> 0:
            raise ProjError("object does not provide the python buffer writeable interface")
        else:
            buflenz = bufleny
        if intime is not None and PyObject_AsWriteBuffer(intime, &tdata, &buflent) <> 0:
            raise ProjError("object does not provide the python buffer writeable interface")
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
            for iii in range(npts):
                xx[iii] = xx[iii]*_DG2RAD
                yy[iii] = yy[iii]*_DG2RAD
        # radians to degrees
        elif not self.is_pipeline and radians\
                and not self._input_radians[pj_direction]\
                and self.input_geographic:
            for iii in range(npts):
                xx[iii] = xx[iii]*_RAD2DG
                yy[iii] = yy[iii]*_RAD2DG
        proj_errno_reset(self.projobj)
        proj_trans_generic(
            self.projobj,
            pj_direction,
            xx, _DOUBLESIZE, npts,
            yy, _DOUBLESIZE, npts,
            zz, _DOUBLESIZE, npts,
            tt, _DOUBLESIZE, npts,
        )
        cdef int errno = proj_errno(self.projobj)
        if errcheck and errno:
            raise ProjError("transform error: {}".format(
                pystrdecode(proj_errno_string(errno))))
        elif errcheck and ProjError.internal_proj_error is not None:
            raise ProjError("transform error")

        # radians to degrees
        if not self.is_pipeline and not radians\
                and self._output_radians[pj_direction]:
            for iii in range(npts):
                xx[iii] = xx[iii]*_RAD2DG
                yy[iii] = yy[iii]*_RAD2DG
        # degrees to radians
        elif not self.is_pipeline and radians\
                and not self._output_radians[pj_direction]\
                and self.output_geographic:
            for iii in range(npts):
                xx[iii] = xx[iii]*_DG2RAD
                yy[iii] = yy[iii]*_DG2RAD
        ProjError.clear()

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _transform_sequence(
        self, Py_ssize_t stride, inseq, bint switch,
        direction, time_3rd, radians, errcheck
    ):
        if self.projections_exact_same or (self.projections_equivalent and self.skip_equivalent):
            return
        tmp_pj_direction = _PJ_DIRECTION_MAP[TransformDirection.create(direction)]
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>tmp_pj_direction
        # private function to itransform function
        cdef:
            void *buffer
            double *coords
            double *x
            double *y
            double *z
            double *tt
            Py_ssize_t buflen, npts, iii, jjj

        if stride < 2:
            raise ProjError("coordinates must contain at least 2 values")
        if PyObject_AsWriteBuffer(inseq, &buffer, &buflen) <> 0:
            raise ProjError("object does not provide the python buffer writeable interface")

        coords = <double*>buffer
        npts = buflen // (stride * _DOUBLESIZE)

        # degrees to radians
        if not self.is_pipeline and not radians\
                and self._input_radians[pj_direction]:
            for iii in range(npts):
                jjj = stride * iii
                coords[jjj] *= _DG2RAD
                coords[jjj + 1] *= _DG2RAD
        # radians to degrees
        elif not self.is_pipeline and radians\
                and not self._input_radians[pj_direction]\
                and self.input_geographic:
            for iii in range(npts):
                jjj = stride * iii
                coords[jjj] *= _RAD2DG
                coords[jjj + 1] *= _RAD2DG

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

        proj_errno_reset(self.projobj)
        proj_trans_generic (
            self.projobj,
            pj_direction,
            x, stride*_DOUBLESIZE, npts,
            y, stride*_DOUBLESIZE, npts,
            z, stride*_DOUBLESIZE, npts,
            tt, stride*_DOUBLESIZE, npts,
        )
        cdef int errno = proj_errno(self.projobj)
        if errcheck and errno:
            raise ProjError("itransform error: {}".format(
                pystrdecode(proj_errno_string(errno))))
        elif errcheck and ProjError.internal_proj_error is not None:
            raise ProjError("itransform error")


        # radians to degrees
        if not self.is_pipeline and not radians\
                and self._output_radians[pj_direction]:
            for iii in range(npts):
                jjj = stride * iii
                coords[jjj] *= _RAD2DG
                coords[jjj + 1] *= _RAD2DG
        # degrees to radians
        elif not self.is_pipeline and radians\
                and not self._output_radians[pj_direction]\
                and self.output_geographic:
            for iii in range(npts):
                jjj = stride * iii
                coords[jjj] *= _DG2RAD
                coords[jjj + 1] *= _DG2RAD

        ProjError.clear()
