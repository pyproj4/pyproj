"""
The transformer module is for performing cartographic transformations.
"""

__all__ = [
    "transform",
    "itransform",
    "Transformer",
    "TransformerGroup",
    "AreaOfInterest",
]
from array import array
from itertools import chain, islice
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union

from pyproj import CRS, Proj
from pyproj._crs import AreaOfUse, CoordinateOperation
from pyproj._transformer import AreaOfInterest, _Transformer, _TransformerGroup  # noqa
from pyproj.compat import cstrencode
from pyproj.enums import TransformDirection, WktVersion
from pyproj.exceptions import ProjError
from pyproj.utils import _convertback, _copytobuffer


class TransformerGroup(_TransformerGroup):
    """
    The TransformerGroup is a set of possible transformers from one CRS to another.

    .. versionadded:: 2.3.0

    From PROJ docs::

        The operations are sorted with the most relevant ones first: by
        descending area (intersection of the transformation area with the
        area of interest, or intersection of the transformation with the
        area of use of the CRS), and by increasing accuracy. Operations
        with unknown accuracy are sorted last, whatever their area.

    """

    def __init__(
        self,
        crs_from: Any,
        crs_to: Any,
        skip_equivalent: bool = False,
        always_xy: bool = False,
        area_of_interest: Optional[AreaOfInterest] = None,
    ) -> None:
        """Get all possible transformations from a :obj:`pyproj.crs.CRS`
        or input used to create one.


        Parameters
        ----------
        crs_from: pyproj.crs.CRS or input used to create one
            Projection of input data.
        crs_to: pyproj.crs.CRS or input used to create one
            Projection of output data.
        skip_equivalent: bool, optional
            If true, will skip the transformation operation if input and output
            projections are equivalent. Default is false.
        always_xy: bool, optional
            If true, the transform method will accept as input and return as output
            coordinates using the traditional GIS order, that is longitude, latitude
            for geographic CRS and easting, northing for most projected CRS.
            Default is false.
        area_of_interest: :class:`pyproj.transformer.AreaOfInterest`, optional
            The area of interest to help order the transformations based on the
            best operation for the area.


        Example:

        >>> from pyproj.transformer import TransformerGroup
        >>> trans_group = TransformerGroup(4326, 2964)
        >>> trans_group
        <TransformerGroup: best_available=True>
        - transformers: 8
        - unavailable_operations: 1

        """
        super().__init__(
            CRS.from_user_input(crs_from),
            CRS.from_user_input(crs_to),
            skip_equivalent=skip_equivalent,
            always_xy=always_xy,
            area_of_interest=area_of_interest,
        )
        for iii, transformer in enumerate(self._transformers):
            self._transformers[iii] = Transformer(transformer)

    @property
    def transformers(self) -> List["Transformer"]:
        """
        list[:obj:`Transformer`]:
            List of available :obj:`Transformer`
            associated with the transformation.
        """
        return self._transformers

    @property
    def unavailable_operations(self) -> List[CoordinateOperation]:
        """
        list[:obj:`pyproj.crs.CoordinateOperation`]:
            List of :obj:`pyproj.crs.CoordinateOperation` that are not
            available due to missing grids.
        """
        return self._unavailable_operations

    @property
    def best_available(self) -> bool:
        """
        bool: If True, the best possible transformer is available.
        """
        return self._best_available

    def __repr__(self) -> str:
        return (
            "<TransformerGroup: best_available={best_available}>\n"
            "- transformers: {transformers}\n"
            "- unavailable_operations: {unavailable_operations}"
        ).format(
            best_available=self.best_available,
            transformers=len(self.transformers),
            unavailable_operations=len(self.unavailable_operations),
        )


class Transformer:
    """
    The Transformer class is for facilitating re-using
    transforms without needing to re-create them. The goal
    is to make repeated transforms faster.

    Additionally, it provides multiple methods for initialization.

    .. versionadded:: 2.1.0

    """

    def __init__(self, base_transformer: Optional[_Transformer] = None) -> None:
        if not isinstance(base_transformer, _Transformer):
            ProjError.clear()
            raise ProjError(
                "Transformer must be initialized using: "
                "'from_crs', 'from_pipeline', or 'from_proj'."
            )
        self._transformer = base_transformer

    @property
    def name(self) -> str:
        """
        str: Name of the projection.
        """
        return self._transformer.id

    @property
    def description(self) -> str:
        """
        str: Description of the projection.
        """
        return self._transformer.description

    @property
    def definition(self) -> str:
        """
        str: Definition of the projection.
        """
        return self._transformer.definition

    @property
    def has_inverse(self) -> bool:
        """
        bool: True if an inverse mapping exists.
        """
        return self._transformer.has_inverse

    @property
    def accuracy(self) -> float:
        """
        float: Expected accuracy of the transformation. -1 if unknown.
        """
        return self._transformer.accuracy

    @property
    def area_of_use(self) -> AreaOfUse:
        """
        .. versionadded:: 2.3.0

        Returns
        -------
        AreaOfUse:
            The area of use object with associated attributes.
        """
        return self._transformer.area_of_use

    @property
    def remarks(self) -> str:
        """
        .. versionadded:: 2.4.0

        Returns
        -------
        str:
            Remarks about object.
        """
        return self._transformer.remarks

    @property
    def scope(self) -> str:
        """
        .. versionadded:: 2.4.0

        Returns
        -------
        str:
            Scope of object.
        """
        return self._transformer.scope

    @property
    def operations(self) -> Optional[Tuple[CoordinateOperation]]:
        """
        .. versionadded:: 2.4.0

        Returns
        -------
        Tuple[CoordinateOperation]:
            The operations in a concatenated operation.
        """
        return self._transformer.operations

    @staticmethod
    def from_proj(
        proj_from: Any,
        proj_to: Any,
        skip_equivalent: bool = False,
        always_xy: bool = False,
        area_of_interest: Optional[AreaOfInterest] = None,
    ) -> "Transformer":
        """Make a Transformer from a :obj:`pyproj.proj.Proj` or input used to create one.

        .. versionadded:: 2.1.2 skip_equivalent
        .. versionadded:: 2.2.0 always_xy
        .. versionadded:: 2.3.0 area_of_interest

        Parameters
        ----------
        proj_from: :obj:`pyproj.proj.Proj` or input used to create one
            Projection of input data.
        proj_to: :obj:`pyproj.proj.Proj` or input used to create one
            Projection of output data.
        skip_equivalent: bool, optional
            If true, will skip the transformation operation if input and output
            projections are equivalent. Default is false.
        always_xy: bool, optional
            If true, the transform method will accept as input and return as output
            coordinates using the traditional GIS order, that is longitude, latitude
            for geographic CRS and easting, northing for most projected CRS.
            Default is false.
        area_of_interest: :class:`pyproj.transformer.AreaOfInterest`, optional
            The area of interest to help select the transformation.

        Returns
        -------
        Transformer

        """
        if not isinstance(proj_from, Proj):
            proj_from = Proj(proj_from)
        if not isinstance(proj_to, Proj):
            proj_to = Proj(proj_to)

        return Transformer.from_crs(
            proj_from.crs,
            proj_to.crs,
            skip_equivalent=skip_equivalent,
            always_xy=always_xy,
            area_of_interest=area_of_interest,
        )

    @staticmethod
    def from_crs(
        crs_from: Any,
        crs_to: Any,
        skip_equivalent: bool = False,
        always_xy: bool = False,
        area_of_interest: Optional[AreaOfInterest] = None,
    ) -> "Transformer":
        """Make a Transformer from a :obj:`pyproj.crs.CRS` or input used to create one.

        .. versionadded:: 2.1.2 skip_equivalent
        .. versionadded:: 2.2.0 always_xy
        .. versionadded:: 2.3.0 area_of_interest

        Parameters
        ----------
        crs_from: pyproj.crs.CRS or input used to create one
            Projection of input data.
        crs_to: pyproj.crs.CRS or input used to create one
            Projection of output data.
        skip_equivalent: bool, optional
            If true, will skip the transformation operation if input and output
            projections are equivalent. Default is false.
        always_xy: bool, optional
            If true, the transform method will accept as input and return as output
            coordinates using the traditional GIS order, that is longitude, latitude
            for geographic CRS and easting, northing for most projected CRS.
            Default is false.
        area_of_interest: :class:`pyproj.transformer.AreaOfInterest`, optional
            The area of interest to help select the transformation.

        Returns
        -------
        Transformer

        """
        return Transformer(
            _Transformer.from_crs(
                CRS.from_user_input(crs_from),
                CRS.from_user_input(crs_to),
                skip_equivalent=skip_equivalent,
                always_xy=always_xy,
                area_of_interest=area_of_interest,
            )
        )

    @staticmethod
    def from_pipeline(proj_pipeline: str) -> "Transformer":
        """Make a Transformer from a PROJ pipeline string.

        https://proj.org/operations/pipeline.html

        Parameters
        ----------
        proj_pipeline: str
            Projection pipeline string.

        Returns
        -------
        Transformer

        """
        return Transformer(_Transformer.from_pipeline(cstrencode(proj_pipeline)))

    def transform(
        self,
        xx: Any,
        yy: Any,
        zz: Any = None,
        tt: Any = None,
        radians: bool = False,
        errcheck: bool = False,
        direction: Union[TransformDirection, str] = TransformDirection.FORWARD,
    ) -> Any:
        """
        Transform points between two coordinate systems.

        .. versionadded:: 2.1.1 errcheck
        .. versionadded:: 2.2.0 direction

        Parameters
        ----------
        xx: scalar or array (numpy or python)
            Input x coordinate(s).
        yy: scalar or array (numpy or python)
            Input y coordinate(s).
        zz: scalar or array (numpy or python), optional
            Input z coordinate(s).
        tt: scalar or array (numpy or python), optional
            Input time coordinate(s).
        radians: boolean, optional
            If True, will expect input data to be in radians and will return radians
            if the projection is geographic. Default is False (degrees). Ignored for
            pipeline transformations.
        errcheck: boolean, optional (default False)
            If True an exception is raised if the transformation is invalid.
            By default errcheck=False and an invalid transformation
            returns ``inf`` and no exception is raised.
        direction: pyproj.enums.TransformDirection, optional
            The direction of the transform.
            Default is :attr:`pyproj.enums.TransformDirection.FORWARD`.


        Example:

        >>> from pyproj import Transformer
        >>> transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        >>> x3, y3 = transformer.transform(33, 98)
        >>> "%.3f  %.3f" % (x3, y3)
        '10909310.098  3895303.963'
        >>> pipeline_str = (
        ...     "+proj=pipeline +step +proj=longlat +ellps=WGS84 "
        ...     "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
        ... )
        >>> pipe_trans = Transformer.from_pipeline(pipeline_str)
        >>> xt, yt = pipe_trans.transform(2.1, 0.001)
        >>> "%.3f  %.3f" % (xt, yt)
        '2.100  0.001'
        >>> transproj = Transformer.from_crs(
        ...     {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
        ...     "EPSG:4326",
        ...     always_xy=True,
        ... )
        >>> xpj, ypj, zpj = transproj.transform(
        ...     -2704026.010,
        ...     -4253051.810,
        ...     3895878.820,
        ...     radians=True,
        ... )
        >>> "%.3f %.3f %.3f" % (xpj, ypj, zpj)
        '-2.137 0.661 -20.531'
        >>> transprojr = Transformer.from_crs(
        ...     "EPSG:4326",
        ...     {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
        ...     always_xy=True,
        ... )
        >>> xpjr, ypjr, zpjr = transprojr.transform(xpj, ypj, zpj, radians=True)
        >>> "%.3f %.3f %.3f" % (xpjr, ypjr, zpjr)
        '-2704026.010 -4253051.810 3895878.820'
        >>> transformer = Transformer.from_proj("epsg:4326", 4326, skip_equivalent=True)
        >>> xeq, yeq = transformer.transform(33, 98)
        >>> "%.0f  %.0f" % (xeq, yeq)
        '33  98'

        """
        # process inputs, making copies that support buffer API.
        inx, xisfloat, xislist, xistuple = _copytobuffer(xx)
        iny, yisfloat, yislist, yistuple = _copytobuffer(yy)
        if zz is not None:
            inz, zisfloat, zislist, zistuple = _copytobuffer(zz)
        else:
            inz = None
        if tt is not None:
            intime, tisfloat, tislist, tistuple = _copytobuffer(tt)
        else:
            intime = None
        # call pj_transform.  inx,iny,inz buffers modified in place.
        self._transformer._transform(
            inx,
            iny,
            inz=inz,
            intime=intime,
            direction=direction,
            radians=radians,
            errcheck=errcheck,
        )
        # if inputs were lists, tuples or floats, convert back.
        outx = _convertback(xisfloat, xislist, xistuple, inx)
        outy = _convertback(yisfloat, yislist, xistuple, iny)
        return_data = (outx, outy)
        if inz is not None:
            return_data += (  # type: ignore
                _convertback(zisfloat, zislist, zistuple, inz),
            )
        if intime is not None:
            return_data += (  # type: ignore
                _convertback(tisfloat, tislist, tistuple, intime),
            )
        return return_data

    def itransform(
        self,
        points: Any,
        switch: bool = False,
        time_3rd: bool = False,
        radians: bool = False,
        errcheck: bool = False,
        direction: Union[TransformDirection, str] = TransformDirection.FORWARD,
    ) -> Iterator[Iterable]:
        """
        Iterator/generator version of the function pyproj.Transformer.transform.

        .. versionadded:: 2.1.1 errcheck
        .. versionadded:: 2.2.0 direction

        Parameters
        ----------
        points: list
            List of point tuples.
        switch: boolean, optional
            If True x, y or lon,lat coordinates of points are switched to y, x
            or lat, lon. Default is False.
        time_3rd: boolean, optional
            If the input coordinates are 3 dimensional and the 3rd dimension is time.
        radians: boolean, optional
            If True, will expect input data to be in radians and will return radians
            if the projection is geographic. Default is False (degrees). Ignored for
            pipeline transformations.
        errcheck: boolean, optional (default False)
            If True an exception is raised if the transformation is invalid.
            By default errcheck=False and an invalid transformation
            returns ``inf`` and no exception is raised.
        direction: pyproj.enums.TransformDirection, optional
            The direction of the transform.
            Default is :attr:`pyproj.enums.TransformDirection.FORWARD`.


        Example:

        >>> from pyproj import Transformer
        >>> transformer = Transformer.from_crs(4326, 2100)
        >>> points = [(22.95, 40.63), (22.81, 40.53), (23.51, 40.86)]
        >>> for pt in transformer.itransform(points): '{:.3f} {:.3f}'.format(*pt)
        '2221638.801 2637034.372'
        '2212924.125 2619851.898'
        '2238294.779 2703763.736'
        >>> pipeline_str = (
        ...     "+proj=pipeline +step +proj=longlat +ellps=WGS84 "
        ...     "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
        ... )
        >>> pipe_trans = Transformer.from_pipeline(pipeline_str)
        >>> for pt in pipe_trans.itransform([(2.1, 0.001)]):
        ...     '{:.3f} {:.3f}'.format(*pt)
        '2.100 0.001'
        >>> transproj = Transformer.from_crs(
        ...     {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
        ...     "EPSG:4326",
        ...     always_xy=True,
        ... )
        >>> for pt in transproj.itransform(
        ...     [(-2704026.010, -4253051.810, 3895878.820)],
        ...     radians=True,
        ... ):
        ...     '{:.3f} {:.3f} {:.3f}'.format(*pt)
        '-2.137 0.661 -20.531'
        >>> transprojr = Transformer.from_crs(
        ...     "EPSG:4326",
        ...     {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
        ...     always_xy=True,
        ... )
        >>> for pt in transprojr.itransform(
        ...     [(-2.137, 0.661, -20.531)],
        ...     radians=True
        ... ):
        ...     '{:.3f} {:.3f} {:.3f}'.format(*pt)
        '-2704214.394 -4254414.478 3894270.731'
        >>> transproj_eq = Transformer.from_proj(
        ...     'EPSG:4326',
        ...     '+proj=longlat +datum=WGS84 +no_defs +type=crs',
        ...     always_xy=True,
        ...     skip_equivalent=True
        ... )
        >>> for pt in transproj_eq.itransform([(-2.137, 0.661)]):
        ...     '{:.3f} {:.3f}'.format(*pt)
        '-2.137 0.661'

        """
        it = iter(points)  # point iterator
        # get first point to check stride
        try:
            fst_pt = next(it)
        except StopIteration:
            raise ValueError("iterable must contain at least one point")

        stride = len(fst_pt)
        if stride not in (2, 3, 4):
            raise ValueError("points can contain up to 4 coordinates")

        if time_3rd and stride != 3:
            raise ValueError("'time_3rd' is only valid for 3 coordinates.")

        # create a coordinate sequence generator etc. x1,y1,z1,x2,y2,z2,....
        # chain so the generator returns the first point that was already acquired
        coord_gen = chain(fst_pt, (coords[c] for coords in it for c in range(stride)))

        while True:
            # create a temporary buffer storage for
            # the next 64 points (64*stride*8 bytes)
            buff = array("d", islice(coord_gen, 0, 64 * stride))
            if len(buff) == 0:
                break

            self._transformer._transform_sequence(
                stride,
                buff,
                switch=switch,
                direction=direction,
                time_3rd=time_3rd,
                radians=radians,
                errcheck=errcheck,
            )

            for pt in zip(*([iter(buff)] * stride)):
                yield pt

    def to_wkt(
        self,
        version: Union[WktVersion, str] = WktVersion.WKT2_2019,
        pretty: bool = False,
    ):
        """
        Convert the projection to a WKT string.

        Version options:
          - WKT2_2015
          - WKT2_2015_SIMPLIFIED
          - WKT2_2019
          - WKT2_2019_SIMPLIFIED
          - WKT1_GDAL
          - WKT1_ESRI


        Parameters
        ----------
        version: pyproj.enums.WktVersion
            The version of the WKT output.
            Default is :attr:`pyproj.enums.WktVersion.WKT2_2019`.
        pretty: bool
            If True, it will set the output to be a multiline string. Defaults to False.

        Returns
        -------
        str:
            The WKT string.
        """
        return self._transformer.to_wkt(version=version, pretty=pretty)

    def to_json(self, pretty: bool = False, indentation: int = 2) -> str:
        """
        Convert the projection to a JSON string.

        .. versionadded:: 2.4.0

        Parameters
        ----------
        pretty: bool
            If True, it will set the output to be a multiline string. Defaults to False.
        indentation: int
            If pretty is True, it will set the width of the indentation. Default is 2.

        Returns
        -------
        str:
            The JSON string.
        """
        return self._transformer.to_json(pretty=pretty, indentation=indentation)

    def to_json_dict(self) -> dict:
        """
        Convert the projection to a JSON dictionary.

        .. versionadded:: 2.4.0

        Returns
        -------
        dict:
            The JSON dictionary.
        """
        return self._transformer.to_json_dict()

    def __str__(self) -> str:
        return self.definition

    def __repr__(self) -> str:
        return (
            "<{type_name}: {name}>\nDescription: {description}\n"
            "Area of Use:\n{area_of_use}"
        ).format(
            type_name=self._transformer.type_name,
            name=self.name,
            description=self.description,
            area_of_use=self.area_of_use or "- undefined",
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Transformer):
            return False
        return self._transformer.__eq__(other._transformer)


def transform(
    p1: Any,
    p2: Any,
    x: Any,
    y: Any,
    z: Any = None,
    tt: Any = None,
    radians: bool = False,
    errcheck: bool = False,
    skip_equivalent: bool = False,
    always_xy: bool = False,
):
    """
    .. versionadded:: 2.1.2 skip_equivalent
    .. versionadded:: 2.2.0 always_xy

    x2, y2, z2 = transform(p1, p2, x1, y1, z1)

    Transform points between two coordinate systems defined by the
    Proj instances p1 and p2.

    The points x1,y1,z1 in the coordinate system defined by p1 are
    transformed to x2,y2,z2 in the coordinate system defined by p2.

    z1 is optional, if it is not set it is assumed to be zero (and
    only x2 and y2 are returned). If the optional keyword
    'radians' is True (default is False), then all input and
    output coordinates will be in radians instead of the default
    of degrees for geographic input/output projections.
    If the optional keyword 'errcheck' is set to True an
    exception is raised if the transformation is
    invalid. By default errcheck=False and ``inf`` is returned for an
    invalid transformation (and no exception is raised).
    If the optional kwarg skip_equivalent is true (default is False),
    it will skip the transformation operation if input and output
    projections are equivalent. If `always_xy` is toggled, the
    transform method will accept as input and return as output
    coordinates using the traditional GIS order, that is longitude, latitude
    for geographic CRS and easting, northing for most projected CRS.

    In addition to converting between cartographic and geographic
    projection coordinates, this function can take care of datum
    shifts (which cannot be done using the __call__ method of the
    Proj instances). It also allows for one of the coordinate
    systems to be geographic (proj = 'latlong').

    x,y and z can be numpy or regular python arrays, python
    lists/tuples or scalars. Arrays are fastest.  For projections in
    geocentric coordinates, values of x and y are given in meters.
    z is always meters.

    Example usage:

    >>> from pyproj import Proj, transform
    >>> # projection 1: UTM zone 15, grs80 ellipse, NAD83 datum
    >>> # (defined by epsg code 26915)
    >>> p1 = Proj('epsg:26915', preserve_units=False)
    >>> # projection 2: UTM zone 15, clrk66 ellipse, NAD27 datum
    >>> p2 = Proj('epsg:26715', preserve_units=False)
    >>> # find x,y of Jefferson City, MO.
    >>> x1, y1 = p1(-92.199881,38.56694)
    >>> # transform this point to projection 2 coordinates.
    >>> x2, y2 = transform(p1,p2,x1,y1)
    >>> '%9.3f %11.3f' % (x1,y1)
    '569704.566 4269024.671'
    >>> '%9.3f %11.3f' % (x2,y2)
    '569722.342 4268814.028'
    >>> '%8.3f %5.3f' % p2(x2,y2,inverse=True)
    ' -92.200 38.567'
    >>> # process 3 points at a time in a tuple
    >>> lats = (38.83,39.32,38.75) # Columbia, KC and StL Missouri
    >>> lons = (-92.22,-94.72,-90.37)
    >>> x1, y1 = p1(lons,lats)
    >>> x2, y2 = transform(p1,p2,x1,y1)
    >>> xy = x1+y1
    >>> '%9.3f %9.3f %9.3f %11.3f %11.3f %11.3f' % xy
    '567703.344 351730.944 728553.093 4298200.739 4353698.725 4292319.005'
    >>> xy = x2+y2
    >>> '%9.3f %9.3f %9.3f %11.3f %11.3f %11.3f' % xy
    '567721.149 351747.558 728569.133 4297989.112 4353489.645 4292106.305'
    >>> lons, lats = p2(x2,y2,inverse=True)
    >>> xy = lons+lats
    >>> '%8.3f %8.3f %8.3f %5.3f %5.3f %5.3f' % xy
    ' -92.220  -94.720  -90.370 38.830 39.320 38.750'
    """
    return Transformer.from_proj(
        p1, p2, skip_equivalent=skip_equivalent, always_xy=always_xy
    ).transform(xx=x, yy=y, zz=z, tt=tt, radians=radians, errcheck=errcheck)


def itransform(
    p1: Any,
    p2: Any,
    points: Iterable[Iterable],
    switch: bool = False,
    time_3rd: bool = False,
    radians: bool = False,
    errcheck: bool = False,
    skip_equivalent: bool = False,
    always_xy: bool = False,
):
    """
    .. versionadded:: 2.1.2 skip_equivalent
    .. versionadded:: 2.2.0 always_xy

    points2 = itransform(p1, p2, points1)
    Iterator/generator version of the function pyproj.transform.
    Transform points between two coordinate systems defined by the
    Proj instances p1 and p2. This function can be used as an alternative
    to pyproj.transform when there is a need to transform a big number of
    coordinates lazily, for example when reading and processing from a file.
    Points1 is an iterable/generator of coordinates x1,y1(,z1) or lon1,lat1(,z1)
    in the coordinate system defined by p1. Points2 is an iterator that returns tuples
    of x2,y2(,z2) or lon2,lat2(,z2) coordinates in the coordinate system defined by p2.
    z are provided optionally.

    Points1 can be:
        - a tuple/list of tuples/lists i.e. for 2d points: [(xi,yi),(xj,yj),....(xn,yn)]
        - a Nx3 or Nx2 2d numpy array where N is the point number
        - a generator of coordinates (xi,yi) for 2d points or (xi,yi,zi) for 3d

    If optional keyword 'switch' is True (default is False) then x, y or lon,lat
    coordinates of points are switched to y, x or lat, lon.
    If the optional keyword 'radians' is True (default is False),
    then all input and output coordinates will be in radians instead
    of the default of degrees for geographic input/output projections.
    If the optional keyword 'errcheck' is set to True an
    exception is raised if the transformation is
    invalid. By default errcheck=False and ``inf`` is returned for an
    invalid transformation (and no exception is raised).
    If the optional kwarg skip_equivalent is true (default is False),
    it will skip the transformation operation if input and output
    projections are equivalent. If `always_xy` is toggled, the
    transform method will accept as input and return as output
    coordinates using the traditional GIS order, that is longitude, latitude
    for geographic CRS and easting, northing for most projected CRS.


    Example usage:

    >>> from pyproj import Proj, itransform
    >>> # projection 1: WGS84
    >>> # (defined by epsg code 4326)
    >>> p1 = Proj('epsg:4326', preserve_units=False)
    >>> # projection 2: GGRS87 / Greek Grid
    >>> p2 = Proj('epsg:2100', preserve_units=False)
    >>> # Three points with coordinates lon, lat in p1
    >>> points = [(22.95, 40.63), (22.81, 40.53), (23.51, 40.86)]
    >>> # transform this point to projection 2 coordinates.
    >>> for pt in itransform(p1,p2,points, always_xy=True): '%6.3f %7.3f' % pt
    '411050.470 4497928.574'
    '399060.236 4486978.710'
    '458553.243 4523045.485'
    >>> for pt in itransform(4326, 4326, [(30, 60)], skip_equivalent=True):
    ...     '{:.0f} {:.0f}'.format(*pt)
    '30 60'

    """
    return Transformer.from_proj(
        p1, p2, skip_equivalent=skip_equivalent, always_xy=always_xy
    ).itransform(
        points, switch=switch, time_3rd=time_3rd, radians=radians, errcheck=errcheck
    )
