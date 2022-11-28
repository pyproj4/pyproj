include "base.pxi"

cimport cython
from cpython.mem cimport PyMem_Free, PyMem_Malloc

import copy
import re
import warnings
from collections import namedtuple

from pyproj._compat cimport cstrencode
from pyproj._crs cimport (
    _CRS,
    Base,
    CoordinateOperation,
    _get_concatenated_operations,
    _to_proj4,
    _to_wkt,
    create_area_of_use,
)
from pyproj._datadir cimport pyproj_context_create, pyproj_context_destroy

from pyproj._datadir import _LOGGER
from pyproj.aoi import AreaOfInterest
from pyproj.enums import ProjVersion, TransformDirection, WktVersion
from pyproj.exceptions import ProjError

# version number string for PROJ
proj_version_str = f"{PROJ_VERSION_MAJOR}.{PROJ_VERSION_MINOR}.{PROJ_VERSION_PATCH}"
PROJ_VERSION = (PROJ_VERSION_MAJOR, PROJ_VERSION_MINOR, PROJ_VERSION_PATCH)
_AUTH_CODE_RE = re.compile(r"(?P<authority>\w+)\:(?P<code>\w+)")

IF (CTE_PROJ_VERSION_MAJOR, CTE_PROJ_VERSION_MINOR) >= (9, 1):
    cdef extern from "proj.h" nogil:
        PJ* proj_trans_get_last_used_operation(PJ *P)


cdef dict _PJ_DIRECTION_MAP = {
    TransformDirection.FORWARD: PJ_FWD,
    TransformDirection.INVERSE: PJ_INV,
    TransformDirection.IDENT: PJ_IDENT,
}

cdef dict _TRANSFORMER_TYPE_MAP = {
    PJ_TYPE_UNKNOWN: "Unknown Transformer",
    PJ_TYPE_CONVERSION: "Conversion Transformer",
    PJ_TYPE_TRANSFORMATION: "Transformation Transformer",
    PJ_TYPE_CONCATENATED_OPERATION: "Concatenated Operation Transformer",
    PJ_TYPE_OTHER_COORDINATE_OPERATION: "Other Coordinate Operation Transformer",
}


Factors = namedtuple(
    "Factors",
    [
        "meridional_scale",
        "parallel_scale",
        "areal_scale",
        "angular_distortion",
        "meridian_parallel_angle",
        "meridian_convergence",
        "tissot_semimajor",
        "tissot_semiminor",
        "dx_dlam",
        "dx_dphi",
        "dy_dlam",
        "dy_dphi",
    ],
)


Factors.__doc__ = """
.. versionadded:: 2.6.0

These are the scaling and angular distortion factors.

See PROJ :c:type:`PJ_FACTORS` documentation.

Parameters
----------
meridional_scale: List[float]
     Meridional scale at coordinate.
parallel_scale: List[float]
    Parallel scale at coordinate.
areal_scale: List[float]
    Areal scale factor at coordinate.
angular_distortion: List[float]
    Angular distortion at coordinate.
meridian_parallel_angle: List[float]
    Meridian/parallel angle at coordinate.
meridian_convergence: List[float]
    Meridian convergence at coordinate. Sometimes also described as *grid declination*.
tissot_semimajor: List[float]
    Maximum scale factor.
tissot_semiminor: List[float]
    Minimum scale factor.
dx_dlam: List[float]
    Partial derivative of coordinate.
dx_dphi: List[float]
    Partial derivative of coordinate.
dy_dlam: List[float]
    Partial derivative of coordinate.
dy_dphi: List[float]
    Partial derivative of coordinate.
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
            pyproj_context_destroy(self.context)

    def __init__(
        self,
        _CRS crs_from not None,
        _CRS crs_to not None,
        bint always_xy,
        area_of_interest,
        bint allow_ballpark,
        str authority,
        double accuracy,
    ):
        """
        From PROJ docs:

        The operations are sorted with the most relevant ones first: by
        descending area (intersection of the transformation area with the
        area of interest, or intersection of the transformation with the
        area of use of the CRS), and by increasing accuracy. Operations
        with unknown accuracy are sorted last, whatever their area.
        """
        self.context = pyproj_context_create()
        cdef PJ_OPERATION_FACTORY_CONTEXT* operation_factory_context = NULL
        cdef PJ_OBJ_LIST * pj_operations = NULL
        cdef PJ* pj_transform = NULL
        cdef PJ_CONTEXT* context = NULL
        cdef const char* c_authority = NULL
        cdef int num_operations = 0
        cdef int is_instantiable = 0
        cdef double west_lon_degree, south_lat_degree, east_lon_degree, north_lat_degree

        if authority is not None:
            c_authority = authority

        try:
            operation_factory_context = proj_create_operation_factory_context(
                self.context,
                c_authority,
            )
            if area_of_interest is not None:
                if not isinstance(area_of_interest, AreaOfInterest):
                    raise ProjError(
                        "Area of interest must be of the type "
                        "pyproj.transformer.AreaOfInterest."
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
            if accuracy > 0:
                proj_operation_factory_context_set_desired_accuracy(
                    self.context,
                    operation_factory_context,
                    accuracy,
                )
            proj_operation_factory_context_set_allow_ballpark_transformations(
                self.context,
                operation_factory_context,
                allow_ballpark,
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
                crs_from.projobj,
                crs_to.projobj,
                operation_factory_context,
            )
            num_operations = proj_list_get_count(pj_operations)
            for iii in range(num_operations):
                context = pyproj_context_create()
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
                            f"{coordinate_operation.grids[0]!r}"
                        )
        finally:
            if operation_factory_context != NULL:
                proj_operation_factory_context_destroy(operation_factory_context)
            if pj_operations != NULL:
                proj_list_destroy(pj_operations)
            ProjError.clear()


cdef PJ* proj_create_crs_to_crs(
    PJ_CONTEXT *ctx,
    const char *source_crs_str,
    const char *target_crs_str,
    PJ_AREA *area,
    str authority,
    str accuracy,
    allow_ballpark,
    bint force_over,
) except NULL:
    """
    This is the same as proj_create_crs_to_crs in proj.h
    with the options added. It is a hack for stabilily
    reasons.

    Reference: https://github.com/pyproj4/pyproj/pull/800
    """
    cdef PJ *source_crs = proj_create(ctx, source_crs_str)
    if source_crs == NULL:
        _LOGGER.debug(
            "PROJ_DEBUG: proj_create_crs_to_crs: Cannot instantiate source_crs"
        )
        return NULL
    cdef PJ *target_crs = proj_create(ctx, target_crs_str)
    if target_crs == NULL:
        proj_destroy(source_crs)
        _LOGGER.debug(
            "PROJ_DEBUG: proj_create_crs_to_crs: Cannot instantiate target_crs"
        )
        return NULL

    cdef const char* options[5]
    cdef bytes b_authority
    cdef bytes b_accuracy
    cdef int options_index = 0
    options[0] = NULL
    options[1] = NULL
    options[2] = NULL
    options[3] = NULL
    options[4] = NULL
    if authority is not None:
        b_authority = cstrencode(f"AUTHORITY={authority}")
        options[options_index] = b_authority
        options_index += 1
    if accuracy is not None:
        b_accuracy = cstrencode(f"ACCURACY={accuracy}")
        options[options_index] = b_accuracy
        options_index += 1
    if allow_ballpark is not None:
        if not allow_ballpark:
            options[options_index] = b"ALLOW_BALLPARK=NO"
        options_index += 1
    if force_over:
        IF CTE_PROJ_VERSION_MAJOR >= 9:
            options[options_index] = b"FORCE_OVER=YES"
        ELSE:
            raise NotImplementedError("force_over requires PROJ 9+.")

    cdef PJ* transform = proj_create_crs_to_crs_from_pj(
        ctx,
        source_crs,
        target_crs,
        area,
        options,
    )
    proj_destroy(source_crs)
    proj_destroy(target_crs)
    if transform == NULL:
        raise ProjError("Error creating Transformer from CRS.")
    return transform


cdef class _Transformer(Base):
    def __cinit__(self):
        self._area_of_use = None
        self.type_name = "Unknown Transformer"
        self._operations = None
        self._source_crs = None
        self._target_crs = None

    def _initialize_from_projobj(self):
        self.proj_info = proj_pj_info(self.projobj)
        if self.proj_info.id == NULL:
            raise ProjError("Input is not a transformation.")
        cdef PJ_TYPE transformer_type = proj_get_type(self.projobj)
        self.type_name = _TRANSFORMER_TYPE_MAP[transformer_type]
        self._set_base_info()
        ProjError.clear()

    @property
    def id(self):
        return self.proj_info.id

    @property
    def description(self):
        return self.proj_info.description

    @property
    def definition(self):
        return self.proj_info.definition

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
        AreaOfUse:
            The area of use object with associated attributes.
        """
        if self._area_of_use is not None:
            return self._area_of_use
        self._area_of_use = create_area_of_use(self.context, self.projobj)
        return self._area_of_use

    @property
    def source_crs(self):
        """
        .. versionadded:: 3.3.0

        Returns
        -------
        Optional[_CRS]:
            The source CRS of a CoordinateOperation.
        """
        if self._source_crs is not None:
            return None if self._source_crs is False else self._source_crs
        cdef PJ * projobj = proj_get_source_crs(self.context, self.projobj)
        ProjError.clear()
        if projobj == NULL:
            self._source_crs = False
            return None
        try:
            self._source_crs = _CRS(_to_wkt(
                self.context,
                projobj,
                version=WktVersion.WKT2_2019,
                pretty=False,
            ))
        finally:
            proj_destroy(projobj)
        return self._source_crs

    @property
    def target_crs(self):
        """
        .. versionadded:: 3.3.0

        Returns
        -------
        Optional[_CRS]:
            The target CRS of a CoordinateOperation.
        """
        if self._target_crs is not None:
            return None if self._target_crs is False else self._target_crs
        cdef PJ * projobj = proj_get_target_crs(self.context, self.projobj)
        ProjError.clear()
        if projobj == NULL:
            self._target_crs = False
            return None
        try:
            self._target_crs = _CRS(_to_wkt(
                self.context,
                projobj,
                version=WktVersion.WKT2_2019,
                pretty=False,
            ))
        finally:
            proj_destroy(projobj)
        return self._target_crs

    @property
    def operations(self):
        """
        .. versionadded:: 2.4.0

        Returns
        -------
        Tuple[CoordinateOperation]:
            The operations in a concatenated operation.
        """
        if self._operations is not None:
            return self._operations
        self._operations = _get_concatenated_operations(self.context, self.projobj)
        return self._operations

    def get_last_used_operation(self):
        IF (CTE_PROJ_VERSION_MAJOR, CTE_PROJ_VERSION_MINOR) >= (9, 1):
            cdef PJ* last_used_operation = proj_trans_get_last_used_operation(self.projobj)
            if last_used_operation == NULL:
                raise ProjError(
                    "Last used operation not found. "
                    "This is likely due to not initiating a transform."
                )
            cdef PJ_CONTEXT* context = NULL
            try:
                context = pyproj_context_create()
            except:
                proj_destroy(last_used_operation)
                raise
            proj_assign_context(last_used_operation, context)
            return _Transformer._from_pj(
                context,
                last_used_operation,
                False,
            )
        ELSE:
            raise NotImplementedError("PROJ 9.1+ required to get last used operation.")

    @property
    def is_network_enabled(self):
        """
        .. versionadded:: 3.0.0

        Returns
        -------
        bool:
            If the network is enabled.
        """
        return proj_context_is_network_enabled(self.context) == 1

    def to_proj4(self, version=ProjVersion.PROJ_5, bint pretty=False):
        """
        Convert the projection to a PROJ string.

        .. versionadded:: 3.1.0

        Parameters
        ----------
        version: pyproj.enums.ProjVersion, default=pyproj.enums.ProjVersion.PROJ_5
            The version of the PROJ string output.
        pretty: bool, default=False
            If True, it will set the output to be a multiline string.

        Returns
        -------
        str:
            The PROJ string.

        """
        return _to_proj4(self.context, self.projobj, version=version, pretty=pretty)

    @staticmethod
    def from_crs(
        const char* crs_from,
        const char* crs_to,
        bint always_xy=False,
        area_of_interest=None,
        str authority=None,
        str accuracy=None,
        allow_ballpark=None,
        bint force_over=False,
    ):
        """
        Create a transformer from CRS objects
        """
        cdef PJ_AREA *pj_area_of_interest = NULL
        cdef double west_lon_degree
        cdef double south_lat_degree
        cdef double east_lon_degree
        cdef double north_lat_degree
        cdef _Transformer transformer = _Transformer()
        try:
            if area_of_interest is not None:
                if not isinstance(area_of_interest, AreaOfInterest):
                    raise ProjError(
                        "Area of interest must be of the type "
                        "pyproj.transformer.AreaOfInterest."
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
            transformer.context = pyproj_context_create()
            transformer.projobj = proj_create_crs_to_crs(
                transformer.context,
                crs_from,
                crs_to,
                pj_area_of_interest,
                authority=authority,
                accuracy=accuracy,
                allow_ballpark=allow_ballpark,
                force_over=force_over,
            )
        finally:
            if pj_area_of_interest != NULL:
                proj_area_destroy(pj_area_of_interest)

        transformer._init_from_crs(always_xy)
        return transformer

    @staticmethod
    cdef _Transformer _from_pj(
        PJ_CONTEXT* context,
        PJ *transform_pj,
        bint always_xy,
    ):
        """
        Create a Transformer from a PJ* object
        """
        cdef _Transformer transformer = _Transformer()
        transformer.context = context
        transformer.projobj = transform_pj

        if transformer.projobj == NULL:
            raise ProjError("Error creating Transformer.")

        transformer._init_from_crs(always_xy)
        return transformer

    @staticmethod
    def from_pipeline(const char *proj_pipeline):
        """
        Create Transformer from a PROJ pipeline string.
        """
        cdef _Transformer transformer = _Transformer()
        transformer.context = pyproj_context_create()

        auth_match = _AUTH_CODE_RE.match(proj_pipeline.strip())
        if auth_match:
            # attempt to create coordinate operation from AUTH:CODE
            match_data = auth_match.groupdict()
            transformer.projobj = proj_create_from_database(
                transformer.context,
                cstrencode(match_data["authority"]),
                cstrencode(match_data["code"]),
                PJ_CATEGORY_COORDINATE_OPERATION,
                False,
                NULL,
            )
        if transformer.projobj == NULL:
            # initialize projection
            transformer.projobj = proj_create(
                transformer.context,
                proj_pipeline,
            )
        if transformer.projobj is NULL:
            raise ProjError(f"Invalid projection {proj_pipeline}.")
        transformer._initialize_from_projobj()
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

    def _init_from_crs(self, bint always_xy):
        """
        Finish initializing transformer properties from CRS objects
        """
        if always_xy:
            self._set_always_xy()
        self._initialize_from_projobj()

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _transform(
        self,
        object inx,
        object iny,
        object inz,
        object intime,
        object direction,
        bint radians,
        bint errcheck,
    ):
        if self.id == "noop":
            return

        tmp_pj_direction = _PJ_DIRECTION_MAP[TransformDirection.create(direction)]
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>tmp_pj_direction
        cdef PyBuffWriteManager xbuff = PyBuffWriteManager(inx)
        cdef PyBuffWriteManager ybuff = PyBuffWriteManager(iny)

        cdef PyBuffWriteManager zbuff
        cdef Py_ssize_t buflenz
        cdef double* zz
        if inz is not None:
            zbuff = PyBuffWriteManager(inz)
            buflenz = zbuff.len
            zz = zbuff.data
        else:
            buflenz = xbuff.len
            zz = NULL

        cdef PyBuffWriteManager tbuff
        cdef Py_ssize_t buflent
        cdef double* tt
        if intime is not None:
            tbuff = PyBuffWriteManager(intime)
            buflent = tbuff.len
            tt = tbuff.data
        else:
            buflent = xbuff.len
            tt = NULL

        if not (xbuff.len == ybuff.len == buflenz == buflent):
            raise ProjError('x, y, z, and time must be same size if included.')

        cdef Py_ssize_t iii
        cdef int errno = 0
        with nogil:
            # degrees to radians
            if not radians and proj_angular_input(self.projobj, pj_direction):
                for iii in range(xbuff.len):
                    xbuff.data[iii] = xbuff.data[iii]*_DG2RAD
                    ybuff.data[iii] = ybuff.data[iii]*_DG2RAD
            # radians to degrees
            elif radians and proj_degree_input(self.projobj, pj_direction):
                for iii in range(xbuff.len):
                    xbuff.data[iii] = xbuff.data[iii]*_RAD2DG
                    ybuff.data[iii] = ybuff.data[iii]*_RAD2DG

            proj_errno_reset(self.projobj)
            proj_trans_generic(
                self.projobj,
                pj_direction,
                xbuff.data, _DOUBLESIZE, xbuff.len,
                ybuff.data, _DOUBLESIZE, ybuff.len,
                zz, _DOUBLESIZE, xbuff.len,
                tt, _DOUBLESIZE, xbuff.len,
            )
            errno = proj_errno(self.projobj)
            if errcheck and errno:
                with gil:
                    raise ProjError(
                        f"transform error: {proj_context_errno_string(self.context, errno)}"
                    )
            elif errcheck:
                with gil:
                    if ProjError.internal_proj_error is not None:
                        raise ProjError("transform error")

            # radians to degrees
            if not radians and proj_angular_output(self.projobj, pj_direction):
                for iii in range(xbuff.len):
                    xbuff.data[iii] = xbuff.data[iii]*_RAD2DG
                    ybuff.data[iii] = ybuff.data[iii]*_RAD2DG
            # degrees to radians
            elif radians and proj_degree_output(self.projobj, pj_direction):
                for iii in range(xbuff.len):
                    xbuff.data[iii] = xbuff.data[iii]*_DG2RAD
                    ybuff.data[iii] = ybuff.data[iii]*_DG2RAD
        ProjError.clear()

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _transform_sequence(
        self,
        Py_ssize_t stride,
        object inseq,
        bint switch,
        object direction,
        bint time_3rd,
        bint radians,
        bint errcheck,
    ):
        if self.id == "noop":
            return
        tmp_pj_direction = _PJ_DIRECTION_MAP[TransformDirection.create(direction)]
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>tmp_pj_direction
        # private function to itransform function
        cdef double *x
        cdef double *y
        cdef double *z
        cdef double *tt

        if stride < 2:
            raise ProjError("coordinates must contain at least 2 values")

        cdef PyBuffWriteManager coordbuff = PyBuffWriteManager(inseq)
        cdef Py_ssize_t npts, iii, jjj
        cdef int errno = 0
        npts = coordbuff.len // stride
        with nogil:
            # degrees to radians
            if not radians and proj_angular_input(self.projobj, pj_direction):
                for iii in range(npts):
                    jjj = stride * iii
                    coordbuff.data[jjj] *= _DG2RAD
                    coordbuff.data[jjj + 1] *= _DG2RAD
            # radians to degrees
            elif radians and proj_degree_input(self.projobj, pj_direction):
                for iii in range(npts):
                    jjj = stride * iii
                    coordbuff.data[jjj] *= _RAD2DG
                    coordbuff.data[jjj + 1] *= _RAD2DG

            if not switch:
                x = coordbuff.data
                y = coordbuff.data + 1
            else:
                x = coordbuff.data + 1
                y = coordbuff.data

            # z coordinate
            if stride == 4 or (stride == 3 and not time_3rd):
                z = coordbuff.data + 2
            else:
                z = NULL
            # time
            if stride == 3 and time_3rd:
                tt = coordbuff.data + 2
            elif stride == 4:
                tt = coordbuff.data + 3
            else:
                tt = NULL

            proj_errno_reset(self.projobj)
            proj_trans_generic(
                self.projobj,
                pj_direction,
                x, stride*_DOUBLESIZE, npts,
                y, stride*_DOUBLESIZE, npts,
                z, stride*_DOUBLESIZE, npts,
                tt, stride*_DOUBLESIZE, npts,
            )
            errno = proj_errno(self.projobj)
            if errcheck and errno:
                with gil:
                    raise ProjError(
                        f"itransform error: {proj_context_errno_string(self.context, errno)}"
                    )
            elif errcheck:
                with gil:
                    if ProjError.internal_proj_error is not None:
                        raise ProjError("itransform error")

            # radians to degrees
            if not radians and proj_angular_output(self.projobj, pj_direction):
                for iii in range(npts):
                    jjj = stride * iii
                    coordbuff.data[jjj] *= _RAD2DG
                    coordbuff.data[jjj + 1] *= _RAD2DG
            # degrees to radians
            elif radians and proj_degree_output(self.projobj, pj_direction):
                for iii in range(npts):
                    jjj = stride * iii
                    coordbuff.data[jjj] *= _DG2RAD
                    coordbuff.data[jjj + 1] *= _DG2RAD

        ProjError.clear()

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _transform_bounds(
        self,
        double left,
        double bottom,
        double right,
        double top,
        int densify_pts,
        bint radians,
        bint errcheck,
        object direction,
    ):
        tmp_pj_direction = _PJ_DIRECTION_MAP[TransformDirection.create(direction)]
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>tmp_pj_direction

        if self.id == "noop" or pj_direction == PJ_IDENT:
            return (left, bottom, right, top)

        cdef int errno = 0
        cdef bint success = True
        cdef double out_left = left
        cdef double out_bottom = bottom
        cdef double out_right = right
        cdef double out_top = top

        with nogil:
            # degrees to radians
            if not radians and proj_angular_input(self.projobj, pj_direction):
                left *= _DG2RAD
                bottom *= _DG2RAD
                right *= _DG2RAD
                top *= _DG2RAD
            # radians to degrees
            elif radians and proj_degree_input(self.projobj, pj_direction):
                left *= _RAD2DG
                bottom *= _RAD2DG
                right *= _RAD2DG
                top *= _RAD2DG

            proj_errno_reset(self.projobj)
            success = proj_trans_bounds(
                self.context,
                self.projobj,
                pj_direction,
                left,
                bottom,
                right,
                top,
                &out_left,
                &out_bottom,
                &out_right,
                &out_top,
                densify_pts,
            )

            if not success or errcheck:
                errno = proj_errno(self.projobj)
                if errno:
                    with gil:
                        raise ProjError(
                            "transform bounds error: "
                            f"{proj_context_errno_string(self.context, errno)}"
                        )
                else:
                    with gil:
                        if ProjError.internal_proj_error is not None:
                            raise ProjError("transform bounds error")

            # radians to degrees
            if not radians and proj_angular_output(self.projobj, pj_direction):
                out_left *= _RAD2DG
                out_bottom *= _RAD2DG
                out_right *= _RAD2DG
                out_top *= _RAD2DG
            # degrees to radians
            elif radians and proj_degree_output(self.projobj, pj_direction):
                out_left *= _DG2RAD
                out_bottom *= _DG2RAD
                out_right *= _DG2RAD
                out_top *= _DG2RAD

        ProjError.clear()
        return out_left, out_bottom, out_right, out_top

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def _get_factors(self, longitude, latitude, bint radians, bint errcheck):
        """
        Calculates the projection factors PJ_FACTORS

        Designed to work with Proj class.

        Equivalent to `proj -S` command line.
        """
        cdef PyBuffWriteManager lonbuff = PyBuffWriteManager(longitude)
        cdef PyBuffWriteManager latbuff = PyBuffWriteManager(latitude)

        if not lonbuff.len or not (lonbuff.len == latbuff.len):
            raise ProjError('longitude and latitude must be same size')

        # prepare the factors output
        meridional_scale = copy.copy(longitude)
        parallel_scale = copy.copy(longitude)
        areal_scale = copy.copy(longitude)
        angular_distortion = copy.copy(longitude)
        meridian_parallel_angle = copy.copy(longitude)
        meridian_convergence = copy.copy(longitude)
        tissot_semimajor = copy.copy(longitude)
        tissot_semiminor = copy.copy(longitude)
        dx_dlam = copy.copy(longitude)
        dx_dphi = copy.copy(longitude)
        dy_dlam = copy.copy(longitude)
        dy_dphi = copy.copy(longitude)
        cdef PyBuffWriteManager meridional_scale_buff = PyBuffWriteManager(
            meridional_scale)
        cdef PyBuffWriteManager parallel_scale_buff = PyBuffWriteManager(
            parallel_scale)
        cdef PyBuffWriteManager areal_scale_buff = PyBuffWriteManager(areal_scale)
        cdef PyBuffWriteManager angular_distortion_buff = PyBuffWriteManager(
            angular_distortion)
        cdef PyBuffWriteManager meridian_parallel_angle_buff = PyBuffWriteManager(
            meridian_parallel_angle)
        cdef PyBuffWriteManager meridian_convergence_buff = PyBuffWriteManager(
            meridian_convergence)
        cdef PyBuffWriteManager tissot_semimajor_buff = PyBuffWriteManager(
            tissot_semimajor)
        cdef PyBuffWriteManager tissot_semiminor_buff = PyBuffWriteManager(
            tissot_semiminor)
        cdef PyBuffWriteManager dx_dlam_buff = PyBuffWriteManager(dx_dlam)
        cdef PyBuffWriteManager dx_dphi_buff = PyBuffWriteManager(dx_dphi)
        cdef PyBuffWriteManager dy_dlam_buff = PyBuffWriteManager(dy_dlam)
        cdef PyBuffWriteManager dy_dphi_buff = PyBuffWriteManager(dy_dphi)

        # calculate the factors
        cdef PJ_COORD pj_coord = proj_coord(0, 0, 0, HUGE_VAL)
        cdef PJ_FACTORS pj_factors
        cdef int errno = 0
        cdef bint invalid_coord = 0
        cdef Py_ssize_t iii
        with nogil:
            for iii in range(lonbuff.len):
                pj_coord.uv.u = lonbuff.data[iii]
                pj_coord.uv.v = latbuff.data[iii]
                if not radians:
                    pj_coord.uv.u *= _DG2RAD
                    pj_coord.uv.v *= _DG2RAD

                # set both to HUGE_VAL if inf or nan
                proj_errno_reset(self.projobj)
                if pj_coord.uv.v == HUGE_VAL \
                        or pj_coord.uv.v != pj_coord.uv.v \
                        or pj_coord.uv.u == HUGE_VAL \
                        or pj_coord.uv.u != pj_coord.uv.u:
                    invalid_coord = True
                else:
                    invalid_coord = False
                    pj_factors = proj_factors(self.projobj, pj_coord)

                errno = proj_errno(self.projobj)
                if errcheck and errno:
                    with gil:
                        raise ProjError(
                            f"proj error: {proj_context_errno_string(self.context, errno)}"
                        )

                if errno or invalid_coord:
                    meridional_scale_buff.data[iii] = HUGE_VAL
                    parallel_scale_buff.data[iii] = HUGE_VAL
                    areal_scale_buff.data[iii] = HUGE_VAL
                    angular_distortion_buff.data[iii] = HUGE_VAL
                    meridian_parallel_angle_buff.data[iii] = HUGE_VAL
                    meridian_convergence_buff.data[iii] = HUGE_VAL
                    tissot_semimajor_buff.data[iii] = HUGE_VAL
                    tissot_semiminor_buff.data[iii] = HUGE_VAL
                    dx_dlam_buff.data[iii] = HUGE_VAL
                    dx_dphi_buff.data[iii] = HUGE_VAL
                    dy_dlam_buff.data[iii] = HUGE_VAL
                    dy_dphi_buff.data[iii] = HUGE_VAL
                else:
                    meridional_scale_buff.data[iii] = pj_factors.meridional_scale
                    parallel_scale_buff.data[iii] = pj_factors.parallel_scale
                    areal_scale_buff.data[iii] = pj_factors.areal_scale
                    angular_distortion_buff.data[iii] = (
                        pj_factors.angular_distortion * _RAD2DG
                    )
                    meridian_parallel_angle_buff.data[iii] = (
                        pj_factors.meridian_parallel_angle * _RAD2DG
                    )
                    meridian_convergence_buff.data[iii] = (
                        pj_factors.meridian_convergence * _RAD2DG
                    )
                    tissot_semimajor_buff.data[iii] = pj_factors.tissot_semimajor
                    tissot_semiminor_buff.data[iii] = pj_factors.tissot_semiminor
                    dx_dlam_buff.data[iii] = pj_factors.dx_dlam
                    dx_dphi_buff.data[iii] = pj_factors.dx_dphi
                    dy_dlam_buff.data[iii] = pj_factors.dy_dlam
                    dy_dphi_buff.data[iii] = pj_factors.dy_dphi

        ProjError.clear()

        return Factors(
            meridional_scale=meridional_scale,
            parallel_scale=parallel_scale,
            areal_scale=areal_scale,
            angular_distortion=angular_distortion,
            meridian_parallel_angle=meridian_parallel_angle,
            meridian_convergence=meridian_convergence,
            tissot_semimajor=tissot_semimajor,
            tissot_semiminor=tissot_semiminor,
            dx_dlam=dx_dlam,
            dx_dphi=dx_dphi,
            dy_dlam=dy_dlam,
            dy_dphi=dy_dphi,
        )
