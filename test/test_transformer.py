import concurrent.futures
import os
from array import array
from functools import partial
from glob import glob
from itertools import permutations
from pathlib import Path
from unittest.mock import call, patch

import numpy as np
import pytest
from numpy.testing import assert_almost_equal, assert_array_equal

import pyproj
from pyproj import CRS, Proj, Transformer, itransform, transform
from pyproj.datadir import append_data_dir
from pyproj.enums import TransformDirection
from pyproj.exceptions import ProjError
from pyproj.transformer import AreaOfInterest, TransformerGroup
from test.conftest import (
    PROJ_GTE_8,
    PROJ_GTE_81,
    grids_available,
    proj_env,
    proj_network_env,
)


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


@pytest.mark.grid
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


@pytest.mark.skipif(PROJ_GTE_8, reason="https://github.com/OSGeo/PROJ/issues/2425")
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
    with pytest.warns(DeprecationWarning):
        Transformer.from_crs("epsg:4326", 4326, skip_equivalent=True)


def test_equivalent_proj():
    with pytest.warns(FutureWarning):
        proj_from = pyproj.Proj("+init=epsg:4326")
    with pytest.warns(DeprecationWarning):
        Transformer.from_proj(proj_from, 4326, skip_equivalent=True)


def test_equivalent_transformer_group():
    with pytest.warns(DeprecationWarning):
        TransformerGroup("epsg:4326", 4326, skip_equivalent=True)


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


@pytest.mark.parametrize("empty_array", [(), [], np.array([])])
def test_transform_empty_array_xy(empty_array):
    transformer = Transformer.from_crs(2193, 4326)
    assert_array_equal(
        transformer.transform(empty_array, empty_array), (empty_array, empty_array)
    )


@pytest.mark.parametrize("empty_array", [(), [], np.array([])])
def test_transform_empty_array_xyzt(empty_array):
    transformer = Transformer.from_pipeline("+init=ITRF2008:ITRF2000")
    assert_array_equal(
        transformer.transform(empty_array, empty_array, empty_array, empty_array),
        (empty_array, empty_array, empty_array, empty_array),
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


def test_to_proj4():
    transformer = Transformer.from_crs(4326, 3857)
    proj_string = transformer.to_proj4()
    assert "+proj=pipeline" in proj_string
    assert "\n" not in proj_string


def test_to_proj4__pretty():
    transformer = Transformer.from_crs(4326, 3857)
    proj_string = transformer.to_proj4(pretty=True)
    assert "+proj=pipeline" in proj_string
    assert "\n" in proj_string


def test_to_wkt():
    transformer = Transformer.from_crs(4326, 3857)
    assert transformer.to_wkt().startswith(
        'CONVERSION["Popular Visualisation Pseudo-Mercator"'
    )


def test_str():
    assert str(Transformer.from_crs(4326, 3857)).startswith("proj=pipeline")


if PROJ_GTE_81:
    _BOUND_REPR = "(-16.1, 32.88, 40.18, 84.73)"
elif PROJ_GTE_8:
    _BOUND_REPR = (
        "(-16.096100515106, 32.884955146013, 40.178745269776, 84.722623821813)"
    )
else:
    _BOUND_REPR = "(-16.1, 32.88, 40.18, 84.17)"


@pytest.mark.parametrize(
    "from_crs, to_crs, expected_repr",
    [
        (
            7789,
            8401,
            (
                "<Transformation Transformer: helmert>\n"
                "Description: ITRF2014 to ETRF2014 (2)\n"
                "Area of Use:\n"
                "- name: Europe - onshore and offshore: Albania; Andorra; Austria; "
                "Belgium; Bosnia and Herzegovina; Bulgaria; Croatia; Cyprus; Czechia; "
                "Denmark; Estonia; Faroe Islands; Finland; France; Germany; Gibraltar; "
                "Greece; Hungary; Ireland; Italy; Kosovo; Latvia; Liechtenstein; "
                "Lithuania; Luxembourg; Malta; Moldova; Monaco; Montenegro; "
                "Netherlands; North Macedonia; "
                "Norway including Svalbard and Jan Mayen; "
                "Poland; Portugal; Romania; San Marino; Serbia; Slovakia; Slovenia; "
                "Spain; Sweden; Switzerland; "
                "United Kingdom (UK) including Channel Islands and Isle of Man; "
                "Vatican City State.\n"
                f"- bounds: {_BOUND_REPR}"
            ),
        ),
        (
            4326,
            3857,
            (
                "<Conversion Transformer: pipeline>\n"
                "Description: Popular Visualisation Pseudo-Mercator\n"
                "Area of Use:\n"
                "- name: World.\n"
                "- bounds: (-180.0, -90.0, 180.0, 90.0)"
            ),
        ),
    ],
)
def test_repr(from_crs, to_crs, expected_repr):
    assert repr(Transformer.from_crs(from_crs, to_crs)) == expected_repr


@pytest.mark.grid
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
            "- name: North America - onshore and offshore: Canada - Alberta;"
            " British Columbia; Manitoba; New Brunswick; "
            "Newfoundland and Labrador; Northwest Territories; "
            "Nova Scotia; Nunavut; Ontario; Prince Edward Island; Quebec; "
            "Saskatchewan; Yukon. United States (USA) - Alabama; "
            "Alaska (mainland); Arizona; Arkansas; California; Colorado; "
            "Connecticut; Delaware; Florida; Georgia; Idaho; Illinois; "
            "Indiana; Iowa; Kansas; Kentucky; Louisiana; Maine; Maryland; "
            "Massachusetts; Michigan; Minnesota; Mississippi; Missouri; "
            "Montana; Nebraska; Nevada; New Hampshire; New Jersey; "
            "New Mexico; New York; North Carolina; North Dakota; Ohio; "
            "Oklahoma; Oregon; Pennsylvania; Rhode Island; South Carolina; "
            "South Dakota; Tennessee; Texas; Utah; Vermont; Virginia; "
            "Washington; West Virginia; Wisconsin; Wyoming.\n"
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
        "Engineering survey, topographic mapping.",
        "Transformation of GDA94 coordinates that have been derived "
        "through GNSS CORS.",
        "Engineering survey, topographic mapping.",
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
    assert trans_group.transformers[1].description == ("ITRF2014 to ETRF2014 (1)")
    assert not trans_group.unavailable_operations
    assert trans_group.best_available


@pytest.mark.grid
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


@pytest.mark.grid
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


@pytest.mark.grid
def test_transform_group__area_of_interest():
    def get_transformer_group():
        return pyproj.transformer.TransformerGroup(
            4326,
            2964,
            area_of_interest=pyproj.transformer.AreaOfInterest(
                -136.46, 49.0, -60.72, 83.17
            ),
        )

    if not grids_available("ca_nrc_ntv2_0.tif"):
        with pytest.warns(
            UserWarning,
            match="Best transformation is not available due to missing Grid",
        ):
            trans_group = get_transformer_group()
        assert (
            trans_group.transformers[0].description
            == "Inverse of NAD27 to WGS 84 (13) + Alaska Albers"
        )
    else:
        trans_group = get_transformer_group()
        assert trans_group.best_available
        assert (
            trans_group.transformers[0].description
            == "Inverse of NAD27 to WGS 84 (33) + Alaska Albers"
        )


@pytest.mark.grid
def test_transformer_group__get_transform_crs():
    tg = TransformerGroup("epsg:4258", "epsg:7415")
    if not grids_available("nl_nsgi_rdtrans2018.tif"):
        assert len(tg.transformers) == 1
    else:
        assert len(tg.transformers) == 2


@pytest.mark.grid
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


@pytest.mark.grid
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
        pyproj.network.set_network_enabled(active=False)
        trans = transformer()
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
        pyproj.network.set_network_enabled(active=True)
        trans = transformer()
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
        pyproj.network.set_network_enabled()
        trans = transformer()
        assert trans.is_network_enabled == (os.environ.get("PROJ_NETWORK") == "ON")


@patch.dict("os.environ", {"PROJ_NETWORK": "OFF"}, clear=True)
def test_transformer_group__network_enabled():
    with proj_network_env():
        pyproj.network.set_network_enabled(active=True)
        trans_group = TransformerGroup(4326, 2964)
        assert len(trans_group.unavailable_operations) == 0
        assert len(trans_group.transformers) == 10
        assert trans_group.best_available
        for transformer in trans_group.transformers:
            assert transformer.is_network_enabled is True
            for operation in transformer.operations:
                for grid in operation.grids:
                    assert grid.available


@pytest.mark.grid
@patch.dict("os.environ", {"PROJ_NETWORK": "ON"}, clear=True)
def test_transformer_group__network_disabled():
    with proj_network_env():
        pyproj.network.set_network_enabled(active=False)
        trans_group = TransformerGroup(4326, 2964)
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


@pytest.mark.grid
@pytest.mark.network
@patch("pyproj.transformer.get_user_data_dir")
def test_transformer_group__download_grids(get_user_data_dir_mock, tmp_path, capsys):
    get_user_data_dir_mock.return_value = str(tmp_path)
    with proj_network_env():
        pyproj.network.set_network_enabled(active=False)
        trans_group = TransformerGroup(4326, 2964)
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
            trans_group = TransformerGroup(4326, 2964)
            trans_group.download_grids()
            get_user_data_dir_mock.assert_called_with(True)
            download_mock.assert_not_called()


@pytest.mark.grid
@patch("pyproj.transformer._download_resource_file")
@patch("pyproj.transformer.get_user_data_dir")
def test_transformer_group__download_grids__directory(
    get_user_data_dir_mock, download_mock, tmp_path, capsys
):
    with proj_network_env():
        pyproj.network.set_network_enabled(active=False)
        trans_group = TransformerGroup(4326, 2964)
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


@pytest.mark.skipif(
    pyproj._datadir._USE_GLOBAL_CONTEXT, reason="Global Context not Threadsafe."
)
def test_transformer_multithread__pipeline():
    # https://github.com/pyproj4/pyproj/issues/782
    trans = Transformer.from_pipeline(
        "+proj=pipeline +step +inv +proj=cart +ellps=WGS84 "
        "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
    )

    def transform(num):
        return trans.transform(-2704026.010, -4253051.810, 3895878.820)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for result in executor.map(transform, range(10)):
            pass


@pytest.mark.skipif(
    pyproj._datadir._USE_GLOBAL_CONTEXT, reason="Global Context not Threadsafe."
)
def test_transformer_multithread__crs():
    # https://github.com/pyproj4/pyproj/issues/782
    trans = Transformer.from_crs(4326, 3857)

    def transform(num):
        return trans.transform(1, 2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for result in executor.map(transform, range(10)):
            pass


@pytest.mark.skipif(not PROJ_GTE_8, reason="Requires PROJ 8+")
def test_transformer_accuracy_filter():
    with pytest.raises(ProjError):
        Transformer.from_crs("EPSG:4326", "EPSG:4258", accuracy=0.05)


@pytest.mark.skipif(PROJ_GTE_8, reason="Warning for PROJ<8")
def test_transformer_accuracy_filter_warning():
    with pytest.warns(UserWarning, match="accuracy requires PROJ 8+"):
        Transformer.from_crs("EPSG:4326", "EPSG:4258", accuracy=0.05)


@pytest.mark.skipif(not PROJ_GTE_8, reason="Requires PROJ 8+")
def test_transformer_allow_ballpark_filter():
    with pytest.raises(ProjError):
        Transformer.from_crs(
            "EPSG:4326", "EPSG:4258", authority="PROJ", allow_ballpark=False
        )


@pytest.mark.skipif(PROJ_GTE_8, reason="Warning for PROJ<8")
def test_transformer_allow_ballpark_filter_warning():
    with pytest.warns(UserWarning, match="allow_ballpark requires PROJ 8+"):
        Transformer.from_crs("EPSG:4326", "EPSG:4258", allow_ballpark=False)


@pytest.mark.skipif(not PROJ_GTE_8, reason="Requires PROJ 8+")
def test_transformer_authority_filter():
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:4258", authority="PROJ")
    assert transformer.description == "Ballpark geographic offset from WGS 84 to ETRS89"


@pytest.mark.skipif(PROJ_GTE_8, reason="Warning for PROJ<8")
def test_transformer_authority_filter_warning():
    with pytest.warns(UserWarning, match="authority requires PROJ 8+"):
        Transformer.from_crs("EPSG:4326", "EPSG:4258", authority="PROJ")


@pytest.mark.parametrize(
    "input_string",
    [
        "EPSG:1671",
        "RGF93 to WGS 84 (1)",
        "urn:ogc:def:coordinateOperation:EPSG::1671",
    ],
)
def test_transformer_from_pipeline__input_types(input_string):
    assert Transformer.from_pipeline(input_string).description == "RGF93 to WGS 84 (1)"


@pytest.mark.parametrize(
    "method_name",
    [
        "to_wkt",
        "to_json",
    ],
)
def test_transformer_from_pipeline__wkt_json(method_name):
    assert (
        Transformer.from_pipeline(
            getattr(
                Transformer.from_pipeline("urn:ogc:def:coordinateOperation:EPSG::1671"),
                method_name,
            )()
        ).description
        == "RGF93 to WGS 84 (1)"
    )


@pytest.mark.parametrize(
    "density,expected",
    [
        (0, (-1684649.41338, -350356.81377, 1684649.41338, 2234551.18559)),
        (100, (-1684649.41338, -555777.79210, 1684649.41338, 2234551.18559)),
    ],
)
def test_transform_bounds_densify(density, expected):
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 "
        "+a=6370997 +b=6370997 +units=m +no_defs",
    )
    assert np.allclose(
        transformer.transform_bounds(40, -120, 64, -80, densify_pts=density),
        expected,
    )


@pytest.mark.parametrize(
    "density,expected",
    [
        (0, (-1684649.41338, -350356.81377, 1684649.41338, 2234551.18559)),
        (100, (-1684649.41338, -555777.79210, 1684649.41338, 2234551.18559)),
    ],
)
@pytest.mark.parametrize(
    "input_bounds, radians",
    [
        ((-120, 40, -80, 64), False),
        ((np.radians(-120), np.radians(40), np.radians(-80), np.radians(64)), True),
    ],
)
def test_transform_bounds_densify__xy(density, expected, input_bounds, radians):
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 "
        "+a=6370997 +b=6370997 +units=m +no_defs",
        always_xy=True,
    )
    assert np.allclose(
        transformer.transform_bounds(
            *input_bounds, densify_pts=density, radians=radians
        ),
        expected,
    )


def test_transform_bounds_densify_out_of_bounds():
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 "
        "+a=6370997 +b=6370997 +units=m +no_defs",
        always_xy=True,
    )
    with pytest.raises(ProjError):
        transformer.transform_bounds(-120, 40, -80, 64, densify_pts=-1)


def test_transform_bounds_densify_out_of_bounds__geographic_output():
    transformer = Transformer.from_crs(
        "+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 "
        "+a=6370997 +b=6370997 +units=m +no_defs",
        "EPSG:4326",
        always_xy=True,
    )
    with pytest.raises(ProjError):
        transformer.transform_bounds(-120, 40, -80, 64, densify_pts=1)


def test_transform_bounds_radians_output():
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "+proj=geocent +ellps=WGS84 +datum=WGS84",
        always_xy=True,
    )
    assert_almost_equal(
        transformer.transform_bounds(
            -2704026.010,
            -4253051.810,
            -2704025.010,
            -4253050.810,
            radians=True,
            direction="INVERSE",
        ),
        (-2.1371136, 0.0, -2.1371133, 0.0),
    )


def test_transform_bounds__antimeridian():
    crs = CRS("EPSG:3851")
    transformer = Transformer.from_crs(crs.geodetic_crs, crs)
    minx, miny, maxx, maxy = crs.area_of_use.bounds
    transformed_bounds = transformer.transform_bounds(miny, minx, maxy, maxx)
    assert_almost_equal(
        transformed_bounds,
        (5228058.6143420935, 1722483.900174921, 8692574.544944234, 4624385.494808555),
    )
    assert_almost_equal(
        transformer.transform_bounds(
            *transformed_bounds,
            direction="INVERSE",
        ),
        (-56.7471249, 153.2799922, -24.6148194, -162.1813873),
    )


def test_transform_bounds__antimeridian__xy():
    crs = CRS("EPSG:3851")
    transformer = Transformer.from_crs(
        crs.geodetic_crs,
        crs,
        always_xy=True,
    )
    transformed_bounds = transformer.transform_bounds(*crs.area_of_use.bounds)
    assert_almost_equal(
        transformed_bounds,
        (1722483.900174921, 5228058.6143420935, 4624385.494808555, 8692574.544944234),
    )
    assert_almost_equal(
        transformer.transform_bounds(*transformed_bounds, direction="INVERSE"),
        (153.2799922, -56.7471249, -162.1813873, -24.6148194),
    )


def test_transform_bounds__beyond_global_bounds():
    transformer = Transformer.from_crs(
        "EPSG:6933",
        "EPSG:4326",
        always_xy=True,
    )
    assert_almost_equal(
        transformer.transform_bounds(
            -17367531.3203125, -7314541.19921875, 17367531.3203125, 7314541.19921875
        ),
        (-180, -85.0445994113099, 180, 85.0445994113099),
    )


@pytest.mark.parametrize(
    "input_crs,expected_bounds",
    [
        ("ESRI:102036", (0, -89178008, 0, 0)),
        ("ESRI:54026", (0, -179545824, 0, 179545824)),
    ],
)
def test_transform_bounds__ignore_inf(input_crs, expected_bounds):
    crs = CRS(input_crs)
    transformer = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    assert_almost_equal(
        transformer.transform_bounds(*crs.area_of_use.bounds),
        expected_bounds,
        decimal=0,
    )


def test_transform_bounds__noop_geographic():
    crs = CRS("Pulkovo 1942")
    transformer = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    assert_almost_equal(
        transformer.transform_bounds(*crs.area_of_use.bounds),
        crs.area_of_use.bounds,
    )


@pytest.mark.parametrize("inplace", [True, False])
def test_transform__fortran_order(inplace):
    lons, lats = np.arange(-180, 180, 20), np.arange(-90, 90, 10)
    lats, lons = np.meshgrid(lats, lons)
    f_lons, f_lats = lons.copy(order="F"), lats.copy(order="F")
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:6933",
        always_xy=True,
    )
    xxx, yyy = transformer.transform(lons, lats)
    f_xxx, f_yyy = transformer.transform(f_lons, f_lats, inplace=inplace)
    assert f_lons.flags.f_contiguous
    assert f_lats.flags.f_contiguous
    assert not f_xxx.flags.f_contiguous
    assert f_xxx.flags.c_contiguous
    assert not f_yyy.flags.f_contiguous
    assert f_yyy.flags.c_contiguous
    assert_array_equal(xxx, f_xxx)
    assert_array_equal(yyy, f_yyy)


def test_4d_transform__inplace__array():
    transformer = Transformer.from_crs(7789, 8401)
    xarr = array("d", [3496737.2679])
    yarr = array("d", [743254.4507])
    zarr = array("d", [5264462.9620])
    tarr = array("d", [2019.0])
    t_xarr, t_yarr, t_zarr, t_tarr = transformer.transform(
        xx=xarr, yy=yarr, zz=zarr, tt=tarr, inplace=True
    )
    assert xarr is t_xarr
    assert_almost_equal(xarr[0], 3496737.757717311)
    assert yarr is t_yarr
    assert_almost_equal(yarr[0], 743253.9940103051)
    assert zarr is t_zarr
    assert_almost_equal(zarr[0], 5264462.701132784)
    assert tarr is t_tarr
    assert_almost_equal(tarr[0], 2019.0)


def test_4d_transform__inplace__array__int():
    transformer = Transformer.from_crs(7789, 8401)
    xarr = array("i", [3496737])
    yarr = array("i", [743254])
    zarr = array("i", [5264462])
    tarr = array("i", [2019])
    t_xarr, t_yarr, t_zarr, t_tarr = transformer.transform(
        xx=xarr, yy=yarr, zz=zarr, tt=tarr, inplace=True
    )
    assert xarr is not t_xarr
    assert xarr[0] == 3496737
    assert yarr is not t_yarr
    assert yarr[0] == 743254
    assert zarr is not t_zarr
    assert zarr[0] == 5264462
    assert tarr is not t_tarr
    assert tarr[0] == 2019


def test_4d_transform__inplace__numpy():
    transformer = Transformer.from_crs(7789, 8401)
    xarr = np.array([3496737.2679], dtype=np.float64)
    yarr = np.array([743254.4507], dtype=np.float64)
    zarr = np.array([5264462.9620], dtype=np.float64)
    tarr = np.array([2019.0], dtype=np.float64)
    t_xarr, t_yarr, t_zarr, t_tarr = transformer.transform(
        xx=xarr, yy=yarr, zz=zarr, tt=tarr, inplace=True
    )
    assert xarr is t_xarr
    assert_almost_equal(xarr[0], 3496737.757717311)
    assert yarr is t_yarr
    assert_almost_equal(yarr[0], 743253.9940103051)
    assert zarr is t_zarr
    assert_almost_equal(zarr[0], 5264462.701132784)
    assert tarr is t_tarr
    assert_almost_equal(tarr[0], 2019.0)


def test_4d_transform__inplace__numpy__int():
    transformer = Transformer.from_crs(7789, 8401)
    xarr = np.array([3496737], dtype=np.int32)
    yarr = np.array([743254], dtype=np.int32)
    zarr = np.array([5264462], dtype=np.int32)
    tarr = np.array([2019], dtype=np.int32)
    t_xarr, t_yarr, t_zarr, t_tarr = transformer.transform(
        xx=xarr, yy=yarr, zz=zarr, tt=tarr, inplace=True
    )
    assert xarr is not t_xarr
    assert xarr[0] == 3496737
    assert yarr is not t_yarr
    assert yarr[0] == 743254
    assert zarr is not t_zarr
    assert zarr[0] == 5264462
    assert tarr is not t_tarr
    assert tarr[0] == 2019
