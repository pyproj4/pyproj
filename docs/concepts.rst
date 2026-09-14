.. _concepts:

Concepts
========

pyproj is a Python interface to the :term:`PROJ` library. Most of what it does
comes down to answering two questions about a pair (or triple) of numbers:

1. *Where on the Earth is this?* The numbers are only meaningful once you know
   the :term:`Coordinate Reference System (CRS)` they belong to. pyproj
   describes a CRS with the :class:`pyproj.crs.CRS` class.
2. *What are these same points in a different CRS?* Converting coordinates
   between two CRSes is a :term:`coordinate operation`. pyproj does this with
   the :class:`pyproj.transformer.Transformer` class.

A third helper, :class:`pyproj.Geod`, answers questions like "how far apart
are these two points?" directly on the curved Earth without picking a
projection at all.

This page explains the ideas behind these classes without much code. The
:ref:`examples` page shows how to use the classes themselves and the
:ref:`glossary` defines the terms used throughout the documentation. If you
already know what a CRS, a datum, and an EPSG code are, you can skip straight
to :ref:`examples`.


Coordinate Reference Systems (CRS)
----------------------------------

A pair of numbers like ``(-93.58, 42.03)`` does not identify a location on its
own. Is it longitude and latitude in degrees? Or is it latitude first? Is it
meters east and north of some origin? On which model of the Earth? A
**Coordinate Reference System** (CRS) is the description that answers those
questions so that the numbers can be tied to a real place.

A CRS bundles a few things together:

- A :term:`datum`: a model of the shape of the Earth (an :term:`ellipsoid`)
  plus how that model is positioned relative to the real Earth. The
  :term:`WGS 84` datum used by GPS is the most common one you will meet.
- A coordinate system: which axes there are, what units they use, and what
  order they come in (see :term:`axis order`).
- For a projected CRS, the :term:`projection`: the recipe for flattening the
  curved Earth onto a plane.

The :class:`pyproj.crs.CRS` class stores all of this and lets you inspect each
part (``crs.datum``, ``crs.ellipsoid``, ``crs.axis_info``,
``crs.coordinate_operation``, ...).

Geographic CRS
~~~~~~~~~~~~~~

A :term:`geographic CRS` describes positions as angles on the ellipsoid:
longitude and latitude, usually in degrees. No projection is involved. The
best-known example is WGS 84 (``EPSG:4326``), which is what most GPS
receivers, many web APIs, and GeoJSON files use.

Projected CRS
~~~~~~~~~~~~~

A :term:`projected CRS` takes a geographic CRS and applies a map projection to
it so that positions become distances on a flat plane, usually in meters.
Working on a plane makes distances, areas, and gridded data much simpler to
handle. Common examples are the :term:`UTM` zones (for example
``EPSG:26917``, NAD83 / UTM zone 17N) and Web Mercator (``EPSG:3857``), the
projection used by most online map tiles.

Every projection distorts something (shapes, areas, distances, or directions)
and each one is designed to keep that distortion small over a particular
region, its :term:`area of use`. Using a CRS far outside its area of use
gives poor or nonsensical results. PROJ documents the theory in its
:ref:`cartographic projection <proj:projections_intro>` page and lists every
supported projection with pictures in :ref:`proj:projections`.

Why it matters
~~~~~~~~~~~~~~

The same numbers in two different CRSes are two different places. Two datasets
that both report "longitude and latitude" may still disagree by tens of meters
if they use different datums. Combining data from different sources therefore
always means knowing the CRS of each source and transforming the coordinates
into one common CRS before comparing them.


How a CRS is written down
-------------------------

There are several textual ways to describe a CRS, and pyproj accepts all of
them. Understanding the three most common ones explains most of what you will
see in the examples.

Authority codes (EPSG:4326)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rather than write out the full definition of a CRS every time, organizations
maintain registries of predefined CRSes where each entry has a short numeric
code. The most widely used registry is the :term:`EPSG` dataset, and an
:term:`authority code` such as ``EPSG:4326`` simply means "entry 4326 in the
EPSG registry", which happens to be WGS 84 longitude/latitude. PROJ ships a
copy of this registry as a database, so codes work without a network
connection.

EPSG is not the only authority. PROJ also knows codes from ``ESRI``, ``IGNF``,
``OGC``, and a few others; :func:`pyproj.database.get_authorities` lists them.
In pyproj you can pass a code as an integer (``4326``, assumed to be EPSG), a
string (``"EPSG:4326"``), or a tuple (``("EPSG", "4326")``).

To find the code for a CRS you can search the PROJ database from Python with
:func:`pyproj.database.query_crs_info` or, for UTM zones,
:func:`pyproj.database.query_utm_crs_info`, or browse online at
`epsg.org <https://epsg.org/>`__ or `epsg.io <https://epsg.io/>`__.
An authority code is the recommended way to identify a CRS when one exists
for it, because it is short, unambiguous, and cannot lose information.

Well-Known Text (WKT)
~~~~~~~~~~~~~~~~~~~~~

:term:`Well-Known Text (WKT)` is a standard, human-readable format that spells
out the complete definition of a CRS: its name, datum, ellipsoid, axes,
units, projection parameters, and authority identifiers. It is what
``print(crs.to_wkt(pretty=True))`` shows you and what most geospatial file
formats and databases store internally. WKT can describe any CRS, including
ones that have no authority code, without losing information. There are two
generations of the format; WKT2 is the current one and is preferred.

PROJ strings (+proj=latlon)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A :term:`PROJ string` is PROJ's own compact ``+key=value`` syntax, for example
``+proj=utm +zone=17 +datum=NAD83`` or ``+proj=latlon``. The ``+proj`` key
names the projection and the remaining keys set its parameters; the available
keys for each projection are documented on the PROJ page for that projection
in :ref:`proj:projections`. ``+proj=latlon`` (an alias of ``+proj=longlat``) is the
special case of "no projection, just longitude and latitude", so
``+proj=latlon`` and ``EPSG:4326`` describe a very similar CRS.

PROJ strings are convenient for building a CRS by hand, and much of the older
documentation and code you will find online uses them. However, they cannot
express everything a CRS can contain, so converting a CRS to a PROJ string may
silently drop information. Prefer an authority code or WKT for storing or
sharing a CRS; see :ref:`gotchas` and the PROJ :ref:`FAQ <proj:faq>` for details.

Other forms
~~~~~~~~~~~

pyproj also accepts PROJ JSON (a JSON equivalent of WKT), Python dictionaries
of PROJ parameters, and objects from other libraries that have a ``to_wkt()``
method. :meth:`pyproj.crs.CRS.from_user_input` lists everything that is
accepted, and :ref:`examples` shows each form in use.


Transformations between CRSes
-----------------------------

A :term:`coordinate operation` takes coordinates expressed in one CRS and
produces the coordinates of the same physical points in another CRS. In
everyday use any such operation is called a "transformation", and that is the
sense in which pyproj's :class:`pyproj.transformer.Transformer` class is
named. PROJ (following the ISO 19111 standard) reserves the word for one of
two more specific kinds of operation:

- A :term:`conversion` is pure mathematics with an exact answer, such as
  turning longitude/latitude into UTM meters on the same datum.
- A :term:`transformation` changes datum, for example from NAD27 to WGS 84.
  Because the relationship between two datums is measured rather than defined,
  transformations are approximate, have an associated accuracy, and the most
  accurate ones often rely on :term:`transformation grid` files that are
  downloaded separately (see :ref:`transformation_grids`).

Going between two arbitrary CRSes often involves both kinds, chained
together. When you call ``Transformer.from_crs(source_crs, target_crs)``
pyproj asks PROJ to find the best available chain of operations between the
two CRSes for your area of interest and wraps it in a single
:class:`pyproj.transformer.Transformer`; the transformer's ``repr`` tells you
which kind it ended up with (``Conversion Transformer`` or
``Transformation Transformer``). The PROJ page on
:doc:`geodetic transformation <proj:usage/transformation>` explains what
happens underneath.

Axis order
~~~~~~~~~~

One surprise for newcomers is :term:`axis order`. Many CRS definitions,
including ``EPSG:4326``, officially list latitude *first* and longitude
second, while most software and file formats assume longitude/latitude (x/y).
pyproj follows the official definition by default, so
``transformer.transform(lat, lon)`` is correct for ``EPSG:4326`` input. If you
prefer to always work in x/y (longitude/latitude) order, create the
transformer with ``always_xy=True``. The :ref:`gotchas` page has more on this.


Geodesic calculations
---------------------

Sometimes you do not want a projection at all; you want the distance between
two points or the area of a polygon *on the curved surface of the Earth*.
These are :term:`geodesic` calculations and pyproj provides them through
:class:`pyproj.Geod`, which only needs to know the ellipsoid (for example
WGS 84). See PROJ's :doc:`geodesic calculations <proj:geodesic>` page for the
background.


Further reading
---------------

- PROJ's own :ref:`quick start <proj:quickstart>` and
  :ref:`cartographic projection <proj:projections_intro>` pages.
- The PROJ :doc:`glossary <proj:glossary>` and :ref:`FAQ <proj:faq>`.
