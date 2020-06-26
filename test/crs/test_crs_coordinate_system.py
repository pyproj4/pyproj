import pytest

from pyproj.crs.coordinate_system import (
    Cartesian2DCS,
    Ellipsoidal2DCS,
    Ellipsoidal3DCS,
    VerticalCS,
)
from pyproj.crs.enums import (
    Cartesian2DCSAxis,
    Ellipsoidal2DCSAxis,
    Ellipsoidal3DCSAxis,
    VerticalCSAxis,
)


@pytest.mark.parametrize(
    "axis, direction, unit_name",
    [
        ("UP", "up", "metre"),
        (VerticalCSAxis.UP, "up", "metre"),
        (VerticalCSAxis.UP_US_FT, "up", "US survey foot"),
        ("UP_FT", "up", "foot"),
        (VerticalCSAxis.DEPTH, "down", "metre"),
        (VerticalCSAxis.DEPTH_US_FT, "down", "US survey foot"),
        ("DEPTH_FT", "down", "foot"),
        (VerticalCSAxis.GRAVITY_HEIGHT_US_FT, "up", "US survey foot"),
        ("GRAVITY_HEIGHT_FT", "up", "foot"),
    ],
)
def test_vertical_cs(axis, direction, unit_name):
    vcs = VerticalCS(axis=axis)
    assert len(vcs.axis_list) == 1
    assert vcs.axis_list[0].direction == direction
    assert vcs.axis_list[0].unit_name == unit_name


@pytest.mark.parametrize(
    "axis, name_0, direction_0, name_1, direction_1, unit",
    [
        ("EASTING_NORTHING", "Easting", "east", "Northing", "north", "metre"),
        (
            Cartesian2DCSAxis.NORTHING_EASTING,
            "Northing",
            "north",
            "Easting",
            "east",
            "metre",
        ),
        ("EASTING_NORTHING_FT", "Easting", "east", "Northing", "north", "foot"),
        (
            Cartesian2DCSAxis.NORTHING_EASTING_FT,
            "Northing",
            "north",
            "Easting",
            "east",
            "foot",
        ),
        (
            "EASTING_NORTHING_US_FT",
            "Easting",
            "east",
            "Northing",
            "north",
            "US survey foot",
        ),
        (
            Cartesian2DCSAxis.NORTHING_EASTING_US_FT,
            "Northing",
            "north",
            "Easting",
            "east",
            "US survey foot",
        ),
        (
            "NORTH_POLE_EASTING_SOUTH_NORTHING_SOUTH",
            "Easting",
            "south",
            "Northing",
            "south",
            "metre",
        ),
        (
            Cartesian2DCSAxis.SOUTH_POLE_EASTING_NORTH_NORTHING_NORTH,
            "Easting",
            "north",
            "Northing",
            "north",
            "metre",
        ),
        ("WESTING_SOUTHING", "Easting", "west", "Northing", "south", "metre"),
    ],
)
def test_cartesian_2d_cs(axis, name_0, direction_0, name_1, direction_1, unit):
    vcs = Cartesian2DCS(axis=axis)
    assert len(vcs.axis_list) == 2
    assert vcs.axis_list[0].direction == direction_0
    assert vcs.axis_list[0].name == name_0
    assert vcs.axis_list[0].unit_name == unit
    assert vcs.axis_list[1].direction == direction_1
    assert vcs.axis_list[1].name == name_1
    assert vcs.axis_list[1].unit_name == unit


@pytest.mark.parametrize(
    "axis, name_0, direction_0, name_1, direction_1",
    [
        (
            Ellipsoidal2DCSAxis.LONGITUDE_LATITUDE,
            "Longitude",
            "east",
            "Latitude",
            "north",
        ),
        (
            Ellipsoidal2DCSAxis.LATITUDE_LONGITUDE,
            "Latitude",
            "north",
            "Longitude",
            "east",
        ),
    ],
)
def test_ellipsoidal_2d_cs(axis, name_0, direction_0, name_1, direction_1):
    vcs = Ellipsoidal2DCS(axis=axis)
    assert len(vcs.axis_list) == 2
    assert vcs.axis_list[0].direction == direction_0
    assert vcs.axis_list[0].name == name_0
    assert vcs.axis_list[0].unit_name == "degree"
    assert vcs.axis_list[1].direction == direction_1
    assert vcs.axis_list[1].name == name_1
    assert vcs.axis_list[1].unit_name == "degree"


@pytest.mark.parametrize(
    "axis, name_0, direction_0, name_1, direction_1",
    [
        (
            Ellipsoidal3DCSAxis.LONGITUDE_LATITUDE_HEIGHT,
            "Longitude",
            "east",
            "Latitude",
            "north",
        ),
        (
            Ellipsoidal3DCSAxis.LATITUDE_LONGITUDE_HEIGHT,
            "Latitude",
            "north",
            "Longitude",
            "east",
        ),
    ],
)
def test_ellipsoidal_3d_cs(axis, name_0, direction_0, name_1, direction_1):
    vcs = Ellipsoidal3DCS(axis=axis)
    assert len(vcs.axis_list) == 3
    assert vcs.axis_list[0].direction == direction_0
    assert vcs.axis_list[0].name == name_0
    assert vcs.axis_list[0].unit_name == "degree"
    assert vcs.axis_list[1].direction == direction_1
    assert vcs.axis_list[1].name == name_1
    assert vcs.axis_list[1].unit_name == "degree"
    assert vcs.axis_list[2].direction == "up"
    assert vcs.axis_list[2].name == "Ellipsoidal height"
    assert vcs.axis_list[2].unit_name == "metre"


def test_ellipsoidal2dcs_to_cf():
    ecs = Ellipsoidal2DCS(axis=Ellipsoidal2DCSAxis.LATITUDE_LONGITUDE)
    assert ecs.to_cf() == [
        {
            "standard_name": "latitude",
            "long_name": "latitude coordinate",
            "units": "degrees_north",
            "axis": "Y",
        },
        {
            "standard_name": "longitude",
            "long_name": "longitude coordinate",
            "units": "degrees_east",
            "axis": "X",
        },
    ]


def test_ellipsoidal3dcs_to_cf():
    ecs = Ellipsoidal3DCS(axis=Ellipsoidal3DCSAxis.LONGITUDE_LATITUDE_HEIGHT)
    assert ecs.to_cf() == [
        {
            "standard_name": "longitude",
            "long_name": "longitude coordinate",
            "units": "degrees_east",
            "axis": "X",
        },
        {
            "standard_name": "latitude",
            "long_name": "latitude coordinate",
            "units": "degrees_north",
            "axis": "Y",
        },
        {
            "standard_name": "height_above_reference_ellipsoid",
            "long_name": "Ellipsoidal height",
            "units": "metre",
            "positive": "up",
            "axis": "Z",
        },
    ]


def test_cartesian2dcs_ft_to_cf():
    csft = Cartesian2DCS(axis=Cartesian2DCSAxis.NORTHING_EASTING_FT)
    csft.to_cf() == [
        {
            "axis": "Y",
            "long_name": "Northing",
            "standard_name": "projection_y_coordinate",
            "units": "0.3048 metre",
        },
        {
            "axis": "X",
            "long_name": "Easting",
            "standard_name": "projection_x_coordinate",
            "units": "0.3048 metre",
        },
    ]


def test_cartesian2dcs_to_cf():
    csm = Cartesian2DCS(axis=Cartesian2DCSAxis.EASTING_NORTHING_FT)
    csm.to_cf() == [
        {
            "axis": "Y",
            "long_name": "Northing",
            "standard_name": "projection_y_coordinate",
            "units": "metre",
        },
        {
            "axis": "X",
            "long_name": "Easting",
            "standard_name": "projection_x_coordinate",
            "units": "metre",
        },
    ]


def test_verticalcs_depth_to_cf():
    vcs = VerticalCS(axis=VerticalCSAxis.DEPTH)
    vcs.to_cf() == [
        {
            "standard_name": "height_above_reference_ellipsoid",
            "long_name": "Depth",
            "units": "metre",
            "positive": "down",
            "axis": "Z",
        }
    ]


def test_verticalcs_height_to_cf():
    vcs = VerticalCS(axis=VerticalCSAxis.GRAVITY_HEIGHT_US_FT)
    vcs.to_cf() == [
        {
            "standard_name": "height_above_reference_ellipsoid",
            "long_name": "Gravity-related height",
            "units": "0.304800609601219 metre",
            "positive": "up",
            "axis": "Z",
        }
    ]
