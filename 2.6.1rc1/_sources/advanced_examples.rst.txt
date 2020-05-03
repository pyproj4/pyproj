.. _advanced_examples:

Advanced Examples
=================

Optimize Transformations
------------------------

Here are a few tricks to try out if you want to optimize your transformations.


Repeated transformations
~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2.1.0

If you use the same transform, using the :class:`pyproj.transformer.Transformer` can help
optimize your transformations.

.. code-block:: python

    import numpy as np
    from pyproj import Transformer, transform

    transformer = Transformer.from_crs(2263, 4326)
    x_coords = np.random.randint(80000, 120000)
    y_coords = np.random.randint(200000, 250000)


Example with :func:`pyproj.transformer.transform`:

.. code-block:: python

   transform(2263, 4326, x_coords, y_coords)

Results: 160 ms ± 3.68 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

Example with :class:`pyproj.transformer.Transformer`:

.. code-block:: python

   transformer.transform(x_coords, y_coords)

Results: 6.32 µs ± 49.7 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)


Tranforming with the same projections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pyproj will skip transformations if they are exacly the same by default. However, if you
sometimes throw in the projections that are about the same and the results being close enough
is what you want, the `skip_equivalent` option can help.

.. note:: From PROJ code: The objects are equivalent for the purpose of coordinate operations.
    They can differ by the name of their objects, identifiers, other metadata.
    Parameters may be expressed in different units, provided that the value is
    (with some tolerance) the same once expressed in a common unit.

Transformation Group
--------------------

.. versionadded:: 2.3.0

The :class:`pyproj.transformer.TransformerGroup` provides both available
transformations as well as missing transformations.

1. Helpful if you want to use an alternate transformation and have a good reason for it.

.. code-block:: python

    >>> from pyproj.transformer import TransformerGroup
    >>> trans_group = TransformerGroup("epsg:4326","epsg:2964")
    >>> trans_group
    <TransformerGroup: best_available=True>
    - transformers: 8
    - unavailable_operations: 1
    >>> trans_group.best_available
    True
    >>> trans_group.transformers[0].transform(66, -153)
    (149661.2825058747, 5849322.174897663)
    >>> trans_group.transformers[1].transform(66, -153)
    (149672.928811047, 5849311.372139239)
    >>> trans_group.transformers[2].transform(66, -153)
    (149748.32734832275, 5849274.621409136)


2. Helpful if want to check that the best possible transformation exists.
   And if not, how to get the missing grid.


.. code-block:: python

    >>> from pyproj.transformer import TransformerGroup
    >>> tg = TransformerGroup("epsg:4326", "+proj=aea +lat_0=50 +lon_0=-154 +lat_1=55 +lat_2=65 +x_0=0 +y_0=0 +datum=NAD27 +no_defs +type=crs +units=m", always_xy=True)
    UserWarning: Best transformation is not available due to missing Grid(short_name=ntv2_0.gsb, full_name=, package_name=proj-datumgrid-north-america, url=https://download.osgeo.org/proj/proj-datumgrid-north-america-latest.zip, direct_download=True, open_license=True, available=False)
    "{!r}".format(operation.grids[0])
    >>> tg
    <TransformerGroup: best_available=False>
    - transformers: 37
    - unavailable_operations: 41
    >>> tg.transformers[0].description
    'axis order change (2D) + Inverse of NAD27 to WGS 84 (3) + axis order change (2D) + unknown'
    >>> tg.unavailable_operations[0].name
    'Inverse of NAD27 to WGS 84 (33) + axis order change (2D) + unknown'
    >>> tg.unavailable_operations[0].grids[0].url
    'https://download.osgeo.org/proj/proj-datumgrid-north-america-latest.zip'


Area of Interest
----------------

.. versionadded:: 2.3.0

Depending on the location of your transformation, using the area of interest may impact
which transformation operation is selected in the transformation.

.. code-block:: python

    >>> from pyproj.transformer import Transformer, AreaOfInterest
    >>> transformer = Transformer.from_crs("epsg:4326", "epsg:2694")
    >>> transformer
    <Concatenated Operation Transformer: pipeline>
    Description: Inverse of Pulkovo 1995 to WGS 84 (2) + 3-degree Gauss-Kruger zone 60
    Area of Use:
    - name: Russia
    - bounds: (18.92, 39.87, -168.97, 85.2)
    >>> transformer = Transformer.from_crs(
    ...     "epsg:4326",
    ...     "epsg:2694",
    ...     area_of_interest=AreaOfInterest(-136.46, 49.0, -60.72, 83.17),
    ... )
    >>> transformer
    <Concatenated Operation Transformer: pipeline>
    Description: Inverse of NAD27 to WGS 84 (13) + Alaska Albers
    Area of Use:
    - name: Canada - NWT; Nunavut; Saskatchewan
    - bounds: (-136.46, 49.0, -60.72, 83.17)


Multithreading
--------------

The :class:`pyproj.transformer.Transformer` and :class:`pyproj.crs.CRS`
classes each have their own PROJ context. However, contexts cannot be
shared across threads. As such, it is recommended to create the object
within the thread that uses it.

Here is a simple demonstration:

.. code-block:: python

    import concurrent.futures

    from pyproj import Transformer


    def transform_point(point):
        transformer = Transformer.from_crs(4326, 3857)
        return transformer.transform(point, point * 2)


    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(transform_point, range(5)):
            print(result)
