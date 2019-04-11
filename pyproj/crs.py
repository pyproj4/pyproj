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
import warnings

from pyproj._crs import _CRS, is_wkt
from pyproj.cf1x8 import (
    GRID_MAPPING_NAME_MAP,
    INVERSE_GRID_MAPPING_NAME_MAP,
    INVERSE_PROJ_PARAM_MAP,
    K_0_MAP,
    LON_0_MAP,
    PROJ_PARAM_MAP,
)
from pyproj.compat import string_types
from pyproj.exceptions import CRSError
from pyproj.geod import Geod


def _dict2string(projparams):
    # convert a dict to a proj4 string.
    pjargs = []
    for key, value in projparams.items():
        # the towgs84 as list
        if isinstance(value, (list, tuple)):
            value = ",".join([str(val) for val in value])
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

    * `rasterio <https://github.com/mapbox/rasterio/blob/c13f0943b95c0eaa36ff3f620bd91107aa67b381/rasterio/_crs.pyx>`_
    * `opendatacube <https://github.com/opendatacube/datacube-core/blob/83bae20d2a2469a6417097168fd4ede37fd2abe5/datacube/utils/geometry/_base.py>`_

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
        ~CRS
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
        ~CRS
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
        ~CRS
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
        ~pyproj.geod.Geod: Geod object based on the ellipsoid.
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

    def to_proj4_dict(self):
        """
        Converts the PROJ string to a dict.

        Returns
        -------
        dict: PROJ params in dict format.

        """

        def parse(val):
            if val.lower() == "true":
                return True
            elif val.lower() == "false":
                return False
            try:
                return int(val)
            except ValueError:
                pass
            try:
                return float(val)
            except ValueError:
                pass
            val_split = val.split(",")
            if len(val_split) > 1:
                val = [float(sval.strip()) for sval in val_split]
            return val

        items = map(
            lambda kv: len(kv) == 2 and (kv[0], parse(kv[1])) or (kv[0], None),
            (
                part.lstrip("+").split("=", 1)
                for part in self.to_proj4().strip().split()
            ),
        )

        return {key: value for key, value in items if value is not False}

    def to_cf(self, wkt_version="WKT2_2018", errcheck=False):
        """
        This converts a :obj:`~pyproj.crs.CRS` object
        to a CF-1.8 dict.

        .. warning:: The full projection will be stored in the
            crs_wkt attribute. However, other parameters may be lost
            if a mapping to the CF parameter is not found.

        Parameters
        ----------
        wkt_version: str
            Version of WKT supported by ~CRS.to_wkt.
        errcheck: bool, optional
            If True, will warn when parameters are ignored. Defaults to False.

        Returns
        -------
        dict: CF-1.8 version of the projection.

        """

        cf_dict = {"crs_wkt": self.to_wkt(wkt_version)}
        if self.is_geographic and self.name != "unknown":
            cf_dict["geographic_crs_name"] = self.name
        elif self.is_projected and self.name != "unknown":
            cf_dict["projected_crs_name"] = self.name

        proj_dict = self.to_proj4_dict()
        proj_name = proj_dict.pop("proj")
        if proj_name in ("lonlat", "latlon", "longlat", "latlong"):
            grid_mapping_name = "latitude_longitude"
        else:
            grid_mapping_name = INVERSE_GRID_MAPPING_NAME_MAP.get(proj_name, "unknown")
        cf_dict["grid_mapping_name"] = grid_mapping_name

        # get best match for lon_0 value for projetion name
        lon_0 = proj_dict.pop("lon_0", None)
        if lon_0 is not None:
            try:
                cf_dict[LON_0_MAP[grid_mapping_name]] = lon_0
            except KeyError:
                cf_dict[LON_0_MAP["DEFAULT"]] = lon_0

        # get best match for k_0 value for projetion name
        k_0 = proj_dict.pop("k_0", None)
        if k_0 is not None:
            try:
                cf_dict[K_0_MAP[grid_mapping_name]] = k_0
            except KeyError:
                cf_dict[K_0_MAP["DEFAULT"]] = k_0

        # format the lat_1 and lat_2 for the standard parallel
        if "lat_1" in proj_dict and "lat_2" in proj_dict:
            cf_dict["standard_parallel"] = [
                proj_dict.pop("lat_1"),
                proj_dict.pop("lat_2"),
            ]
        elif "lat_1" in proj_dict:
            cf_dict["standard_parallel"] = proj_dict.pop("lat_1")

        skipped_params = []
        for proj_param, proj_val in proj_dict.items():
            try:
                cf_dict[INVERSE_PROJ_PARAM_MAP[proj_param]] = proj_val
            except KeyError:
                skipped_params.append(proj_param)

        if errcheck and skipped_params:
            warnings.warn(
                "PROJ parameters not mapped to CF: {}".format(tuple(skipped_params))
            )
        return cf_dict

    @staticmethod
    def from_cf(in_cf, errcheck=False):
        """
        This converts a CF-1.8 dict to a
        :obj:`~pyproj.crs.CRS` object.

        .. warning:: Parameters may be lost if a mapping 
            from the CF parameter is not found. For best results
            store the WKT of the projection in the crs_wkt attribute.

        Parameters
        ----------
        in_cf: dict
            CF version of the projection.
        errcheck: bool, optional
            If True, will warn when parameters are ignored. Defaults to False.

        Returns
        -------
        ~pyproj.crs.CRS: CRS object.
        """
        in_cf = in_cf.copy()  # preserve user input
        if "crs_wkt" in in_cf:
            return CRS(in_cf["crs_wkt"])
        elif "spatial_ref" in in_cf:  # for previous supported WKT key
            return CRS(in_cf["spatial_ref"])

        grid_mapping_name = in_cf.pop("grid_mapping_name", None)
        if grid_mapping_name is None:
            raise CRSError("CF projection parameters missing 'grid_mapping_name'")
        proj_name = GRID_MAPPING_NAME_MAP.get(grid_mapping_name)
        if proj_name is None:
            raise CRSError(
                "Unsupported grid mapping name: {}".format(grid_mapping_name)
            )
        proj_dict = {"proj": proj_name}
        if grid_mapping_name == "rotated_latitude_longitude":
            proj_dict["o_proj"] = "latlon"
        elif grid_mapping_name == "oblique_mercator":
            try:
                proj_dict["lonc"] = in_cf.pop("longitude_of_projection_origin")
            except KeyError:
                pass

        if "standard_parallel" in in_cf:
            standard_parallel = in_cf.pop("standard_parallel")
            if isinstance(standard_parallel, list):
                proj_dict["lat_1"] = standard_parallel[0]
                proj_dict["lat_2"] = standard_parallel[1]
            else:
                proj_dict["lat_1"] = standard_parallel

        skipped_params = []
        for cf_param, proj_val in in_cf.items():
            try:
                proj_dict[PROJ_PARAM_MAP[cf_param]] = proj_val
            except KeyError:
                skipped_params.append(cf_param)

        if errcheck and skipped_params:
            warnings.warn(
                "CF parameters not mapped to PROJ: {}".format(tuple(skipped_params))
            )

        return CRS(proj_dict)

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
