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
----------

.. autoclass:: pyproj.crs.Ellipsoid
    :members:
    :inherited-members:


CustomEllipsoid
----------------

.. autoclass:: pyproj.crs.datum.CustomEllipsoid
    :members:
    :show-inheritance:
    :special-members: __new__


PrimeMeridian
--------------

.. autoclass:: pyproj.crs.PrimeMeridian
    :members:
    :inherited-members:


CustomPrimeMeridian
--------------------

.. autoclass:: pyproj.crs.datum.CustomPrimeMeridian
    :members:
    :show-inheritance:
    :special-members: __new__
