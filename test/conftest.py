import os
from pathlib import Path

from pyproj.datadir import get_data_dir, get_user_data_dir


def grids_available(*grid_names, check_network=True, check_all=False):
    """
    Check if the grids are available
    """
    if check_network and os.environ.get("PROJ_NETWORK") == "ON":
        return True
    available = [
        (
            Path(get_data_dir(), grid_name).exists()
            or Path(get_user_data_dir(), grid_name).exists()
        )
        for grid_name in grid_names
    ]
    if check_all:
        return all(available)
    return any(available)
