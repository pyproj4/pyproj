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


Example with `pyproj.transform`:

.. code-block:: python

   transform(2263, 4326, x_coords, y_coords)                                             

Results: 160 ms ± 3.68 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

Example with :class:`pyproj.Transformer`:

.. code-block:: python

   transformer.transform(x_coords, y_coords)                                             

Results: 6.32 µs ± 49.7 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)


Tranforming with the same projections
-------------------------------------

If you sometimes throw in the same projections, `skip_equivalent` can help speed things up.

.. code-block:: python

    import numpy as np                                                      
    from pyproj import Transformer

    in_coords = np.random.randint(80000, 120000, 1000000) 

Example without `skip_equivalent`:

.. code-block:: python

   transformer = Transformer.from_proj(4326, 4326)
   transformer.transform(in_coords, in_coords)                                             

Results: 90.5 ms ± 6.46 ms per loop (mean ± std. dev. of 5 runs, 5 loops each)

Example with `skip_equivalent`:

.. code-block:: python

   transformer = Transformer.from_proj(4326, 4326, skip_equivalent=True)
   transformer.transform(in_coords, in_coords)                                             

Results: 15.9 ms ± 5.76 ms per loop (mean ± std. dev. of 5 runs, 5 loops each)
