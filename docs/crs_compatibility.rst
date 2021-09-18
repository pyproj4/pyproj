CRS Compatibility Guide for Geospatial Python
==============================================

This is meant to be a guide to help you along the way of you use :class:`pyproj.crs.CRS`
with other Python Geospatial libraries.

.. note:: WKT2 is the best format for storing your CRS according to the
          `PROJ FAQ <https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems>`__.


osgeo/gdal
----------

https://github.com/osgeo/gdal

Converting from `osgeo.osr.SpatialReference` to `pyproj.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from osgeo.osr import SpatialReference
    from pyproj.crs import CRS

    osr_crs = SpatialReference()
    osr_crs.ImportFromEPSG(4326)
    if osgeo.version_info.major < 3:
        proj_crs = CRS.from_wkt(osr_crs.ExportToWkt())
    else:
        proj_crs = CRS.from_wkt(osr_crs.ExportToWkt(["FORMAT=WKT2_2018"]))


Converting from `pyproj.crs.CRS` to `osgeo.osr.SpatialReference`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning:: WKT2 is only supported in GDAL 3+

.. code-block:: python

    import osgeo
    from osgeo.osr import SpatialReference
    from pyproj.crs import CRS
    from pyproj.enums import WktVersion

    proj_crs = CRS.from_epsg(4326)

    osr_crs = SpatialReference()
    if osgeo.version_info.major < 3:
        osr_crs.ImportFromWkt(proj_crs.to_wkt(WktVersion.WKT1_GDAL))
    else:
        osr_crs.ImportFromWkt(proj_crs.to_wkt())


rasterio
--------

https://github.com/mapbox/rasterio

Converting from `rasterio.crs.CRS` to `pyproj.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have `rasterio >= 1.0.14`, then you can pass in the `rasterio.crs.CRS`
directly::

    import rasterio
    import rasterio.crs
    from pyproj.crs import CRS

    with rasterio.Env(OSR_WKT_FORMAT="WKT2_2018"):
        rio_crs = rasterio.crs.CRS.from_epsg(4326)
        proj_crs = CRS.from_user_input(rio_crs)

Otherwise, you should use the `wkt` property::

    import rasterio.crs
    from pyproj.crs import CRS

    with rasterio.Env(OSR_WKT_FORMAT="WKT2_2018"):
        rio_crs = rasterio.crs.CRS.from_epsg(4326)
        proj_crs = CRS.from_wkt(rio_crs.wkt)

Converting from `pyproj.crs.CRS` to `rasterio.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning:: WKT2 is only supported in GDAL 3+

If you have rasterio >= 1.0.26 and GDAL 3+, then you can pass in the `pyproj.crs.CRS`
directly::

    import rasterio.crs
    from pyproj.crs import CRS

    proj_crs = CRS.from_epsg(4326)
    rio_crs = rasterio.crs.CRS.from_user_input(proj_crs)

If you want to be compatible across GDAL/rasterio versions, you can do::

    from packaging import version

    import rasterio
    import rasterio.crs
    from pyproj.crs import CRS
    from pyproj.enums import WktVersion

    proj_crs = CRS.from_epsg(4326)
    if version.parse(rasterio.__gdal_version__) < version.parse("3.0.0")
        rio_crs = rasterio.crs.CRS.from_wkt(proj_crs.to_wkt(WktVersion.WKT1_GDAL))
    else:
        rio_crs = rasterio.crs.CRS.from_wkt(proj_crs.to_wkt())

fiona
------

https://github.com/Toblerity/Fiona

Converting from `fiona` CRS to `pyproj.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Fiona currently stores the CRS as a PROJ string dictionary in the `crs`
attribute. As such, it is best to use the `crs_wkt` attribute.

It is also useful to know that plans exist to add CRS class.
Related GitHub issue `here <https://github.com/Toblerity/Fiona/issues/714>`__.


Example::

    import fiona
    from pyproj.crs import CRS

    with fiona.Env(OSR_WKT_FORMAT="WKT2_2018"), fiona.open(...) as fds:
        proj_crs = CRS.from_wkt(fds.crs_wkt)


Converting from `pyproj.crs.CRS` for `fiona`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning:: WKT2 is only supported in GDAL 3+

If you want to be compatible across GDAL versions, you can do::

    from packaging import version

    import fiona
    from pyproj.crs import CRS

    proj_crs = CRS.from_epsg(4326)

    if version.parse(fiona.__gdal_version__) < version.parse("3.0.0"):
        fio_crs = proj_crs.to_wkt(WktVersion.WKT1_GDAL)
    else:
        # GDAL 3+ can use WKT2
        fio_crs = dc_crs.to_wkt()

    # with fiona.open(..., "w", crs_wkt=fio_crs) as fds:
    #     ...


geopandas
---------

https://github.com/geopandas/geopandas

Also see the `geopandas guide for upgrading to use pyproj CRS class <https://geopandas.readthedocs.io/en/latest/projections.html#upgrading-to-geopandas-0-7-with-pyproj-2-2-and-proj-6>`__

Preparing `pyproj.crs.CRS` for `geopandas`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import fiona
    import geopandas
    from pyproj.crs import CRS
    from pyproj.enums import WktVersion

    proj_crs = CRS.from_epsg(4326)

    if version.parse(geopandas.__version__) >= version.parse("0.7.0"):
        # geopandas uses pyproj.crs.CRS
        geo_crs = proj_crs
    elif version.parse(geopandas.__version__) >= version.parse("0.6.0"):
        # this version of geopandas uses always_xy=True so WKT version is safe
        if version.parse(fiona.__gdal_version__) < version.parse("3.0.0"):
            geo_crs = proj_crs.to_wkt(WktVersion.WKT1_GDAL)
        else:
            # GDAL 3+ can use WKT2
            geo_crs = dc_crs.to_wkt()
    else:
        geo_crs = dc_crs.to_proj4()


`geopandas` to `pyproj.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`pyproj.crs.CRS.from_user_input` can handle anything across the `geopandas`
versions. The only gotcha would be if it is `None`.


.. code-block:: python

    import geopandas
    from pyproj.crs import CRS

    gdf = geopandas.read_file(...)
    proj_crs = CRS.from_user_input(gdf.crs)


cartopy
-------

https://github.com/SciTools/cartopy

.. note:: These examples require cartopy 0.20+

Preparing `pyproj.crs.CRS` for `cartopy.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning:: This only works for CRS created with WKT2,
             PROJ JSON, or a spatial reference ID (i.e. EPSG)
             with the area of use defined. Otherwise,
             the x_limits and y_limits will not work.

.. code-block:: python

    import cartopy.crs as ccrs
    from pyproj.crs import CRS

    # geographic
    proj_crs = CRS.from_epsg(4326)
    cart_crs = ccrs.CRS(proj_crs)

    # projected
    proj_crs = CRS.from_epsg(6933)
    cart_crs = ccrs.Projection(proj_crs)


Preparing `cartopy.crs.CRS` for `pyproj.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: `cartopy.crs.CRS` inherits from `pyproj.crs.CRS`,
          so it should behave like a `pyproj.crs.CRS`.

.. code-block:: python


    from cartopy.crs import PlateCarree
    from pyproj.crs import CRS

    cart_crs = PlateCarree()
    proj_crs = CRS.from_user_input(cart_crs)


pycrs
-----

https://github.com/karimbahgat/PyCRS

.. warning:: Currently does not support WKT2

Preparing `pyproj.crs.CRS` for `pycrs`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import pycrs
    from pyproj.crs import CRS

    proj_crs = CRS.from_epsg(4326)
    py_crs = pycrs.parse.from_ogc_wkt(proj_crs.to_wkt("WKT1_GDAL"))


Preparing `cartopy.crs.CRS` for `pyproj.crs.CRS`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python


    import pycrs
    from pyproj.crs import CRS

    py_crs = pycrs.parse.from_epsg_code(4326)
    proj_crs = CRS.from_wkt(py_crs.to_ogc_wkt())
