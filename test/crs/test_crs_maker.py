import pytest

from pyproj.crs import (
    CRS,
    BoundCRS,
    CompoundCRS,
    CustomConstructorCRS,
    DerivedGeographicCRS,
    GeocentricCRS,
    GeographicCRS,
    ProjectedCRS,
    VerticalCRS,
)
from pyproj.crs.coordinate_operation import (
    AlbersEqualAreaConversion,
    LambertConformalConic2SPConversion,
    RotatedLatitudeLongitudeConversion,
    ToWGS84Transformation,
    TransverseMercatorConversion,
    UTMConversion,
)
from pyproj.crs.coordinate_system import Cartesian2DCS, Ellipsoidal3DCS, VerticalCS
from pyproj.crs.datum import CustomDatum
from pyproj.crs.enums import VerticalCSAxis
from pyproj.exceptions import CRSError
from test.conftest import PROJ_GTE_901, assert_can_pickle


def assert_maker_inheritance_valid(new_crs, class_type):
    assert isinstance(new_crs, class_type)
    assert isinstance(new_crs.geodetic_crs, (type(None), CRS))
    assert isinstance(new_crs.source_crs, (type(None), CRS))
    assert isinstance(new_crs.target_crs, (type(None), CRS))
    assert isinstance(new_crs.to_3d(), CRS)
    for sub_crs in new_crs.sub_crs_list:
        assert isinstance(sub_crs, CRS)


def test_make_projected_crs(tmp_path):
    aeaop = AlbersEqualAreaConversion(0, 0)
    pc = ProjectedCRS(conversion=aeaop, name="Albers")
    assert pc.name == "Albers"
    assert pc.type_name == "Projected CRS"
    assert pc.coordinate_operation == aeaop
    assert_can_pickle(pc, tmp_path)


def test_projected_crs__from_methods():
    assert_maker_inheritance_valid(ProjectedCRS.from_epsg(6933), ProjectedCRS)
    assert_maker_inheritance_valid(ProjectedCRS.from_string("EPSG:6933"), ProjectedCRS)
    assert_maker_inheritance_valid(
        ProjectedCRS.from_proj4("+proj=aea +lat_1=1"), ProjectedCRS
    )
    assert_maker_inheritance_valid(
        ProjectedCRS.from_user_input(ProjectedCRS.from_string("EPSG:6933")),
        ProjectedCRS,
    )
    assert_maker_inheritance_valid(
        ProjectedCRS.from_json(CRS(6933).to_json()), ProjectedCRS
    )
    assert_maker_inheritance_valid(
        ProjectedCRS.from_json_dict(CRS(6933).to_json_dict()), ProjectedCRS
    )
    with pytest.raises(CRSError, match="Invalid type"):
        ProjectedCRS.from_epsg(4326)


def test_make_geographic_crs(tmp_path):
    gc = GeographicCRS(name="WGS 84")
    assert gc.name == "WGS 84"
    assert gc.type_name == "Geographic 2D CRS"
    assert gc.to_authority() == ("OGC", "CRS84")
    assert_can_pickle(gc, tmp_path)


def test_geographic_crs__from_methods():
    assert_maker_inheritance_valid(GeographicCRS.from_epsg(4326), GeographicCRS)
    assert_maker_inheritance_valid(
        GeographicCRS.from_string("EPSG:4326"), GeographicCRS
    )
    assert_maker_inheritance_valid(
        GeographicCRS.from_proj4("+proj=latlon"), GeographicCRS
    )
    assert_maker_inheritance_valid(
        GeographicCRS.from_user_input(GeographicCRS.from_string("EPSG:4326")),
        GeographicCRS,
    )
    assert_maker_inheritance_valid(
        GeographicCRS.from_json(CRS(4326).to_json()), GeographicCRS
    )
    assert_maker_inheritance_valid(
        GeographicCRS.from_json_dict(CRS(4326).to_json_dict()), GeographicCRS
    )
    with pytest.raises(CRSError, match="Invalid type"):
        GeographicCRS.from_epsg(6933)


def test_make_geographic_3d_crs():
    gcrs = GeographicCRS(ellipsoidal_cs=Ellipsoidal3DCS())
    assert gcrs.type_name == "Geographic 3D CRS"
    expected_authority = ("IGNF", "WGS84GEODD")
    if PROJ_GTE_901:
        expected_authority = ("OGC", "CRS84h")
    assert gcrs.to_authority() == expected_authority


def test_make_derived_geographic_crs(tmp_path):
    conversion = RotatedLatitudeLongitudeConversion(o_lat_p=0, o_lon_p=0)
    dgc = DerivedGeographicCRS(base_crs=GeographicCRS(), conversion=conversion)
    assert dgc.name == "undefined"
    assert dgc.type_name == "Derived Geographic 2D CRS"
    assert dgc.coordinate_operation == conversion
    assert dgc.is_derived
    assert_can_pickle(dgc, tmp_path)


def test_derived_geographic_crs__from_methods():
    crs_str = "+proj=ob_tran +o_proj=longlat +o_lat_p=0 +o_lon_p=0 +lon_0=0"
    with pytest.raises(CRSError, match="Invalid type Geographic 2D CRS"):
        DerivedGeographicCRS.from_epsg(4326)
    assert_maker_inheritance_valid(
        DerivedGeographicCRS.from_string(crs_str), DerivedGeographicCRS
    )
    assert_maker_inheritance_valid(
        DerivedGeographicCRS.from_proj4(crs_str), DerivedGeographicCRS
    )
    assert_maker_inheritance_valid(
        DerivedGeographicCRS.from_user_input(DerivedGeographicCRS.from_string(crs_str)),
        DerivedGeographicCRS,
    )
    assert_maker_inheritance_valid(
        DerivedGeographicCRS.from_json(CRS(crs_str).to_json()), DerivedGeographicCRS
    )
    assert_maker_inheritance_valid(
        DerivedGeographicCRS.from_json_dict(CRS(crs_str).to_json_dict()),
        DerivedGeographicCRS,
    )


def test_make_geocentric_crs(tmp_path):
    gc = GeocentricCRS(name="WGS 84")
    assert gc.name == "WGS 84"
    assert gc.is_geocentric
    assert gc.type_name == "Geocentric CRS"
    assert gc.to_authority() == ("EPSG", "4978")
    assert_can_pickle(gc, tmp_path)


def test_geocentric_crs__from_methods():
    assert_maker_inheritance_valid(GeocentricCRS.from_epsg(4978), GeocentricCRS)
    assert_maker_inheritance_valid(
        GeocentricCRS.from_string("EPSG:4978"), GeocentricCRS
    )
    assert_maker_inheritance_valid(
        GeocentricCRS.from_proj4("+proj=geocent"), GeocentricCRS
    )
    assert_maker_inheritance_valid(
        GeocentricCRS.from_user_input(GeocentricCRS.from_string("EPSG:4978")),
        GeocentricCRS,
    )
    assert_maker_inheritance_valid(
        GeocentricCRS.from_json(CRS(4978).to_json()), GeocentricCRS
    )
    assert_maker_inheritance_valid(
        GeocentricCRS.from_json_dict(CRS(4978).to_json_dict()), GeocentricCRS
    )
    with pytest.raises(CRSError, match="Invalid type"):
        GeocentricCRS.from_epsg(6933)


def test_vertical_crs(tmp_path):
    vc = VerticalCRS(
        name="NAVD88 height",
        datum="North American Vertical Datum 1988",
        geoid_model="GEOID12B",
    )
    assert vc.name == "NAVD88 height"
    assert vc.type_name == "Vertical CRS"
    assert vc.coordinate_system == VerticalCS()
    assert vc.to_json_dict()["geoid_model"]["name"] == "GEOID12B"
    assert_can_pickle(vc, tmp_path)


def test_vertical_crs__from_methods():
    assert_maker_inheritance_valid(VerticalCRS.from_epsg(5703), VerticalCRS)
    assert_maker_inheritance_valid(VerticalCRS.from_string("EPSG:5703"), VerticalCRS)
    with pytest.raises(CRSError, match="Invalid type"):
        VerticalCRS.from_proj4("+proj=latlon")
    assert_maker_inheritance_valid(
        VerticalCRS.from_user_input(VerticalCRS.from_string("EPSG:5703")), VerticalCRS
    )
    assert_maker_inheritance_valid(
        VerticalCRS.from_json(CRS(5703).to_json()), VerticalCRS
    )
    assert_maker_inheritance_valid(
        VerticalCRS.from_json_dict(CRS(5703).to_json_dict()), VerticalCRS
    )


@pytest.mark.parametrize(
    "axis",
    [
        VerticalCSAxis.UP,
        VerticalCSAxis.UP_FT,
        VerticalCSAxis.DEPTH,
        VerticalCSAxis.DEPTH_FT,
        VerticalCSAxis.GRAVITY_HEIGHT_FT,
    ],
)
def test_vertical_crs__chance_cs_axis(axis):
    vc = VerticalCRS(
        name="NAVD88 height",
        datum="North American Vertical Datum 1988",
        vertical_cs=VerticalCS(axis=axis),
    )
    assert vc.name == "NAVD88 height"
    assert vc.type_name == "Vertical CRS"
    assert vc.coordinate_system == VerticalCS(axis=axis)


def test_compund_crs(tmp_path):
    vertcrs = VerticalCRS(
        name="NAVD88 height",
        datum="North American Vertical Datum 1988",
        vertical_cs=VerticalCS(),
        geoid_model="GEOID12B",
    )
    projcrs = ProjectedCRS(
        name="NAD83 / Pennsylvania South",
        conversion=LambertConformalConic2SPConversion(
            latitude_false_origin=39.3333333333333,
            longitude_false_origin=-77.75,
            latitude_first_parallel=40.9666666666667,
            latitude_second_parallel=39.9333333333333,
            easting_false_origin=600000,
            northing_false_origin=0,
        ),
        geodetic_crs=GeographicCRS(datum="North American Datum 1983"),
        cartesian_cs=Cartesian2DCS(),
    )
    compcrs = CompoundCRS(
        name="NAD83 / Pennsylvania South + NAVD88 height", components=[projcrs, vertcrs]
    )
    assert compcrs.name == "NAD83 / Pennsylvania South + NAVD88 height"
    assert compcrs.type_name == "Compound CRS"
    assert compcrs.sub_crs_list[0].type_name == "Projected CRS"
    assert compcrs.sub_crs_list[1].type_name == "Vertical CRS"
    assert_can_pickle(compcrs, tmp_path)


def test_compund_crs__from_methods():
    crs = CompoundCRS.from_string("EPSG:4326+5773")
    with pytest.raises(CRSError, match="Invalid type"):
        CompoundCRS.from_epsg(4326)
    assert_maker_inheritance_valid(crs, CompoundCRS)
    with pytest.raises(CRSError, match="Invalid type"):
        CompoundCRS.from_proj4("+proj=longlat +datum=WGS84 +vunits=m")
    assert_maker_inheritance_valid(CompoundCRS.from_user_input(crs), CompoundCRS)
    assert_maker_inheritance_valid(CompoundCRS.from_json(crs.to_json()), CompoundCRS)
    assert_maker_inheritance_valid(
        CompoundCRS.from_json_dict(crs.to_json_dict()), CompoundCRS
    )


def test_bound_crs(tmp_path):
    proj_crs = ProjectedCRS(conversion=UTMConversion(12))
    bound_crs = BoundCRS(
        source_crs=proj_crs,
        target_crs="WGS 84",
        transformation=ToWGS84Transformation(
            proj_crs.geodetic_crs, 1, 2, 3, 4, 5, 6, 7
        ),
    )
    assert bound_crs.type_name == "Bound CRS"
    assert bound_crs.source_crs.coordinate_operation.name == "UTM zone 12N"
    assert bound_crs.coordinate_operation.towgs84 == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert bound_crs.target_crs.name == "WGS 84"
    assert_can_pickle(bound_crs, tmp_path)


def test_bound_crs__example():
    proj_crs = ProjectedCRS(
        conversion=TransverseMercatorConversion(
            latitude_natural_origin=0,
            longitude_natural_origin=15,
            false_easting=2520000,
            false_northing=0,
            scale_factor_natural_origin=0.9996,
        ),
        geodetic_crs=GeographicCRS(
            datum=CustomDatum(ellipsoid="International 1924 (Hayford 1909, 1910)")
        ),
    )
    bound_crs = BoundCRS(
        source_crs=proj_crs,
        target_crs="WGS 84",
        transformation=ToWGS84Transformation(
            proj_crs.geodetic_crs, -122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62
        ),
    )
    with pytest.warns(UserWarning):
        assert bound_crs.to_dict() == {
            "ellps": "intl",
            "k": 0.9996,
            "lat_0": 0,
            "lon_0": 15,
            "no_defs": None,
            "proj": "tmerc",
            "towgs84": [-122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62],
            "type": "crs",
            "units": "m",
            "x_0": 2520000,
            "y_0": 0,
        }


def test_bound_crs_crs__from_methods():
    crs_str = "+proj=latlon +towgs84=0,0,0"
    with pytest.raises(CRSError, match="Invalid type"):
        BoundCRS.from_epsg(4326)
    assert_maker_inheritance_valid(BoundCRS.from_string(crs_str), BoundCRS)
    assert_maker_inheritance_valid(BoundCRS.from_proj4(crs_str), BoundCRS)
    assert_maker_inheritance_valid(
        BoundCRS.from_user_input(BoundCRS.from_string(crs_str)), BoundCRS
    )
    assert_maker_inheritance_valid(BoundCRS.from_json(CRS(crs_str).to_json()), BoundCRS)
    assert_maker_inheritance_valid(
        BoundCRS.from_json_dict(CRS(crs_str).to_json_dict()), BoundCRS
    )


def test_custom_constructor_crs__not_implemented():
    class MyCustomInit(CustomConstructorCRS):
        def __init__(self, *, name: str):
            super().__init__(name)

    with pytest.raises(NotImplementedError):
        MyCustomInit.from_epsg(4326)


def test_custom_constructor_crs():
    class MyCustomInit(CustomConstructorCRS):
        _expected_types = ("Geographic 2D CRS",)

        def __init__(self, *, name: str):
            super().__init__(name)

    assert isinstance(MyCustomInit.from_epsg(4326), MyCustomInit)
