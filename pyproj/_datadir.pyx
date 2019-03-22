
from libc.stdlib cimport malloc, free

from pyproj.compat import cstrencode
from pyproj.datadir import get_data_dir


cdef PJ_CONTEXT* get_pyproj_context():
    data_dir = get_data_dir()
    data_dir_list = data_dir.split(";")
    cdef PJ_CONTEXT* pyproj_context = NULL
    cdef char **c_data_dir = <char **>malloc(len(data_dir_list) * sizeof(char*))
    try:
        pyproj_context = proj_context_create()
        for iii in range(len(data_dir_list)):
            b_data_dir = cstrencode(data_dir_list[iii])
            c_data_dir[iii] = b_data_dir
        proj_context_set_search_paths(pyproj_context, len(data_dir_list), c_data_dir)
        proj_context_use_proj4_init_rules(pyproj_context, 1)
    except:
        if pyproj_context != NULL:
            proj_context_destroy(pyproj_context)
        raise
    finally:
        free(c_data_dir)
    return pyproj_context
