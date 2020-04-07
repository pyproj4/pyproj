import os
from pathlib import Path

from pyproj.datadir import get_data_dir


def grids_available(*grid_names):
    """
    Check if the grids are available
    """
    if os.environ.get("PROJ_NETWORK") == "ON":
        return True
    for grid_name in grid_names:
        if Path(get_data_dir(), grid_name).exists():
            return True
    return False
