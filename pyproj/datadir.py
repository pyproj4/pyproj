"""
Module for managing the PROJ data directory.
"""
import os
import sys
from distutils.spawn import find_executable
from pathlib import Path
from typing import Union

from pyproj._datadir import (  # noqa: F401
    _global_context_set_data_dir,
    get_user_data_dir,
)
from pyproj.exceptions import DataDirError

_USER_PROJ_DATA = None
_VALIDATED_PROJ_DATA = None


def set_data_dir(proj_data_dir: Union[str, Path]) -> None:
    """
    Set the data directory for PROJ to use.

    Parameters
    ----------
    proj_data_dir: Union[str, Path]
        The path to the PROJ data directory.
    """
    global _USER_PROJ_DATA
    global _VALIDATED_PROJ_DATA
    _USER_PROJ_DATA = str(proj_data_dir)
    # set to none to re-validate
    _VALIDATED_PROJ_DATA = None
    # need to reset the global PROJ context
    # to prevent core dumping if the data directory
    # is not found.
    _global_context_set_data_dir()


def append_data_dir(proj_data_dir: Union[str, Path]) -> None:
    """
    Add an additional data directory for PROJ to use.

    Parameters
    ----------
    proj_data_dir: Union[str, Path]
        The path to the PROJ data directory.
    """
    set_data_dir(os.pathsep.join([get_data_dir(), str(proj_data_dir)]))


def get_data_dir() -> str:
    """
    The order of preference for the data directory is:

    1. The one set by pyproj.datadir.set_data_dir (if exists & valid)
    2. The internal proj directory (if exists & valid)
    3. The directory in PROJ_LIB (if exists & valid)
    4. The directory on sys.prefix (if exists & valid)
    5. The directory on the PATH (if exists & valid)

    Returns
    -------
    str:
        The valid data directory.

    """
    # to avoid re-validating
    global _VALIDATED_PROJ_DATA
    if _VALIDATED_PROJ_DATA is not None:
        return _VALIDATED_PROJ_DATA
    global _USER_PROJ_DATA
    internal_datadir = Path(__file__).absolute().parent / "proj_dir" / "share" / "proj"
    proj_lib_dirs = os.environ.get("PROJ_LIB", "")
    prefix_datadir = Path(sys.prefix, "share", "proj")

    def valid_data_dir(potential_data_dir):
        if (
            potential_data_dir is not None
            and Path(potential_data_dir, "proj.db").exists()
        ):
            return True
        return False

    def valid_data_dirs(potential_data_dirs):
        if potential_data_dirs is None:
            return False
        for proj_data_dir in potential_data_dirs.split(os.pathsep):
            if valid_data_dir(proj_data_dir):
                return True
        return None

    if valid_data_dirs(_USER_PROJ_DATA):
        _VALIDATED_PROJ_DATA = _USER_PROJ_DATA
    elif valid_data_dir(internal_datadir):
        _VALIDATED_PROJ_DATA = str(internal_datadir)
    elif valid_data_dirs(proj_lib_dirs):
        _VALIDATED_PROJ_DATA = proj_lib_dirs
    elif valid_data_dir(prefix_datadir):
        _VALIDATED_PROJ_DATA = str(prefix_datadir)
    else:
        proj_exe = find_executable("proj")
        if proj_exe is not None:
            system_proj_dir = Path(proj_exe).parent.parent / "share" / "proj"
            if valid_data_dir(system_proj_dir):
                _VALIDATED_PROJ_DATA = str(system_proj_dir)

    if _VALIDATED_PROJ_DATA is None:
        raise DataDirError(
            "Valid PROJ data directory not found. "
            "Either set the path using the environmental variable PROJ_LIB or "
            "with `pyproj.datadir.set_data_dir`."
        )
    return _VALIDATED_PROJ_DATA
