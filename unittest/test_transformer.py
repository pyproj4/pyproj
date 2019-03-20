import numpy as np
from numpy.testing import assert_almost_equal, assert_equal

import pyproj
from pyproj import Transformer
from pyproj.exceptions import ProjError


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


def test_illegal_transformation():
    # issue 202
    p1 = pyproj.Proj(init="epsg:4326")
    p2 = pyproj.Proj(init="epsg:3857")
    xx, yy = pyproj.transform(
        p1, p2, (-180, -180, 180, 180, -180), (-90, 90, 90, -90, -90)
    )
    assert np.all(np.isinf(xx))
    assert np.all(np.isinf(yy))
    try:
        xx, yy = pyproj.transform(
            p1, p2, (-180, -180, 180, 180, -180), (-90, 90, 90, -90, -90), errcheck=True
        )
        assert_equal(None, "Should throw an exception when errcheck=True")
    except ProjError:
        pass


def test_lambert_conformal_transform():
    # issue 207
    Midelt = pyproj.Proj(init="epsg:26191")
    WGS84 = pyproj.Proj(init="epsg:4326")

    E = 567623.931
    N = 256422.787
    h = 1341.467

    Long1, Lat1, H1 = pyproj.transform(Midelt, WGS84, E, N, h, radians=False)
    assert_almost_equal((Long1, Lat1, H1), (-4.6753456, 32.902199, 1341.467), decimal=5)


def test_equivalent_crs():
    transformer = Transformer.from_crs("epsg:4326", 4326, skip_equivalent=True)
    assert transformer._transformer.projections_equivalent
    assert transformer._transformer.projections_exact_same
    assert transformer._transformer.skip_equivalent


def test_equivalent_crs__disabled():
    transformer = Transformer.from_crs("epsg:4326", 4326)
    assert not transformer._transformer.skip_equivalent
    assert transformer._transformer.projections_equivalent
    assert transformer._transformer.projections_exact_same


def test_equivalent_crs__different():
    transformer = Transformer.from_crs("epsg:4326", 3857, skip_equivalent=True)
    assert transformer._transformer.skip_equivalent
    assert not transformer._transformer.projections_equivalent
    assert not transformer._transformer.projections_exact_same


def test_equivalent_proj():
    transformer = Transformer.from_proj(
        "+init=epsg:4326", pyproj.Proj(4326).crs.to_proj4(), skip_equivalent=True
    )
    assert transformer._transformer.skip_equivalent
    assert transformer._transformer.projections_equivalent
    assert transformer._transformer.projections_exact_same


def test_equivalent_proj__disabled():
    transformer = Transformer.from_proj(3857, pyproj.Proj(3857).crs.to_proj4())
    assert not transformer._transformer.skip_equivalent
    assert transformer._transformer.projections_equivalent
    assert transformer._transformer.projections_exact_same


def test_equivalent_proj__different():
    transformer = Transformer.from_proj(3857, 4326, skip_equivalent=True)
    assert transformer._transformer.skip_equivalent
    assert not transformer._transformer.projections_equivalent
    assert not transformer._transformer.projections_exact_same


def test_equivalent_pipeline():
    transformer = Transformer.from_pipeline(
        "+proj=pipeline +step +proj=longlat +ellps=WGS84 +step "
        "+proj=unitconvert +xy_in=rad +xy_out=deg"
    )
    assert not transformer._transformer.skip_equivalent
    assert not transformer._transformer.projections_equivalent
    assert not transformer._transformer.projections_exact_same
