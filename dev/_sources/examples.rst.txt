Getting Started
===============

There are examples of usage within the API documentation and tests. This
section is to demonstrate recommended usage.


Transformations from CRS to CRS
-------------------------------

Step 1: Inspect CRS definition to ensure proper area of use and axis order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For more options available for inspection, usage examples,
and documentation see :class:`~pyproj.crs.CRS`.

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
second projection is a UTM procection with bounds (-84.0, 23.81, -78.0, 84.0) which
are in the form (min_x, min_y, max_x, max_y), so the transformation input/output should
be within those bounds for best results.


Step 2: Create Transformer to convert from CRS to CRS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`~pyproj.transformer.Transformer` can be initialized with anything supported
by :meth:`~pyproj.crs.CRS.from_user_input`. There are a couple of examples added
here for demonstration. For more usage examples and documentation,
see :class:`~pyproj.transformer.Transformer`.


.. code:: python

    >>> from pyproj import Transformer
    >>> transformer = Transformer.from_crs(crs_4326, crs_26917)
    >>> transformer = Transformer.from_crs(4326, 26917)
    >>> transformer = Transformer.from_crs("EPSG:4326", "EPSG:26917")
    >>> transformer
    Definiton:
    unavailable until proj_trans is called
    WKT:
    undefined
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
    Definiton:
    proj=pipeline step proj=axisswap order=2,1 step proj=unitconvert xy_in=deg xy_out=rad step proj=webmerc lat_0=0 lon_0=0 x_0=0 y_0=0 ellps=WGS84
    WKT:
    CONVERSION["Popular Visualisation Pseudo-Mercator",
        METHOD["Popular Visualisation Pseudo Mercator",
            ID["EPSG",1024]],
        PARAMETER["Latitude of natural origin",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8801]],
        PARAMETER["Longitude of natural origin",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8802]],
        PARAMETER["False easting",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8806]],
        PARAMETER["False northing",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8807]],
        ID["EPSG",3856]]

    >>> proj.transform(12, 15)
    (1669792.3618991035, 1345708.4084091093)


4D Transformations with Time
----------------------------

.. note:: If you are doing a transformation with a CRS that is time based,
    it is recommended to include the time in the transformaton operation.


.. code:: python

    >>> transformer = Transformer.from_crs(7789, 8401)
    >>> transformer.transform(xx=3496737.2679, yy=743254.4507, zz=5264462.9620, tt=2019.0)
    (3496737.757717311, 743253.9940103051, 5264462.701132784, 2019.0)


Geodetic calculations
---------------------

For more examples of usage and documentation, see :class:`~pyproj.Geod`.

This example demonstrates creating a :class:`~pyproj.Geod` using an
ellipsoid name as well as deriving one using a :class:`~pyproj.crs.CRS`.

.. code:: python

    >>> from pyproj import CRS, Geod
    >>> from pyproj import CRS, Geod
    >>> geod_clrk = Geod(ellps='clrk66') # Use Clarke 1866 ellipsoid.
    >>> geod_clrk
    Geod(ellps='clrk66')
    >>> geod_wgs84 = CRS("epsg:4326").get_geod()
    >>> geod_wgs84
    Geod('+a=6378137 +f=0.0033528106647475126')
    >>> portland_lat = 45.+(31./60.); portland_lon = -123.-(41./60.)
    >>> boston_lat = 42.+(15./60.); boston_lon = -71.-(7./60.)
    >>> az12, az21, dist = geod_clrk.inv(boston_lon, boston_lat, portland_lon, portland_lat)
    >>> az12, az21, dist
    (-66.5305947876623, 75.65363415556968, 4164192.7080994667)
    >>> az12_wgs, az21_wgs, dist_wgs = geod_wgs84.inv(boston_lon, boston_lat, portland_lon, portland_lat)
    >>> az12_wgs, az21_wgs, dist_wgs
    (-66.53043696156747, 75.65384304856798, 4164074.2392955828)