import numpy as np
import pytest
from numpy.testing import assert_almost_equal

import pyproj
from pyproj import Proj, Transformer, itransform, transform
from pyproj.enums import TransformDirection
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
    with pytest.raises(ProjError):
        pyproj.transform(
            p1, p2, (-180, -180, 180, 180, -180), (-90, 90, 90, -90, -90), errcheck=True
        )


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
    assert not transformer._transformer.projections_exact_same


def test_equivalent_proj__disabled():
    transformer = Transformer.from_proj(3857, pyproj.Proj(3857).crs.to_proj4())
    assert not transformer._transformer.skip_equivalent
    assert not transformer._transformer.projections_equivalent
    assert not transformer._transformer.projections_exact_same


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


def test_4d_transform():
    transformer = Transformer.from_pipeline("+init=ITRF2008:ITRF2000")
    assert_almost_equal(
        transformer.transform(
            xx=3513638.19380, yy=778956.45250, zz=5248216.46900, tt=2008.75
        ),
        (3513638.1999428216, 778956.4532640711, 5248216.453456361, 2008.75),
    )


def test_2d_with_time_transform():
    transformer = Transformer.from_pipeline("+init=ITRF2008:ITRF2000")
    assert_almost_equal(
        transformer.transform(xx=3513638.19380, yy=778956.45250, tt=2008.75),
        (3513638.1999428216, 778956.4532640711, 2008.75),
    )


def test_4d_transform_crs_obs1():
    transformer = Transformer.from_proj(7789, 8401)
    assert_almost_equal(
        transformer.transform(
            xx=3496737.2679, yy=743254.4507, zz=5264462.9620, tt=2019.0
        ),
        (3496737.757717311, 743253.9940103051, 5264462.701132784, 2019.0),
    )


def test_4d_transform_orginal_crs_obs1():
    assert_almost_equal(
        transform(7789, 8401, x=3496737.2679, y=743254.4507, z=5264462.9620, tt=2019.0),
        (3496737.757717311, 743253.9940103051, 5264462.701132784, 2019.0),
    )


def test_4d_transform_crs_obs2():
    transformer = Transformer.from_proj(4896, 7930)
    assert_almost_equal(
        transformer.transform(
            xx=3496737.2679, yy=743254.4507, zz=5264462.9620, tt=2019.0
        ),
        (3496737.7857162016, 743254.0394113371, 5264462.643659916, 2019.0),
    )


def test_2d_with_time_transform_crs_obs2():
    transformer = Transformer.from_proj(4896, 7930)
    assert_almost_equal(
        transformer.transform(xx=3496737.2679, yy=743254.4507, tt=2019.0),
        (3496737.4105305015, 743254.1014318303, 2019.0),
    )


def test_2d_with_time_transform_original_crs_obs2():
    assert_almost_equal(
        transform(4896, 7930, x=3496737.2679, y=743254.4507, tt=2019.0),
        (3496737.4105305015, 743254.1014318303, 2019.0),
    )


def test_4d_itransform():
    transformer = Transformer.from_pipeline("+init=ITRF2008:ITRF2000")
    assert_almost_equal(
        list(
            transformer.itransform(
                [(3513638.19380, 778956.45250, 5248216.46900, 2008.75)]
            )
        ),
        [(3513638.1999428216, 778956.4532640711, 5248216.453456361, 2008.75)],
    )


def test_3d_time_itransform():
    transformer = Transformer.from_pipeline("+init=ITRF2008:ITRF2000")
    assert_almost_equal(
        list(
            transformer.itransform(
                [(3513638.19380, 778956.45250, 2008.75)], time_3rd=True
            )
        ),
        [(3513638.1999428216, 778956.4532640711, 2008.75)],
    )


def test_4d_itransform_orginal_crs_obs1():
    assert_almost_equal(
        list(
            itransform(7789, 8401, [(3496737.2679, 743254.4507, 5264462.9620, 2019.0)])
        ),
        [(3496737.757717311, 743253.9940103051, 5264462.701132784, 2019.0)],
    )


def test_2d_with_time_itransform_original_crs_obs2():
    assert_almost_equal(
        list(
            itransform(4896, 7930, [(3496737.2679, 743254.4507, 2019.0)], time_3rd=True)
        ),
        [(3496737.4105305015, 743254.1014318303, 2019.0)],
    )


def test_itransform_time_3rd_invalid():

    with pytest.raises(ValueError, match="'time_3rd' is only valid for 3 coordinates."):
        list(
            itransform(
                7789,
                8401,
                [(3496737.2679, 743254.4507, 5264462.9620, 2019.0)],
                time_3rd=True,
            )
        )
    with pytest.raises(ValueError, match="'time_3rd' is only valid for 3 coordinates."):
        list(itransform(7789, 8401, [(3496737.2679, 743254.4507)], time_3rd=True))


def test_transform_no_error():
    pj = Proj(init="epsg:4555")
    pjx, pjy = pj(116.366, 39.867)
    transform(pj, Proj(4326), pjx, pjy, radians=True, errcheck=True)


def test_itransform_no_error():
    pj = Proj(init="epsg:4555")
    pjx, pjy = pj(116.366, 39.867)
    list(itransform(pj, Proj(4326), [(pjx, pjy)], radians=True, errcheck=True))


def test_transform_no_exception():
    # issue 249
    transformer = Transformer.from_proj("+init=epsg:4326", "+init=epsg:27700")
    transformer.transform(1.716073972, 52.658007833, errcheck=True)
    transformer.itransform([(1.716073972, 52.658007833)], errcheck=True)


def test_transform__out_of_bounds():
    transformer = Transformer.from_proj("+init=epsg:4326", "+init=epsg:27700")
    assert np.all(np.isinf(transformer.transform(100000, 100000, errcheck=True)))


def test_transform_radians():
    WGS84 = pyproj.Proj("+init=EPSG:4326")
    ECEF = pyproj.Proj(proj="geocent", ellps="WGS84", datum="WGS84")
    assert_almost_equal(
        pyproj.transform(
            ECEF, WGS84, -2704026.010, -4253051.810, 3895878.820, radians=True
        ),
        (-2.137113493845668, 0.6613203738996222, -20.531156923621893),
    )

    assert_almost_equal(
        pyproj.transform(
            WGS84,
            ECEF,
            -2.137113493845668,
            0.6613203738996222,
            -20.531156923621893,
            radians=True,
        ),
        (-2704026.010, -4253051.810, 3895878.820),
    )


def test_itransform_radians():
    WGS84 = pyproj.Proj("+init=EPSG:4326")
    ECEF = pyproj.Proj(proj="geocent", ellps="WGS84", datum="WGS84")
    assert_almost_equal(
        list(
            pyproj.itransform(
                ECEF, WGS84, [(-2704026.010, -4253051.810, 3895878.820)], radians=True
            )
        ),
        [(-2.137113493845668, 0.6613203738996222, -20.531156923621893)],
    )

    assert_almost_equal(
        list(
            pyproj.itransform(
                WGS84,
                ECEF,
                [(-2.137113493845668, 0.6613203738996222, -20.531156923621893)],
                radians=True,
            )
        ),
        [(-2704026.010, -4253051.810, 3895878.820)],
    )


def test_4d_transform__inverse():
    transformer = Transformer.from_pipeline("+init=ITRF2008:ITRF2000")
    assert_almost_equal(
        transformer.transform(
            xx=3513638.1999428216,
            yy=778956.4532640711,
            zz=5248216.453456361,
            tt=2008.75,
            direction=TransformDirection.INVERSE,
        ),
        (3513638.19380, 778956.45250, 5248216.46900, 2008.75),
    )


def test_transform_direction():
    forward_transformer = Transformer.from_crs(4326, 3857)
    inverse_transformer = Transformer.from_crs(3857, 4326)
    assert inverse_transformer.transform(
        -33, 24, direction=TransformDirection.INVERSE
    ) == forward_transformer.transform(-33, 24)
    ident_transformer = Transformer.from_crs(4326, 3857)
    ident_transformer.transform(-33, 24, direction=TransformDirection.IDENT) == (
        -33,
        24,
    )


def test_always_xy__transformer():
    transformer = Transformer.from_crs(2193, 4326, always_xy=True)
    assert_almost_equal(
        transformer.transform(1625350, 5504853),
        (173.29964730317386, -40.60674802693758),
    )


def test_always_xy__transform():
    assert_almost_equal(
        transform(2193, 4326, 1625350, 5504853, always_xy=True),
        (173.29964730317386, -40.60674802693758),
    )


def test_always_xy__itransform():
    assert_almost_equal(
        list(itransform(2193, 4326, [(1625350, 5504853)], always_xy=True)),
        [(173.29964730317386, -40.60674802693758)],
    )


def test_transform_direction__string():
    forward_transformer = Transformer.from_crs(4326, 3857)
    inverse_transformer = Transformer.from_crs(3857, 4326)
    assert inverse_transformer.transform(
        -33, 24, direction="INVERSE"
    ) == forward_transformer.transform(-33, 24, direction="FORWARD")
    ident_transformer = Transformer.from_crs(4326, 3857)
    ident_transformer.transform(-33, 24, direction="IDENT") == (-33, 24)


def test_transform_direction__string_lowercase():
    forward_transformer = Transformer.from_crs(4326, 3857)
    inverse_transformer = Transformer.from_crs(3857, 4326)
    assert inverse_transformer.transform(
        -33, 24, direction="inverse"
    ) == forward_transformer.transform(-33, 24, direction="forward")
    ident_transformer = Transformer.from_crs(4326, 3857)
    ident_transformer.transform(-33, 24, direction="ident") == (-33, 24)


def test_transform_direction__invalid():
    transformer = Transformer.from_crs(4326, 3857)
    with pytest.raises(ValueError, match="Invalid value"):
        transformer.transform(-33, 24, direction="WHEREVER")


def test_from_pipeline__non_transform_input():
    with pytest.raises(ProjError, match="Input is not a transformation"):
        Transformer.from_pipeline("epsg:4326")


def test_non_supported_initialization():
    with pytest.raises(ProjError, match="Transformer must be initialized using"):
        Transformer()


def test_pj_info_properties():
    transformer = Transformer.from_crs(4326, 3857)
    assert transformer.name == "pipeline"
    assert transformer.description == "Popular Visualisation Pseudo-Mercator"
    assert transformer.definition.startswith("proj=pipeline")
    assert transformer.has_inverse
    assert transformer.accuracy == 0


def test_to_wkt():
    transformer = Transformer.from_crs(4326, 3857)
    assert transformer.to_wkt().startswith(
        'CONVERSION["Popular Visualisation Pseudo-Mercator"'
    )


def test_str():
    assert str(Transformer.from_crs(4326, 3857)).startswith("proj=pipeline")


def test_repr():
    assert repr(Transformer.from_crs(7789, 8401)) == (
        "<Transformation Transformer: helmert>\n" "ITRF2014 to ETRF2014 (1)"
    )

    assert repr(Transformer.from_crs(4326, 3857)) == (
        "<Conversion Transformer: pipeline>\n" "Popular Visualisation Pseudo-Mercator"
    )

    assert repr(Transformer.from_crs(4326, 26917)) == (
        "<Unknown Transformer: unknown>\n" "unavailable until proj_trans is called"
    )
