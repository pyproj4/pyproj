"""
Performs cartographic transformations (converts from
longitude,latitude to native map projection x,y coordinates and
vice versa) using PROJ (https://proj.org).

A Proj class instance is initialized with proj map projection
control parameter key/value pairs. The key/value pairs can
either be passed in a dictionary, or as keyword arguments,
or as a PROJ string (compatible with the proj command). See
https://proj.org/operations/projections/index.html for examples of
key/value pairs defining different map projections.

Calling a Proj class instance with the arguments lon, lat will
convert lon/lat (in degrees) to x/y native map projection
coordinates (in meters).
"""
import re
import warnings
from typing import Any, Optional, Tuple, Type

from pyproj._transformer import Factors, _Transformer
from pyproj.compat import cstrencode, pystrdecode
from pyproj.crs import CRS
from pyproj.enums import TransformDirection
from pyproj.list import get_proj_operations_map
from pyproj.transformer import Transformer
from pyproj.utils import _convertback, _copytobuffer

pj_list = get_proj_operations_map()


class Proj(Transformer):
    """
    Performs cartographic transformations. Converts from
    longitude, latitude to native map projection x,y coordinates and
    vice versa using PROJ (https://proj.org).

    Attributes
    ----------
    srs: str
        The string form of the user input used to create the Proj.
    crs: pyproj.crs.CRS
        The CRS object associated with the Proj.

    """

    def __init__(
        self, projparams: Any = None, preserve_units: bool = True, **kwargs
    ) -> None:
        """
        A Proj class instance is initialized with proj map projection
        control parameter key/value pairs. The key/value pairs can
        either be passed in a dictionary, or as keyword arguments,
        or as a PROJ string (compatible with the proj command). See
        https://proj.org/operations/projections/index.html for examples of
        key/value pairs defining different map projections.

        Parameters
        ----------
        projparams: int, str, dict, pyproj.CRS
            A PROJ or WKT string, PROJ dict, EPSG integer, or a pyproj.CRS instance.
        preserve_units: bool
            If false, will ensure +units=m.
        **kwargs:
            PROJ projection parameters.


        Example usage:

        >>> from pyproj import Proj
        >>> p = Proj(proj='utm',zone=10,ellps='WGS84', preserve_units=False)
        >>> x,y = p(-120.108, 34.36116666)
        >>> 'x=%9.3f y=%11.3f' % (x,y)
        'x=765975.641 y=3805993.134'
        >>> 'lon=%8.3f lat=%5.3f' % p(x,y,inverse=True)
        'lon=-120.108 lat=34.361'
        >>> # do 3 cities at a time in a tuple (Fresno, LA, SF)
        >>> lons = (-119.72,-118.40,-122.38)
        >>> lats = (36.77, 33.93, 37.62 )
        >>> x,y = p(lons, lats)
        >>> 'x: %9.3f %9.3f %9.3f' % x
        'x: 792763.863 925321.537 554714.301'
        >>> 'y: %9.3f %9.3f %9.3f' % y
        'y: 4074377.617 3763936.941 4163835.303'
        >>> lons, lats = p(x, y, inverse=True) # inverse transform
        >>> 'lons: %8.3f %8.3f %8.3f' % lons
        'lons: -119.720 -118.400 -122.380'
        >>> 'lats: %8.3f %8.3f %8.3f' % lats
        'lats:   36.770   33.930   37.620'
        >>> p2 = Proj('+proj=utm +zone=10 +ellps=WGS84', preserve_units=False)
        >>> x,y = p2(-120.108, 34.36116666)
        >>> 'x=%9.3f y=%11.3f' % (x,y)
        'x=765975.641 y=3805993.134'
        >>> p = Proj("epsg:32667", preserve_units=False)
        >>> 'x=%12.3f y=%12.3f (meters)' % p(-114.057222, 51.045)
        'x=-1783506.250 y= 6193827.033 (meters)'
        >>> p = Proj("epsg:32667")
        >>> 'x=%12.3f y=%12.3f (feet)' % p(-114.057222, 51.045)
        'x=-5851386.754 y=20320914.191 (feet)'
        >>> # test data with radian inputs
        >>> p1 = Proj("epsg:4214")
        >>> x1, y1 = p1(116.366, 39.867)
        >>> f'{x1:.3f} {y1:.3f}'
        '116.366 39.867'
        >>> x2, y2 = p1(x1, y1, inverse=True)
        >>> f'{x2:.3f} {y2:.3f}'
        '116.366 39.867'
        """
        self.crs = CRS.from_user_input(projparams, **kwargs)
        # make sure units are meters if preserve_units is False.
        if not preserve_units and "foot" in self.crs.axis_info[0].unit_name:
            # ignore export to PROJ string deprecation warning
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    "You will likely lose important projection information",
                    UserWarning,
                )
                projstring = self.crs.to_proj4(4)
            projstring = re.sub(r"\s\+units=[\w-]+", "", projstring)
            projstring += " +units=m"
            self.crs = CRS(projstring)

        # ignore export to PROJ string deprecation warning
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                "You will likely lose important projection information",
                UserWarning,
            )
            projstring = self.crs.to_proj4() or self.crs.srs

        self.srs = re.sub(r"\s\+?type=crs", "", projstring).strip()
        super().__init__(_Transformer.from_pipeline(cstrencode(self.srs)))

    def __call__(
        self,
        longitude: Any,
        latitude: Any,
        inverse: bool = False,
        errcheck: bool = False,
        radians: bool = False,
    ) -> Tuple[Any, Any]:
        """
        Calling a Proj class instance with the arguments lon, lat will
        convert lon/lat (in degrees) to x/y native map projection
        coordinates (in meters).

        Inputs should be doubles (they will be cast to doubles if they
        are not, causing a slight performance hit).

        Works with numpy and regular python array objects, python
        sequences and scalars, but is fastest for array objects.

        Parameters
        ----------
        longitude: scalar or array (numpy or python)
            Input longitude coordinate(s).
        latitude: scalar or array (numpy or python)
            Input latitude coordinate(s).
        inverse: boolean, optional
            If inverse is True the inverse transformation from x/y to
            lon/lat is performed. Default is False.
        radians: boolean, optional
            If True, will expect input data to be in radians and will return radians
            if the projection is geographic. Default is False (degrees).
            This does not work with pyproj 2 and is ignored. It will be enabled again
            in pyproj 3.
        errcheck: boolean, optional
            If True an exception is raised if the errors are found in the process.
            By default errcheck=False and ``inf`` is returned.

        Returns
        -------
        Tuple[Any, Any]:
            The transformed coordinates.
        """
        if inverse:
            direction = TransformDirection.INVERSE
        else:
            direction = TransformDirection.FORWARD
        return self.transform(
            xx=longitude,
            yy=latitude,
            direction=direction,
            errcheck=errcheck,
            radians=radians,
        )

    def get_factors(
        self,
        longitude: Any,
        latitude: Any,
        radians: bool = False,
        errcheck: bool = False,
    ) -> Factors:
        """
        .. versionadded:: 2.6.0

        Calculate various cartographic properties, such as scale factors, angular
        distortion and meridian convergence. Depending on the underlying projection
        values will be calculated either numerically (default) or analytically.

        The function also calculates the partial derivatives of the given
        coordinate.

        Parameters
        ----------
        longitude: scalar or array (numpy or python)
            Input longitude coordinate(s).
        latitude: scalar or array (numpy or python)
            Input latitude coordinate(s).
        radians: boolean, optional
            If True, will expect input data to be in radians.
            Default is False (degrees).
        errcheck: boolean, optional
            If True an exception is raised if the errors are found in the process.
            By default errcheck=False and ``inf`` is returned.

        Returns
        -------
        Factors
        """
        # process inputs, making copies that support buffer API.
        inx, xisfloat, xislist, xistuple = _copytobuffer(longitude)
        iny, yisfloat, yislist, yistuple = _copytobuffer(latitude)

        # calculate the factors
        factors = self._transformer._get_factors(
            inx, iny, radians=radians, errcheck=errcheck
        )

        # if inputs were lists, tuples or floats, convert back.
        return Factors(
            meridional_scale=_convertback(
                xisfloat, xislist, xistuple, factors.meridional_scale
            ),
            parallel_scale=_convertback(
                xisfloat, xislist, xistuple, factors.parallel_scale
            ),
            areal_scale=_convertback(xisfloat, xislist, xistuple, factors.areal_scale),
            angular_distortion=_convertback(
                xisfloat, xislist, xistuple, factors.angular_distortion
            ),
            meridian_parallel_angle=_convertback(
                xisfloat, xislist, xistuple, factors.meridian_parallel_angle
            ),
            meridian_convergence=_convertback(
                xisfloat, xislist, xistuple, factors.meridian_convergence
            ),
            tissot_semimajor=_convertback(
                xisfloat, xislist, xistuple, factors.tissot_semimajor
            ),
            tissot_semiminor=_convertback(
                xisfloat, xislist, xistuple, factors.tissot_semiminor
            ),
            dx_dlam=_convertback(xisfloat, xislist, xistuple, factors.dx_dlam),
            dx_dphi=_convertback(xisfloat, xislist, xistuple, factors.dx_dphi),
            dy_dlam=_convertback(xisfloat, xislist, xistuple, factors.dy_dlam),
            dy_dphi=_convertback(xisfloat, xislist, xistuple, factors.dy_dphi),
        )

    def definition_string(self) -> str:
        """Returns formal definition string for projection

        >>> Proj("epsg:4326").definition_string()
        'proj=longlat datum=WGS84 no_defs ellps=WGS84 towgs84=0,0,0'
        """
        return pystrdecode(self.definition)

    def to_latlong_def(self) -> Optional[str]:
        """return the definition string of the geographic (lat/lon)
        coordinate version of the current projection"""
        return self.crs.geodetic_crs.to_proj4(4) if self.crs.geodetic_crs else None

    def to_latlong(self) -> "Proj":
        """return a new Proj instance which is the geographic (lat/lon)
        coordinate version of the current projection"""
        return Proj(self.crs.geodetic_crs)

    def __reduce__(self) -> Tuple[Type["Proj"], Tuple[str]]:
        """special method that allows pyproj.Proj instance to be pickled"""
        return self.__class__, (self.crs.srs,)
