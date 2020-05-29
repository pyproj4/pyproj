include "proj.pxi"

from pyproj.compat import pystrdecode


def get_proj_endpoint() -> str:
    """
    Returns
    -------
    str:
        URL of the endpoint where PROJ grids are stored.
    """
    return pystrdecode(proj_context_get_url_endpoint(NULL))
