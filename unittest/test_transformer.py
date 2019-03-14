import pyproj


def test_tranform_wgs84_to_custom():
    custom_proj = pyproj.Proj(
        "+proj=geos +lon_0=0.000000 +lat_0=0 +h=35807.414063"
        " +a=6378.169000 +b=6356.583984"
    )
    wgs84 = pyproj.Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    lat, lon = 51.04715, 3.23406
    xx, yy = pyproj.transform(wgs84, custom_proj, lon, lat)
    assert "{:.3f} {:.3f}".format(xx, yy) == "212.623 4604.975"


def test_transform_wgs84_to_alaska():
    lat_lon_proj = pyproj.Proj(init="epsg:4326", preserve_units=False)
    alaska_aea_proj = pyproj.Proj(init="epsg:2964", preserve_units=False)
    test = (-179.72638, 49.752533)
    xx, yy = pyproj.transform(lat_lon_proj, alaska_aea_proj, *test)
    assert "{:.3f} {:.3f}".format(xx, yy) == "-1824924.495 330822.800"
