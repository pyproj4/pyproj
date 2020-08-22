include "proj.pxi"

from pyproj.compat import cstrencode


def _set_ca_bundle_path(ca_bundle_path):
    """
    Sets the path to the CA Bundle used by the `curl`
    built into PROJ.

    Parameters
    ----------
    ca_bundle_path: str
        The path to the CA Bundle.
    """
    proj_context_set_ca_bundle_path(NULL, cstrencode(ca_bundle_path))
