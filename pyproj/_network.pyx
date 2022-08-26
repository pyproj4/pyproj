include "proj.pxi"

import os

from pyproj.utils import strtobool

from pyproj._compat cimport cstrencode
from pyproj._datadir cimport PYPROJ_GLOBAL_CONTEXT


def _set_ca_bundle_path(str ca_bundle_path):
    """
    Sets the path to the CA Bundle used by the `curl`
    built into PROJ.

    Parameters
    ----------
    ca_bundle_path: str
        The path to the CA Bundle.
    """
    proj_context_set_ca_bundle_path(PYPROJ_GLOBAL_CONTEXT, cstrencode(ca_bundle_path))


def set_network_enabled(active=None):
    """
    .. versionadded:: 3.0.0

    Set whether PROJ network is enabled by default. This has the same
    behavior as the `PROJ_NETWORK` environment variable.

    See: :c:func:`proj_context_set_enable_network`

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
    proj_context_set_enable_network(PYPROJ_GLOBAL_CONTEXT, bool(active))


def is_network_enabled():
    """
    .. versionadded:: 3.0.0

    See: :c:func:`proj_context_is_network_enabled`

    Returns
    -------
    bool:
        If PROJ network is enabled by default.
    """
    return proj_context_is_network_enabled(PYPROJ_GLOBAL_CONTEXT) == 1
