"""
Set the datadir path to the local data directory
"""
import os

if "PROJ_LIB" not in os.environ:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pyproj_datadir = os.path.join(base_dir, "proj_dir", "share", "proj")
    if not os.path.exists(pyproj_datadir):
        pyproj_datadir = os.path.join(base_dir, "proj_dir", "share")
    if not os.path.exists(pyproj_datadir):
        raise RuntimeError("PROJ_LIB directory not found. Please set PROJ_LIB.")
    os.environ["PROJ_LIB"] = pyproj_datadir
else:
    pyproj_datadir = os.environ["PROJ_LIB"]
