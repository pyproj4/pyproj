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


Transforming with the same projections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pyproj skips `noop` transformations.


Transformation Group
--------------------

.. versionadded:: 2.3.0

The :class:`pyproj.transformer.TransformerGroup` provides both available
transformations as well as missing transformations.

1. Helpful if you want to use an alternate transformation and have a good reason for it.

.. code-block:: python

    >>> from pyproj.transformer import TransformerGroup
    >>> trans_group = TransformerGroup("EPSG:4326","EPSG:2964")
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
    >>> tg = TransformerGroup("EPSG:4326", "+proj=aea +lat_0=50 +lon_0=-154 +lat_1=55 +lat_2=65 +x_0=0 +y_0=0 +datum=NAD27 +no_defs +type=crs +units=m", always_xy=True)
    UserWarning: Best transformation is not available due to missing Grid(short_name=ntv2_0.gsb, full_name=, package_name=proj-datumgrid-north-america, url=https://download.osgeo.org/proj/proj-datumgrid-north-america-latest.zip, direct_download=True, open_license=True, available=False)
    f"{operation.grids[0]!r}"
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
    >>> transformer = Transformer.from_crs("EPSG:4326", "EPSG:2694")
    >>> transformer
    <Concatenated Operation Transformer: pipeline>
    Description: Inverse of Pulkovo 1995 to WGS 84 (2) + 3-degree Gauss-Kruger zone 60
    Area of Use:
    - name: Russia
    - bounds: (18.92, 39.87, -168.97, 85.2)
    >>> transformer = Transformer.from_crs(
    ...     "EPSG:4326",
    ...     "EPSG:2694",
    ...     area_of_interest=AreaOfInterest(-136.46, 49.0, -60.72, 83.17),
    ... )
    >>> transformer
    <Concatenated Operation Transformer: pipeline>
    Description: Inverse of NAD27 to WGS 84 (13) + Alaska Albers
    Area of Use:
    - name: Canada - NWT; Nunavut; Saskatchewan
    - bounds: (-136.46, 49.0, -60.72, 83.17)


Promote CRS to 3D
-------------------

.. versionadded:: 3.1


In PROJ 6+ you need to explicitly change your CRS to 3D if you have
2D CRS and you want the ellipsoidal height taken into account.


.. code-block:: python

    >>> from pyproj import CRS, Transformer
    >>> transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    >>> transformer.transform(8.37909, 47.01987, 1000)
    (2671499.8913080636, 1208075.1135782297, 1000.0)
    >>> transformer_3d = Transformer.from_crs(
    ...     CRS("EPSG:4326").to_3d(),
    ...     CRS("EPSG:2056").to_3d(),
    ...     always_xy=True,
    ...)
    >>> transformer_3d.transform(8.37909, 47.01987, 1000)
    (2671499.8913080636, 1208075.1135782297, 951.4265527743846)

Projected CRS Bounds
----------------------

.. versionadded:: 3.1

The boundary of the CRS is given in geographic coordinates.
This is the recommended method for calculating the projected bounds.

.. code-block:: python

    >>> from pyproj import CRS, Transformer
    >>> crs = CRS("EPSG:3857")
    >>> transformer = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    >>> transformer.transform_bounds(*crs.area_of_use.bounds)
    (-20037508.342789244, -20048966.104014594, 20037508.342789244, 20048966.104014594)


Multithreading
--------------

As of version 3.1, these objects are thread-safe:

- :class:`pyproj.crs.CRS`
- :class:`pyproj.transformer.Transformer`

If you have pyproj<3.1, you will need to create create the object
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


Optimizing Single-Threaded Applications
----------------------------------------

If you have a single-threaded application that generates many objects,
enabling the use of the global context can provide performance enhancements.

For information about using the global context, see: :ref:`global_context`

Here is an example where enabling the global context can help:

.. code-block:: python

    import pyproj

    codes = pyproj.get_codes("EPSG", pyproj.enums.PJType.PROJECTED_CRS, False)
    crs_list = [pyproj.CRS.from_epsg(code) for code in codes]


Caching pyproj objects
-----------------------

If you are likely to re-create pyproj objects such as :class:`pyproj.transformer.Transformer`
or :class:`pyproj.crs.CRS`, using a cache can help reduce the cost
of re-creating the objects.

Transformer
~~~~~~~~~~~~

.. code-block:: python

    from functools import lru_cache

    from pyproj import Transformer

    TransformerFromCRS = lru_cache(Transformer.from_crs)

    Transformer.from_crs(2263, 4326)  # no cache
    TransformerFromCRS(2263, 4326)  # cache


Try it:

.. code-block:: python

    from timeit import timeit

    timeit(
        "CachedTransformer(2263, 4326)",
        setup=(
            "from pyproj import Transformer; "
            "from functools import lru_cache; "
            "CachedTransformer = lru_cache(Transformer.from_crs)"
        ),
        number=1000000,
    )

    timeit(
        "Transformer.from_crs(2263, 4326)",
        setup=("from pyproj import Transformer"),
        number=100,
    )


Without the cache, it takes around 2 seconds to do 100 iterations. With the cache,
it takes 0.1 seconds to do 1 million iterations.


CRS Example
~~~~~~~~~~~~

.. code-block:: python


    from functools import lru_cache

    from pyproj import CRS

    CachedCRS = lru_cache(CRS)

    crs = CRS(4326)  # no cache
    crs = CachedCRS(4326)  # cache


Try it:

.. code-block:: python

    from timeit import timeit

    timeit(
        "CachedCRS(4326)",
        setup=(
            "from pyproj import CRS; "
            "from functools import lru_cache; "
            "CachedCRS = lru_cache(CRS)"
        ),
        number=1000000,
    )

    timeit(
        "CRS(4326)",
        setup=("from pyproj import CRS"),
        number=1000,
    )


Without the cache, it takes around 1 seconds to do 1000 iterations. With the cache,
it takes 0.1 seconds to do 1 million iterations.


.. _debugging-internal-proj:

Debugging Internal PROJ
------------------------

.. versionadded:: 3.0.0

To get more debugging information from the internal PROJ code:

1. Set the :envvar:`PROJ_DEBUG`
   environment variable to the desired level.

2. Activate logging in `pyproj` with the devel `DEBUG`:

    More information available here: https://docs.python.org/3/howto/logging.html

    Here are examples to get started.

    Add handler to the `pyproj` logger:

    .. code-block:: python

        import logging

        console_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s:%(message)s")
        console_handler.setFormatter(formatter)
        logger = logging.getLogger("pyproj")
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)


    Activate default logging config:

    .. code-block:: python

        import logging

        logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
