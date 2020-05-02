Building a Coordinate Reference System
======================================

.. versionadded:: 2.5.0

PROJ strings have the potential to lose much of the information
about a coordinate reference system (CRS).

More information: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems

However, PROJ strings make it really simple to construct a CRS.
This addition is meant to simplify the process of transitioning
from the PROJ form of the string to the WKT form WKT. The CRS
classes can be used in the :meth:`pyproj.transformer.Transformer.from_crs`
method just like the :class:`pyproj.crs.CRS` class.

The current set of classes does not cover every possible use case,
but hopefully it is enough to get you started.
If you notice something is missing that you need, feel free to open an issue on GitHub.


.. note:: PROJ >= 7.0.0 will have better support for aliases for datum names.
          If you have a previous version of PROJ, you will need to use the
          full name of the datum. There is support currently for the old PROJ
          names for datums such as WGS84 and NAD83.


Here are links to the API docs for the pieces you need to get started:

- :ref:`crs`
- :ref:`coordinate_operation`
- :ref:`datum`
- :ref:`coordinate_system`


Geographic CRS
--------------

This is a simple example of creating a lonlat projection.

PROJ string::

    +proj=longlat +datum=WGS84 +no_defs

.. code-block:: python

    from pyproj.crs import GeographicCRS

    geog_crs = GeographicCRS()
    geog_wkt = geog_crs.to_wkt()


This example is meant to show off different intialization methods.
It can be simplified to not use the Ellipsoid or PrimeMeridian objects.

PROJ string::

    +proj=longlat +ellps=airy +pm=lisbon +no_defs

.. code-block:: python

    from pyproj.crs import Ellipsoid, GeographicCRS, PrimeMeridian
    from pyproj.crs.datum import CustomDatum

    cd = CustomDatum(
        ellipsoid=Ellipsoid.from_epsg(7001),
        prime_meridian=PrimeMeridian.from_name("Lisbon"),
    )
    geog_crs = GeographicCRS(datum=cd)
    geog_wkt = geog_crs.to_wkt()


Projected CRS
-------------

Simple example using defaults.

PROJ string::

    +proj=aea +lat_0=0 +lon_0=0 +lat_1=0 +lat_2=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs

.. code-block:: python

    from pyproj.crs import ProjectedCRS
    from pyproj.crs.coordinate_operation import AlbersEqualAreaConversion

    aeaop = AlbersEqualAreaConversion(0, 0)
    proj_crs = ProjectedCRS(conversion=aeaop)
    crs_wkt = proj_crs.to_wkt()


More complex example with custom parameters.

PROJ string::

    +proj=utm +zone=14 +a=6378137 +b=6356752 +pm=lisbon +units=m +no_defs

.. code-block:: python

    from pyproj.crs import GeographicCRS, ProjectedCRS
    from pyproj.crs.coordinate_operation import UTMConversion
    from pyproj.crs.datum import CustomDatum, CustomEllipsoid

    ell = CustomEllipsoid(semi_major_axis=6378137, semi_minor_axis=6356752)
    cd = CustomDatum(ellipsoid=ell, prime_meridian="Lisbon")
    proj_crs = ProjectedCRS(
        conversion=UTMConversion(14), geodetic_crs=GeographicCRS(datum=cd),
    )
    crs_wkt = proj_crs.to_wkt()


Bound CRS
---------

This is an example building a CRS with `towgs84`.

PROJ string::

    +proj=tmerc +lat_0=0 +lon_0=15 +k=0.9996 +x_0=2520000 +y_0=0 +ellps=intl +towgs84=-122.74,-34.27,-22.83,-1.884,-3.4,-3.03,-15.62 +units=m +no_defs

.. code-block:: python

    from pyproj.crs import BoundCRS, Ellipsoid, GeographicCRS, ProjectedCRS
    from pyproj.crs.coordinate_operation import (
        TransverseMercatorConversion,
        ToWGS84Transformation,
    )
    from pyproj.crs.datum import CustomDatum

    proj_crs = ProjectedCRS(
        conversion=TransverseMercatorConversion(
            latitude_natural_origin=0,
            longitude_natural_origin=15,
            false_easting=2520000,
            false_northing=0,
            scale_factor_natural_origin=0.9996,
        ),
        geodetic_crs=GeographicCRS(
            datum=CustomDatum(ellipsoid="International 1909 (Hayford)")
        ),
    )
    bound_crs = BoundCRS(
        source_crs=proj_crs,
        target_crs="WGS 84",
        transformation=ToWGS84Transformation(
            proj_crs.geodetic_crs, -122.74, -34.27, -22.83, -1.884, -3.4, -3.03, -15.62
        ),
    )
    crs_wkt = bound_crs.to_wkt()


Compound CRS
-------------

The PROJ string is quite lossy in this example, so it is not provided.

.. warning:: geoid_model support only exists in PROJ >= 6.3.0

.. code-block:: python

    from pyproj.crs import CompoundCRS, GeographicCRS, ProjectedCRS, VerticalCRS
    from pyproj.crs.coordinate_system import Cartesian2DCS, VerticalCS
    from pyproj.crs.coordinate_operation import LambertConformalConic2SPConversion


    vertcrs = VerticalCRS(
        name="NAVD88 height",
        datum="North American Vertical Datum 1988",
        vertical_cs=VerticalCS(),
        geoid_model="GEOID12B",
    )
    projcrs = ProjectedCRS(
        name="NAD83 / Pennsylvania South",
        conversion=LambertConformalConic2SPConversion(
            latitude_false_origin=39.3333333333333,
            longitude_false_origin=-77.75,
            latitude_first_parallel=40.9666666666667,
            latitude_second_parallel=39.9333333333333,
            easting_false_origin=600000,
            northing_false_origin=0,
        ),
        geodetic_crs=GeographicCRS(datum="North American Datum 1983"),
        cartesian_cs=Cartesian2DCS(),
    )
    compcrs = CompoundCRS(
        name="NAD83 / Pennsylvania South + NAVD88 height", components=[projcrs, vertcrs],
    )
    crs_wkt = compcrs.to_wkt()
