"""
This module contains the structures related to areas of interest.
"""
from typing import NamedTuple, Optional, Union


class AreaOfInterest(NamedTuple):
    """
    .. versionadded:: 2.3

    This is the area of interest for:

    - Transformations
    - Querying for CRS data.
    """

    #: The west bound in degrees of the area of interest.
    west_lon_degree: float
    #: The south bound in degrees of the area of interest.
    south_lat_degree: float
    #: The east bound in degrees of the area of interest.
    east_lon_degree: float
    #: The north bound in degrees of the area of interest.
    north_lat_degree: float


class AreaOfUse(NamedTuple):
    """
    .. versionadded:: 2.0

    Area of Use for CRS, CoordinateOperation, or a Transformer.
    """

    #: West bound of area of use.
    west: float
    #: South bound of area of use.
    south: float
    #: East bound of area of use.
    east: float
    #: North bound of area of use.
    north: float
    #: Name of area of use.
    name: Optional[str] = None

    @property
    def bounds(self):
        return self.west, self.south, self.east, self.north

    def __str__(self):
        return f"- name: {self.name}\n" f"- bounds: {self.bounds}"


class BBox:
    """
    Bounding box to check if data intersects/contains other
    bounding boxes.

    .. versionadded:: 3.0

    """

    def __init__(self, west: float, south: float, east: float, north: float):
        self.west = west
        self.south = south
        self.east = east
        self.north = north

    def intersects(self, other: Union["BBox", AreaOfUse]) -> bool:
        """
        Parameters
        ----------
        other: BBox
            The other BBox to use to check.

        Returns
        -------
        bool:
            True if this BBox intersects the other bbox.
        """
        return (
            self.west < other.east
            and other.west < self.east
            and self.south < other.north
            and other.south < self.north
        )

    def contains(self, other: Union["BBox", AreaOfUse]) -> bool:
        """
        Parameters
        ----------
        other: Union["BBox", AreaOfUse]
            The other BBox to use to check.

        Returns
        -------
        bool:
            True if this BBox contains the other bbox.
        """
        return (
            other.west >= self.west
            and other.east <= self.east
            and other.south >= self.south
            and other.north <= self.north
        )

    def __repr__(self) -> str:
        return (
            f"BBox(west={self.west},south={self.south},"
            f"east={self.east},north={self.north})"
        )
