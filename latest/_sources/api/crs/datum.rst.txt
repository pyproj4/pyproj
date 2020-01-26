.. _datum:

Datum
=====


.. note:: PROJ >= 7.0.0 will have better support for aliases for datum names.
          Until then, you will need to use the full name of the datum. There is support
          currently for the old PROJ names for datums such as WGS84 and NAD83.


Datum
---------

.. autoclass:: pyproj.crs.Datum
    :members:
    :inherited-members:


CustomDatum
------------

.. autoclass:: pyproj.crs.datum.CustomDatum
    :members:
    :show-inheritance:
    :special-members: __new__


Ellipsoid
---------

- :class:`pyproj.crs.Ellipsoid`
- :class:`pyproj.crs.ellipsoid.CustomEllipsoid`


Prime Meridian
--------------

.. autoclass:: pyproj.crs.PrimeMeridian
    :members:
    :inherited-members:

