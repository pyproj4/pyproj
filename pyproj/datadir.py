"""
Set the datadir path to the local data directory
"""
import os

if "PROJ_DATA" not in os.environ:
    pyproj_datadir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "proj_dir", "share", "proj"
    )
    os.environ["PROJ_DATA"] = pyproj_datadir
else:
    pyproj_datadir = os.environ["PROJ_DATA"]
