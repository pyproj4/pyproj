import os
import warnings
from distutils.util import strtobool

from libc.stdlib cimport free, malloc

from pyproj.compat import cstrencode, pystrdecode
from pyproj.exceptions import DataDirError, ProjError

# default to False is the safest mode
# as it supports multithreading
_USE_GLOBAL_CONTEXT = strtobool(os.environ.get("PYPROJ_GLOBAL_CONTEXT", "OFF"))
# static user data directory to prevent core dumping
# see: https://github.com/pyproj4/pyproj/issues/678
cdef const char* _USER_DATA_DIR = proj_context_get_user_writable_directory(NULL, False)


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

    .. note:: You can change the network settings with
              :func:`pyproj.set_global_context_network`.

    Parameters
    ----------
    active: bool, optional
        If True, it activates the use of the global context. If False,
        the use of the global context is deactivated. If None, it uses
        the environment variable PYPROJ_GLOBAL_CONTEXT and defaults
        to False if it is not found. The default is None.
    """
    global _USE_GLOBAL_CONTEXT
    if active is None:
        active = strtobool(os.environ.get("PYPROJ_GLOBAL_CONTEXT", "OFF"))
    _USE_GLOBAL_CONTEXT = bool(active)
    proj_context_set_autoclose_database(NULL, not _USE_GLOBAL_CONTEXT)


def set_global_context_network(active=None):
    """
    .. versionadded:: 3.0.0

    Manages whether PROJ network is enabled on the global context.

    .. note:: You can activate the global context with
              :func:`pyproj.set_use_global_context` or with
              the PYPROJ_GLOBAL_CONTEXT environment variable.

    Parameters
    ----------
    active: bool, optional
        Default is None, which uses the system defaults for networking.
        If True, it will force the use of network for grids regardless of
        any other network setting. If False, it will force disable use of
        network for grids regardless of any other network setting.
    """
    if active is None:
        # in the case of the global context, need to reset network
        # setting based on the environment variable every time if None
        # because it could have been changed by the user previously
        active = strtobool(os.environ.get("PROJ_NETWORK", "OFF"))
    pyproj_context_set_enable_network(NULL, bool(active))


def is_global_context_network_enabled():
    """
    .. versionadded:: 3.0.0

    .. note:: You can activate the global context with
              :func:`pyproj.set_use_global_context` or with
              the PYPROJ_GLOBAL_CONTEXT environment variable.

    bool:
        If the network is enabled on the global context.
    """
    return proj_context_is_network_enabled(NULL) == 1


def get_user_data_dir(create=False):
    """
    .. versionadded:: 3.0.0

    Get the PROJ user writable directory for datumgrid files.

    This is where grids will be downloaded when
    `PROJ network <https://proj.org/usage/network.html>`__ capabilities
    are enabled. It is also the default download location for the
    `projsync <https://proj.org/apps/projsync.html>`__ command line program.

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
    return pystrdecode(proj_context_get_user_writable_directory(NULL, bool(create)))


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
    from pyproj.datadir import get_data_dir

    data_dir_list = get_data_dir().split(os.pathsep)
    # the first path will always have the database
    b_database_path = cstrencode(os.path.join(data_dir_list[0], "proj.db"))
    cdef const char* c_database_path = b_database_path
    if not proj_context_set_database_path(context, c_database_path, NULL, NULL):
        warnings.warn("pyproj unable to set database path.")
    cdef int dir_list_len = len(data_dir_list)
    cdef const char **c_data_dir = <const char **>malloc(
        (dir_list_len + 1) * sizeof(const char*)
    )
    try:
        for iii in range(dir_list_len):
            b_data_dir = cstrencode(data_dir_list[iii])
            c_data_dir[iii] = b_data_dir
        c_data_dir[dir_list_len] = _USER_DATA_DIR
        proj_context_set_search_paths(context, dir_list_len + 1, c_data_dir)
    finally:
        free(c_data_dir)


cdef void pyproj_context_set_enable_network(
    PJ_CONTEXT* context,
    network=None,
) except *:
    if network is not None:
        enabled = proj_context_set_enable_network(context, bool(network))
        if network and not enabled:
            warnings.warn("PROJ network cannot be enabled.")


cdef void pyproj_context_initialize(
    PJ_CONTEXT* context,
    network=None,
    bint autoclose_database=True,
) except *:
    """
    Setup the context for pyproj
    """
    proj_log_func(context, NULL, pyproj_log_function)
    proj_context_use_proj4_init_rules(context, 1)
    if autoclose_database:
        proj_context_set_autoclose_database(context, 1)
    pyproj_context_set_enable_network(context, network=network)
    set_context_data_dir(context)


cdef PJ_CONTEXT* pyproj_context_create(
    network=None,
) except *:
    """
    Create and initialize the context(s) for pyproj.
    This also manages whether the global context is used.
    """
    global _USE_GLOBAL_CONTEXT
    if _USE_GLOBAL_CONTEXT:
        return NULL
    cdef PJ_CONTEXT* context = proj_context_create()
    pyproj_context_set_enable_network(context, network=network)
    return context


def _pyproj_global_context_initialize():
    global _USE_GLOBAL_CONTEXT
    pyproj_context_initialize(
        NULL,
        network=None,
        autoclose_database=not _USE_GLOBAL_CONTEXT
    )


def _global_context_set_data_dir():
    set_context_data_dir(NULL)
