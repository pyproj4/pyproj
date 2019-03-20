# -*- coding: utf-8 -*-
"""
The transformer module is for performing cartographic transformations.

Copyright (c) 2019 pyproj Contributors.

Permission to use, copy, modify, and distribute this software
and its documentation for any purpose and without fee is hereby
granted, provided that the above copyright notice appear in all
copies and that both the copyright notice and this permission
notice appear in supporting documentation. THE AUTHOR DISCLAIMS
ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT
SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

from array import array
from itertools import chain, islice

from pyproj._transformer import _Transformer
from pyproj.compat import cstrencode
from pyproj.utils import _convertback, _copytobuffer

try:
    from future_builtins import zip  # python 2.6+
except ImportError:
    pass  # python 3.x


class Transformer(object):
    """
    The Transformer class is for facilitating re-using
    transforms without needing to re-create them. The goal
    is to make repeated transforms faster.

    Additionally, it provides multiple methods for initialization.
    """

    @staticmethod
    def from_proj(proj_from, proj_to, skip_equivalent=False):
        """Make a Transformer from a :obj:`pyproj.Proj` or input used to create one.

        Parameters
        ----------
        proj_from: :obj:`pyproj.Proj` or input used to create one
            Projection of input data.
        proj_from: :obj:`pyproj.Proj` or input used to create one
            Projection of output data.
        skip_equivalent: bool, optional
            If true, will skip the transformation operation if input and output 
            projections are equivalent. Default is false.

        Returns
        -------
        :obj:`pyproj.Transformer`

        """

        transformer = Transformer()
        transformer._transformer = _Transformer.from_proj(
            proj_from, proj_to, skip_equivalent
        )
        return transformer

    @staticmethod
    def from_crs(crs_from, crs_to, skip_equivalent=False):
        """Make a Transformer from a :obj:`pyproj.CRS` or input used to create one.

        Parameters
        ----------
        proj_from: :obj:`pyproj.CRS` or input used to create one
            Projection of input data.
        proj_from: :obj:`pyproj.CRS` or input used to create one
            Projection of output data.
        skip_equivalent: bool, optional
            If true, will skip the transformation operation if input and output
            projections are equivalent. Default is false.

        Returns
        -------
        :obj:`pyproj.Transformer`

        """
        transformer = Transformer()
        transformer._transformer = _Transformer.from_crs(
            crs_from, crs_to, skip_equivalent
        )
        return transformer

    @staticmethod
    def from_pipeline(proj_pipeline):
        """Make a Transformer from a PROJ pipeline string.

        https://proj4.org/operations/pipeline.html

        Parameters
        ----------
        proj_pipeline: str
            Projection pipeline string.

        Returns
        -------
        :obj:`pyproj.Transformer`

        """
        transformer = Transformer()
        transformer._transformer = _Transformer.from_pipeline(cstrencode(proj_pipeline))
        return transformer

    def transform(self, xx, yy, zz=None, radians=False, errcheck=False):
        """
        Transform points between two coordinate systems.

        Parameters
        ----------
        xx: scalar or array (numpy or python)
            Input x coordinate(s).
        yy: scalar or array (numpy or python)
            Input y coordinate(s).
        zz: scalar or array (numpy or python), optional
            Input z coordinate(s).
        radians: boolean, optional
            If True, will expect input data to be in radians and will return radians
            if the projection is geographic. Default is False (degrees). Ignored for
            pipeline transformations.
        errcheck: boolean, optional (default False)
            If True an exception is raised if the transformation is invalid.
            By default errcheck=False and an invalid transformation 
            returns ``inf`` and no exception is raised.


        Example:

        >>> from pyproj import Transformer
        >>> transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        >>> x3, y3 = transformer.transform(33, 98)
        >>> "%.3f  %.3f" % (x3, y3)
        '10909310.098  3895303.963'
        >>> pipeline_str = "+proj=pipeline +step +proj=longlat +ellps=WGS84 +step +proj=unitconvert +xy_in=rad +xy_out=deg"
        >>> pipe_trans = Transformer.from_pipeline(pipeline_str)
        >>> xt, yt = pipe_trans.transform(2.1, 0.001)
        >>> "%.3f  %.3f" % (xt, yt)
        '120.321  0.057'
        >>> transproj = Transformer.from_proj({"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'}, '+init=EPSG:4326')
        >>> xpj, ypj, zpj = transproj.transform(-2704026.010, -4253051.810, 3895878.820, radians=True)
        >>> "%.3f %.3f %.3f" % (xpj, ypj, zpj)
        '-2.137 0.661 -20.531'
        >>> transprojr = Transformer.from_proj('+init=EPSG:4326', {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'})
        >>> xpjr, ypjr, zpjr = transprojr.transform(xpj, ypj, zpj, radians=True)
        >>> "%.3f %.3f %.3f" % (xpjr, ypjr, zpjr)
        '-2704026.010 -4253051.810 3895878.820'
        >>> transformer = Transformer.from_crs("epsg:4326", 4326, skip_equivalent=True)
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
        # call pj_transform.  inx,iny,inz buffers modified in place.
        self._transformer._transform(inx, iny, inz, radians, errcheck=errcheck)
        # if inputs were lists, tuples or floats, convert back.
        outx = _convertback(xisfloat, xislist, xistuple, inx)
        outy = _convertback(yisfloat, yislist, xistuple, iny)
        if inz is not None:
            outz = _convertback(zisfloat, zislist, zistuple, inz)
            return outx, outy, outz
        else:
            return outx, outy

    def itransform(self, points, switch=False, radians=False, errcheck=False):
        """
        Iterator/generator version of the function pyproj.Transformer.transform.


        Parameters
        ----------
        points: list
            List of point tuples.
        switch: boolean, optional
            If True x, y or lon,lat coordinates of points are switched to y, x 
            or lat, lon. Default is False.
        radians: boolean, optional
            If True, will expect input data to be in radians and will return radians
            if the projection is geographic. Default is False (degrees). Ignored for
            pipeline transformations.
        errcheck: boolean, optional (default False)
            If True an exception is raised if the transformation is invalid.
            By default errcheck=False and an invalid transformation 
            returns ``inf`` and no exception is raised.


        Example:

        >>> from pyproj import Transformer
        >>> transformer = Transformer.from_crs(4326, 2100)
        >>> points = [(22.95, 40.63), (22.81, 40.53), (23.51, 40.86)]
        >>> for pt in transformer.itransform(points): '{:.3f} {:.3f}'.format(*pt)
        '2221638.801 2637034.372'
        '2212924.125 2619851.898'
        '2238294.779 2703763.736'
        >>> pipeline_str = "+proj=pipeline +step +proj=longlat +ellps=WGS84 +step +proj=unitconvert +xy_in=rad +xy_out=deg"
        >>> pipe_trans = Transformer.from_pipeline(pipeline_str)
        >>> for pt in pipe_trans.itransform([(2.1, 0.001)]): '{:.3f} {:.3f}'.format(*pt)
        '120.321 0.057'
        >>> transproj = Transformer.from_proj({"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'}, '+init=EPSG:4326')
        >>> for pt in transproj.itransform([(-2704026.010, -4253051.810, 3895878.820)], radians=True): '{:.3f} {:.3f} {:.3f}'.format(*pt)
        '-2.137 0.661 -20.531'
        >>> transprojr = Transformer.from_proj('+init=EPSG:4326', {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'})
        >>> for pt in transprojr.itransform([(-2.137, 0.661, -20.531)], radians=True): '{:.3f} {:.3f} {:.3f}'.format(*pt)
        '-2704214.394 -4254414.478 3894270.731'
        >>> transproj_eq = Transformer.from_proj('+init=EPSG:4326', 4326, skip_equivalent=True)
        >>> for pt in transproj_eq.itransform([(-2.137, 0.661)]): '{:.3f} {:.3f}'.format(*pt)
        '-2.137 0.661'

        """
        it = iter(points)  # point iterator
        # get first point to check stride
        try:
            fst_pt = next(it)
        except StopIteration:
            raise ValueError("iterable must contain at least one point")

        stride = len(fst_pt)
        if stride not in (2, 3):
            raise ValueError("points can contain up to 3 coordinates")

        # create a coordinate sequence generator etc. x1,y1,z1,x2,y2,z2,....
        # chain so the generator returns the first point that was already acquired
        coord_gen = chain(fst_pt, (coords[c] for coords in it for c in range(stride)))

        while True:
            # create a temporary buffer storage for the next 64 points (64*stride*8 bytes)
            buff = array("d", islice(coord_gen, 0, 64 * stride))
            if len(buff) == 0:
                break

            self._transformer._transform_sequence(
                stride, buff, switch, radians, errcheck=errcheck
            )

            for pt in zip(*([iter(buff)] * stride)):
                yield pt


def transform(
    p1, p2, x, y, z=None, radians=False, errcheck=False, skip_equivalent=False
):
    """
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
    projections are equivalent.

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
    >>> p1 = Proj(init='epsg:26915', preserve_units=False)
    >>> # projection 2: UTM zone 15, clrk66 ellipse, NAD27 datum
    >>> p2 = Proj(init='epsg:26715', preserve_units=False)
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
    >>> # test datum shifting, installation of extra datum grid files.
    >>> p1 = Proj(proj='latlong',datum='WGS84')
    >>> x1 = -111.5; y1 = 45.25919444444
    >>> p2 = Proj(proj="utm",zone=10,datum='NAD27', preserve_units=False)
    >>> x2, y2 = transform(p1, p2, x1, y1)
    >>> "%s  %s" % (str(x2)[:9],str(y2)[:9])
    '1402291.0  5076289.5'
    >>> from pyproj import CRS
    >>> c1 = CRS(proj='latlong',datum='WGS84')
    >>> x1 = -111.5; y1 = 45.25919444444
    >>> c2 = CRS(proj="utm",zone=10,datum='NAD27')
    >>> x2, y2 = transform(c1, c2, x1, y1)
    >>> "%s  %s" % (str(x2)[:9],str(y2)[:9])
    '1402291.0  5076289.5'
    >>> pj = Proj(init="epsg:4214")
    >>> pjx, pjy = pj(116.366, 39.867)
    >>> xr, yr = transform(pj, Proj(4326), pjx, pjy, radians=True, errcheck=True)
    >>> "%.3f %.3f" % (xr, yr)
    '0.696 2.031'
    >>> xeq, yeq = transform(4326, 4326, 30, 60, skip_equivalent=True)
    >>> "%.0f %.0f" % (xeq, yeq)
    '30 60'
    """
    return Transformer.from_proj(p1, p2, skip_equivalent=skip_equivalent).transform(
        x, y, z, radians, errcheck=errcheck
    )


def itransform(
    p1, p2, points, switch=False, radians=False, errcheck=False, skip_equivalent=False
):
    """
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

    If optional keyword 'switch' is True (default is False) then x, y or lon,lat coordinates
    of points are switched to y, x or lat, lon. If the optional keyword 'radians' is True
    (default is False), then all input and output coordinates will be in radians instead
    of the default of degrees for geographic input/output projections.
    If the optional keyword 'errcheck' is set to True an 
    exception is raised if the transformation is
    invalid. By default errcheck=False and ``inf`` is returned for an
    invalid transformation (and no exception is raised).
    If the optional kwarg skip_equivalent is true (default is False), 
    it will skip the transformation operation if input and output 
    projections are equivalent.


    Example usage:

    >>> from pyproj import Proj, itransform 
    >>> # projection 1: WGS84
    >>> # (defined by epsg code 4326)
    >>> p1 = Proj(init='epsg:4326', preserve_units=False)
    >>> # projection 2: GGRS87 / Greek Grid
    >>> p2 = Proj(init='epsg:2100', preserve_units=False)
    >>> # Three points with coordinates lon, lat in p1
    >>> points = [(22.95, 40.63), (22.81, 40.53), (23.51, 40.86)]
    >>> # transform this point to projection 2 coordinates.
    >>> for pt in itransform(p1,p2,points): '%6.3f %7.3f' % pt
    '411050.470 4497928.574'
    '399060.236 4486978.710'
    '458553.243 4523045.485'
    >>> pj = Proj(init="epsg:4214")
    >>> pjx, pjy = pj(116.366, 39.867)
    >>> for pt in itransform(pj, Proj(4326), [(pjx, pjy)], radians=True, errcheck=True): '{:.3f} {:.3f}'.format(*pt)
    '0.696 2.031'
    >>> for pt in itransform(4326, 4326, [(30, 60)], skip_equivalent=True): '{:.0f} {:.0f}'.format(*pt)
    '30 60'

    """
    return Transformer.from_proj(p1, p2, skip_equivalent=skip_equivalent).itransform(
        points, switch, radians, errcheck=errcheck
    )
