import os
from functools import partial
from glob import glob
from itertools import permutations
from pathlib import Path

import numpy as np
import pytest
from mock import call, patch
from numpy.testing import assert_almost_equal

import pyproj
from pyproj import Proj, Transformer, itransform, transform
from pyproj.datadir import append_data_dir
from pyproj.enums import TransformDirection
from pyproj.exceptions import ProjError
from pyproj.transformer import AreaOfInterest, TransformerGroup
from test.conftest import grids_available, proj_env, proj_network_env


def test_tranform_wgs84_to_custom():
    custom_proj = pyproj.Proj(
        "+proj=geos +lon_0=0.000000 +lat_0=0 +h=35807.414063"
        " +a=6378.169000 +b=6356.583984"
    )
    wgs84 = pyproj.Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    lat, lon = 51.04715, 3.23406
    with pytest.warns(DeprecationWarning):
        xx, yy = pyproj.transform(wgs84, custom_proj, lon, lat)
    assert f"{xx:.3f} {yy:.3f}" == "212.623 4604.975"


def test_transform_wgs84_to_alaska():
    with pytest.warns(FutureWarning):
        lat_lon_proj = pyproj.Proj(init="epsg:4326", preserve_units=False)
        alaska_aea_proj = pyproj.Proj(init="epsg:2964", preserve_units=False)
    test = (-179.72638, 49.752533)
    with pytest.warns(DeprecationWarning):
        xx, yy = pyproj.transform(lat_lon_proj, alaska_aea_proj, *test)
    if grids_available("us_noaa_alaska.tif"):
        assert f"{xx:.3f} {yy:.3f}" == "-1824924.495 330822.800"
    else:
        assert f"{xx:.3f} {yy:.3f}" == "-1825155.697 330730.391"


def test_illegal_transformation():
    # issue 202
    with pytest.warns(FutureWarning):
        p1 = pyproj.Proj(init="epsg:4326")
        p2 = pyproj.Proj(init="epsg:3857")
    with pytest.warns(DeprecationWarning):
        xx, yy = pyproj.transform(
            p1, p2, (-180, -180, 180, 180, -180), (-90, 90, 90, -90, -90)
        )
    assert np.all(np.isinf(xx))
    assert np.all(np.isinf(yy))
    with pytest.warns(DeprecationWarning), pytest.raises(ProjError):
        pyproj.transform(
            p1, p2, (-180, -180, 180, 180, -180), (-90, 90, 90, -90, -90), errcheck=True
        )


def test_lambert_conformal_transform():
    # issue 207
    with pytest.warns(FutureWarning):
        Midelt = pyproj.Proj(init="epsg:26191")
        WGS84 = pyproj.Proj(init="epsg:4326")

    E = 567623.931
    N = 256422.787
    h = 1341.467
    with pytest.warns(DeprecationWarning):
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
    with pytest.warns(UserWarning):
        proj_to = pyproj.Proj(4326).crs.to_proj4()
    with pytest.warns(FutureWarning):
        transformer = Transformer.from_proj(
            "+init=epsg:4326", proj_to, skip_equivalent=True
        )
    assert transformer._transformer.skip_equivalent
    assert transformer._transformer.projections_equivalent
    assert not transformer._transformer.projections_exact_same


def test_equivalent_proj__disabled():
    with pytest.warns(UserWarning):
        transformer = Transformer.from_proj(3857, pyproj.Proj(3857).crs.to_proj4())
    assert not transformer._transformer.skip_equivalent
    assert transformer._transformer.projections_equivalent
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
    with pytest.warns(DeprecationWarning):
        assert_almost_equal(
            transform(
                7789, 8401, x=3496737.2679, y=743254.4507, z=5264462.9620, tt=2019.0
            ),
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
    with pytest.warns(DeprecationWarning):
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
    with pytest.warns(DeprecationWarning):
        assert_almost_equal(
            list(
                itransform(
                    7789, 8401, [(3496737.2679, 743254.4507, 5264462.9620, 2019.0)]
                )
            ),
            [(3496737.757717311, 743253.9940103051, 5264462.701132784, 2019.0)],
        )


def test_2d_with_time_itransform_original_crs_obs2():
    with pytest.warns(DeprecationWarning):
        assert_almost_equal(
            list(
                itransform(
                    4896, 7930, [(3496737.2679, 743254.4507, 2019.0)], time_3rd=True
                )
            ),
            [(3496737.4105305015, 743254.1014318303, 2019.0)],
        )


def test_itransform_time_3rd_invalid():

    with pytest.warns(DeprecationWarning), pytest.raises(
        ValueError, match="'time_3rd' is only valid for 3 coordinates."
    ):
        list(
            itransform(
                7789,
                8401,
                [(3496737.2679, 743254.4507, 5264462.9620, 2019.0)],
                time_3rd=True,
            )
        )
    with pytest.warns(DeprecationWarning), pytest.raises(
        ValueError, match="'time_3rd' is only valid for 3 coordinates."
    ):
        list(itransform(7789, 8401, [(3496737.2679, 743254.4507)], time_3rd=True))


def test_transform_no_error():
    with pytest.warns(FutureWarning):
        pj = Proj(init="epsg:4555")
    pjx, pjy = pj(116.366, 39.867)
    with pytest.warns(DeprecationWarning):
        transform(pj, Proj(4326), pjx, pjy, radians=True, errcheck=True)


def test_itransform_no_error():
    with pytest.warns(FutureWarning):
        pj = Proj(init="epsg:4555")
    pjx, pjy = pj(116.366, 39.867)
    with pytest.warns(DeprecationWarning):
        list(itransform(pj, Proj(4326), [(pjx, pjy)], radians=True, errcheck=True))


def test_transform_no_exception():
    # issue 249
    with pytest.warns(FutureWarning):
        transformer = Transformer.from_proj("+init=epsg:4326", "+init=epsg:27700")
    transformer.transform(1.716073972, 52.658007833, errcheck=True)
    transformer.itransform([(1.716073972, 52.658007833)], errcheck=True)


def test_transform__out_of_bounds():
    with pytest.warns(FutureWarning):
        transformer = Transformer.from_proj("+init=epsg:4326", "+init=epsg:27700")
    with pytest.raises(pyproj.exceptions.ProjError):
        transformer.transform(100000, 100000, errcheck=True)


def test_transform_radians():
    with pytest.warns(FutureWarning):
        WGS84 = pyproj.Proj("+init=EPSG:4326")
    ECEF = pyproj.Proj(proj="geocent", ellps="WGS84", datum="WGS84")
    with pytest.warns(DeprecationWarning):
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
    with pytest.warns(FutureWarning):
        WGS84 = pyproj.Proj("+init=EPSG:4326")
    ECEF = pyproj.Proj(proj="geocent", ellps="WGS84", datum="WGS84")
    with pytest.warns(DeprecationWarning):
        assert_almost_equal(
            list(
                pyproj.itransform(
                    ECEF,
                    WGS84,
                    [(-2704026.010, -4253051.810, 3895878.820)],
                    radians=True,
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
    with pytest.warns(DeprecationWarning):
        assert_almost_equal(
            transform(2193, 4326, 1625350, 5504853, always_xy=True),
            (173.29964730317386, -40.60674802693758),
        )


def test_always_xy__itransform():
    with pytest.warns(DeprecationWarning):
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


@pytest.mark.parametrize(
    "from_crs, to_crs, expected_repr",
    [
        (
            7789,
            8401,
            (
                "<Transformation Transformer: helmert>\n"
                "Description: ITRF2014 to ETRF2014 (1)\n"
                "Area of Use:\n"
                "- name: Europe - ETRF by country\n"
                "- bounds: (-16.1, 32.88, 40.18, 84.17)"
            ),
        ),
        (
            4326,
            3857,
            (
                "<Conversion Transformer: pipeline>\n"
                "Description: Popular Visualisation Pseudo-Mercator\n"
                "Area of Use:\n"
                "- name: World\n"
                "- bounds: (-180.0, -90.0, 180.0, 90.0)"
            ),
        ),
    ],
)
def test_repr(from_crs, to_crs, expected_repr):
    assert repr(Transformer.from_crs(from_crs, to_crs)) == expected_repr


def test_repr__conditional():
    trans_repr = repr(Transformer.from_crs(4326, 26917))
    if grids_available(
        "ca_nrc_NA83SCRS.tif",
        "us_noaa_FL.tif",
        "us_noaa_MD.tif",
        "us_noaa_TN.tif",
        "us_noaa_gahpgn.tif",
        "us_noaa_kyhpgn.tif",
        "us_noaa_mihpgn.tif",
        "us_noaa_nchpgn.tif",
        "us_noaa_nyhpgn.tif",
        "us_noaa_ohhpgn.tif",
        "us_noaa_pahpgn.tif",
        "us_noaa_schpgn.tif",
        "us_noaa_vahpgn.tif",
        "us_noaa_wvhpgn.tif",
    ):
        assert trans_repr == (
            "<Unknown Transformer: unknown>\n"
            "Description: unavailable until proj_trans is called\n"
            "Area of Use:\n- undefined"
        )
    else:
        assert trans_repr == (
            "<Concatenated Operation Transformer: pipeline>\n"
            "Description: Inverse of NAD83 to WGS 84 (1) + UTM zone 17N\n"
            "Area of Use:\n"
            "- name: North America - Canada and USA (CONUS, Alaska mainland)\n"
            "- bounds: (-172.54, 23.81, -47.74, 86.46)"
        )


def test_to_json_dict():
    transformer = Transformer.from_crs(4326, 3857)
    json_dict = transformer.to_json_dict()
    assert json_dict["type"] == "Conversion"


def test_to_json():
    transformer = Transformer.from_crs(4326, 3857)
    json_data = transformer.to_json()
    assert "Conversion" in json_data
    assert "\n" not in json_data


def test_to_json__pretty():
    transformer = Transformer.from_crs(4326, 3857)
    json_data = transformer.to_json(pretty=True)
    assert "Conversion" in json_data
    assert json_data.startswith('{\n  "')


def test_to_json__pretty__indenation():
    transformer = Transformer.from_crs(4326, 3857)
    json_data = transformer.to_json(pretty=True, indentation=4)
    assert "Conversion" in json_data
    assert json_data.startswith('{\n    "')


def test_transformer__operations():
    transformer = TransformerGroup(28356, 7856).transformers[0]
    assert [op.name for op in transformer.operations] == [
        "Inverse of Map Grid of Australia zone 56",
        "GDA94 to GDA2020 (1)",
        "Map Grid of Australia zone 56",
    ]


def test_transformer__operations_missing():
    assert Transformer.from_crs(7789, 8401).operations == ()


def test_transformer__operations__scope_remarks():
    transformer = TransformerGroup(28356, 7856).transformers[0]
    assert transformer.scope is None
    assert [op.scope for op in transformer.operations] == [
        "Large and medium scale topographic mapping and engineering survey.",
        "Conformal transformation of GDA94 coordinates that have been derived through "
        "GNSS CORS.",
        "Large and medium scale topographic mapping and engineering survey.",
    ]
    assert [str(op.remarks)[:5].strip() for op in transformer.operations] == [
        "Grid",
        "Scale",
        "Grid",
    ]


def test_transformer_group():
    trans_group = TransformerGroup(7789, 8401)
    assert len(trans_group.transformers) == 2
    assert trans_group.transformers[0].name == "helmert"
    assert trans_group.transformers[1].description == ("ITRF2014 to ETRF2014 (2)")
    assert not trans_group.unavailable_operations
    assert trans_group.best_available


def test_transformer_group__unavailable():
    trans_group = TransformerGroup(4326, 2964)
    for transformer in trans_group.transformers:
        assert transformer.is_network_enabled == (
            os.environ.get("PROJ_NETWORK") == "ON"
        )

    if grids_available("us_noaa_alaska.tif", "ca_nrc_ntv2_0.tif", check_all=True):
        assert len(trans_group.unavailable_operations) == 0
        assert len(trans_group.transformers) == 10
        assert (
            trans_group.transformers[0].description
            == "Inverse of NAD27 to WGS 84 (85) + Alaska Albers"
        )
        assert trans_group.best_available
    elif grids_available("us_noaa_alaska.tif"):
        assert len(trans_group.unavailable_operations) == 1
        assert (
            trans_group.transformers[0].description
            == "Inverse of NAD27 to WGS 84 (85) + Alaska Albers"
        )
        assert len(trans_group.transformers) == 9
        assert trans_group.best_available
    elif grids_available("ca_nrc_ntv2_0.tif"):
        assert len(trans_group.unavailable_operations) == 1
        assert (
            trans_group.transformers[0].description
            == "Inverse of NAD27 to WGS 84 (7) + Alaska Albers"
        )
        assert len(trans_group.transformers) == 9
        assert not trans_group.best_available
    else:
        assert len(trans_group.unavailable_operations) == 2
        assert (
            trans_group.unavailable_operations[0].name
            == "Inverse of NAD27 to WGS 84 (85) + Alaska Albers"
        )
        assert len(trans_group.transformers) == 8
        assert not trans_group.best_available


def test_transform_group__missing_best():
    with pytest.warns(FutureWarning):
        lat_lon_proj = pyproj.Proj(init="epsg:4326", preserve_units=False)
        alaska_aea_proj = pyproj.Proj(init="epsg:2964", preserve_units=False)

    if not grids_available("ca_nrc_ntv2_0.tif"):
        with pytest.warns(
            UserWarning,
            match="Best transformation is not available due to missing Grid",
        ):
            trans_group = pyproj.transformer.TransformerGroup(
                lat_lon_proj.crs, alaska_aea_proj.crs
            )

        assert not trans_group.best_available
        assert "ntv2_0" not in trans_group.transformers[0].definition
        assert "ntv2_0" in trans_group.unavailable_operations[0].to_proj4()
    else:
        # assuming all grids avaiable or PROJ_NETWORK=ON
        trans_group = pyproj.transformer.TransformerGroup(
            lat_lon_proj.crs, alaska_aea_proj.crs
        )
        assert trans_group.best_available
        assert "ntv2_0" in trans_group.transformers[0].definition


def test_transform_group__area_of_interest():
    if not grids_available("ca_nrc_ntv2_0.tif"):
        with pytest.warns(
            UserWarning,
            match="Best transformation is not available due to missing Grid",
        ):
            trans_group = pyproj.transformer.TransformerGroup(
                4326,
                2964,
                area_of_interest=pyproj.transformer.AreaOfInterest(
                    -136.46, 49.0, -60.72, 83.17
                ),
            )
        assert (
            trans_group.transformers[0].description
            == "Inverse of NAD27 to WGS 84 (13) + Alaska Albers"
        )
    else:
        trans_group = pyproj.transformer.TransformerGroup(
            4326,
            2964,
            area_of_interest=pyproj.transformer.AreaOfInterest(
                -136.46, 49.0, -60.72, 83.17
            ),
        )
        assert trans_group.best_available
        assert (
            trans_group.transformers[0].description
            == "Inverse of NAD27 to WGS 84 (33) + Alaska Albers"
        )


def test_transformer_group__get_transform_crs():
    tg = TransformerGroup("epsg:4258", "epsg:7415")
    if not grids_available("nl_nsgi_rdtrans2018.tif"):
        assert len(tg.transformers) == 1
    else:
        assert len(tg.transformers) == 2


def test_transformer__area_of_interest():
    transformer = Transformer.from_crs(
        4326, 2964, area_of_interest=AreaOfInterest(-136.46, 49.0, -60.72, 83.17)
    )
    if not grids_available("ca_nrc_ntv2_0.tif"):
        assert (
            transformer.description == "Inverse of NAD27 to WGS 84 (13) + Alaska Albers"
        )
    else:
        assert (
            transformer.description == "Inverse of NAD27 to WGS 84 (33) + Alaska Albers"
        )


def test_transformer_proj__area_of_interest():
    transformer = Transformer.from_proj(
        4326, 2964, area_of_interest=AreaOfInterest(-136.46, 49.0, -60.72, 83.17)
    )
    if not grids_available("ca_nrc_ntv2_0.tif"):
        assert (
            transformer.description == "Inverse of NAD27 to WGS 84 (13) + Alaska Albers"
        )
    else:
        assert (
            transformer.description == "Inverse of NAD27 to WGS 84 (33) + Alaska Albers"
        )


def test_transformer__area_of_interest__invalid():
    with pytest.raises(ProjError):
        Transformer.from_crs(
            4326, 2964, area_of_interest=(-136.46, 49.0, -60.72, 83.17)
        )


def test_transformer_group__area_of_interest__invalid():
    with pytest.raises(ProjError):
        TransformerGroup(4326, 2964, area_of_interest=(-136.46, 49.0, -60.72, 83.17))


def test_transformer_equals():
    assert (
        TransformerGroup(28356, 7856).transformers[0]
        == TransformerGroup(28356, 7856).transformers[0]
    )


@pytest.mark.parametrize(
    "comparison",
    [Transformer.from_pipeline("+proj=pipeline +ellps=GRS80 +step +proj=cart"), 22],
)
def test_transformer_not_equals(comparison):
    assert Transformer.from_crs(28356, 7856) != comparison


@pytest.mark.parametrize(
    "pipeline_str",
    [
        "+proj=pipeline +ellps=GRS80 +step +proj=cart",
        "+proj=pipeline +step +proj=unitconvert +xy_in=deg "
        "+xy_out=rad +ellps=GRS80 +step +proj=cart",
    ],
)
def test_pipeline_transform(pipeline_str):
    trans = Transformer.from_pipeline(pipeline_str)
    assert_almost_equal(
        trans.transform(50, 25, 0),
        (3717892.6072086394, 4430811.87152035, 2679074.4628772778),
    )


@pytest.mark.parametrize(
    "pipeline_str",
    [
        "+proj=pipeline +ellps=GRS80 +step +proj=cart",
        "+proj=pipeline +step +proj=unitconvert +xy_in=deg "
        "+xy_out=rad +ellps=GRS80 +step +proj=cart",
    ],
)
def test_pipeline_itransform(pipeline_str):
    trans = Transformer.from_pipeline(pipeline_str)
    assert_almost_equal(
        list(trans.itransform([(50, 25, 0)])),
        [(3717892.6072086394, 4430811.87152035, 2679074.4628772778)],
    )


@pytest.mark.parametrize(
    "transformer",
    [
        partial(
            Transformer.from_pipeline, "+proj=pipeline +ellps=GRS80 +step +proj=cart"
        ),
        partial(Transformer.from_crs, 4326, 3857),
        partial(Transformer.from_proj, 4326, 3857),
    ],
)
@patch.dict("os.environ", {"PROJ_NETWORK": "ON"}, clear=True)
def test_network__disable(transformer):
    with proj_network_env():
        if pyproj._datadir._USE_GLOBAL_CONTEXT:
            pyproj.network.set_network_enabled(active=False)
        trans = transformer(network=False)
        assert trans.is_network_enabled is False


@pytest.mark.parametrize(
    "transformer",
    [
        partial(
            Transformer.from_pipeline, "+proj=pipeline +ellps=GRS80 +step +proj=cart"
        ),
        partial(Transformer.from_crs, 4326, 3857),
        partial(Transformer.from_proj, 4326, 3857),
    ],
)
@patch.dict("os.environ", {"PROJ_NETWORK": "OFF"}, clear=True)
def test_network__enable(transformer):
    with proj_network_env():
        if pyproj._datadir._USE_GLOBAL_CONTEXT:
            pyproj.network.set_network_enabled(active=True)
        trans = transformer(network=True)
        assert trans.is_network_enabled is True


@pytest.mark.parametrize(
    "transformer",
    [
        partial(
            Transformer.from_pipeline, "+proj=pipeline +ellps=GRS80 +step +proj=cart"
        ),
        partial(Transformer.from_crs, 4326, 3857),
        partial(Transformer.from_proj, 4326, 3857),
    ],
)
def test_network__default(transformer):
    with proj_network_env():
        if pyproj._datadir._USE_GLOBAL_CONTEXT:
            pyproj.network.set_network_enabled()
        trans = transformer()
        assert trans.is_network_enabled == (os.environ.get("PROJ_NETWORK") == "ON")


@patch.dict("os.environ", {"PROJ_NETWORK": "OFF"}, clear=True)
def test_transformer_group__network_enabled():
    with proj_network_env():
        if pyproj._datadir._USE_GLOBAL_CONTEXT:
            pyproj.network.set_network_enabled(active=True)
        trans_group = TransformerGroup(4326, 2964, network=True)
        assert len(trans_group.unavailable_operations) == 0
        assert len(trans_group.transformers) == 10
        assert trans_group.best_available
        for transformer in trans_group.transformers:
            assert transformer.is_network_enabled is True
            for operation in transformer.operations:
                for grid in operation.grids:
                    assert grid.available


@patch.dict("os.environ", {"PROJ_NETWORK": "ON"}, clear=True)
def test_transformer_group__network_disabled():
    with proj_network_env():
        if pyproj._datadir._USE_GLOBAL_CONTEXT:
            pyproj.network.set_network_enabled(active=False)
        trans_group = TransformerGroup(4326, 2964, network=False)
        for transformer in trans_group.transformers:
            assert transformer.is_network_enabled is False

        if grids_available(
            "us_noaa_alaska.tif",
            "ca_nrc_ntv2_0.tif",
            check_network=False,
            check_all=True,
        ):
            assert len(trans_group.unavailable_operations) == 0
            assert len(trans_group.transformers) == 10
            assert (
                trans_group.transformers[0].description
                == "Inverse of NAD27 to WGS 84 (85) + Alaska Albers"
            )
            assert trans_group.best_available
        elif grids_available("us_noaa_alaska.tif", check_network=False):
            assert len(trans_group.unavailable_operations) == 1
            assert (
                trans_group.transformers[0].description
                == "Inverse of NAD27 to WGS 84 (85) + Alaska Albers"
            )
            assert len(trans_group.transformers) == 9
            assert trans_group.best_available
        elif grids_available("ca_nrc_ntv2_0.tif", check_network=False):
            assert len(trans_group.unavailable_operations) == 1
            assert (
                trans_group.transformers[0].description
                == "Inverse of NAD27 to WGS 84 (7) + Alaska Albers"
            )
            assert len(trans_group.transformers) == 9
            assert not trans_group.best_available
        else:
            assert len(trans_group.unavailable_operations) == 2
            assert (
                trans_group.unavailable_operations[0].name
                == "Inverse of NAD27 to WGS 84 (85) + Alaska Albers"
            )
            assert len(trans_group.transformers) == 8
            assert not trans_group.best_available


def test_transform_pipeline_radians():
    trans = Transformer.from_pipeline(
        "+proj=pipeline +step +inv +proj=cart +ellps=WGS84 "
        "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
    )
    assert_almost_equal(
        trans.transform(-2704026.010, -4253051.810, 3895878.820, radians=True),
        (-2.137113493845668, 0.6613203738996222, -20.531156923621893),
    )

    assert_almost_equal(
        trans.transform(
            -2.137113493845668,
            0.6613203738996222,
            -20.531156923621893,
            radians=True,
            direction=TransformDirection.INVERSE,
        ),
        (-2704026.010, -4253051.810, 3895878.820),
    )


def test_itransform_pipeline_radians():
    trans = Transformer.from_pipeline(
        "+proj=pipeline +step +inv +proj=cart +ellps=WGS84 "
        "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
    )
    assert_almost_equal(
        list(
            trans.itransform([(-2704026.010, -4253051.810, 3895878.820)], radians=True)
        ),
        [(-2.137113493845668, 0.6613203738996222, -20.531156923621893)],
    )

    assert_almost_equal(
        list(
            trans.itransform(
                [(-2.137113493845668, 0.6613203738996222, -20.531156923621893)],
                radians=True,
                direction=TransformDirection.INVERSE,
            )
        ),
        [(-2704026.010, -4253051.810, 3895878.820)],
    )


@pytest.mark.parametrize("x,y,z", permutations([10, [10], (10,)]))  # 6 test cases
def test_transform_honours_input_types(x, y, z):
    # 622
    transformer = Transformer.from_proj(4896, 4896)
    assert transformer.transform(xx=x, yy=y, zz=z) == (x, y, z)


@patch("pyproj.transformer.get_user_data_dir")
def test_transformer_group__download_grids(get_user_data_dir_mock, tmp_path, capsys):
    get_user_data_dir_mock.return_value = str(tmp_path)
    with proj_network_env():
        if pyproj._datadir._USE_GLOBAL_CONTEXT:
            pyproj.network.set_network_enabled(active=False)
        trans_group = TransformerGroup(4326, 2964, network=False)
        trans_group.download_grids(verbose=True)
        captured = capsys.readouterr()
        get_user_data_dir_mock.assert_called_with(True)
        paths = sorted(Path(path).name for path in glob(str(tmp_path.joinpath("*"))))
        if grids_available(
            "us_noaa_alaska.tif",
            "ca_nrc_ntv2_0.tif",
            check_network=False,
            check_all=True,
        ):
            assert paths == []
            assert captured.out == ""
        elif grids_available("us_noaa_alaska.tif", check_network=False):
            assert paths == ["ca_nrc_ntv2_0.tif"]
            assert (
                captured.out == "Downloading: https://cdn.proj.org/ca_nrc_ntv2_0.tif\n"
            )
        elif grids_available("ca_nrc_ntv2_0.tif", check_network=False):
            assert paths == ["us_noaa_alaska.tif"]
            assert captured.out == (
                "Downloading: https://cdn.proj.org/us_noaa_alaska.tif\n"
            )
        else:
            assert paths == ["ca_nrc_ntv2_0.tif", "us_noaa_alaska.tif"]
            assert captured.out == (
                "Downloading: https://cdn.proj.org/us_noaa_alaska.tif\n"
                "Downloading: https://cdn.proj.org/ca_nrc_ntv2_0.tif\n"
            )
        # make sure not downloaded again
        with proj_env(), patch(
            "pyproj.transformer._download_resource_file"
        ) as download_mock:
            append_data_dir(str(tmp_path))
            trans_group = TransformerGroup(4326, 2964, network=False)
            trans_group.download_grids()
            get_user_data_dir_mock.assert_called_with(True)
            download_mock.assert_not_called()


@patch("pyproj.transformer._download_resource_file")
@patch("pyproj.transformer.get_user_data_dir")
def test_transformer_group__download_grids__directory(
    get_user_data_dir_mock, download_mock, tmp_path, capsys
):
    with proj_network_env():
        if pyproj._datadir._USE_GLOBAL_CONTEXT:
            pyproj.network.set_network_enabled(active=False)
        trans_group = TransformerGroup(4326, 2964, network=False)
        trans_group.download_grids(directory=tmp_path)
        get_user_data_dir_mock.assert_not_called()
        captured = capsys.readouterr()
        assert captured.out == ""
        if grids_available(
            "us_noaa_alaska.tif",
            "ca_nrc_ntv2_0.tif",
            check_network=False,
            check_all=True,
        ):
            download_mock.assert_not_called()
        elif grids_available("us_noaa_alaska.tif", check_network=False):
            download_mock.assert_called_with(
                file_url="https://cdn.proj.org/ca_nrc_ntv2_0.tif",
                short_name="ca_nrc_ntv2_0.tif",
                directory=tmp_path,
                verbose=False,
            )
        elif grids_available("ca_nrc_ntv2_0.tif", check_network=False):
            download_mock.assert_called_with(
                file_url="https://cdn.proj.org/us_noaa_alaska.tif",
                short_name="us_noaa_alaska.tif",
                directory=tmp_path,
                verbose=False,
            )
        else:
            download_mock.assert_has_calls(
                [
                    call(
                        file_url="https://cdn.proj.org/us_noaa_alaska.tif",
                        short_name="us_noaa_alaska.tif",
                        directory=tmp_path,
                        verbose=False,
                    ),
                    call(
                        file_url="https://cdn.proj.org/ca_nrc_ntv2_0.tif",
                        short_name="ca_nrc_ntv2_0.tif",
                        directory=tmp_path,
                        verbose=False,
                    ),
                ],
                any_order=True,
            )
