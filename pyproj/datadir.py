"""
Set the datadir path to the local data directory
"""
import os

if "PROJ_DATA" not in os.environ:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pyproj_datadir = os.path.join(base_dir, "proj_dir", "share", "proj")
    if not os.path.exists(pyproj_datadir):
        pyproj_datadir = os.path.join(base_dir, "proj_dir", "share")
    if not os.path.exists(pyproj_datadir):
        raise RuntimeError("PROJ_DATA directory not found. Please set PROJ_DATA.")
    os.environ["PROJ_DATA"] = pyproj_datadir
else:
    pyproj_datadir = os.environ["PROJ_DATA"]
