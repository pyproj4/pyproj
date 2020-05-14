.. _transformation_grids:

Transformation Grids
=====================

Transformation grids improve accuracy when you are performing datum transformations.

More information about the data available is located under the PROJ
`resource files <https://proj.org/resource_files.html#transformation-grids>`__
documentation.

`pyproj` API for managing the :ref:`data_directory`

.. warning:: pyproj 2 includes datumgrid 1.8 in the wheels. pyproj 3 will not include any datum grids.


Downloading data
----------------

PROJ 7+
^^^^^^^^

PROJ 7.0 has introduced, per
`PROJ RFC 4: Remote access to grids and GeoTIFF grids <https://proj.org/community/rfc/rfc-4.html#rfc4>`__,
the capability to work with grid files that are not installed on the local machine where PROJ is executed.

Available methods for download include:

- `Mirroing the data <https://proj.org/usage/network.html#mirroring>`__:

  To download to PROJ user writable data directory:

  .. versionadded:: 7.1.0

  .. code-block:: bash

    export PROJ_DOWNLOAD_DIR=$(python -c "import pyproj; print(pyproj.datadir.get_user_data_dir())

  To download to the main PROJ data data directory:

  .. code-block:: bash

    export PROJ_DOWNLOAD_DIR=$(python -c "import pyproj; print(pyproj.datadir.get_data_dir())

  Download the files:

  .. code-block:: bash

    aws s3 sync s3://cdn.proj.org ${PROJ_DOWNLOAD_DIR}

  .. code-block:: bash

    wget --mirror https://cdn.proj.org/ -P ${PROJ_DOWNLOAD_DIR}

- The `projsync <https://proj.org/apps/projsync.html>`__ command line program.

- Enabling `PROJ network <https://proj.org/usage/network.html>`__ capabilities.

  .. note:: You can use the `network` kwarg when initializing
            :class:`pyproj.Proj <pyproj.proj.Proj>` or :class:`pyproj.Transformer <pyproj.transformer.Transformer>`

- Use `conda <https://conda.io/en/latest/>`__ with the `conda-forge <https://conda-forge.org/>`__ channel:

  .. code-block:: bash

     conda install -c conda-forge proj-data


PROJ <= 6
^^^^^^^^^^

Available methods for download include:

- Download stable from https://download.osgeo.org/proj or latest from https://github.com/OSGeo/proj-datumgrid

- Use `conda <https://conda.io/en/latest/>`__ with the `conda-forge <https://conda-forge.org/>`__ channel:

  .. code-block:: bash

     conda install -c conda-forge proj-datumgrid-europe proj-datumgrid-north-america proj-datumgrid-oceania proj-datumgrid-world


What grids to download?
-----------------------

- Only using the :obj:`pyproj.crs.CRS` or :obj:`pyproj.Geod` classes? Then no grids are needed.

- Have a machine that can hold and extra 500 MB - 1 GB of data? Then downloading all grids shouldn't be an issue.

- Have a machine with limited space, a great network connection, and PROJ 7+? Look into `PROJ network <https://proj.org/usage/network.html>`__ capabilities.

- Have a machine with limited space and want to pre-download files?

  The :class:`pyproj.transformer.TransformerGroup` can assist finding the grids you need to download.

  .. code-block:: python

    >>> from pyproj.transformer import TransformerGroup
    >>> tg = TransformerGroup("epsg:4326", "+proj=aea +lat_0=50 +lon_0=-154 +lat_1=55 +lat_2=65 +x_0=0 +y_0=0 +datum=NAD27 +no_defs +type=crs +units=m", always_xy=True)
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
