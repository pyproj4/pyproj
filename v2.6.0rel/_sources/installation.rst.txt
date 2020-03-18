.. highlight:: shell

============
Installation
============

The easiest methods for installing pyproj are:

1. Use pip to install the binary wheels on `PyPI <https://pypi.org/project/pyproj/>`__:

  .. code-block:: bash

      pip install pyproj

  .. note:: pip>=19.0 is required to install manylinux2010 wheels

  - The MacOS and Linux wheels are powered by `multibuild by Matthew Brett <https://github.com/matthew-brett/multibuild>`__
  - The Windows wheels are built by `Christoph Gohlke <https://www.lfd.uci.edu/~gohlke/pythonlibs/>`__


2. Use `conda <https://conda.io/en/latest/>`__ with the `conda-forge <https://conda-forge.org/>`__ channel:

  .. code-block:: bash

      conda install -c conda-forge pyproj

  - `pypoj` is maintaned by the `pyproj-feedtstock maintainers <http://github.com/conda-forge/pyproj-feedstock>`__
  - `PROJ` is maintaned by the `proj.4-feedtstock maintainers <http://github.com/conda-forge/proj.4-feedstock>`__

If these installation methods do not meet your needs, the section below provides further instructions
for getting setup.


Datum Grids
===========

You can add datum grids to your PROJ data directory for better accuracy for some transformations.

Available methods for download include:

1. Download stable from https://download.osgeo.org/proj or latest from https://github.com/OSGeo/proj-datumgrid

2. Use `conda <https://conda.io/en/latest/>`__ with the `conda-forge <https://conda-forge.org/>`__ channel:

  .. code-block:: bash

     conda install -c conda-forge proj-datumgrid-europe proj-datumgrid-north-america proj-datumgrid-oceania proj-datumgrid-world



Installing from source
======================

Setup PROJ
------------

Version compatibility matrix:

============   ============
pyproj         PROJ
============   ============
<= 1.9.6       <= 5.2
2.0-2.1        6.0+
2.2-2.3        6.1+
2.4+           6.2+
============   ============

PROJ is required when building from source.
You can download PROJ from https://download.osgeo.org/proj
or from https://github.com/OSGeo/PROJ.
Installation instructions can be fount at https://proj.org/.

In the setup.py, the order for searching for PROJ is:

    1. The PROJ_DIR environment variable
    2. The internal PROJ directory (pyproj/proj_dir)
    3. The `proj` executable in sys.prefix
    4. The `proj` executable on the PATH.

For best results, set the PROJ_DIR environment variable to
point to location of PROJ installation before running setup.py.

Examples of how to set the PROJ_DIR environment variable:

Windows::

    set PROJ_DIR=C:\OSGeo4W\

Linux::

    export PROJ_DIR=/usr/local

If you have a previous version of PROJ installed alongside the current
version of PROJ, the best way to avoid conflicts is to:

    1. Remove the previous PROJ from PATH & unset old PROJ_LIB environment variable (temporarily)
    2. Install PROJ to the internal PROJ directory (pyproj/proj_dir)
    3. Set the environment variable PROJ_DIR to point to the internal PROJ directory
    4. Set the environment variable PROJ_WHEEL=true
    5. Build pyproj

Setup pyproj
------------

The data directory
~~~~~~~~~~~~~~~~~~

The order of preference for the data directory is:

1. The one set by pyproj.datadir.set_data_dir (if exists & valid)
2. The internal proj directory (if exists & valid)
3. The directory in PROJ_LIB (if exists & valid)
4. The directory on sys.prefix (if exists & valid)
5. The directory on the PATH (if exists & valid)


Install pyproj
~~~~~~~~~~~~~~

.. note:: `Cython <http://cython.org/>`_ or pip>=10.0.1 is required for the installation.

.. note:: You may need to run pip with administrative privileges (e.g. `sudo pip`) or
          perform a user only installation (e.g. `pip install --user`).


From pypi:
^^^^^^^^^^

.. code-block:: bash

    pip install pyproj --no-binary pyproj


From GitHub with `pip`:
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install git+https://github.com/pyproj4/pyproj.git

From cloned GitHub repo for development:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install -e .
