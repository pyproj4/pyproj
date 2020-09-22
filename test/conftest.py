import os
from contextlib import contextmanager
from pathlib import Path

import pyproj
from pyproj.datadir import get_data_dir, get_user_data_dir, set_data_dir


def unset_data_dir():
    pyproj.datadir._USER_PROJ_DATA = None
    pyproj.datadir._VALIDATED_PROJ_DATA = None


@contextmanager
def proj_network_env():
    """
    Ensure global context network settings reset
    """
    network = pyproj.network.is_network_enabled()
    try:
        yield
    finally:
        pyproj.network.set_network_enabled(network)


@contextmanager
def proj_env():
    """
    Ensure environment variable the same at the end of the test.
    """
    unset_data_dir()
    try:
        yield
    finally:
        # make sure the data dir is cleared
        unset_data_dir()
        # reset back to the original path
        set_data_dir(get_data_dir())


@contextmanager
def tmp_chdir(new_dir):
    """
    This temporarily changes directories when running the tests.
    Useful for when testing wheels in the pyproj directory
    when pyproj has not been build and prevents conflicts.
    """
    curdir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(curdir)


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
