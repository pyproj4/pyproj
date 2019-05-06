Optimize Transformations
========================

Here are a few tricks to try out if you want to optimize your transformations.


Repeated transformations
------------------------

If you use the same transform, using the :class:`pyproj.Transformer` can help
optimize your transformations.

.. code-block:: python

    import numpy as np                                                      
    from pyproj import Transformer, transform
    
    transformer = Transformer.from_proj(2263, 4326)
    x_coords = np.random.randint(80000, 120000)                            
    y_coords = np.random.randint(200000, 250000) 


Example with :func:`~pyproj.transformer.transform`:

.. code-block:: python

   transform(2263, 4326, x_coords, y_coords)                                             

Results: 160 ms ± 3.68 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

Example with :class:`~pyproj.transformer.Transformer`:

.. code-block:: python

   transformer.transform(x_coords, y_coords)                                             

Results: 6.32 µs ± 49.7 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)


Tranforming with the same projections
-------------------------------------

pyproj will skip transformations if they are exacly the same by default. However, if you
sometimes throw in the projections that are about the same and the results being close enough
is what you want, the `skip_equivalent` option can help.

.. note:: From PROJ code: The objects are equivalent for the purpose of coordinate operations.
    They can differ by the name of their objects, identifiers, other metadata.
    Parameters may be expressed in different units, provided that the value is 
    (with some tolerance) the same once expressed in a common unit.
