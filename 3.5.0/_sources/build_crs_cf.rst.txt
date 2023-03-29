.. _build_crs_cf:

Managing CRS to and from CF
============================

http://cfconventions.org/cf-conventions/cf-conventions.html

Exporting CRS to CF
--------------------
When exporting a CRS to the Climate and Forecast (CF) conventions,
you need both the grid mapping as well as the coordinate system.
If you don't use the coordinate system, then you will lose the units
of your projection.


In this example, this is the CRS we will use:

.. code-block:: python

    from pyproj import CRS

    crs = CRS("EPSG:4326")


To get the grid mapping you use :meth:`pyproj.crs.CRS.to_cf`:

.. versionadded:: 2.2.0

.. code-block:: python

    cf_grid_mapping = crs.to_cf()


Contents of `cf_grid_mapping`::


    {'crs_wkt': 'GEOGCRS["WGS 84",DATUM["World Geodetic System '
                ....,ID["EPSG",4326]]',
    'geographic_crs_name': 'WGS 84',
    'grid_mapping_name': 'latitude_longitude',
    'inverse_flattening': 298.257223563,
    'longitude_of_prime_meridian': 0.0,
    'prime_meridian_name': 'Greenwich',
    'reference_ellipsoid_name': 'WGS 84',
    'semi_major_axis': 6378137.0,
    'semi_minor_axis': 6356752.314245179}


To get the coordinate system, you use :meth:`pyproj.crs.CRS.cs_to_cf`:

.. versionadded:: 3.0.0

.. code-block:: python

    cf_coordinate_system = crs.cs_to_cf()


Contents of `cf_coordinate_system`::

    [{'long_name': 'geodetic latitude coordinate',
    'standard_name': 'latitude',
    'units': 'degrees_north',
    'axis': 'Y'},
    {'long_name': 'geodetic longitude coordinate',
    'standard_name': 'longitude',
    'units': 'degrees_east',
    'axis': 'X'}]


Importing CRS from CF
----------------------

When importing a CRS from the Climate and Forecast (CF) conventions,
you need both the grid mapping as well as the coordinate system.
If you don't use the coordinate system, then you will lose the units
of your projection.

.. note:: If the CF `crs_wkt` attribute is available, the coordinate system is
          inside of the WKT and can be used to create the CRS in a single step.

.. warning:: If building from grid mapping, be mindful of the axis order. https://github.com/cf-convention/cf-conventions/pull/224


Build the CRS from CF grid mapping:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, this is the grid mapping and coordinate system we will use::

  variables:
    double x(x) ;
      x:standard_name = "projection_x_coordinate" ;
      x:long_name = "Easting" ;
      x:units = "m" ;
    double y(y) ;
      y:standard_name = "projection_y_coordinate" ;
      y:long_name = "Northing" ;
      y:units = "m" ;
    int crsOSGB ;
      crsOSGB:grid_mapping_name = "transverse_mercator";
      crsOSGB:semi_major_axis = 6377563.396 ;
      crsOSGB:inverse_flattening = 299.3249646 ;
      crsOSGB:longitude_of_prime_meridian = 0.0 ;
      crsOSGB:latitude_of_projection_origin = 49.0 ;
      crsOSGB:longitude_of_central_meridian = -2.0 ;
      crsOSGB:scale_factor_at_central_meridian = 0.9996012717 ;
      crsOSGB:false_easting = 400000.0 ;
      crsOSGB:false_northing = -100000.0 ;

.. note:: If the units are meters as in this example,
          then no further changes are necessary.

.. code-block:: python

    from pyproj import CRS

    crs = CRS.from_cf(
        {
            "grid_mapping_name": "transverse_mercator",
            "semi_major_axis": 6377563.396,
            "inverse_flattening": 299.3249646,
            "longitude_of_prime_meridian": 0.0,
            "latitude_of_projection_origin": 49.0,
            "longitude_of_central_meridian": -2.0,
            "scale_factor_at_central_meridian": 0.9996012717,
            "false_easting": 400000.0,
            "false_northing": -100000.0,
        }
    )


Modify the CRS with coordinate system:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 3.0.0

.. note:: If the CF `crs_wkt` attribute is available, the coordinate system is
          inside of the WKT and can be used to create the CRS in a single step.

.. warning:: Be mindful of the axis order. https://github.com/cf-convention/cf-conventions/pull/224


In this example, assume everything is the same as above.
However, the units are instead `US_Survey_Foot`::

  variables:
    double x(x) ;
      x:standard_name = "projection_x_coordinate" ;
      x:long_name = "Easting" ;
      x:units = "US_Survey_Foot" ;
    double y(y) ;
      y:standard_name = "projection_y_coordinate" ;
      y:long_name = "Northing" ;
      y:units = "US_Survey_Foot" ;
    ...


In this case, you will need to get the unit conversion factor:

https://github.com/SciTools/cf-units


.. code-block:: python

    from cf_units import Unit
    from pyproj import CRS

    cf_unit = Unit("US_Survey_Foot")
    unit = {
        "type": "LinearUnit",
        "name": "US Survey Foot",
        "conversion_factor": cf_unit.convert(1, "m"),
    }
    cartesian_cs = {
        "$schema": "https://proj.org/schemas/v0.2/projjson.schema.json",
        "type": "CoordinateSystem",
        "subtype": "Cartesian",
        "axis": [
            {"name": "Easting", "abbreviation": "E", "direction": "east", "unit": unit},
            {"name": "Northing", "abbreviation": "N", "direction": "north", "unit": unit},
        ],
    }
    crs = CRS.from_cf(
        {
            "grid_mapping_name": "transverse_mercator",
            "semi_major_axis": 6377563.396,
            "inverse_flattening": 299.3249646,
            "longitude_of_prime_meridian": 0.0,
            "latitude_of_projection_origin": 49.0,
            "longitude_of_central_meridian": -2.0,
            "scale_factor_at_central_meridian": 0.9996012717,
            "false_easting": 400000.0,
            "false_northing": -100000.0,
        },
        cartesian_cs=cartesian_cs,
    )
