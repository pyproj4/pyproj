import os
import warnings
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
    # the first path will always have the database
    b_database_path = cstrencode(os.path.join(data_dir_list[0], "proj.db"))
    cdef const char* c_database_path = b_database_path
    if not proj_context_set_database_path(context, c_database_path, NULL, NULL):
        warnings.warn("pyproj unable to set database path.")
    data_dir_list.append(get_user_data_dir())
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
    network=None,
) except *:
    """
    Setup the context for pyproj
    """
    proj_log_func(context, NULL, pyproj_log_function)
    proj_context_use_proj4_init_rules(context, 1)
    proj_context_set_autoclose_database(context, 1)
    if network is not None:
        enabled = proj_context_set_enable_network(context, bool(network))
        if network and not enabled:
            warnings.warn("PROJ network cannot be enabled.")
    try:
        set_context_data_dir(context)
    except DataDirError:
        if free_context_on_error and context != NULL:
            proj_context_destroy(context)
        raise


def pyproj_global_context_initialize():
    proj_log_func(NULL, NULL, pyproj_log_function)
    set_context_data_dir(NULL)


def get_user_data_dir(bint create: bool = False) -> str:
    """
    Parameters
    ----------
    create: bool, optional
        If True, it will create the directory if it does not already exist.
        Default is False.

    Returns
    -------
    str:
        The user writable data directory.
    """
    return pystrdecode(proj_context_get_user_writable_directory(NULL, create))
