from pyproj.compat import cstrencode, pystrdecode
from pyproj._datadir cimport get_pyproj_context
from pyproj.exceptions import CRSError

def is_wkt(proj_string):
    """
    Check if the input projection string is in the Well-Known Text format.

    Parameters
    ----------
    proj_string: str
        The projection string.

    Returns
    -------
    bool: True if the string is in the Well-Known Text format
    """
    tmp_string = cstrencode(proj_string)
    return proj_context_guess_wkt_dialect(NULL, tmp_string) != PJ_GUESSED_NOT_WKT


cdef class AxisInfo:
    def __init__(self):
        self.name = None
        self.abbrev = None
        self.direction = None
        self.unit_conversion_factor = float("NaN")
        self.unit_name = None
        self.unit_auth_code = None
        self.unit_code = None

    def __str__(self):
        return "- {name}[{abbrev}] ({direction}) {unit_auth_code}:{unit_code} ({unit_name})".format(
            name=self.name,
            abbrev=self.abbrev,
            direction=self.direction,
            unit_name=self.unit_name,
            unit_auth_code=self.unit_auth_code,
            unit_code=self.unit_code,
        )

    def __repr__(self):
        return ("AxisInfo(name={name}, abbrev={abbrev}, direction={direction}, "
                "unit_auth_code={unit_auth_code}, unit_code={unit_code}, "
                "unit_name={unit_name})").format(
            name=self.name,
            abbrev=self.abbrev,
            direction=self.direction,
            unit_name=self.unit_name,
            unit_auth_code=self.unit_auth_code,
            unit_code=self.unit_code,
        )

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj, int index):
        cdef AxisInfo axis_info = AxisInfo()
        cdef const char * name = NULL
        cdef const char * abbrev = NULL
        cdef const char * direction = NULL
        cdef const char * unit_name = NULL
        cdef const char * unit_auth_code = NULL
        cdef const char * unit_code = NULL
        if not proj_cs_get_axis_info(
                projcontext,
                projobj,
                index,
                &name,
                &abbrev,
                &direction,
                &axis_info.unit_conversion_factor,
                &unit_name,
                &unit_auth_code,
                &unit_code):
            return None
        axis_info.name = pystrdecode(name)
        axis_info.abbrev = pystrdecode(abbrev)
        axis_info.direction = pystrdecode(direction)
        axis_info.unit_name = pystrdecode(unit_name)
        axis_info.unit_auth_code = pystrdecode(unit_auth_code)
        axis_info.unit_code = pystrdecode(unit_code)
        return axis_info


cdef class AreaOfUse:
    def __init__(self):
        self.west = float("NaN")
        self.south = float("NaN")
        self.east = float("NaN")
        self.north = float("NaN")
        self.name = None

    def __str__(self):
        return "- name: {name}\n" \
               "- bounds: {bounds}".format(
            name=self.name, bounds=self.bounds)

    def __repr__(self):
        return ("AreaOfUse(name={name}, west={west}, south={south},"
                " east={east}, north={north})").format(
            name=self.name,
            west=self.west,
            south=self.south,
            east=self.east,
            north=self.north
        )

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj):
        cdef AreaOfUse area_of_use = AreaOfUse()
        cdef const char * area_name = NULL
        if not proj_get_area_of_use(
                projcontext,
                projobj,
                &area_of_use.west,
                &area_of_use.south,
                &area_of_use.east,
                &area_of_use.north,
                &area_name):
            return None
        area_of_use.name = pystrdecode(area_name)
        return area_of_use

    @property
    def bounds(self):
        return self.west, self.south, self.east, self.north


cdef class Ellipsoid:
    def __init__(self):
        # load in ellipsoid information if applicable
        self._semi_major_metre = float("NaN")
        self._semi_minor_metre = float("NaN")
        self.is_semi_minor_computed = 0
        self._inv_flattening = float("NaN")
        self.ellipsoid_loaded = False


    def __str__(self):
        return "- semi_major_metre: {semi_major_metre:.2f}\n" \
               "- semi_minor_metre: {semi_minor_metre:.2f}\n" \
               "- inverse_flattening: {inverse_flattening:.2f}".format(
            semi_major_metre=self.semi_major_metre,
            semi_minor_metre=self.semi_minor_metre,
            inverse_flattening=self.inverse_flattening
        )

    def __repr__(self):
        return "Ellipsoid(semi_major_metre={semi_major_metre:.2f}, " \
               "semi_minor_metre={semi_minor_metre:.2f}, " \
               "inverse_flattening={inverse_flattening:.2f})".format(
            semi_major_metre=self.semi_major_metre,
            semi_minor_metre=self.semi_minor_metre,
            inverse_flattening=self.inverse_flattening
        )

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj):
        cdef Ellipsoid ellips = Ellipsoid()
        cdef PJ * ellips_prod = NULL
        ellips_prod = proj_get_ellipsoid(projcontext, projobj)
        if ellips_prod == NULL:
            return None
        try:
            proj_ellipsoid_get_parameters(
                projcontext,
                ellips_prod,
                &ellips._semi_major_metre,
                &ellips._semi_minor_metre,
                &ellips.is_semi_minor_computed,
                &ellips._inv_flattening)
            ellips.ellipsoid_loaded = True
        finally:
            proj_destroy(ellips_prod)
        return ellips

    @property
    def semi_major_metre(self):
        """
        The ellipsoid semi major metre.

        Returns
        -------
        float or None: The semi major metre if the projection is an ellipsoid.
        """
        if self.ellipsoid_loaded:
            return self._semi_major_metre
        return float("NaN")

    @property
    def semi_minor_metre(self):
        """
        The ellipsoid semi minor metre.

        Returns
        -------
        float or None: The semi minor metre if the projection is an ellipsoid
            and the value was com
            puted.
        """
        if self.ellipsoid_loaded and self.is_semi_minor_computed:
            return self._semi_minor_metre
        return float("NaN")

    @property
    def inverse_flattening(self):
        """
        The ellipsoid inverse flattening.

        Returns
        -------
        float or None: The inverse flattening if the projection is an ellipsoid.
        """
        if self.ellipsoid_loaded:
            return self._inv_flattening
        return float("NaN")


cdef class PrimeMeridian:
    def __init__(self):
        self.unit_name = None

    def __str__(self):
        return ("- longitude: {longitude:.4f}\n"
                "- unit_name: {unit_name}\n"
                "- unit_conversion_factor: {unit_conversion_factor:.8f}").format(
            longitude=self.longitude,
            unit_name=self.unit_name,
            unit_conversion_factor=self.unit_conversion_factor,
        )

    def __repr__(self):
        return ("PrimeMeridian(longitude={longitude:.4f}, "
                "unit_name={unit_name}, "
                "unit_conversion_factor={unit_conversion_factor:.8f})").format(
            longitude=self.longitude,
            unit_name=self.unit_name,
            unit_conversion_factor=self.unit_conversion_factor
        )

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj):
        cdef PrimeMeridian prime_meridian = PrimeMeridian()
        cdef PJ * prime_meridian_prod = NULL
        prime_meridian_prod = proj_get_prime_meridian(projcontext, projobj)
        if prime_meridian_prod == NULL:
            return None

        cdef const char * unit_name
        if not proj_prime_meridian_get_parameters(
                projcontext,
                prime_meridian_prod,
                &prime_meridian.longitude,
                &prime_meridian.unit_conversion_factor,
                &unit_name):
            return None

        prime_meridian.unit_name = pystrdecode(unit_name)
        return prime_meridian


cdef _to_wkt(PJ_CONTEXT* projctx, PJ* projobj, PJ_WKT_TYPE wkt_out_type=PJ_WKT2_2018):
    """
    Convert a PJ object to a wkt string.

    Parameters
    ----------
    projctx: 
    projobj: 
    wkt_out_type:
    
    Return
    ------
    str or None
    """
    cdef const char* options_wkt[2]
    options_wkt[0] = "MULTILINE=NO"
    options_wkt[1] = NULL
    cdef const char* proj_string
    proj_string = proj_as_wkt(
        projctx,
        projobj,
        wkt_out_type,
        options_wkt)
    if proj_string != NULL:
        return pystrdecode(proj_string)
    return None

cdef class _CRS:
    def __cinit__(self):
        self.projobj = NULL
        self.projctx = NULL

    def __dealloc__(self):
        """destroy projection definition"""
        if self.projobj != NULL:
            proj_destroy(self.projobj)
        if self.projctx != NULL:
            proj_context_destroy(self.projctx)

    def __init__(self, projstring):
        self._axis_info = None
        self._ellipsoid = None
        self._area_of_use = None
        self._prime_meridian = None
        # setup the context
        self.projctx = get_pyproj_context()
        # setup proj initialization string.
        if not is_wkt(projstring) \
                and not projstring.lower().startswith("epsg")\
                and "type=crs" not in projstring:
            projstring += " +type=crs"
        self.projobj = proj_create(self.projctx, cstrencode(projstring))

        self.srs = pystrdecode(projstring)
        # initialize projection
        if self.projobj is NULL:
            raise CRSError(
                "Invalid projection: {}".format(self.srs))
        # get proj information
        self.proj_type = proj_get_type(self.projobj)
        cdef const char* proj_name = proj_get_name(self.projobj)
        self.name = pystrdecode(proj_name)

    @property
    def axis_info(self):
        """
        Returns
        -------
        list[AxisInfo]: The list of axis information.
        """
        if self._axis_info is not None:
            return self._axis_info
        self._axis_info = []

        cdef PJ * coord_system = NULL
        coord_system = proj_crs_get_coordinate_system(self.projctx, self.projobj)
        if coord_system == NULL:
            return self._axis_info

        cdef int num_axes = 0
        try:
            num_axes = proj_cs_get_axis_count(self.projctx, coord_system)
            for axis_idx from 0 <= axis_idx < num_axes:
                self._axis_info.append(AxisInfo.create(self.projctx, coord_system, axis_idx))
        finally:
            proj_destroy(coord_system)
        return self._axis_info

    @property
    def ellipsoid(self):
        """
        Returns
        -------
        Ellipsoid: The CRS ellipsoid object with associated attributes.
        """
        if self._ellipsoid is not None:
            return self._ellipsoid
        self._ellipsoid = Ellipsoid.create(self.projctx, self.projobj)
        return self._ellipsoid

    @property
    def area_of_use(self):
        """
        Returns
        -------
        AreaOfUse: The CRS area of use object with associated attributes.
        """
        if self._area_of_use is not None:
            return self._area_of_use
        self._area_of_use = AreaOfUse.create(self.projctx, self.projobj)
        return self._area_of_use

    @property
    def prime_meridian(self):
        """
        Returns
        -------
        PrimeMeridian: The CRS prime meridian object with associated attributes.
        """
        if self._prime_meridian is not None:
            return self._prime_meridian
        self._prime_meridian = PrimeMeridian.create(self.projctx, self.projobj)
        return self._prime_meridian

    @property
    def datum(self):
        """
        Returns
        -------
        :obj:`pyproj.CRS`: The datum as a CRS.
        """
        cdef PJ *projobj = proj_crs_get_datum(self.projctx, self.projobj)
        if projobj == NULL:
            return None
        try:
            return self.__class__(_to_wkt(self.projctx, projobj))
        finally:
            proj_destroy(projobj) # deallocate temp proj

    def to_proj4(self, version=4):
        """
        Convert the projection to a proj.4 string.

        Parameters
        ----------
        version: int
            The version of the proj.4 output. Default is 4.

        Returns
        -------
        str: The proj.4 string.
        """
        # get the output proj.4 format
        supported_prj_types = {
            4: PJ_PROJ_4,
            5: PJ_PROJ_5,
        }
        cdef PJ_PROJ_STRING_TYPE proj_out_type
        try:
            proj_out_type = supported_prj_types[version]
        except KeyError:
            raise ValueError(
                "Invalid version supplied '{}'. "
                "Only {} are supported."
                .format(version, tuple(supported_prj_types)))

        # convert projection to string
        cdef const char* proj_string
        proj_string = proj_as_proj_string(
            self.projctx,
            self.projobj,
            proj_out_type,
            NULL)
        if proj_string != NULL:
            return pystrdecode(proj_string)
        return None

    def to_geodetic(self):
        """return a new CRS instance which is the geographic (lat/lon)
        coordinate version of the current projection"""
        cdef PJ * projobj
        projobj = proj_crs_get_geodetic_crs(self.projctx, self.projobj)
        if projobj == NULL:
            return None
        try:
            return self.__class__(_to_wkt(self.projctx, projobj))
        finally:
            proj_destroy(projobj) # deallocate temp proj

    def to_wkt(self, version="WKT2_2018"):
        """
        Convert the projection to a WKT string.

        Parameters
        ----------
        version: str
            The version of the WKT output. Default is WKT2_2018.

        Returns
        -------
        str: The WKT string.
        """
        # get the output WKT format
        supported_wkt_types = {
            "WKT2_2015": PJ_WKT2_2015,
            "WKT2_2015_SIMPLIFIED": PJ_WKT2_2015_SIMPLIFIED,
            "WKT2_2018": PJ_WKT2_2018,
            "WKT2_2018_SIMPLIFIED": PJ_WKT2_2018_SIMPLIFIED,
            "WKT1_GDAL": PJ_WKT1_GDAL,
            "WKT1_ESRI": PJ_WKT1_ESRI
        }
        cdef PJ_WKT_TYPE proj_out_type
        try:
            proj_out_type = supported_wkt_types[version.upper()]
        except KeyError:
            raise ValueError(
                "Invalid version supplied '{}'. "
                "Only {} are supported."
                .format(version, tuple(supported_wkt_types)))

        return _to_wkt(self.projctx, self.projobj, proj_out_type)

    def to_epsg(self, min_confidence=70):
        """
        Return the EPSG code best matching the projection.

        Parameters
        ----------
        min_confidence: int, optional
            A value between 0-100 where 100 is the most confident. Default is 70.

        Returns
        -------
        int or None: The best matching EPSG code matching the confidence level.
        """
        # get list of possible matching projections
        cdef PJ_OBJ_LIST *proj_list = NULL
        cdef int *out_confidence_list = NULL
        cdef int out_confidence = -9999
        cdef int num_proj_objects = -9999

        try:
            proj_list  = proj_identify(self.projctx,
                self.projobj,
                b"EPSG",
                NULL,
                &out_confidence_list
            )
            num_proj_objects = proj_list_get_count(proj_list)
            if out_confidence_list != NULL and num_proj_objects>0:
                out_confidence = out_confidence_list[0]
        finally:
            if out_confidence_list != NULL:
                proj_int_list_destroy(out_confidence_list)

        # check to make sure that the projection found is valid
        if proj_list == NULL or num_proj_objects <= 0 or out_confidence < min_confidence:
            if proj_list != NULL:
                proj_list_destroy(proj_list)
            return None

        # retrieve the best matching projection
        cdef PJ* proj
        try:
            proj = proj_list_get(self.projctx, proj_list, 0)
        finally:
            proj_list_destroy(proj_list)
        if proj == NULL:
            return None

        # convert the matching projection to the EPSG code
        cdef const char* code
        try:
            code = proj_get_id_code(proj, 0)
            if code != NULL:
                return int(code)
        finally:
            proj_destroy(proj)

        return None

    @property
    def is_geographic(self):
        """
        Returns
        -------
        bool: True if projection in geographic (lon/lat) coordinates.
        """
        return self.proj_type in (
            PJ_TYPE_GEOGRAPHIC_CRS,
            PJ_TYPE_GEOGRAPHIC_2D_CRS,
            PJ_TYPE_GEOGRAPHIC_3D_CRS
        )

    @property
    def is_projected(self):
        """
        Returns
        -------
        bool: True if projection is a projected type.
        """
        return self.proj_type == PJ_TYPE_PROJECTED_CRS

    @property
    def is_valid(self):
        """
        Returns
        -------
        bool: True if projection is a valid type.
        """
        return self.proj_type != PJ_TYPE_UNKNOWN

    @property
    def is_geocentric(self):
        """
        Returns
        -------
        bool: True if projection in geocentric (x/y) coordinates
        """
        return self.proj_type == PJ_TYPE_GEOCENTRIC_CRS

    def is_exact_same(self, _CRS other):
        """Compares projections to see if they are exactly the same."""
        return proj_is_equivalent_to(
            self.projobj, other.projobj, PJ_COMP_STRICT) == 1

    def __eq__(self, _CRS other):
        """Compares projections to see if they are equivalent."""
        return proj_is_equivalent_to(
            self.projobj, other.projobj, PJ_COMP_EQUIVALENT) == 1
