.. _transformer:

Transformer
===========


The `pyproj.Transformer` has the capabilities of performing 2D, 3D, and 4D (time)
transformations. It can do anything that the PROJ command line programs
`proj <https://proj.org/apps/proj.html>`__, `cs2cs <https://proj.org/apps/cs2cs.html>`__,
and `cct <https://proj.org/apps/cct.html>`__ can do.
This means that it allows translation between any pair of definable coordinate systems,
including support for datum transformation.


.. warning:: The axis order may be swapped if the source and destination
    CRS's are defined as having the first coordinate component point in a
    northerly direction (See PROJ FAQ on
    `axis order <https://proj.org/faq.html#why-is-the-axis-ordering-in-proj-not-consistent>`_).
    You can check the axis order with the :class:`pyproj.crs.CRS` class. If you prefer to
    keep your axis order as always x,y, you can use the `always_xy` option when
    creating the :class:`pyproj.transformer.Transformer`.


pyproj.Transformer
------------------

.. autoclass:: pyproj.transformer.Transformer
    :members:


pyproj.transformer.TransformerGroup
-----------------------------------

.. autoclass:: pyproj.transformer.TransformerGroup
    :members:
    :special-members: __init__


pyproj.transformer.AreaOfInterest
-----------------------------------

.. autoclass:: pyproj.transformer.AreaOfInterest
    :members:


pyproj.transform
----------------

.. autofunction:: pyproj.transformer.transform


pyproj.itransform
-----------------

.. autofunction:: pyproj.transformer.itransform
