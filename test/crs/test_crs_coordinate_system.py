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
