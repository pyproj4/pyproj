.. _transformation_grids:

Transformation Grids
=====================

Transformation grids improve accuracy when you are performing datum transformations.

More information about the data available is located under the PROJ
:ref:`resource files <datumgrid>` documentation.

.. note:: `pyproj` API for managing the :ref:`data_directory` and :ref:`network_api`.

.. note:: pyproj 3 wheels do not include any transformation grids.


Downloading data
----------------

PROJ 7+
^^^^^^^^

PROJ 7.0 has introduced, per
:ref:`PROJ RFC 4: Remote access to grids and GeoTIFF grids <rfc4>`,
the capability to work with grid files that are not installed on the local machine where PROJ is executed.

Available methods for download include:

- `Mirroring the data <https://proj.org/usage/network.html#mirroring>`__:

  To download to the PROJ user-writable data directory:

  .. versionadded:: 7.1.0

  .. code-block:: bash

    export PROJ_DOWNLOAD_DIR=$(python -c "import pyproj; print(pyproj.datadir.get_user_data_dir())")

  To download to the main PROJ data directory:

  .. code-block:: bash

    export PROJ_DOWNLOAD_DIR=$(python -c "import pyproj; print(pyproj.datadir.get_data_dir())")

  Download the files with either:

  .. code-block:: bash

    aws s3 sync s3://cdn.proj.org ${PROJ_DOWNLOAD_DIR}

  or:

  .. code-block:: bash

    wget --mirror https://cdn.proj.org/ -P ${PROJ_DOWNLOAD_DIR}

- The :ref:`projsync <projsync>` command line program.

- `pyproj sync <cli.html#sync>`__ command line program (pyproj 3+; useful if you use pyproj wheels).

- Enabling :ref:`PROJ network <network>` capabilities. See also :ref:`network_api`.

- Download stable from https://download.osgeo.org/proj or latest from https://github.com/OSGeo/PROJ-data

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

- Have a machine with limited space, a great network connection, and PROJ 7+?
  Look into `PROJ network <network>`__ capabilities. See also :ref:`network_api`.

- Have a machine with limited space and want to pre-download files?

  You can enable enable :ref:`debugging-internal-proj` with pyproj 3+ and perform a transformation.
  The logs will show the grids PROJ searches for.

  Additionally, the :class:`pyproj.transformer.TransformerGroup` can assist finding the grids you need to download.

  .. warning:: There are cases where the URL to download the grid is missing.

  .. code-block:: python

    >>> from pyproj.transformer import TransformerGroup
    >>> tg = trans_group = TransformerGroup(4326, 2964)
    UserWarning: Best transformation is not available due to missing Grid(short_name=us_noaa_alaska.tif, full_name=, package_name=, url=https://cdn.proj.org/us_noaa_alaska.tif, direct_download=True, open_license=True, available=False)
    >>> tg
    <TransformerGroup: best_available=False>
    - transformers: 8
    - unavailable_operations: 2
    >>> tg.transformers[0].description
    'Inverse of NAD27 to WGS 84 (7) + Alaska Albers'
    >>> tg.unavailable_operations[0].name
    'Inverse of NAD27 to WGS 84 (85) + Alaska Albers'
    >>> tg.unavailable_operations[0].grids[0].url
    'https://cdn.proj.org/us_noaa_alaska.tif'
    >>> tg.download_grids(verbose=True)  # pyproj 3+
    Downloading: https://cdn.proj.org/us_noaa_alaska.tif
    Downloading: https://cdn.proj.org/ca_nrc_ntv2_0.tif
