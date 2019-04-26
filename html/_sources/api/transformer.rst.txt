Transformer
===========

.. warning:: The axis order may be swapped if the source and destination
    CRS's are defined as having the first coordinate component point in a
    northerly direction (See PROJ FAQ on 
    `axis order <https://proj4.org/faq.html#why-is-the-axis-ordering-in-proj-not-consistent>`_).
    You can check the axis order with the `pyproj.CRS` class.


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