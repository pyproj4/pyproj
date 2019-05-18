from pyproj import Proj


def test_initialize_proj_crs_no_proj4():
    proj = Proj(
        {
            "a": 6371229.0,
            "b": 6371229.0,
            "lon_0": -10.0,
            "o_lat_p": 30.0,
            "o_lon_p": 0.0,
            "o_proj": "longlat",
            "proj": "ob_tran",
        }
    )
    assert proj.srs.startswith("+proj=ob_tran")


def test_initialize_proj_crs_no_plus():
    proj = Proj("proj=lonlat")
    assert proj.crs.srs == "proj=lonlat type=crs"
