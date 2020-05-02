.. _examples:

Getting Started
===============

There are examples of usage within the API documentation and tests. This
section is to demonstrate recommended usage.

Also see: :ref:`gotchas`


Using CRS
---------
For more usage examples and documentation see :class:`pyproj.crs.CRS`.

Initializing CRS
~~~~~~~~~~~~~~~~

The :class:`pyproj.crs.CRS` class can be initialized in many different ways.
Here are some examples of initialization.


.. code:: python

    >>> from pyproj import CRS
    >>> crs = CRS.from_epsg(4326)
    >>> crs = CRS.from_string("epsg:4326")
    >>> crs = CRS.from_proj4("+proj=latlon")
    >>> crs = CRS.from_user_input(4326)


Converting CRS to a different format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning:: You will likely lose important projection
    information when converting to a PROJ string from
    another format. See: https://proj4.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems


.. code:: python

    >>> from pyproj import CRS
    >>> crs = CRS.from_epsg(4326)
    >>> crs.to_epsg()
    4326
    >>> crs.to_authority()
    ('EPSG', '4326')
    >>> crs = CRS.from_proj4("+proj=omerc +lat_0=-36 +lonc=147 +alpha=-54 +k=1 +x_0=0 +y_0=0 +gamma=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0")
    >>> crs
    <Bound CRS: +proj=omerc +lat_0=-36 +lonc=147 +alpha=-54 +k=1 + ...>
    Name: unknown
    Axis Info [cartesian]:
    - E[east]: Easting (metre)
    - N[north]: Northing (metre)
    Area of Use:
    - undefined
    Coordinate Operation:
    - name: Transformation from unknown to WGS84
    - method: Position Vector transformation (geog2D domain)
    Datum: Unknown based on WGS84 ellipsoid
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich
    Source CRS: unknown

    >>> print(crs.to_wkt(pretty=True))
    BOUNDCRS[
        SOURCECRS[
            PROJCRS["unknown",
                BASEGEOGCRS["unknown",
                    DATUM["Unknown based on WGS84 ellipsoid",
                        ELLIPSOID["WGS 84",6378137,298.257223563,
                            LENGTHUNIT["metre",1],
                            ID["EPSG",7030]]],
    ...
            PARAMETER["Z-axis rotation",0,
                ID["EPSG",8610]],
            PARAMETER["Scale difference",1,
                ID["EPSG",8611]]]]

    >>> from pyproj.enums import WktVersion
    >>> print(crs.to_wkt(WktVersion.WKT1_GDAL, pretty=True))
    PROJCS["unknown",
        GEOGCS["unknown",
            DATUM["Unknown_based_on_WGS84_ellipsoid",
                SPHEROID["WGS 84",6378137,298.257223563,
                    AUTHORITY["EPSG","7030"]],
                TOWGS84[0,0,0,0,0,0,0]],
            PRIMEM["Greenwich",0,
                AUTHORITY["EPSG","8901"]],
            UNIT["degree",0.0174532925199433,
                AUTHORITY["EPSG","9122"]]],
        PROJECTION["Hotine_Oblique_Mercator_Azimuth_Center"],
        PARAMETER["latitude_of_center",-36],
        PARAMETER["longitude_of_center",147],
        PARAMETER["azimuth",-54],
        PARAMETER["rectified_grid_angle",0],
        PARAMETER["scale_factor",1],
        PARAMETER["false_easting",0],
        PARAMETER["false_northing",0],
        UNIT["metre",1,
            AUTHORITY["EPSG","9001"]],
        AXIS["Easting",EAST],
        AXIS["Northing",NORTH]]

    >>> from pprint import pprint
    >>> pprint(crs.to_cf())
    {'azimuth_of_central_line': -54,
    'crs_wkt': 'BOUNDCRS[SOURCECRS[PROJCRS["unknown",BASEGEOGCRS["unknown",DATUM["Unknown '
    ...
                'difference",1,ID["EPSG",8611]]]]',
    'false_easting': 0.0,
    'false_northing': 0.0,
    'grid_mapping_name': 'oblique_mercator',
    'horizontal_datum_name': 'Unknown based on WGS84 ellipsoid',
    'inverse_flattening': 298.257223563,
    'latitude_of_projection_origin': -36.0,
    'longitude_of_prime_meridian': 0.0,
    'longitude_of_projection_origin': 147.0,
    'prime_meridian_name': 'Greenwich',
    'reference_ellipsoid_name': 'WGS 84',
    'scale_factor_at_projection_origin': 1.0,
    'semi_major_axis': 6378137.0,
    'semi_minor_axis': 6356752.314245179,
    'towgs84': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}


Extracting attributes from CRS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are many attributes you can pull from the :class:`pyproj.crs.CRS`.
This is just a small subset of what is available.


.. code:: python

    >>> crs = CRS("urn:ogc:def:crs,crs:EPSG::2393,crs:EPSG::5717")
    >>> crs
    <Compound CRS: EPSG:3901>
    Name: KKJ / Finland Uniform Coordinate System + N60 height
    Axis Info [cartesian|vertical]:
    - X[north]: Northing (metre)
    - Y[east]: Easting (metre)
    - H[up]: Gravity-related height (metre)
    Area of Use:
    - undefined
    Datum: Kartastokoordinaattijarjestelma (1966)
    - Ellipsoid: International 1924
    - Prime Meridian: Greenwich
    Sub CRS:
    - KKJ / Finland Uniform Coordinate System
    - N60 height
    >>> crs.sub_crs_list
    [<Projected CRS: EPSG:2393>
    Name: KKJ / Finland Uniform Coordinate System
    Axis Info [cartesian]:
    - X[north]: Northing (metre)
    - Y[east]: Easting (metre)
    Area of Use:
    - name: Finland - 25.5°E to 28.5°E onshore. Also all country.
    - bounds: (19.24, 59.75, 31.59, 70.09)
    Coordinate Operation:
    - name: Finland Uniform Coordinate System
    - method: Transverse Mercator
    Datum: Kartastokoordinaattijarjestelma (1966)
    - Ellipsoid: International 1924
    - Prime Meridian: Greenwich
    , <Vertical CRS: EPSG:5717>
    Name: N60 height
    Axis Info [vertical]:
    - H[up]: Gravity-related height (metre)
    Area of Use:
    - name: Finland - onshore
    - bounds: (19.24, 59.75, 31.59, 70.09)
    Datum: Helsinki 1960
    - Ellipsoid: undefined
    - Prime Meridian: undefined
    ]
    >>> print(crs.sub_crs_list[0].coordinate_operation.to_wkt(pretty=True))
    CONVERSION["Finland Uniform Coordinate System",
        METHOD["Transverse Mercator",
            ID["EPSG",9807]],
        PARAMETER["Latitude of natural origin",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8801]],
        PARAMETER["Longitude of natural origin",27,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8802]],
        PARAMETER["Scale factor at natural origin",1,
            SCALEUNIT["unity",1],
            ID["EPSG",8805]],
        PARAMETER["False easting",3500000,
            LENGTHUNIT["metre",1],
            ID["EPSG",8806]],
        PARAMETER["False northing",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8807]]]
    >>> cop.method_code
    '9807'
    >>> cop.method_name
    'Transverse Mercator'
    >>> cop.params
    [Param(name=Latitude of natural origin, auth_name=EPSG, code=8801, value=0.0, unit_name=degree, unit_auth_name=, unit_code=, unit_category=angular),
     ...
     Param(name=False northing, auth_name=EPSG, code=8807, value=0.0, unit_name=metre, unit_auth_name=, unit_code=, unit_category=linear)]


Transformations from CRS to CRS
-------------------------------

Step 1: Inspect CRS definition to ensure proper area of use and axis order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For more options available for inspection, usage examples,
and documentation see :class:`pyproj.crs.CRS`.

.. code:: python

    >>> from pyproj import CRS
    >>> crs_4326 = CRS.from_epsg(4326)
    >>> crs_4326
    <Geographic 2D CRS: EPSG:4326>
    Name: WGS 84
    Axis Info [ellipsoidal]:
    - Lat[north]: Geodetic latitude (degree)
    - Lon[east]: Geodetic longitude (degree)
    Area of Use:
    - name: World
    - bounds: (-180.0, -90.0, 180.0, 90.0)
    Datum: World Geodetic System 1984
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

    >>> crs_26917 = CRS.from_epsg(26917)
    >>> crs_26917
    <Projected CRS: EPSG:26917>
    Name: NAD83 / UTM zone 17N
    Axis Info [cartesian]:
    - E[east]: Easting (metre)
    - N[north]: Northing (metre)
    Area of Use:
    - name: North America - 84°W to 78°W and NAD83 by country
    - bounds: (-84.0, 23.81, -78.0, 84.0)
    Coordinate Operation:
    - name: UTM zone 17N
    - method: Transverse Mercator
    Datum: North American Datum 1983
    - Ellipsoid: GRS 1980
    - Prime Meridian: Greenwich


Note that `crs_4326` has the latitude (north) axis first and the `crs_26917`
has the easting axis first. This means that in the transformation, we will need
to input the data with latitude first and longitude second. Also, note that the
second projection is a UTM projection with bounds (-84.0, 23.81, -78.0, 84.0) which
are in the form (min_x, min_y, max_x, max_y), so the transformation input/output should
be within those bounds for best results.


Step 2: Create Transformer to convert from CRS to CRS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`pyproj.transformer.Transformer` can be initialized with anything supported
by :meth:`pyproj.crs.CRS.from_user_input`. There are a couple of examples added
here for demonstration. For more usage examples and documentation,
see :class:`pyproj.transformer.Transformer`.


.. code:: python

    >>> from pyproj import Transformer
    >>> transformer = Transformer.from_crs(crs_4326, crs_26917)
    >>> transformer = Transformer.from_crs(4326, 26917)
    >>> transformer = Transformer.from_crs("EPSG:4326", "EPSG:26917")
    >>> transformer
    <Unknown Transformer: unknown>
    Inverse of NAD83 to WGS 84 (1) + UTM zone 17N
    >>> transformer.transform(50, -80)
    (571666.4475041276, 5539109.815175673)

If you prefer to always have the axis order in the x,y or lon,lat order,
you can use the `always_xy` option when creating the transformer.

.. code:: python

    >>> from pyproj import Transformer
    >>> transformer = Transformer.from_crs("EPSG:4326", "EPSG:26917", always_xy=True)
    >>> transformer.transform(-80, 50)
    (571666.4475041276, 5539109.815175673)



Converting between geographic and projection coordinates within one datum
-------------------------------------------------------------------------

Step 1: Retrieve the geodetic CRS based on original CRS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    >>> from pyproj import CRS
    >>> crs = CRS.from_epsg(3857)
    >>> crs
    <Projected CRS: EPSG:3857>
    Name: WGS 84 / Pseudo-Mercator
    Axis Info [cartesian]:
    - X[east]: Easting (metre)
    - Y[north]: Northing (metre)
    Area of Use:
    - name: World - 85°S to 85°N
    - bounds: (-180.0, -85.06, 180.0, 85.06)
    Coordinate Operation:
    - name: Popular Visualisation Pseudo-Mercator
    - method: Popular Visualisation Pseudo Mercator
    Datum: World Geodetic System 1984
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

    >>> crs.geodetic_crs
    <Geographic 2D CRS: EPSG:4326>
    Name: WGS 84
    Axis Info [ellipsoidal]:
    - Lat[north]: Geodetic latitude (degree)
    - Lon[east]: Geodetic longitude (degree)
    Area of Use:
    - name: World
    - bounds: (-180.0, -90.0, 180.0, 90.0)
    Datum: World Geodetic System 1984
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich



Step 2: Create Transformer to convert from geodetic CRS to CRS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    >>> proj = Transformer.from_crs(crs.geodetic_crs, crs)
    >>> proj
    <Conversion Transformer: pipeline>
    Popular Visualisation Pseudo-Mercator
    Area of Use:
    - name: World
    - bounds: (-180.0, -90.0, 180.0, 90.0)
    >>> proj.transform(12, 15)
    (1669792.3618991035, 1345708.4084091093)


4D Transformations with Time
----------------------------

.. note:: If you are doing a transformation with a CRS that is time based,
    it is recommended to include the time in the transformaton operation.


.. code:: python

    >>> transformer = Transformer.from_crs(7789, 8401)
    >>> transformer
    <Transformation Transformer: helmert>
    ITRF2014 to ETRF2014 (1)
    >>> transformer.transform(xx=3496737.2679, yy=743254.4507, zz=5264462.9620, tt=2019.0)
    (3496737.757717311, 743253.9940103051, 5264462.701132784, 2019.0)



Geodesic calculations
---------------------
This is useful if you need to calculate the distance between two
points or the area of a geometry on Earth's surface.

For more examples of usage and documentation, see :class:`pyproj.Geod`.


Creating Geod class
~~~~~~~~~~~~~~~~~~~

This example demonstrates creating a :class:`pyproj.Geod` using an
ellipsoid name as well as deriving one using a :class:`pyproj.crs.CRS`.

.. code:: python

    >>> from pyproj import CRS, Geod
    >>> geod_clrk = Geod(ellps='clrk66') # Use Clarke 1866 ellipsoid.
    >>> geod_clrk
    Geod(ellps='clrk66')
    >>> geod_wgs84 = CRS("epsg:4326").get_geod()
    >>> geod_wgs84
    Geod('+a=6378137 +f=0.0033528106647475126')


Geodesic line length
~~~~~~~~~~~~~~~~~~~~

Calculate the geodesic length of a line (See: :meth:`pyproj.Geod.line_length`):

.. code:: python

    >>> from pyproj import Geod
    >>> lats = [-72.9, -71.9, -74.9, -74.3, -77.5, -77.4, -71.7, -65.9, -65.7,
    ...         -66.6, -66.9, -69.8, -70.0, -71.0, -77.3, -77.9, -74.7]
    >>> lons = [-74, -102, -102, -131, -163, 163, 172, 140, 113,
    ...         88, 59, 25, -4, -14, -33, -46, -61]
    >>> geod = Geod(ellps="WGS84")
    >>> total_length = geod.line_length(lons, lats)
    >>> "{:.3f}".format(total_length)
    '14259605.611'

Calculate the geodesic length of a shapely geometry (See: :meth:`pyproj.Geod.geometry_length`):

.. code:: python

    >>> from pyproj import Geod
    >>> from shapely.geometry import Point, LineString
    >>> line_string = LineString([Point(1, 2), Point(3, 4)]))
    >>> geod = Geod(ellps="WGS84")
    >>> total_length = geod.geometry_length(line_string)
    >>> "{:.3f}".format(total_length)
    '313588.397'


Geodesic area
~~~~~~~~~~~~~

Calculate the geodesic area and perimeter of a polygon (See: :meth:`pyproj.Geod.polygon_area_perimeter`):

.. code:: python

    >>> from pyproj import Geod
    >>> geod = Geod('+a=6378137 +f=0.0033528106647475126')
    >>> lats = [-72.9, -71.9, -74.9, -74.3, -77.5, -77.4, -71.7, -65.9, -65.7,
    ...         -66.6, -66.9, -69.8, -70.0, -71.0, -77.3, -77.9, -74.7]
    >>> lons = [-74, -102, -102, -131, -163, 163, 172, 140, 113,
    ...         88, 59, 25, -4, -14, -33, -46, -61]
    >>> poly_area, poly_perimeter = geod.polygon_area_perimeter(lons, lats)
    >>> "{:.3f} {:.3f}".format(poly_area, poly_perimeter)
    '13376856682207.406 14710425.407'


Calculate the geodesic area and perimeter of a shapely polygon (See: :meth:`pyproj.Geod.geometry_area_perimeter`):


.. code:: python

    >>> from pyproj import Geod
    >>> from shapely.geometry import LineString, Point, Polygon
    >>> geod = Geod('+a=6378137 +f=0.0033528106647475126')
    >>> poly_area, poly_perimeter = geod.geometry_area_perimeter(
            Polygon(
                LineString([Point(1, 1), Point(1, 10), Point(10, 10), Point(10, 1)]),
                holes=[LineString([Point(1, 2), Point(3, 4), Point(5, 2)])],
            )
        )
    >>> "{:.3f} {:.3f}".format(poly_area, poly_perimeter)
    '-944373881400.339 3979008.036'
