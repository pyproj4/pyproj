# -*- coding: utf-8 -*-
"""
This module interfaces with proj.4 to produce a pythonic interface
to the coordinate reference system (CRS) information through the CRS
class.

Original Author: Alan D. Snow [github.com/snowman2] (2019)

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
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""
__all__ = ["CRS", "is_wkt"]

import json

from pyproj._crs import _CRS, is_wkt
from pyproj.compat import string_types
from pyproj.exceptions import CRSError
from pyproj.geod import Geod


def _dict2string(projparams):
    # convert a dict to a proj4 string.
    pjargs = []
    for key, value in projparams.items():
        # issue 183 (+ no_rot)
        if value is None or value is True:
            pjargs.append("+" + key + " ")
        elif value is False:
            pass
        else:
            pjargs.append("+" + key + "=" + str(value) + " ")
    return "".join(pjargs)


class CRS(_CRS):
    """
    A pythonic Coordinate Reference System manager.

    The functionality is based on other fantastic projects:

    * https://github.com/opendatacube/datacube-core/blob/83bae20d2a2469a6417097168fd4ede37fd2abe5/datacube/utils/geometry/_base.py
    * https://github.com/mapbox/rasterio/blob/c13f0943b95c0eaa36ff3f620bd91107aa67b381/rasterio/_crs.pyx

    """

    def __init__(self, projparams=None, **kwargs):
        """
        Initialize a CRS class instance with a WKT string,
        a proj,4 string, a proj.4 dictionary, or with
        proj.4 keyword arguments.

        CRS projection control parameters must either be given in a
        dictionary 'projparams' or as keyword arguments. See the proj.4
        documentation (https://github.com/OSGeo/proj.4/wiki) for more information
        about specifying projection parameters.

        Example usage:

        >>> from pyproj import CRS
        >>> crs_utm = CRS.from_user_input(26915)
        >>> crs_utm
        <CRS: epsg:26915>
        Name: NAD83 / UTM zone 15N
        Ellipsoid:
        - semi_major_metre: 6378137.00
        - semi_minor_metre: 6356752.31
        - inverse_flattening: 298.26
        Area of Use:
        - name: North America - 96°W to 90°W and NAD83 by country
        - bounds: (-96.0, 25.61, -90.0, 84.0)
        Prime Meridian:
        - longitude: 0.0000
        - unit_name: degree
        - unit_conversion_factor: 0.01745329
        Axis Info:
        - Easting[E] (east) EPSG:9001 (metre)
        - Northing[N] (north) EPSG:9001 (metre)
        <BLANKLINE>
        >>> crs_utm.area_of_use.bounds
        (-96.0, 25.61, -90.0, 84.0)
        >>> crs_utm.ellipsoid.inverse_flattening
        298.257222101
        >>> crs_utm.ellipsoid.semi_major_metre
        6378137.0
        >>> crs_utm.ellipsoid.semi_minor_metre
        6356752.314140356
        >>> crs_utm.prime_meridian.unit_name
        'degree'
        >>> crs_utm.prime_meridian.unit_conversion_factor
        0.017453292519943295
        >>> crs_utm.prime_meridian.longitude
        0.0
        >>> crs = CRS(proj='utm', zone=10, ellps='WGS84')
        >>> crs.to_proj4()
        '+proj=utm +zone=10 +ellps=WGS84 +units=m +no_defs +type=crs'
        >>> crs.to_wkt()
        'PROJCRS["unknown",BASEGEOGCRS["unknown",DATUM["Unknown based on WGS84 ellipsoid",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1],ID["EPSG",7030]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8901]]],CONVERSION["UTM zone 10N",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",-123,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]],ID["EPSG",16010]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1,ID["EPSG",9001]]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1,ID["EPSG",9001]]]]'
        >>> geod = crs.get_geod()
        >>> "+a={:.0f} +f={:.8f}".format(geod.a, geod.f)
        '+a=6378137 +f=0.00335281'
        >>> crs.is_projected
        True
        >>> crs.is_geographic
        False
        >>> crs.is_valid
        True
        """
        # if projparams is None, use kwargs.
        if projparams is None:
            if len(kwargs) == 0:
                raise CRSError("no projection control parameters specified")
            else:
                projstring = _dict2string(kwargs)
        elif isinstance(projparams, string_types):
            # if projparams is a string or a unicode string, interpret as a proj4 init string.
            projstring = projparams
        else:  # projparams a dict
            projstring = _dict2string(projparams)

        # make sure the projection starts with +proj or +init
        starting_params = ("+init", "+proj")
        if not projstring.lstrip().startswith(starting_params):
            kvpairs = []
            first_item_inserted = False
            for kvpair in projstring.split():
                if not first_item_inserted and (kvpair.startswith(starting_params)):
                    kvpairs.insert(0, kvpair)
                    first_item_inserted = True
                else:
                    kvpairs.append(kvpair)
            projstring = " ".join(kvpairs)
        # look for EPSG, replace with epsg (EPSG only works
        # on case-insensitive filesystems).
        projstring = projstring.replace("+init=EPSG", "+init=epsg").strip()
        super(CRS, self).__init__(projstring)

    @classmethod
    def from_epsg(cls, code):
        """Make a CRS from an EPSG code

        Parameters
        ----------
        code : int or str
            An EPSG code. Strings will be converted to integers.

        Notes
        -----
        The input code is not validated against an EPSG database.

        Returns
        -------
        CRS
        """
        if int(code) <= 0:
            raise CRSError("EPSG codes are positive integers")
        return cls("epsg:{}".format(code))

    @classmethod
    def from_string(cls, proj_string):
        """Make a CRS from an EPSG, PROJ, or WKT string

        Parameters
        ----------
        proj_string : str
            An EPSG, PROJ, or WKT string.

        Returns
        -------
        CRS
        """
        if not proj_string:
            raise CRSError("CRS is empty or invalid: {!r}".format(proj_string))

        elif proj_string.strip().upper().startswith("EPSG:"):
            auth, val = proj_string.strip().split(":")
            if not val:
                raise CRSError("Invalid CRS: {!r}".format(proj_string))
            return cls.from_epsg(val)

        elif "{" in proj_string:
            # may be json, try to decode it
            try:
                val = json.loads(proj_string, strict=False)
            except ValueError:
                raise CRSError("CRS appears to be JSON but is not valid")

            if not val:
                raise CRSError("CRS is empty JSON")
            else:
                return cls(**val)
        return cls(proj_string)

    @classmethod
    def from_user_input(cls, value):
        """Make a CRS from various input

        Dispatches to from_epsg, from_proj, or from_string

        Parameters
        ----------
        value : obj
            A Python int, dict, or str.

        Returns
        -------
        CRS
        """
        if isinstance(value, _CRS):
            return value
        elif isinstance(value, int):
            return cls.from_epsg(value)
        elif isinstance(value, dict):
            return cls(**value)
        elif isinstance(value, string_types):
            return cls.from_string(value)
        elif hasattr(value, "to_wkt"):
            return cls(value.to_wkt())
        else:
            raise CRSError("CRS is invalid: {!r}".format(value))

    def get_geod(self):
        """
        Returns
        -------
        :obj:`pyproj.Geod`: Geod object based on the CRS.ellipsoid.
        """
        if self.ellipsoid is None or not self.ellipsoid.ellipsoid_loaded:
            return None
        in_kwargs = {
            "a": self.ellipsoid.semi_major_metre,
            "rf": self.ellipsoid.inverse_flattening,
        }
        if self.ellipsoid.is_semi_minor_computed:
            in_kwargs["b"] = self.ellipsoid.semi_minor_metre
        return Geod(**in_kwargs)

    def __reduce__(self):
        """special method that allows CRS instance to be pickled"""
        return self.__class__, (self.srs,)

    def __str__(self):
        return self.srs

    def __repr__(self):
        axis_info_list = []
        for axis_info in self.axis_info:
            axis_info_list.extend([str(axis_info), "\n"])

        axis_info_str = "".join(axis_info_list)
        string_repr = (
            "<CRS: {srs}>\n"
            "Name: {name}\n"
            "Ellipsoid:\n"
            "{ellipsoid}\n"
            "Area of Use:\n"
            "{area_of_use}\n"
            "Prime Meridian:\n"
            "{prime_meridian}\n"
            "Axis Info:\n"
            "{axis_info_str}"
        ).format(
            name=self.name,
            srs=self.srs if len(self.srs) <= 50 else " ".join([self.srs[:50], "..."]),
            ellipsoid=self.ellipsoid or "- UNDEFINED",
            area_of_use=self.area_of_use or "- UNDEFINED",
            prime_meridian=self.prime_meridian or "- UNDEFINED",
            axis_info_str=axis_info_str or "- UNDEFINED",
        )
        return string_repr
