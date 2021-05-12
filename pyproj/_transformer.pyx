include "base.pxi"

cimport cython
from cpython cimport array
from cpython.mem cimport PyMem_Free, PyMem_Malloc

import copy
import re
import warnings
from collections import namedtuple

from pyproj._crs cimport (
    _CRS,
    Base,
    CoordinateOperation,
    _get_concatenated_operations,
    _to_proj4,
    create_area_of_use,
)
from pyproj._datadir cimport pyproj_context_create, pyproj_context_destroy

from pyproj._datadir import _LOGGER
from pyproj.aoi import AreaOfInterest
from pyproj.compat import cstrencode, pystrdecode
from pyproj.enums import ProjVersion, TransformDirection
from pyproj.exceptions import ProjError

# version number string for PROJ
proj_version_str = f"{PROJ_VERSION_MAJOR}.{PROJ_VERSION_MINOR}.{PROJ_VERSION_PATCH}"
_AUTH_CODE_RE = re.compile(r"(?P<authority>\w+)\:(?P<code>\w+)")


cdef pyproj_errno_string(PJ_CONTEXT* ctx, int err):
    # https://github.com/pyproj4/pyproj/issues/760
    IF CTE_PROJ_VERSION_MAJOR >= 8:
        return pystrdecode(proj_context_errno_string(ctx, err))
    ELSE:
        return pystrdecode(proj_errno_string(err))


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

See `PJ_FACTORS documentation <https://proj.org/development/reference/datatypes.html?highlight=pj_factors#c.PJ_FACTORS>`__  # noqa

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
        _CRS crs_from,
        _CRS crs_to,
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
        self.context = pyproj_context_create()
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


cdef _CRS get_transform_crs(_CRS in_crs):
    for sub_crs in in_crs.sub_crs_list:
        if (
            not sub_crs.type_name.startswith("Temporal") and
            not sub_crs.type_name.startswith("Temporal")
        ):
            return sub_crs.source_crs if sub_crs.is_bound else sub_crs
    return in_crs.source_crs if in_crs.is_bound else in_crs


cdef PJ* proj_create_crs_to_crs(
    PJ_CONTEXT *ctx,
    const char *source_crs_str,
    const char *target_crs_str,
    PJ_AREA *area,
    authority,
    accuracy,
    allow_ballpark,
):
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

    cdef const char* options[4]
    cdef int options_index = 0
    options[0] = NULL
    options[1] = NULL
    options[2] = NULL
    options[3] = NULL
    if authority is not None:
        if PROJ_VERSION_MAJOR < 8:
            warnings.warn("authority requires PROJ 8+")
        b_authority = cstrencode(f"AUTHORITY={authority}")
        options[options_index] = b_authority
        options_index += 1
    if accuracy is not None:
        if PROJ_VERSION_MAJOR < 8:
            warnings.warn("accuracy requires PROJ 8+")
        b_accuracy = cstrencode(f"ACCURACY={accuracy}")
        options[options_index] = b_accuracy
        options_index += 1
    if allow_ballpark is not None:
        if PROJ_VERSION_MAJOR < 8:
            warnings.warn("allow_ballpark requires PROJ 8+")
        if not allow_ballpark:
            options[options_index] = b"ALLOW_BALLPARK=NO"

    cdef PJ* transform = proj_create_crs_to_crs_from_pj(
        ctx,
        source_crs,
        target_crs,
        area,
        options,
    )
    proj_destroy(source_crs)
    proj_destroy(target_crs)
    return transform


cdef class PySimpleArray:
    cdef double* data
    cdef public Py_ssize_t len

    def __cinit__(self):
        self.data = NULL

    def __init__(self, Py_ssize_t arr_len):
        self.len = arr_len
        self.data = <double*> PyMem_Malloc(arr_len * sizeof(double))
        if self.data == NULL:
            raise MemoryError("error creating array for pyproj")

    def __dealloc__(self):
        PyMem_Free(self.data)
        self.data = NULL


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double simple_min(double* data, Py_ssize_t arr_len) nogil:
    cdef int iii = 0
    cdef double min_value = data[0]
    for iii in range(1, arr_len):
        if data[iii] < min_value:
            min_value = data[iii]
    return min_value


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double simple_max(double* data, Py_ssize_t arr_len) nogil:
    cdef int iii = 0
    cdef double max_value = data[0]
    for iii in range(1, arr_len):
        if (data[iii] > max_value or max_value == HUGE_VAL) and data[iii] != HUGE_VAL:
            max_value = data[iii]
    return max_value


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double antimeridian_min(double* data, Py_ssize_t arr_len) nogil:
    """
    Handles the case when longitude values cross the antimeridian
    when calculating the minumum.

    Note: The data array must be in a linear ring.

    Note: This requires a densified ring with at least 2 additional
          points per edge to correctly handle global extents.

    If only 1 additional point:

      |        |
      |RL--x0--|RL--
      |        |
    -180    180|-180

    If they are evenly spaced and it crosses the antimeridian:
    x0 - L = 180
    R - x0 = -180

    For example:
    Let R = -179.9, x0 = 0.1, L = -179.89
    x0 - L = 0.1 - -179.9 = 180
    R - x0 = -179.89 - 0.1 ~= -180
    This is the same in the case when it didn't cross the antimeridian.

    If you have 2 additional points:
      |            |
      |RL--x0--x1--|RL--
      |            |
    -180        180|-180

    If they are evenly spaced and it crosses the antimeridian:
    x0 - L = 120
    x1 - x0 = 120
    R - x1 = -240

    For example:
    Let R = -179.9, x0 = -59.9, x1 = 60.1 L = -179.89
    x0 - L = 59.9 - -179.9 = 120
    x1 - x0 = 60.1 - 59.9 = 120
    R - x1 = -179.89 - 60.1 ~= -240

    However, if they are evenly spaced and it didn't cross the antimeridian:
    x0 - L = 120
    x1 - x0 = 120
    R - x1 = 120

    From this, we have a delta that is guaranteed to be significantly
    large enough to tell the difference reguarless of the direction
    the antimeridian was crossed.

    However, even though the spacing was even in the source projection, it isn't
    guaranteed in the targed geographic projection. So, instead of 240, 200 is used
    as it significantly larger than 120 to be sure that the antimeridian was crossed
    but smalller than 240 to account for possible irregularities in distances
    when re-projecting. Also, 200 ensures latitudes are ignored for axis order handling.
    """
    cdef int iii = 0
    cdef int prev_iii = arr_len - 1
    cdef double positive_min = HUGE_VAL
    cdef double min_value = HUGE_VAL
    cdef double delta = 0
    cdef int crossed_meridian_count = 0
    cdef bint positive_meridian = False

    for iii in range(0, arr_len):
        prev_iii = iii - 1
        if prev_iii == -1:
            prev_iii = arr_len - 1
        # check if crossed meridian
        delta = data[prev_iii] - data[iii]
        # 180 -> -180
        if delta >= 200:
            if crossed_meridian_count == 0:
                positive_min = min_value
            crossed_meridian_count += 1
            positive_meridian = False
        # -180 -> 180
        elif delta <= -200:
            if crossed_meridian_count == 0:
                positive_min = data[iii]
            crossed_meridian_count += 1
            positive_meridian = True
        # positive meridian side min
        if positive_meridian and data[iii] < positive_min:
            positive_min = data[iii]
        # track genral min value
        if data[iii] < min_value:
            min_value = data[iii]
    if crossed_meridian_count == 2:
        return positive_min
    elif crossed_meridian_count == 4:
        # bounds extends beyond -180/180
        return -180
    return min_value


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double antimeridian_max(double* data, Py_ssize_t arr_len) nogil:
    """
    Handles the case when longitude values cross the antimeridian
    when calculating the minumum.

    Note: The data array must be in a linear ring.

    Note: This requires a densified ring with at least 2 additional
          points per edge to correctly handle global extents.

    See antimeridian_min docstring for reasoning.
    """
    cdef int iii = 0
    cdef int prev_iii = arr_len - 1
    cdef double negative_max = -HUGE_VAL
    cdef double max_value = -HUGE_VAL
    cdef double delta = 0
    cdef bint negative_meridian = False
    cdef int crossed_meridian_count = 0
    for iii in range(0, arr_len):
        prev_iii = iii - 1
        if prev_iii == -1:
            prev_iii = arr_len - 1
        # check if crossed meridian
        delta = data[prev_iii] - data[iii]
        # 180 -> -180
        if delta >= 200:
            if crossed_meridian_count == 0:
                negative_max = data[iii]
            crossed_meridian_count += 1
            negative_meridian = True
        # -180 -> 180
        elif delta <= -200:
            if crossed_meridian_count == 0:
                negative_max = max_value
            negative_meridian = False
            crossed_meridian_count += 1
        # negative meridian side max
        if (negative_meridian
            and (data[iii] > negative_max or negative_max == HUGE_VAL)
            and data[iii] != HUGE_VAL
        ):
            negative_max = data[iii]
        # track genral max value
        if (data[iii] > max_value or max_value == HUGE_VAL) and data[iii] != HUGE_VAL:
            max_value = data[iii]
    if crossed_meridian_count == 2:
        return negative_max
    elif crossed_meridian_count == 4:
        # bounds extends beyond -180/180
        return 180
    return max_value


cdef class _Transformer(Base):
    def __cinit__(self):
        self._area_of_use = None
        self.type_name = "Unknown Transformer"
        self._operations = None

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
        AreaOfUse:
            The area of use object with associated attributes.
        """
        if self._area_of_use is not None:
            return self._area_of_use
        self._area_of_use = create_area_of_use(self.context, self.projobj)
        return self._area_of_use

    @property
    def operations(self):
        """
        .. versionadded:: 2.4.0

        Tuple[CoordinateOperation]:
            The operations in a concatenated operation.
        """
        if self._operations is not None:
            return self._operations
        self._operations = _get_concatenated_operations(self.context, self.projobj)
        return self._operations

    @property
    def is_network_enabled(self):
        """
        .. versionadded:: 3.0.0

        bool:
            If the network is enabled.
        """
        return proj_context_is_network_enabled(self.context) == 1

    def to_proj4(self, version=ProjVersion.PROJ_5, pretty=False):
        """
        Convert the projection to a PROJ string.

        .. versionadded:: 3.1.0

        Parameters
        ----------
        version: pyproj.enums.ProjVersion
            The version of the PROJ string output.
            Default is :attr:`pyproj.enums.ProjVersion.PROJ_5`.
        pretty: bool
            If True, it will set the output to be a multiline string. Defaults to False.

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
        always_xy=False,
        area_of_interest=None,
        authority=None,
        accuracy=None,
        allow_ballpark=None,
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
            )
        finally:
            if pj_area_of_interest != NULL:
                proj_area_destroy(pj_area_of_interest)

        if transformer.projobj == NULL:
            raise ProjError("Error creating Transformer from CRS.")

        transformer._init_from_crs(always_xy)
        return transformer

    @staticmethod
    cdef _Transformer _from_pj(
        PJ_CONTEXT* context,
        PJ *transform_pj,
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

        transformer._init_from_crs(always_xy)
        return transformer

    @staticmethod
    def from_pipeline(const char *proj_pipeline):
        """
        Create Transformer from a PROJ pipeline string.
        """
        cdef _Transformer transformer = _Transformer()
        transformer.context = pyproj_context_create()

        auth_match = _AUTH_CODE_RE.match(pystrdecode(proj_pipeline.strip()))
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

    def _init_from_crs(self, always_xy):
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
                        f"transform error: {pyproj_errno_string(self.context, errno)}"
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
        array.array inseq,
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
                        f"itransform error: {pyproj_errno_string(self.context, errno)}"
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
        if self.id == "noop":
            return (left, bottom, right, top)

        if densify_pts < 0:
            raise ProjError("densify_pts must be positive")

        tmp_pj_direction = _PJ_DIRECTION_MAP[TransformDirection.create(direction)]
        cdef PJ_DIRECTION pj_direction = <PJ_DIRECTION>tmp_pj_direction

        cdef bint degree_output = proj_degree_output(self.projobj, pj_direction)
        cdef bint degree_input = proj_degree_input(self.projobj, pj_direction)
        if degree_output and densify_pts < 2:
            raise ProjError("densify_pts must be 2+ for degree output")

        cdef int side_pts = densify_pts + 1  # add one because we are densifying
        cdef Py_ssize_t boundary_len = side_pts * 4
        cdef PySimpleArray x_boundary_array = PySimpleArray(boundary_len)
        cdef PySimpleArray y_boundary_array = PySimpleArray(boundary_len)
        cdef double delta_x = 0
        cdef double delta_y = 0
        cdef int iii = 0

        with nogil:
            # degrees to radians
            if not radians and proj_angular_input(self.projobj, pj_direction):
                left *= _DG2RAD
                bottom *= _DG2RAD
                right *= _DG2RAD
                top *= _DG2RAD
            # radians to degrees
            elif radians and degree_input:
                left *= _RAD2DG
                bottom *= _RAD2DG
                right *= _RAD2DG
                top *= _RAD2DG

            if degree_input and right < left:
                # handle antimeridian
                delta_x = (right - left + 360.0) / side_pts
            else:
                delta_x = (right - left) / side_pts
            if degree_input and top < bottom:
                # handle antimeridian
                # depending on the axis order, longitude has the potential
                # to be on the y axis. It shouldn't reach here if it is latitude.
                delta_y = (top - bottom + 360.0) / side_pts
            else:
                delta_y = (top - bottom) / side_pts

            # build densified bounding box
            # Note: must be a linear ring for antimeridian logic
            for iii in range(side_pts):
                # left boundary
                y_boundary_array.data[iii] = top - iii * delta_y
                x_boundary_array.data[iii] = left
                # bottom boundary
                y_boundary_array.data[iii + side_pts] = bottom
                x_boundary_array.data[iii + side_pts] = left + iii * delta_x
                # right boundary
                y_boundary_array.data[iii + side_pts * 2] = bottom + iii * delta_y
                x_boundary_array.data[iii + side_pts * 2] = right
                # top boundary
                y_boundary_array.data[iii + side_pts * 3] = top
                x_boundary_array.data[iii + side_pts * 3] = right - iii * delta_x

            proj_errno_reset(self.projobj)
            proj_trans_generic(
                self.projobj,
                pj_direction,
                x_boundary_array.data, _DOUBLESIZE, x_boundary_array.len,
                y_boundary_array.data, _DOUBLESIZE, y_boundary_array.len,
                NULL, 0, 0,
                NULL, 0, 0,
            )
            errno = proj_errno(self.projobj)
            if errcheck and errno:
                with gil:
                    raise ProjError(
                        f"itransform error: {pyproj_errno_string(self.context, errno)}"
                    )
            elif errcheck:
                with gil:
                    if ProjError.internal_proj_error is not None:
                        raise ProjError("itransform error")

            if degree_output:
                left = antimeridian_min(x_boundary_array.data, x_boundary_array.len)
                right = antimeridian_max(x_boundary_array.data, x_boundary_array.len)
                # depending on the axis order, longitude has the potential
                # to be on the y axis. It shouldn't cause troubles if it is latitude.
                bottom = antimeridian_min(y_boundary_array.data, y_boundary_array.len)
                top = antimeridian_max(y_boundary_array.data, y_boundary_array.len)
            else:
                left = simple_min(x_boundary_array.data, x_boundary_array.len)
                right = simple_max(x_boundary_array.data, x_boundary_array.len)
                bottom = simple_min(y_boundary_array.data, y_boundary_array.len)
                top = simple_max(y_boundary_array.data, y_boundary_array.len)
            # radians to degrees
            if not radians and proj_angular_output(self.projobj, pj_direction):
                left *= _RAD2DG
                bottom *= _RAD2DG
                right *= _RAD2DG
                top *= _RAD2DG
            # degrees to radians
            elif radians and degree_output:
                left *= _DG2RAD
                bottom *= _DG2RAD
                right *= _DG2RAD
                top *= _DG2RAD

        ProjError.clear()
        return left, bottom, right, top

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
                            f"proj error: {pyproj_errno_string(self.context, errno)}"
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
