import logging
import os
import warnings

from libc.stdlib cimport free, malloc

from pyproj._compat cimport cstrencode

from pyproj.exceptions import DataDirError
from pyproj.utils import strtobool

# for logging the internal PROJ messages
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
_LOGGER = logging.getLogger("pyproj")
_LOGGER.addHandler(logging.NullHandler())
# default to False is the safest mode
# as it supports multithreading
_USE_GLOBAL_CONTEXT = strtobool(os.environ.get("PYPROJ_GLOBAL_CONTEXT", "OFF"))
# static user data directory to prevent core dumping
# see: https://github.com/pyproj4/pyproj/issues/678
cdef const char* _USER_DATA_DIR = proj_context_get_user_writable_directory(NULL, False)
# Store the message from any internal PROJ errors
cdef str _INTERNAL_PROJ_ERROR = None

def set_use_global_context(active=None):
    """
    .. versionadded:: 3.0.0

    Activates the usage of the global context. Using this
    option can enhance the performance of initializing objects
    in single-threaded applications.

    .. warning:: The global context is not thread safe.
    .. warning:: The global context maintains a connection to the database
                 through the duration of each python session and is closed
                 once the program terminates.

    .. note:: To modify network settings see: :ref:`network`.

    Parameters
    ----------
    active: bool, optional
        If True, it activates the use of the global context. If False,
        the use of the global context is deactivated. If None, it uses
        the environment variable PYPROJ_GLOBAL_CONTEXT and defaults
        to False if it is not found.
    """
    global _USE_GLOBAL_CONTEXT
    if active is None:
        active = strtobool(os.environ.get("PYPROJ_GLOBAL_CONTEXT", "OFF"))
    _USE_GLOBAL_CONTEXT = bool(active)


def get_user_data_dir(create=False):
    """
    .. versionadded:: 3.0.0

    Get the PROJ user writable directory for datumgrid files.

    See: :c:func:`proj_context_get_user_writable_directory`

    This is where grids will be downloaded when
    :ref:`PROJ network <network>` capabilities
    are enabled. It is also the default download location for the
    :ref:`projsync` command line program.

    Parameters
    ----------
    create: bool, default=False
        If True, it will create the directory if it does not already exist.

    Returns
    -------
    str:
        The user writable data directory.
    """
    return proj_context_get_user_writable_directory(
        PYPROJ_GLOBAL_CONTEXT, bool(create)
    )


cpdef str _get_proj_error():
    """
    Get the internal PROJ error message. Returns None if no error was set.
    """
    return _INTERNAL_PROJ_ERROR


cpdef void _clear_proj_error():
    """
    Clear the internal PROJ error message.
    """
    global _INTERNAL_PROJ_ERROR
    _INTERNAL_PROJ_ERROR = None


cdef void pyproj_log_function(void *user_data, int level, const char *error_msg) nogil:
    """
    Log function for catching PROJ errors.
    """
    # from pyproj perspective, everything from PROJ is for debugging.
    # The verbosity should be managed via the
    # PROJ_DEBUG environment variable.
    if level == PJ_LOG_ERROR:
        with gil:
            global _INTERNAL_PROJ_ERROR
            _INTERNAL_PROJ_ERROR = error_msg
            _LOGGER.debug(f"PROJ_ERROR: {_INTERNAL_PROJ_ERROR}")
    elif level == PJ_LOG_DEBUG:
        with gil:
            _LOGGER.debug(f"PROJ_DEBUG: {error_msg}")
    elif level == PJ_LOG_TRACE:
        with gil:
            _LOGGER.debug(f"PROJ_TRACE: {error_msg}")


cdef void set_context_data_dir(PJ_CONTEXT* context) except *:
    """
    Setup the data directory for the context for pyproj
    """
    from pyproj.datadir import get_data_dir

    data_dir_list = get_data_dir().split(os.pathsep)
    # the first path will always have the database
    cdef bytes b_database_path = cstrencode(os.path.join(data_dir_list[0], "proj.db"))
    cdef const char* c_database_path = b_database_path
    if not proj_context_set_database_path(context, c_database_path, NULL, NULL):
        warnings.warn("pyproj unable to set database path.")
    cdef int dir_list_len = len(data_dir_list)
    cdef const char **c_data_dir = <const char **>malloc(
        (dir_list_len + 1) * sizeof(const char*)
    )
    cdef bytes b_data_dir
    try:
        for iii in range(dir_list_len):
            b_data_dir = cstrencode(data_dir_list[iii])
            c_data_dir[iii] = b_data_dir
        c_data_dir[dir_list_len] = _USER_DATA_DIR
        proj_context_set_search_paths(context, dir_list_len + 1, c_data_dir)
    finally:
        free(c_data_dir)


cdef void pyproj_context_initialize(PJ_CONTEXT* context) except *:
    """
    Setup the context for pyproj
    """
    proj_log_func(context, NULL, pyproj_log_function)
    proj_context_use_proj4_init_rules(context, 1)
    set_context_data_dir(context)


cdef class ContextManager:
    """
    The only purpose of this class is
    to ensure the context is cleaned up properly.
    """
    cdef PJ_CONTEXT* context

    def __cinit__(self):
        self.context = NULL

    def __dealloc__(self):
        if self.context != NULL:
            proj_context_destroy(self.context)

    @staticmethod
    cdef create(PJ_CONTEXT* context):
        cdef ContextManager context_manager = ContextManager()
        context_manager.context = context
        return context_manager


# Different libraries that modify the PROJ global context will influence
# each other without realizing it. Due to this, pyproj is creating it's own
# global context so that it doesn't bother other libraries and is insulated
# against possible external changes made to the PROJ global context.
# See: https://github.com/pyproj4/pyproj/issues/722
cdef PJ_CONTEXT* PYPROJ_GLOBAL_CONTEXT = proj_context_create()
cdef ContextManager CONTEXT_MANAGER = ContextManager.create(PYPROJ_GLOBAL_CONTEXT)


cdef PJ_CONTEXT* pyproj_context_create() except *:
    """
    Create and initialize the context(s) for pyproj.
    This also manages whether the global context is used.
    """
    if _USE_GLOBAL_CONTEXT:
        return PYPROJ_GLOBAL_CONTEXT
    return proj_context_clone(PYPROJ_GLOBAL_CONTEXT)

cdef void pyproj_context_destroy(PJ_CONTEXT* context) except *:
    """
    Destroy context only if not the global context
    """
    if context != PYPROJ_GLOBAL_CONTEXT:
        proj_context_destroy(context)


cpdef _pyproj_global_context_initialize():
    pyproj_context_initialize(PYPROJ_GLOBAL_CONTEXT)


cpdef _global_context_set_data_dir():
    set_context_data_dir(PYPROJ_GLOBAL_CONTEXT)
