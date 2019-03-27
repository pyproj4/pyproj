Transformer
===========

.. warning:: The axis order may be swapped if the source and destination
    CRS's are defined as having the first coordinate component point in a
    northerly direction. A general rule of thumb is that a CRS in geographic
    coordinates has an axis ordering of (latitude, longitude) where as most
    projected CRS's has axis on ordering of (easting, northing). You can check
    the axis order with the `pyproj.CRS` class.
    See `issue #225 <https://github.com/pyproj4/pyproj/issues/225>`_.



pyproj.Transformer
------------------

.. autoclass:: pyproj.transformer.Transformer
    :members:

pyproj.transform
----------------

.. autofunction:: pyproj.transformer.transform


pyproj.itransform
-----------------

.. autofunction:: pyproj.transformer.itransform