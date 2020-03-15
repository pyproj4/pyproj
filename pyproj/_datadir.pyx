import os

from libc.stdlib cimport malloc, free

from pyproj.compat import cstrencode, pystrdecode
from pyproj.datadir import get_data_dir
from pyproj.exceptions import ProjError, DataDirError


cdef void pyproj_log_function(void *user_data, int level, const char *error_msg):
    """
    Log function for catching PROJ errors.
    """
    if level == PJ_LOG_ERROR:
        ProjError.internal_proj_error = pystrdecode(error_msg)


cdef void set_context_data_dir(PJ_CONTEXT* context) except *:
    """
    Setup the data directory for the context for pyproj
    """
    data_dir_list = get_data_dir().split(os.pathsep)
    cdef char **c_data_dir = <char **>malloc(len(data_dir_list) * sizeof(char*))
    try:
        for iii in range(len(data_dir_list)):
            b_data_dir = cstrencode(data_dir_list[iii])
            c_data_dir[iii] = b_data_dir
        proj_context_set_search_paths(context, len(data_dir_list), c_data_dir)
    finally:
        free(c_data_dir)


cdef void pyproj_context_initialize(
    PJ_CONTEXT* context,
    bint free_context_on_error,
) except *:
    """
    Setup the context for pyproj
    """
    proj_log_func(context, NULL, pyproj_log_function)
    proj_context_use_proj4_init_rules(context, 1)
    proj_context_set_autoclose_database(context, 1)
    try:
        set_context_data_dir(context)
    except DataDirError:
        if free_context_on_error and context != NULL:
            proj_context_destroy(context)
        raise


def pyproj_global_context_initialize():
    proj_log_func(NULL, NULL, pyproj_log_function)
    set_context_data_dir(NULL)
