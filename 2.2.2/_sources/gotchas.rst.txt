.. _gotchas:

Gotchas/FAQ
===========

This is a page for some suggestions, gotchas, and FAQs.

Also see:
  - :ref:`examples`
  - `PROJ FAQ <https://proj.org/faq.html>`__


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

:class:`~pyproj.proj.Proj` is limited to converting between geographic and 
projection coordinates within one datum. If you have coordinates in latitude
and longitude, and you want to convert it to your projection, it is recommended
to use the :class:`~pyproj.transformer.Transformer` as it takes into account datum
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

Then, use the :class:`~pyproj.transformer.Transformer` to transform from latitude
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

If you use :class:`~pyproj.proj.Proj`, it will use the geodetic CRS with
from the projected CRS with the same datum to do the transformation,
which may not be what you want.

.. code-block:: python

    >>> from pyproj import Proj
    >>> Proj('epsg:28992')(5.068913, 52.067567)
    (133148.22970574044, 453192.24450392975)
    >>> transg = Transformer.from_crs(crs_proj.geodetic_crs, crs_proj)
    >>> transg.transform(52.067567, 5.068913)
    (133148.22970574044, 453192.24450392975)


Upgrading to pyproj 2 from pyproj 1
-----------------------------------

We recommended using the :class:`~pyproj.transformer.Transformer` and
:class:`~pyproj.crs.CRS` in place of the :class:`~pyproj.proj.Proj` and
:meth:`~pyproj.transformer.transform`.

Also see:
  - :ref:`examples`
  - :ref:`optimize_transformations`


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
