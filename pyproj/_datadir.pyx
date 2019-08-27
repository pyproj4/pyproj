import os

from libc.stdlib cimport malloc, free

from pyproj.compat import cstrencode, pystrdecode
from pyproj.datadir import get_data_dir
from pyproj.exceptions import ProjError

cdef void pyproj_log_function(void *user_data, int level, const char *error_msg):
    """
    Log function for catching PROJ errors.
    """
    if level == PJ_LOG_ERROR:
        ProjError.internal_proj_error = pystrdecode(error_msg)

cdef class ContextManager:
    def __cinit__(self):
        self.context = NULL

    def __dealloc__(self):
        if self.context != NULL:
            proj_context_destroy(self.context)
            self.context = NULL

    def __init__(self, global_context=False):
        """
        Parameters
        ----------
        global_context: bool, optional
            If True, it will modify the global PROJ context. Default is False.
        """
        if not global_context:
            self.context = proj_context_create()
        proj_log_func(self.context, NULL, pyproj_log_function)
        self.set_search_paths()
        proj_context_use_proj4_init_rules(self.context, 1)
        proj_context_set_autoclose_database(self.context, 1)

    def set_search_paths(self):
        """
        This method sets the search paths
        based on pyproj.datadir.get_data_dir()
        """
        data_dir_list = get_data_dir().split(os.pathsep)
        cdef char **c_data_dir = <char **>malloc(len(data_dir_list) * sizeof(char*))
        try:
            for iii in range(len(data_dir_list)):
                b_data_dir = cstrencode(data_dir_list[iii])
                c_data_dir[iii] = b_data_dir
            proj_context_set_search_paths(self.context, len(data_dir_list), c_data_dir)
        finally:
            free(c_data_dir)
