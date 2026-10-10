.. _glossary:

Glossary
========

Short definitions of terms used throughout the pyproj documentation. For a
longer, narrative introduction see :ref:`concepts`. The PROJ project also
maintains its own :doc:`glossary <proj:glossary>`.

.. glossary::
   :sorted:

   Area of use
      The geographic region a :term:`Coordinate Reference System (CRS)` or
      :term:`coordinate operation` is intended for. Outside of it the
      projection may be badly distorted or the transformation inaccurate.
      Available as :attr:`pyproj.crs.CRS.area_of_use`.

   Authority code
      A short identifier for a predefined CRS, datum, ellipsoid, or operation
      in a registry, written as ``AUTHORITY:CODE``, for example ``EPSG:4326``
      or ``ESRI:54009``. The most common authority is :term:`EPSG`.
      :func:`pyproj.database.get_authorities` lists the authorities known to
      PROJ.

   Axis order
      The order in which a CRS lists its coordinates. Many geographic CRSes,
      including ``EPSG:4326``, define latitude first and longitude second,
      whereas many software packages assume x/y (longitude/latitude). Check
      :attr:`pyproj.crs.CRS.axis_info` or use ``always_xy=True`` when
      creating a :class:`pyproj.transformer.Transformer`. See also the
      :ref:`gotchas` page.

   Bound CRS
      A CRS bundled with an explicit :term:`transformation` to a target CRS
      (usually WGS 84), for example a PROJ string containing ``+towgs84=``.
      Represented by :class:`pyproj.crs.BoundCRS`.

   Compound CRS
      A CRS made of a horizontal CRS plus a :term:`vertical CRS`, so that
      coordinates carry a height as well as a position. Represented by
      :class:`pyproj.crs.CompoundCRS`.

   Conversion
      In the strict sense used by PROJ and the ISO 19111 standard, a
      :term:`coordinate operation` defined purely by mathematics, with no
      change of :term:`datum`, such as applying a map :term:`projection`.
      Conversions are exact. Compare with :term:`transformation`.

   Coordinate operation
      Any process that takes coordinates in one CRS and produces coordinates
      in another. Either a :term:`conversion` or a :term:`transformation`, or
      a chain of both. Represented in pyproj by
      :class:`pyproj.transformer.Transformer`.

   Coordinate Reference System (CRS)
      The full description needed to tie coordinates to positions on the
      Earth: a :term:`datum`, a coordinate system (axes, units, and
      :term:`axis order`), and for a :term:`projected CRS` a
      :term:`projection`. Represented by :class:`pyproj.crs.CRS`.

   Datum
      A model of the Earth's shape (an :term:`ellipsoid`) together with how
      that model is positioned and oriented relative to the real Earth. Two
      CRSes with different datums can report different coordinates for the
      same physical location. Available as :attr:`pyproj.crs.CRS.datum`.

   Ellipsoid
      The slightly flattened sphere used to approximate the Earth's shape,
      defined by a semi-major axis and a flattening. Examples: WGS 84,
      GRS 1980, Clarke 1866. Available as :attr:`pyproj.crs.CRS.ellipsoid`.

   EPSG
      The most widely used registry of CRS, datum, ellipsoid, and coordinate
      operation definitions, originally created by the European Petroleum
      Survey Group and now maintained by the International Association of Oil
      & Gas Producers (IOGP) at `epsg.org <https://epsg.org/>`__. PROJ ships
      a copy of it as its database, so ``EPSG:4326`` style
      :term:`authority codes <Authority code>` work offline.

   Geodesic
      The shortest path between two points on the surface of an
      :term:`ellipsoid`. Geodesic calculations give distances, azimuths, and
      areas on the curved Earth without using a projection. Provided by
      :class:`pyproj.Geod`.

   Geographic CRS
      A CRS whose coordinates are angles on the :term:`ellipsoid`, i.e.
      longitude and latitude, usually in degrees. Example: WGS 84
      (``EPSG:4326``). Represented by :class:`pyproj.crs.GeographicCRS`.

   OGC
      The Open Geospatial Consortium, the standards body that (jointly with
      ISO) publishes the specifications PROJ implements, including
      :term:`Well-Known Text (WKT)` and the ``urn:ogc:def:...`` :term:`URN`
      scheme for identifying CRSes.

   Prime meridian
      The line of zero longitude for a CRS. Almost always Greenwich, but some
      historical CRSes use others (Paris, Ferro, ...).

   PROJ
      The C/C++ library (https://proj.org) that pyproj wraps. PROJ implements
      the projections and transformations and ships the CRS database.

   PROJ string
      PROJ's compact ``+key=value`` syntax for describing a CRS or a
      pipeline, for example ``+proj=utm +zone=17 +datum=NAD83`` or
      ``+proj=latlon``. Convenient, but it cannot express everything in a
      CRS, so prefer an :term:`authority code` or :term:`Well-Known Text (WKT)`
      for storing a CRS. See :ref:`gotchas`.

   Projected CRS
      A CRS in which a map :term:`projection` has been applied to a
      :term:`geographic CRS`, so that coordinates are distances (usually
      meters) on a plane. Examples: :term:`UTM` zones, Web Mercator
      (``EPSG:3857``). Represented by :class:`pyproj.crs.ProjectedCRS`.

   Projection
      The mathematical recipe for flattening the curved surface of the Earth
      onto a plane, such as Transverse Mercator or Lambert Conformal Conic.
      Every projection distorts some combination of shape, area, distance, or
      direction. PROJ lists all supported projections in :ref:`proj:projections`.

   Transformation
      In everyday use, and in the names of :class:`pyproj.transformer.Transformer`
      and its ``transform`` method, any :term:`coordinate operation` from one
      CRS to another. In the stricter sense used by PROJ and the ISO 19111
      standard, only an operation between two different :term:`datums
      <Datum>`; because such an operation is based on measurements rather
      than pure mathematics it is approximate and has an accuracy, and the
      most accurate ones often need a :term:`transformation grid`. Compare
      with :term:`conversion`.

   Transformation grid
      A data file of measured corrections that PROJ uses to make some
      :term:`transformations <Transformation>` more accurate. Grids are not
      bundled with pyproj wheels; see :ref:`transformation_grids`.

   URN
      Uniform Resource Name: a standard syntax for persistent identifiers.
      The :term:`OGC` defines a URN form of :term:`authority codes <Authority
      code>`, for example ``urn:ogc:def:crs:EPSG::4326`` is the same CRS as
      ``EPSG:4326``, and several codes can be combined into a
      :term:`compound CRS` with ``urn:ogc:def:crs,crs:EPSG::2393,crs:EPSG::5717``.
      :class:`pyproj.crs.CRS` accepts both forms.

   UTM
      Universal Transverse Mercator: a projection system that divides the
      Earth into 60 longitude zones, each 6° wide, with a northern and
      southern hemisphere variant of each zone. Each zone/hemisphere/datum
      combination is a separate :term:`projected CRS <Projected CRS>` with
      coordinates in meters, for example ``EPSG:26917`` (NAD83 / UTM zone
      17N) and ``EPSG:32617`` (WGS 84 / UTM zone 17N). Use
      :func:`pyproj.database.query_utm_crs_info` to find the zone for a
      location.

   Vertical CRS
      A CRS describing heights only, for example height above a particular
      sea-level model. Usually combined with a horizontal CRS in a
      :term:`compound CRS`. Represented by :class:`pyproj.crs.VerticalCRS`.

   Well-Known Text (WKT)
      A standard text format that spells out the complete definition of a
      CRS (datum, ellipsoid, axes, units, projection parameters, identifiers).
      Lossless, and the preferred way to store a CRS that has no
      :term:`authority code`. Two versions exist; WKT2 is current and
      preferred. Produced by :meth:`pyproj.crs.CRS.to_wkt`.

   WGS 84
      World Geodetic System 1984, the :term:`datum` (and :term:`ellipsoid`)
      used by GPS and most web mapping. As a :term:`geographic CRS` it is
      ``EPSG:4326``.
