include "proj.pxi"

from collections import namedtuple
from enum import IntEnum
import warnings

from pyproj.compat import cstrencode, pystrdecode
from pyproj.enums import PJType
from pyproj._datadir cimport pyproj_context_create


def get_proj_operations_map():
    """
    Returns
    -------
    dict:
        Operations supported by PROJ.
    """
    cdef const PJ_OPERATIONS *proj_operations = proj_list_operations()
    cdef int iii = 0
    operations_map = {}
    while proj_operations[iii].id != NULL:
        operations_map[pystrdecode(proj_operations[iii].id)] = \
            pystrdecode(proj_operations[iii].descr[0]).split("\n\t")[0]
        iii += 1
    return operations_map


def get_ellps_map():
    """
    Returns
    -------
    dict:
        Ellipsoids supported by PROJ.
    """
    cdef const PJ_ELLPS *proj_ellps = proj_list_ellps()
    cdef int iii = 0
    ellps_map = {}
    while proj_ellps[iii].id != NULL:
        major_key, major_val = pystrdecode(proj_ellps[iii].major).split("=")
        ell_key, ell_val = pystrdecode(proj_ellps[iii].ell).split("=")
        ellps_map[pystrdecode(proj_ellps[iii].id)] = {
            major_key: float(major_val),
            ell_key: float(ell_val),
            "description": pystrdecode(proj_ellps[iii].name)
        }
        iii += 1
    return ellps_map


def get_prime_meridians_map():
    """
    Returns
    -------
    dict:
        Prime Meridians supported by PROJ.
    """
    cdef const PJ_PRIME_MERIDIANS *prime_meridians = proj_list_prime_meridians()
    cdef int iii = 0
    prime_meridians_map = {}
    while prime_meridians[iii].id != NULL:
        prime_meridians_map[pystrdecode(prime_meridians[iii].id)] = \
            pystrdecode(prime_meridians[iii].defn)
        iii += 1
    return prime_meridians_map


def get_authorities():
    """
    .. versionadded:: 2.4.0

    Returns
    -------
    List[str]:
        Authorities in PROJ database.
    """
    cdef PJ_CONTEXT* context = pyproj_context_create()
    cdef PROJ_STRING_LIST proj_auth_list = proj_get_authorities_from_database(context)
    if proj_auth_list == NULL:
        proj_context_destroy(context)
        return []
    cdef int iii = 0
    try:
        auth_list = []
        while proj_auth_list[iii] != NULL:
            auth_list.append(pystrdecode(proj_auth_list[iii]))
            iii += 1
    finally:
        proj_context_destroy(context)
        proj_string_list_destroy(proj_auth_list)
    return auth_list


PJ_TYPE_MAP = {
    PJType.UNKNOWN: PJ_TYPE_UNKNOWN,
    PJType.ELLIPSOID: PJ_TYPE_ELLIPSOID,
    PJType.PRIME_MERIDIAN: PJ_TYPE_PRIME_MERIDIAN,
    PJType.GEODETIC_REFERENCE_FRAME: PJ_TYPE_GEODETIC_REFERENCE_FRAME,
    PJType.DYNAMIC_GEODETIC_REFERENCE_FRAME: PJ_TYPE_DYNAMIC_GEODETIC_REFERENCE_FRAME,
    PJType.VERTICAL_REFERENCE_FRAME: PJ_TYPE_VERTICAL_REFERENCE_FRAME,
    PJType.DYNAMIC_VERTICAL_REFERENCE_FRAME: PJ_TYPE_DYNAMIC_VERTICAL_REFERENCE_FRAME,
    PJType.DATUM_ENSEMBLE: PJ_TYPE_DATUM_ENSEMBLE,
    PJType.CRS: PJ_TYPE_CRS,
    PJType.GEODETIC_CRS: PJ_TYPE_GEODETIC_CRS,
    PJType.GEOCENTRIC_CRS: PJ_TYPE_GEOCENTRIC_CRS,
    PJType.GEOGRAPHIC_CRS: PJ_TYPE_GEOGRAPHIC_CRS,
    PJType.GEOGRAPHIC_2D_CRS: PJ_TYPE_GEOGRAPHIC_2D_CRS,
    PJType.GEOGRAPHIC_3D_CRS: PJ_TYPE_GEOGRAPHIC_3D_CRS,
    PJType.VERTICAL_CRS: PJ_TYPE_VERTICAL_CRS,
    PJType.PROJECTED_CRS: PJ_TYPE_PROJECTED_CRS,
    PJType.COMPOUND_CRS: PJ_TYPE_COMPOUND_CRS,
    PJType.TEMPORAL_CRS: PJ_TYPE_TEMPORAL_CRS,
    PJType.ENGINEERING_CRS: PJ_TYPE_ENGINEERING_CRS,
    PJType.BOUND_CRS: PJ_TYPE_BOUND_CRS,
    PJType.OTHER_CRS: PJ_TYPE_OTHER_CRS,
    PJType.CONVERSION: PJ_TYPE_CONVERSION,
    PJType.TRANSFORMATION: PJ_TYPE_TRANSFORMATION,
    PJType.CONCATENATED_OPERATION: PJ_TYPE_CONCATENATED_OPERATION,
    PJType.OTHER_COORDINATE_OPERATION: PJ_TYPE_OTHER_COORDINATE_OPERATION,
}


def get_codes(auth_name, pj_type, allow_deprecated=False):
    """
    .. versionadded:: 2.4.0

    Parameters
    ----------
    auth_name: str
        The name of the authority.
    pj_type: pyproj.enums.PJType
        The type of object to get the authorities.
    allow_deprecated: bool, optional
        Allow a deprecated code in the return.

    Returns
    -------
    List[str]:
        Codes associated with authorities in PROJ database.
    """
    cdef PJ_CONTEXT* context = NULL
    cdef PJ_TYPE cpj_type = PJ_TYPE_MAP[PJType.create(pj_type)]
    cdef PROJ_STRING_LIST proj_code_list = NULL
    try:
        context = pyproj_context_create()
        proj_code_list = proj_get_codes_from_database(
            context,
            cstrencode(auth_name),
            cpj_type,
            allow_deprecated,
        )
    finally:
        proj_context_destroy(context)
    if proj_code_list == NULL:
        return []
    cdef int iii = 0
    try:
        code_list = []
        while proj_code_list[iii] != NULL:
            code_list.append(pystrdecode(proj_code_list[iii]))
            iii += 1
    finally:
        proj_string_list_destroy(proj_code_list)
    return code_list


Unit = namedtuple(
    "Unit",
    [
        "auth_name",
        "code",
        "name",
        "category",
        "conv_factor",
        "proj_short_name",
        "deprecated",
    ],
)
Unit.__doc__ = """
.. versionadded:: 3.0.0

Parameters
----------
auth_name: str
    Authority name.
code: str
    Object code.
name: str
    Object name. For example "metre", "US survey foot", etc.
category: str
    Category of the unit: one of "linear", "linear_per_time", "angular",
    "angular_per_time", "scale", "scale_per_time" or "time".
conv_factor: float
    Conversion factor to apply to transform from that unit to the
    corresponding SI unit (metre for "linear", radian for "angular", etc.).
    It might be 0 in some cases to indicate no known conversion factor.
proj_short_name: Optional[str]
    PROJ short name, like "m", "ft", "us-ft", etc... Might be None.
deprecated: bool
    Whether the object is deprecated.
"""


def get_units_map(auth_name=None, category=None, allow_deprecated=False):
    """
    Get the units available in the PROJ database.

    Parameters
    ----------
    auth_name: str, optional
        The authority name to filter by (e.g. EPSG, PROJ). Default is all.
    category: str, optional
        Category of the unit: one of "linear", "linear_per_time", "angular",
        "angular_per_time", "scale", "scale_per_time" or "time". Default is all.
    allow_deprecated: bool, optional
        Whether or not to allow deprecated units. Default is False.

    Returns
    -------
    Dict[str, Unit]
    """
    cdef const char* c_auth_name = NULL
    cdef const char* c_category = NULL
    if auth_name is not None:
        auth_name = cstrencode(auth_name)
        c_auth_name = auth_name
    if category is not None:
        category = cstrencode(category)
        c_category = category

    cdef int num_units = 0
    cdef PJ_CONTEXT* context = pyproj_context_create()
    cdef PROJ_UNIT_INFO** db_unit_list = proj_get_units_from_database(
        context,
        c_auth_name,
        c_category,
        bool(allow_deprecated),
        &num_units,
    )
    units_map = {}
    try:
        for iii in range(num_units):
            proj_short_name = None
            if db_unit_list[iii].proj_short_name != NULL:
                proj_short_name = pystrdecode(db_unit_list[iii].proj_short_name)
            name = pystrdecode(db_unit_list[iii].name)
            units_map[name] = Unit(
                auth_name=pystrdecode(db_unit_list[iii].auth_name),
                code=pystrdecode(db_unit_list[iii].code),
                name=name,
                category=pystrdecode(db_unit_list[iii].category),
                conv_factor=db_unit_list[iii].conv_factor,
                proj_short_name=proj_short_name,
                deprecated=bool(db_unit_list[iii].deprecated),
            )
    finally:
        proj_unit_list_destroy(db_unit_list)
        proj_context_destroy(context)
    return units_map
