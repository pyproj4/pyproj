"""
This module interfaces with PROJ to produce a pythonic interface
to the coordinate reference system (CRS) information.
"""
import json
import re
import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from pyproj._crs import (  # noqa
    _CRS,
    CoordinateOperation,
    CoordinateSystem,
    Datum,
    Ellipsoid,
    PrimeMeridian,
    _load_proj_json,
    is_proj,
    is_wkt,
)
from pyproj.crs._cf1x8 import (
    _GEOGRAPHIC_GRID_MAPPING_NAME_MAP,
    _GRID_MAPPING_NAME_MAP,
    _INVERSE_GEOGRAPHIC_GRID_MAPPING_NAME_MAP,
    _INVERSE_GRID_MAPPING_NAME_MAP,
    _horizontal_datum_from_params,
    _try_list_if_string,
)
from pyproj.crs.coordinate_operation import ToWGS84Transformation
from pyproj.crs.coordinate_system import Cartesian2DCS, Ellipsoidal2DCS, VerticalCS
from pyproj.enums import WktVersion
from pyproj.exceptions import CRSError
from pyproj.geod import Geod


def _prepare_from_dict(projparams: dict, allow_json: bool = True) -> str:
    # check if it is a PROJ JSON dict
    if "proj" not in projparams and "init" not in projparams and allow_json:
        return json.dumps(projparams)
    # convert a dict to a proj string.
    pjargs = []
    for key, value in projparams.items():
        # the towgs84 as list
        if isinstance(value, (list, tuple)):
            value = ",".join([str(val) for val in value])
        # issue 183 (+ no_rot)
        if value is None or value is True:
            pjargs.append("+{key}".format(key=key))
        elif str(value) == str(False):
            pass
        else:
            pjargs.append("+{key}={value}".format(key=key, value=value))
    return _prepare_from_string(" ".join(pjargs))


def _prepare_from_string(in_crs_string: str) -> str:
    if not in_crs_string:
        raise CRSError("CRS is empty or invalid: {!r}".format(in_crs_string))
    elif "{" in in_crs_string:
        # may be json, try to decode it
        try:
            crs_dict = json.loads(in_crs_string, strict=False)
        except ValueError:
            raise CRSError("CRS appears to be JSON but is not valid")

        if not crs_dict:
            raise CRSError("CRS is empty JSON")
        return _prepare_from_dict(crs_dict)
    elif is_proj(in_crs_string):
        in_crs_string = re.sub(r"[\s+]?=[\s+]?", "=", in_crs_string.lstrip())
        # make sure the projection starts with +proj or +init
        starting_params = ("+init", "+proj", "init", "proj")
        if not in_crs_string.startswith(starting_params):
            kvpairs = []  # type: List[str]
            first_item_inserted = False
            for kvpair in in_crs_string.split():
                if not first_item_inserted and (kvpair.startswith(starting_params)):
                    kvpairs.insert(0, kvpair)
                    first_item_inserted = True
                else:
                    kvpairs.append(kvpair)
            in_crs_string = " ".join(kvpairs)

        # make sure it is the CRS type
        if "type=crs" not in in_crs_string:
            if "+" in in_crs_string:
                in_crs_string += " +type=crs"
            else:
                in_crs_string += " type=crs"

        # look for EPSG, replace with epsg (EPSG only works
        # on case-insensitive filesystems).
        in_crs_string = in_crs_string.replace("+init=EPSG", "+init=epsg").strip()
        if in_crs_string.startswith(("+init", "init")):
            warnings.warn(
                "'+init=<authority>:<code>' syntax is deprecated. "
                "'<authority>:<code>' is the preferred initialization method. "
                "When making the change, be mindful of axis order changes: "
                "https://pyproj4.github.io/pyproj/stable/gotchas.html"
                "#axis-order-changes-in-proj-6",
                FutureWarning,
                stacklevel=2,
            )
    return in_crs_string


def _prepare_from_authority(auth_name: str, auth_code: Union[str, int]):
    return "{}:{}".format(auth_name, auth_code)


def _prepare_from_epsg(auth_code: Union[str, int]):
    return _prepare_from_authority("epsg", auth_code)


class CRS(_CRS):
    """
    A pythonic Coordinate Reference System manager.

    .. versionadded:: 2.0.0

    The functionality is based on other fantastic projects:

    * `rasterio <https://github.com/mapbox/rasterio/blob/c13f0943b95c0eaa36ff3f620bd91107aa67b381/rasterio/_crs.pyx>`_  # noqa: E501
    * `opendatacube <https://github.com/opendatacube/datacube-core/blob/83bae20d2a2469a6417097168fd4ede37fd2abe5/datacube/utils/geometry/_base.py>`_  # noqa: E501

    Attributes
    ----------
    srs: str
        The string form of the user input used to create the CRS.
    name: str
        The name of the CRS (from `proj_get_name <https://proj.org/
        development/reference/functions.html#_CPPv313proj_get_namePK2PJ>`_).
    type_name: str
        The name of the type of the CRS object.

    """

    def __init__(self, projparams: Any = None, **kwargs) -> None:
        """
        Initialize a CRS class instance with:
          - PROJ string
          - Dictionary of PROJ parameters
          - PROJ keyword arguments for parameters
          - JSON string with PROJ parameters
          - CRS WKT string
          - An authority string [i.e. 'epsg:4326']
          - An EPSG integer code [i.e. 4326]
          - A tuple of ("auth_name": "auth_code") [i.e ('epsg', '4326')]
          - An object with a `to_wkt` method.
          - A :class:`pyproj.crs.CRS` class

        Example usage:

        >>> from pyproj import CRS
        >>> crs_utm = CRS.from_user_input(26915)
        >>> crs_utm
        <Projected CRS: EPSG:26915>
        Name: NAD83 / UTM zone 15N
        Axis Info [cartesian]:
        - E[east]: Easting (metre)
        - N[north]: Northing (metre)
        Area of Use:
        - name: North America - 96°W to 90°W and NAD83 by country
        - bounds: (-96.0, 25.61, -90.0, 84.0)
        Coordinate Operation:
        - name: UTM zone 15N
        - method: Transverse Mercator
        Datum: North American Datum 1983
        - Ellipsoid: GRS 1980
        - Prime Meridian: Greenwich
        <BLANKLINE>
        >>> crs_utm.area_of_use.bounds
        (-96.0, 25.61, -90.0, 84.0)
        >>> crs_utm.ellipsoid
        ELLIPSOID["GRS 1980",6378137,298.257222101,
            LENGTHUNIT["metre",1],
            ID["EPSG",7019]]
        >>> crs_utm.ellipsoid.inverse_flattening
        298.257222101
        >>> crs_utm.ellipsoid.semi_major_metre
        6378137.0
        >>> crs_utm.ellipsoid.semi_minor_metre
        6356752.314140356
        >>> crs_utm.prime_meridian
        PRIMEM["Greenwich",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8901]]
        >>> crs_utm.prime_meridian.unit_name
        'degree'
        >>> crs_utm.prime_meridian.unit_conversion_factor
        0.017453292519943295
        >>> crs_utm.prime_meridian.longitude
        0.0
        >>> crs_utm.datum
        DATUM["North American Datum 1983",
            ELLIPSOID["GRS 1980",6378137,298.257222101,
                LENGTHUNIT["metre",1]],
            ID["EPSG",6269]]
        >>> crs_utm.coordinate_system
        CS[Cartesian,2],
            AXIS["(E)",east,
                ORDER[1],
                LENGTHUNIT["metre",1,
                    ID["EPSG",9001]]],
            AXIS["(N)",north,
                ORDER[2],
                LENGTHUNIT["metre",1,
                    ID["EPSG",9001]]]
        >>> print(crs_utm.coordinate_operation.to_wkt(pretty=True))
        CONVERSION["UTM zone 15N",
            METHOD["Transverse Mercator",
                ID["EPSG",9807]],
            PARAMETER["Latitude of natural origin",0,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8801]],
            PARAMETER["Longitude of natural origin",-93,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8802]],
            PARAMETER["Scale factor at natural origin",0.9996,
                SCALEUNIT["unity",1],
                ID["EPSG",8805]],
            PARAMETER["False easting",500000,
                LENGTHUNIT["metre",1],
                ID["EPSG",8806]],
            PARAMETER["False northing",0,
                LENGTHUNIT["metre",1],
                ID["EPSG",8807]],
            ID["EPSG",16015]]
        >>> crs = CRS(proj='utm', zone=10, ellps='WGS84')
        >>> print(crs.to_wkt(pretty=True))
        PROJCRS["unknown",
            BASEGEOGCRS["unknown",
                DATUM["Unknown based on WGS84 ellipsoid",
                    ELLIPSOID["WGS 84",6378137,298.257223563,
                        LENGTHUNIT["metre",1],
                        ID["EPSG",7030]]],
                PRIMEM["Greenwich",0,
                    ANGLEUNIT["degree",0.0174532925199433],
                    ID["EPSG",8901]]],
            CONVERSION["UTM zone 10N",
                METHOD["Transverse Mercator",
                    ID["EPSG",9807]],
                PARAMETER["Latitude of natural origin",0,
                    ANGLEUNIT["degree",0.0174532925199433],
                    ID["EPSG",8801]],
                PARAMETER["Longitude of natural origin",-123,
                    ANGLEUNIT["degree",0.0174532925199433],
                    ID["EPSG",8802]],
                PARAMETER["Scale factor at natural origin",0.9996,
                    SCALEUNIT["unity",1],
                    ID["EPSG",8805]],
                PARAMETER["False easting",500000,
                    LENGTHUNIT["metre",1],
                    ID["EPSG",8806]],
                PARAMETER["False northing",0,
                    LENGTHUNIT["metre",1],
                    ID["EPSG",8807]],
                ID["EPSG",16010]],
            CS[Cartesian,2],
                AXIS["(E)",east,
                    ORDER[1],
                    LENGTHUNIT["metre",1,
                        ID["EPSG",9001]]],
                AXIS["(N)",north,
                    ORDER[2],
                    LENGTHUNIT["metre",1,
                        ID["EPSG",9001]]]]
        >>> geod = crs.get_geod()
        >>> "+a={:.0f} +f={:.8f}".format(geod.a, geod.f)
        '+a=6378137 +f=0.00335281'
        >>> crs.is_projected
        True
        >>> crs.is_geographic
        False
        """
        projstring = ""

        if projparams:
            if isinstance(projparams, str):
                projstring = _prepare_from_string(projparams)
            elif isinstance(projparams, dict):
                projstring = _prepare_from_dict(projparams)
            elif isinstance(projparams, int):
                projstring = _prepare_from_epsg(projparams)
            elif isinstance(projparams, (list, tuple)) and len(projparams) == 2:
                projstring = _prepare_from_authority(*projparams)
            elif hasattr(projparams, "to_wkt"):
                projstring = projparams.to_wkt()  # type: ignore
            else:
                raise CRSError("Invalid CRS input: {!r}".format(projparams))

        if kwargs:
            projkwargs = _prepare_from_dict(kwargs, allow_json=False)
            projstring = _prepare_from_string(" ".join((projstring, projkwargs)))

        super().__init__(projstring)

    @staticmethod
    def from_authority(auth_name: str, code: Union[str, int]) -> "CRS":
        """
        .. versionadded:: 2.2.0

        Make a CRS from an authority name and authority code

        Parameters
        ----------
        auth_name: str
            The name of the authority.
        code : int or str
            The code used by the authority.

        Returns
        -------
        CRS
        """
        return CRS(_prepare_from_authority(auth_name, code))

    @staticmethod
    def from_epsg(code: Union[str, int]) -> "CRS":
        """Make a CRS from an EPSG code

        Parameters
        ----------
        code : int or str
            An EPSG code.

        Returns
        -------
        CRS
        """
        return CRS(_prepare_from_epsg(code))

    @staticmethod
    def from_proj4(in_proj_string: str) -> "CRS":
        """
        .. versionadded:: 2.2.0

        Make a CRS from a PROJ string

        Parameters
        ----------
        in_proj_string : str
            A PROJ string.

        Returns
        -------
        CRS
        """
        if not is_proj(in_proj_string):
            raise CRSError("Invalid PROJ string: {}".format(in_proj_string))
        return CRS(_prepare_from_string(in_proj_string))

    @staticmethod
    def from_wkt(in_wkt_string: str) -> "CRS":
        """
        .. versionadded:: 2.2.0

        Make a CRS from a WKT string

        Parameters
        ----------
        in_wkt_string : str
            A WKT string.

        Returns
        -------
        CRS
        """
        if not is_wkt(in_wkt_string):
            raise CRSError("Invalid WKT string: {}".format(in_wkt_string))
        return CRS(_prepare_from_string(in_wkt_string))

    @staticmethod
    def from_string(in_crs_string: str) -> "CRS":
        """
        Make a CRS from:

        Initialize a CRS class instance with:
         - PROJ string
         - JSON string with PROJ parameters
         - CRS WKT string
         - An authority string [i.e. 'epsg:4326']

        Parameters
        ----------
        in_crs_string : str
            An EPSG, PROJ, or WKT string.

        Returns
        -------
        CRS
        """
        return CRS(_prepare_from_string(in_crs_string))

    def to_string(self) -> str:
        """
        .. versionadded:: 2.2.0

        Convert the CRS to a string.

        It attempts to convert it to the authority string.
        Otherwise, it uses the string format of the user
        input to create the CRS.

        Returns
        -------
        str
        """
        auth_info = self.to_authority(min_confidence=100)
        if auth_info:
            return ":".join(auth_info)
        return self.srs

    @staticmethod
    def from_user_input(value: Any, **kwargs) -> "CRS":
        """
        Initialize a CRS class instance with:
          - PROJ string
          - Dictionary of PROJ parameters
          - PROJ keyword arguments for parameters
          - JSON string with PROJ parameters
          - CRS WKT string
          - An authority string [i.e. 'epsg:4326']
          - An EPSG integer code [i.e. 4326]
          - A tuple of ("auth_name": "auth_code") [i.e ('epsg', '4326')]
          - An object with a `to_wkt` method.
          - A :class:`pyproj.crs.CRS` class

        Parameters
        ----------
        value : obj
            A Python int, dict, or str.

        Returns
        -------
        CRS
        """
        if isinstance(value, CRS):
            return value
        return CRS(value, **kwargs)

    def get_geod(self) -> Optional[Geod]:
        """
        Returns
        -------
        pyproj.geod.Geod:
            Geod object based on the ellipsoid.
        """
        if self.ellipsoid is None:
            return None
        return Geod(
            a=self.ellipsoid.semi_major_metre,
            rf=self.ellipsoid.inverse_flattening,
            b=self.ellipsoid.semi_minor_metre,
        )

    @staticmethod
    def from_dict(proj_dict: dict) -> "CRS":
        """
        .. versionadded:: 2.2.0

        Make a CRS from a dictionary of PROJ parameters.

        Parameters
        ----------
        proj_dict : str
            PROJ params in dict format.

        Returns
        -------
        CRS
        """
        return CRS(_prepare_from_dict(proj_dict))

    @staticmethod
    def from_json(crs_json: str) -> "CRS":
        """
        .. versionadded:: 2.4.0

        Create CRS from a CRS JSON string.

        Parameters
        ----------
        crs_json: str
            CRS JSON string.

        Returns
        -------
        CRS
        """
        return CRS.from_json_dict(_load_proj_json(crs_json))

    @staticmethod
    def from_json_dict(crs_dict: dict) -> "CRS":
        """
        .. versionadded:: 2.4.0

        Create CRS from a JSON dictionary.

        Parameters
        ----------
        crs_dict: dict
            CRS dictionary.

        Returns
        -------
        CRS
        """
        return CRS(json.dumps(crs_dict))

    def to_dict(self) -> dict:
        """
        .. versionadded:: 2.2.0

        Converts the CRS to dictionary of PROJ parameters.

        .. warning:: You will likely lose important projection
          information when converting to a PROJ string from
          another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems  # noqa: E501

        Returns
        -------
        dict:
            PROJ params in dict format.

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
            return _try_list_if_string(val)

        proj_string = self.to_proj4()
        if proj_string is None:
            return {}

        items = map(
            lambda kv: len(kv) == 2 and (kv[0], parse(kv[1])) or (kv[0], None),
            (part.lstrip("+").split("=", 1) for part in proj_string.strip().split()),
        )

        return {key: value for key, value in items if value is not False}

    def to_cf(
        self,
        wkt_version: Union[WktVersion, str] = WktVersion.WKT2_2019,
        errcheck: bool = False,
    ) -> dict:
        """
        .. versionadded:: 2.2.0

        This converts a :obj:`pyproj.crs.CRS` object
        to a Climate and Forecast (CF) Grid Mapping Version 1.8 dict.

        .. warning:: The full projection will be stored in the
            crs_wkt attribute. However, other parameters may be lost
            if a mapping to the CF parameter is not found.

        Parameters
        ----------
        wkt_version: str or pyproj.enums.WktVersion
            Version of WKT supported by CRS.to_wkt.
            Default is :attr:`pyproj.enums.WktVersion.WKT2_2019`.
        errcheck: bool, optional
            If True, will warn when parameters are ignored. Defaults to False.

        Returns
        -------
        dict:
            CF-1.8 version of the projection.

        """
        unknown_names = ("unknown", "undefined")
        cf_dict = {"crs_wkt": self.to_wkt(wkt_version)}  # type: Dict[str, Any]

        # handle bound CRS
        if (
            self.is_bound
            and self.coordinate_operation
            and self.coordinate_operation.towgs84
        ):
            sub_cf = self.source_crs.to_cf(errcheck=errcheck)  # type: ignore
            sub_cf.pop("crs_wkt")
            cf_dict.update(sub_cf)
            cf_dict["towgs84"] = self.coordinate_operation.towgs84
            return cf_dict

        # handle compound CRS
        elif self.sub_crs_list:
            for sub_crs in self.sub_crs_list:
                sub_cf = sub_crs.to_cf(errcheck=errcheck)
                sub_cf.pop("crs_wkt")
                cf_dict.update(sub_cf)
            return cf_dict

        # handle vertical CRS
        elif self.is_vertical:
            vert_json = self.to_json_dict()
            if "geoid_model" in vert_json:
                cf_dict["geoid_name"] = vert_json["geoid_model"]["name"]
            if self.datum and self.datum.name not in unknown_names:
                cf_dict["geopotential_datum_name"] = self.datum.name
            return cf_dict

        # write out datum parameters
        if self.ellipsoid:
            cf_dict.update(
                semi_major_axis=self.ellipsoid.semi_major_metre,
                semi_minor_axis=self.ellipsoid.semi_minor_metre,
                inverse_flattening=self.ellipsoid.inverse_flattening,
            )
            if self.ellipsoid.name not in unknown_names:
                cf_dict["reference_ellipsoid_name"] = self.ellipsoid.name
        if self.prime_meridian:
            cf_dict["longitude_of_prime_meridian"] = self.prime_meridian.longitude
            if self.prime_meridian.name not in unknown_names:
                cf_dict["prime_meridian_name"] = self.prime_meridian.name

        # handle geographic CRS
        if self.geodetic_crs and self.geodetic_crs.name not in unknown_names:
            cf_dict["geographic_crs_name"] = self.geodetic_crs.name

        if self.is_geographic:
            if self.coordinate_operation:
                cf_dict.update(
                    _INVERSE_GEOGRAPHIC_GRID_MAPPING_NAME_MAP[
                        self.coordinate_operation.method_name.lower()
                    ](self.coordinate_operation)
                )
                if self.datum and self.datum.name not in unknown_names:
                    cf_dict["horizontal_datum_name"] = self.datum.name
            else:
                cf_dict["grid_mapping_name"] = "latitude_longitude"
            return cf_dict

        # handle projected CRS
        if self.is_projected and self.datum and self.datum.name not in unknown_names:
            cf_dict["horizontal_datum_name"] = self.datum.name
        coordinate_operation = None
        if not self.is_bound and self.is_projected:
            coordinate_operation = self.coordinate_operation
            if self.name not in unknown_names:
                cf_dict["projected_crs_name"] = self.name
        coordinate_operation_name = (
            None
            if not coordinate_operation
            else coordinate_operation.method_name.lower().replace(" ", "_")
        )
        if coordinate_operation_name not in _INVERSE_GRID_MAPPING_NAME_MAP:
            if errcheck:
                if coordinate_operation:
                    warnings.warn(
                        "Unsupported coordinate operation: {}".format(
                            coordinate_operation.method_name
                        )
                    )
                else:
                    warnings.warn("Coordinate operation not found.")

            return {"crs_wkt": self.to_wkt(wkt_version)}

        cf_dict.update(
            _INVERSE_GRID_MAPPING_NAME_MAP[coordinate_operation_name](
                coordinate_operation
            )
        )
        return cf_dict

    @staticmethod
    def from_cf(in_cf: dict, errcheck=False) -> "CRS":
        """
        .. versionadded:: 2.2.0

        This converts a Climate and Forecast (CF) Grid Mapping Version 1.8
        dict to a :obj:`pyproj.crs.CRS` object.

        .. warning:: Parameters may be lost if a mapping
            from the CF parameter is not found. For best results
            store the WKT of the projection in the crs_wkt attribute.

        Parameters
        ----------
        in_cf: dict
            CF version of the projection.
        errcheck: bool, optional
            This parameter is for backwards compatibility with the old version.
            It currently does nothing when True or False.

        Returns
        -------
        CRS
        """
        if "crs_wkt" in in_cf:
            return CRS(in_cf["crs_wkt"])
        elif "spatial_ref" in in_cf:  # for previous supported WKT key
            return CRS(in_cf["spatial_ref"])

        grid_mapping_name = in_cf.get("grid_mapping_name")
        if grid_mapping_name is None:
            raise CRSError("CF projection parameters missing 'grid_mapping_name'")

        # build datum if possible
        datum = _horizontal_datum_from_params(in_cf)

        # build geographic CRS
        try:
            geographic_conversion_method = _GEOGRAPHIC_GRID_MAPPING_NAME_MAP[
                grid_mapping_name
            ]  # type: Optional[Callable]
        except KeyError:
            geographic_conversion_method = None

        geographic_crs_name = in_cf.get("geographic_crs_name")
        if datum:
            geographic_crs = GeographicCRS(
                name=geographic_crs_name or "undefined", datum=datum,
            )  # type: CRS
        elif geographic_crs_name:
            geographic_crs = CRS(geographic_crs_name)
        else:
            geographic_crs = GeographicCRS()
        if grid_mapping_name == "latitude_longitude":
            return geographic_crs
        if geographic_conversion_method is not None:
            return DerivedGeographicCRS(
                base_crs=geographic_crs, conversion=geographic_conversion_method(in_cf),
            )

        # build projected CRS
        try:
            conversion_method = _GRID_MAPPING_NAME_MAP[grid_mapping_name]
        except KeyError:
            raise CRSError(
                "Unsupported grid mapping name: {}".format(grid_mapping_name)
            )
        projected_crs = ProjectedCRS(
            name=in_cf.get("projected_crs_name", "undefined"),
            conversion=conversion_method(in_cf),
            geodetic_crs=geographic_crs,
        )

        # build bound CRS if exists
        bound_crs = None
        if "towgs84" in in_cf:
            bound_crs = BoundCRS(
                source_crs=projected_crs,
                target_crs="WGS 84",
                transformation=ToWGS84Transformation(
                    projected_crs.geodetic_crs, *_try_list_if_string(in_cf["towgs84"])
                ),
            )
        if "geopotential_datum_name" not in in_cf:
            return bound_crs or projected_crs

        # build Vertical CRS
        vertical_crs = VerticalCRS(
            name="undefined",
            datum=in_cf["geopotential_datum_name"],
            geoid_model=in_cf.get("geoid_name"),
        )

        # build compound CRS
        return CompoundCRS(
            name="undefined", components=[bound_crs or projected_crs, vertical_crs]
        )

    def is_exact_same(self, other: Any, ignore_axis_order: bool = False) -> bool:
        """
        Check if the CRS objects are the exact same.

        Parameters
        ----------
        other: Any
            Check if the other CRS is the exact same to this object.
            If the other object is not a CRS, it will try to create one.
            On Failure, it will return False.

        Returns
        -------
        bool
        """
        try:
            other = CRS.from_user_input(other)
        except CRSError:
            return False
        return super().is_exact_same(other)

    def equals(self, other: Any, ignore_axis_order: bool = False) -> bool:
        """

        .. versionadded:: 2.5.0

        Check if the CRS objects are equivalent.

        Parameters
        ----------
        other: Any
            Check if the other object is equivalent to this object.
            If the other object is not a CRS, it will try to create one.
            On Failure, it will return False.
        ignore_axis_order: bool, optional
            If True, it will compare the CRS class and ignore the axis order.
            Default is False.

        Returns
        -------
        bool
        """
        try:
            other = CRS.from_user_input(other)
        except CRSError:
            return False
        return super().equals(other, ignore_axis_order=ignore_axis_order)

    @property
    def geodetic_crs(self) -> Optional["CRS"]:
        """
        .. versionadded:: 2.2.0

        Returns
        -------
        CRS:
            The the geodeticCRS / geographicCRS from the CRS.

        """
        geodetic_crs = super().geodetic_crs
        if geodetic_crs is None:
            return None
        return CRS(geodetic_crs.srs)

    @property
    def source_crs(self) -> Optional["CRS"]:
        """
        The the base CRS of a BoundCRS or a DerivedCRS/ProjectedCRS,
        or the source CRS of a CoordinateOperation.

        Returns
        -------
        CRS
        """
        source_crs = super().source_crs
        if source_crs is None:
            return None
        return CRS(source_crs.srs)

    @property
    def target_crs(self) -> Optional["CRS"]:
        """
        .. versionadded:: 2.2.0

        Returns
        -------
        CRS:
            The hub CRS of a BoundCRS or the target CRS of a CoordinateOperation.

        """
        target_crs = super().target_crs
        if target_crs is None:
            return None
        return CRS(target_crs.srs)

    @property
    def sub_crs_list(self) -> List["CRS"]:
        """
        If the CRS is a compound CRS, it will return a list of sub CRS objects.

        Returns
        -------
        List[CRS]
        """
        return [CRS(sub_crs.srs) for sub_crs in super().sub_crs_list]

    @property
    def utm_zone(self) -> Optional[str]:
        """
        .. versionadded:: 2.6.0

        Finds the UTM zone in a Projected CRS, Bound CRS, or Compound CRS

        Returns
        -------
        Optional[str]:
            The UTM zone number and letter if applicable.
        """
        if self.is_bound and self.source_crs:
            return self.source_crs.utm_zone
        elif self.sub_crs_list:
            for sub_crs in self.sub_crs_list:
                if sub_crs.utm_zone:
                    return sub_crs.utm_zone
        elif (
            self.coordinate_operation
            and "UTM ZONE" in self.coordinate_operation.name.upper()
        ):
            return self.coordinate_operation.name.upper().split("UTM ZONE ")[-1]
        return None

    def __eq__(self, other: Any) -> bool:
        return self.equals(other)

    def __reduce__(self) -> Tuple[Type["CRS"], Tuple[str]]:
        """special method that allows CRS instance to be pickled"""
        return self.__class__, (self.srs,)

    def __hash__(self) -> int:
        return hash(self.to_wkt())

    def __str__(self) -> str:
        return self.srs

    def __repr__(self) -> str:
        # get axis information
        axis_info_list = []  # type: List[str]
        for axis in self.axis_info:
            axis_info_list.extend(["- ", str(axis), "\n"])
        axis_info_str = "".join(axis_info_list)

        # get coordinate system & sub CRS info
        source_crs_repr = ""
        sub_crs_repr = ""
        if self.coordinate_system and self.coordinate_system.axis_list:
            coordinate_system_name = str(self.coordinate_system)
        elif self.is_bound and self.source_crs:
            coordinate_system_name = str(self.source_crs.coordinate_system)
            source_crs_repr = "Source CRS: {}\n".format(self.source_crs.name)
        else:
            coordinate_system_names = []
            sub_crs_repr_list = ["Sub CRS:\n"]
            for sub_crs in self.sub_crs_list:
                coordinate_system_names.append(str(sub_crs.coordinate_system))
                sub_crs_repr_list.extend(["- ", sub_crs.name, "\n"])
            coordinate_system_name = "|".join(coordinate_system_names)
            sub_crs_repr = "".join(sub_crs_repr_list)

        # get coordinate operation repr
        coordinate_operation = ""
        if self.coordinate_operation:
            coordinate_operation = "".join(
                [
                    "Coordinate Operation:\n",
                    "- name: ",
                    str(self.coordinate_operation),
                    "\n" "- method: ",
                    str(self.coordinate_operation.method_name),
                    "\n",
                ]
            )

        # get SRS representation
        srs_repr = self.to_string()
        srs_repr = srs_repr if len(srs_repr) <= 50 else " ".join([srs_repr[:50], "..."])
        string_repr = (
            "<{type_name}: {srs_repr}>\n"
            "Name: {name}\n"
            "Axis Info [{coordinate_system}]:\n"
            "{axis_info_str}"
            "Area of Use:\n"
            "{area_of_use}\n"
            "{coordinate_operation}"
            "Datum: {datum}\n"
            "- Ellipsoid: {ellipsoid}\n"
            "- Prime Meridian: {prime_meridian}\n"
            "{source_crs_repr}"
            "{sub_crs_repr}"
        ).format(
            type_name=self.type_name,
            srs_repr=srs_repr,
            name=self.name,
            axis_info_str=axis_info_str or "- undefined\n",
            area_of_use=self.area_of_use or "- undefined",
            coordinate_system=coordinate_system_name or "undefined",
            coordinate_operation=coordinate_operation,
            datum=self.datum,
            ellipsoid=self.ellipsoid or "undefined",
            prime_meridian=self.prime_meridian or "undefined",
            source_crs_repr=source_crs_repr,
            sub_crs_repr=sub_crs_repr,
        )
        return string_repr


class GeographicCRS(CRS):
    """
    .. versionadded:: 2.5.0

    This class is for building a Geographic CRS
    """

    def __init__(
        self,
        name: str = "undefined",
        datum: Any = "urn:ogc:def:datum:EPSG::6326",
        ellipsoidal_cs: Any = None,
    ) -> None:
        """
        Parameters
        ----------
        name: str, optional
            Name of the CRS. Default is undefined.
        datum: Any, optional
            Anything accepted by :meth:`pyproj.crs.Datum.from_user_input` or
            a :class:`pyproj.crs.datum.CustomDatum`.
        ellipsoidal_cs: Any, optional
            Input to create an Ellipsoidal Coordinate System.
            Anything accepted by :meth:`pyproj.crs.CoordinateSystem.from_user_input`
            or an Ellipsoidal Coordinate System created from :ref:`coordinate_system`.
        """
        geographic_crs_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "GeographicCRS",
            "name": name,
            "datum": Datum.from_user_input(datum).to_json_dict(),
            "coordinate_system": CoordinateSystem.from_user_input(
                ellipsoidal_cs or Ellipsoidal2DCS()
            ).to_json_dict(),
        }
        super().__init__(geographic_crs_json)


class DerivedGeographicCRS(CRS):
    """
    .. versionadded:: 2.5.0

    This class is for building a Derived Geographic CRS
    """

    def __init__(
        self,
        base_crs: Any,
        conversion: Any,
        ellipsoidal_cs: Any = None,
        name: str = "undefined",
    ) -> None:
        """
        Parameters
        ----------
        base_crs: Any
            Input to create the Geodetic CRS, a :class:`GeographicCRS` or
            anything accepted by :meth:`pyproj.crs.CRS.from_user_input`.
        conversion: Any
            Anything accepted by :meth:`pyproj.crs.CoordinateSystem.from_user_input`
            or a conversion from :ref:`coordinate_operation`.
        ellipsoidal_cs: Any, optional
            Input to create an Ellipsoidal Coordinate System.
            Anything accepted by :meth:`pyproj.crs.CoordinateSystem.from_user_input`
            or an Ellipsoidal Coordinate System created from :ref:`coordinate_system`.
        name: str, optional
            Name of the CRS. Default is undefined.
        """
        derived_geographic_crs_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "DerivedGeographicCRS",
            "name": name,
            "base_crs": CRS.from_user_input(base_crs).to_json_dict(),
            "conversion": CoordinateOperation.from_user_input(
                conversion
            ).to_json_dict(),
            "coordinate_system": CoordinateSystem.from_user_input(
                ellipsoidal_cs or Ellipsoidal2DCS()
            ).to_json_dict(),
        }
        super().__init__(derived_geographic_crs_json)


class ProjectedCRS(CRS):
    """
    .. versionadded:: 2.5.0

    This class is for building a Projected CRS.
    """

    def __init__(
        self,
        conversion: Any,
        name: str = "undefined",
        cartesian_cs: Any = None,
        geodetic_crs: Any = None,
    ) -> None:
        """
        Parameters
        ----------
        conversion: Any
            Anything accepted by :meth:`pyproj.crs.CoordinateSystem.from_user_input`
            or a conversion from :ref:`coordinate_operation`.
        name: str, optional
            The name of the Projected CRS. Default is undefined.
        cartesian_cs: Any, optional
            Input to create a Cartesian Coordinate System.
            Anything accepted by :meth:`pyproj.crs.CoordinateSystem.from_user_input`
            or :class:`pyproj.crs.coordinate_system.Cartesian2DCS`.
        geodetic_crs: Any, optional
            Input to create the Geodetic CRS, a :class:`GeographicCRS` or
            anything accepted by :meth:`pyproj.crs.CRS.from_user_input`.
        """
        proj_crs_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "ProjectedCRS",
            "name": name,
            "base_crs": CRS.from_user_input(
                geodetic_crs or GeographicCRS()
            ).to_json_dict(),
            "conversion": CoordinateOperation.from_user_input(
                conversion
            ).to_json_dict(),
            "coordinate_system": CoordinateSystem.from_user_input(
                cartesian_cs or Cartesian2DCS()
            ).to_json_dict(),
        }
        super().__init__(proj_crs_json)


class VerticalCRS(CRS):
    """
    .. versionadded:: 2.5.0

    This class is for building a Vetical CRS.

    .. warning:: geoid_model support only exists in PROJ >= 6.3.0

    """

    def __init__(
        self,
        name: str,
        datum: Any,
        vertical_cs: Any = None,
        geoid_model: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        name: str
            The name of the Vertical CRS (e.g. NAVD88 height).
        datum: Any
            Anything accepted by :meth:`pyproj.crs.Datum.from_user_input`
        vertical_cs: Any, optional
            Input to create a Vertical Coordinate System accepted by
            :meth:`pyproj.crs.CoordinateSystem.from_user_input`
            or :class:`pyproj.crs.coordinate_system.VerticalCS`
        geoid_model: str, optional
            The name of the GEOID Model (e.g. GEOID12B).
        """
        vert_crs_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "VerticalCRS",
            "name": name,
            "datum": Datum.from_user_input(datum).to_json_dict(),
            "coordinate_system": CoordinateSystem.from_user_input(
                vertical_cs or VerticalCS()
            ).to_json_dict(),
        }
        if geoid_model is not None:
            vert_crs_json["geoid_model"] = {"name": geoid_model}

        super().__init__(vert_crs_json)


class CompoundCRS(CRS):
    """
    .. versionadded:: 2.5.0

    This class is for building a Compound CRS.
    """

    def __init__(self, name: str, components: List[Any]) -> None:
        """
        Parameters
        ----------
        name: str
            The name of the Compound CRS.
        components: List[Any], optional
            List of CRS to create a Compound Coordinate System.
            List of anything accepted by :meth:`pyproj.crs.CRS.from_user_input`
        """
        compound_crs_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "CompoundCRS",
            "name": name,
            "components": [
                CRS.from_user_input(component).to_json_dict()
                for component in components
            ],
        }

        super().__init__(compound_crs_json)


class BoundCRS(CRS):
    """
    .. versionadded:: 2.5.0

    This class is for building a Bound CRS.
    """

    def __init__(self, source_crs: Any, target_crs: Any, transformation: Any) -> None:
        """
        Parameters
        ----------
        source_crs: Any
            Input to create a source CRS.
        target_crs: Any
            Input to create the target CRS.
        transformation: Any
            Input to create the transformation.
        """
        bound_crs_json = {
            "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
            "type": "BoundCRS",
            "source_crs": CRS.from_user_input(source_crs).to_json_dict(),
            "target_crs": CRS.from_user_input(target_crs).to_json_dict(),
            "transformation": CoordinateOperation.from_user_input(
                transformation
            ).to_json_dict(),
        }

        super().__init__(bound_crs_json)
