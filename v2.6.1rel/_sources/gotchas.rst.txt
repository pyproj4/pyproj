.. _gotchas:

Gotchas/FAQ
===========

This is a page for some suggestions, gotchas, and FAQs.

Also see:
  - :ref:`examples`
  - `PROJ FAQ <https://proj.org/faq.html>`__


What is the best format to store the CRS information?
-----------------------------------------------------
PROJ strings can be lossy for storing CRS information.
If you can avoid it, it is best to not use them.
Additionally, PROJ strings will likely not be supported
in future major version of PROJ for storing CRS information.

More info: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems


Axis order changes in PROJ 6+
-----------------------------
- https://proj.org/faq.html#why-is-the-axis-ordering-in-proj-not-consistent
- See warning at the top of :ref:`transformer`
- Examples of how to handle it: :ref:`examples`
- :ref:`min_confidence`


`+init=<auth>:<auth_code>` should be replaced with `<auth>:<auth_code>`
-----------------------------------------------------------------------

The `+init=<auth>:<auth_code>` syntax is deprecated and will be removed
in future versions of PROJ. Also, if you use the `+init` syntax,
you may have problems initializing projections when the other syntax works.

.. code-block:: python

    >>> from pyproj import CRS
    >>> CRS("ESRI:54009")
    <Projected CRS: ESRI:54009>
    Name: World_Mollweide
    Axis Info [cartesian]:
    - E[east]: Easting (metre)
    - N[north]: Northing (metre)
    Area of Use:
    - name: World
    - bounds: (-180.0, -90.0, 180.0, 90.0)
    Coordinate Operation:
    - name: World_Mollweide
    - method: Mollweide
    Datum: World Geodetic System 1984
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

    >>> CRS("+init=ESRI:54009")
    ...
    pyproj.exceptions.CRSError: Invalid projection: +init=ESRI:54009 +type=crs: (Internal Proj Error: proj_create: cannot expand +init=ESRI:54009 +type=crs)


Proj (Not a generic latitude/longitude to projection converter)
---------------------------------------------------------------

:class:`pyproj.proj.Proj` is limited to converting between geographic and
projection coordinates within one datum. If you have coordinates in latitude
and longitude, and you want to convert it to your projection, it is recommended
to use the :class:`pyproj.transformer.Transformer` as it takes into account datum
shifts.

You likely want to start from `EPSG:4326` (WGS84) for coordinates as
latitude and longitude.

.. code-block:: python

    >>> from pyproj import CRS
    >>> crs_4326 = CRS("WGS84")
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

Then, use the :class:`pyproj.transformer.Transformer` to transform from latitude
and longitude to your projection as you might have a projection with a different
datum.

.. code-block:: python

    >>> crs_proj = CRS("EPSG:28992")
    >>> crs_proj
    <Projected CRS: EPSG:28992>
    Name: Amersfoort / RD New
    Axis Info [cartesian]:
    - X[east]: Easting (metre)
    - Y[north]: Northing (metre)
    Area of Use:
    - name: Netherlands - onshore
    - bounds: (3.2, 50.75, 7.22, 53.7)
    Coordinate Operation:
    - name: RD New
    - method: Oblique Stereographic
    Datum: Amersfoort
    - Ellipsoid: Bessel 1841
    - Prime Meridian: Greenwich
    >>> crs_proj.datum == crs_4326.datum
    False
    >>> from pyproj import Transformer
    >>> transformer = Transformer.from_crs(crs_4326, crs_proj)
    >>> transformer.transform(52.067567, 5.068913)
    (133175.3690698233, 453300.86739169655)

If you use :class:`pyproj.proj.Proj`, it will use the geodetic CRS with
from the projected CRS with the same datum to do the transformation,
which may not be what you want.

.. code-block:: python

    >>> from pyproj import Proj
    >>> Proj('epsg:28992')(5.068913, 52.067567)
    (133148.22970574044, 453192.24450392975)
    >>> transg = Transformer.from_crs(crs_proj.geodetic_crs, crs_proj)
    >>> transg.transform(52.067567, 5.068913)
    (133148.22970574044, 453192.24450392975)


.. _min_confidence:

Why does the EPSG code return when using `EPSG:xxxx` and not with `+init=EPSG:xxxx`?
------------------------------------------------------------------------------------

From: https://gis.stackexchange.com/a/326919/144357


The reason that the EPSG code does not appear with the CRS initialized with
the `init=` syntax is that the CRS are different.

.. code-block:: python

    >>> from pyproj import CRS
    >>> crs_deprecated = CRS(init="epsg:4544")
    >>> crs = CRS("epsg:4544")
    >>> crs == crs_deprecated
    False

Upon further inspection of the `Axis Info` section, you can see that the difference
is in the **axis order**.

.. code-block:: python

    >>> crs_deprecated
    <Projected CRS: +init=epsg:4544 +type=crs>
    Name: CGCS2000 / 3-degree Gauss-Kruger CM 105E
    Axis Info [cartesian]:
    - E[east]: Easting (metre)
    - N[north]: Northing (metre)
    Area of Use:
    - name: China - 103.5°E to 106.5°E
    - bounds: (103.5, 22.5, 106.5, 42.21)
    Coordinate Operation:
    - name: Gauss-Kruger CM 105E
    - method: Transverse Mercator
    Datum: China 2000
    - Ellipsoid: CGCS2000
    - Prime Meridian: Greenwich

    >>> crs
    <Projected CRS: EPSG:4544>
    Name: CGCS2000 / 3-degree Gauss-Kruger CM 105E
    Axis Info [cartesian]:
    - X[north]: Northing (metre)
    - Y[east]: Easting (metre)
    Area of Use:
    - name: China - 103.5°E to 106.5°E
    - bounds: (103.5, 22.5, 106.5, 42.21)
    Coordinate Operation:
    - name: Gauss-Kruger CM 105E
    - method: Transverse Mercator
    Datum: China 2000
    - Ellipsoid: CGCS2000
    - Prime Meridian: Greenwich


The reason the `min_confidence` parameter in
:meth:`pyproj.crs.CRS.to_epsg` and :meth:`pyproj.crs.CRS.to_authority`
exists is because you can initialize a CRS in several different methods and
some of them do not always coorespond to an EPSG or authortiy code, but it
can be close enough.

For example, if you have a WKT/PROJ string and you use it to create the CRS instance,
in most cases you want to be sure that the EPSG code given by to_epsg will give you a
CRS instance similar to the one created by the WKT/PROJ string.
However, if an EPSG code does not exist that matches you WKT/PROJ string with
a `min_confidence` you don't want to get that EPSG code back as it will make
you think that the WKT/PROJ string and the EPSG code are one and the same when
they are not.

However, if you are only wanting to get the EPSG code that is closest
to the PROJ/WKT string, then you can reduce your min_confidence to a
threshold you are comfortable with.

Here is an example of that:

.. code-block:: python

    >>> crs_deprecated = CRS("+init=epsg:4326")
    >>> crs_deprecated.to_epsg(100)
    >>> crs_deprecated.to_epsg(70)
    >>> crs_deprecated.to_epsg(20)
    4326
    >>> crs_latlon = CRS("+proj=latlon")
    >>> crs_latlon.to_epsg(100)
    >>> crs_latlon.to_epsg(70)
    4326
    >>> crs_epsg = CRS.from_epsg(4326)
    >>> crs_epsg.to_epsg(100)
    4326
    >>> crs_wkt = CRS(crs_epsg.to_wkt())
    >>> crs_wkt.to_epsg(100)
    4326
    >>> crs_wkt == crs_epsg
    True
    >>> crs_epsg == crs_latlon
    False
    >>> crs_epsg == crs_deprecated
    False


Internal PROJ Error ... SQLite error on SELECT
----------------------------------------------

The PROJ database is based on the EPSG database. With each release,
there is a good chance that there are database updates. If you have multiple
versions of PROJ installed on your systems and the search path for
the data directory becomes mixed up, you may see an error message like:
`SQLite error on SELECT`. This is likely due to a version of PROJ
attempting to use an incompatible database.


Debugging tips:

- To get data directory being used: :func:`pyproj.datadir.get_data_dir`
- The order for searching for the data directory can be found in
  the docstrings of :func:`pyproj.datadir.get_data_dir`
- To change the data directory: :func:`pyproj.datadir.get_data_dir`


.. _upgrade_transformer:

Upgrading to pyproj 2 from pyproj 1
-----------------------------------

We recommended using the :class:`pyproj.transformer.Transformer` and
:class:`pyproj.crs.CRS` in place of the :class:`pyproj.proj.Proj` and
:meth:`pyproj.transformer.transform`.

Also see:
  - :ref:`examples`
  - :ref:`optimize_transformations`

.. warning:: :meth:`pyproj.transformer.transform` and :meth:`pyproj.transformer.itransform`
             are deprecated.

pyproj 1 style:

    >>> from functools import partial
    >>> from pyproj import Proj, transform
    >>> proj_4326 = Proj(init="epsg:4326")
    >>> proj_3857 = Proj(init="epsg:3857")
    >>> transformer = partial(transform, proj_4326, proj_3857)
    >>> transformer(12, 12)


pyproj 2 style:

    >>> from pyproj import Transformer
    >>> transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
    >>> transformer.transform(12, 12)
