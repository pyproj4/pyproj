.. highlight:: shell

============
Installation
============

The easiest methods for installing pyproj are:

1. Use the wheels on pypi or from https://www.lfd.uci.edu/~gohlke/pythonlibs/

  .. code-block:: bash
    
      pip install pyproj

2. Use conda:

  .. code-block:: bash

      conda install -c conda-forge pyproj

If that does not meet your needs, the section below provides further instructions
for getting setup.


Setup PROJ.4
------------

PROJ.4 6.0.0 is required when building from source.
You can download PROJ.4 from https://download.osgeo.org/proj
or from https://github.com/OSGeo/proj.4. 
Installation instructions can be fount at https://proj4.org/.

In the setup.py, the order for searching for PROJ.4 is:

    1. The PROJ_DIR environment variable
    2. The internal PROJ.4 directory (pyproj/proj_dir)
    3. The `proj` executable on the PATH.

For best results, set the PROJ_DIR environment variable to 
point to location of PROJ.4 installation before running setup.py.

Examples of how to set the PROJ_DIR environment variable:

Windows::
    
    set PROJ_DIR=C:\OSGeo4W\

Linux::

    export PROJ_DIR=/usr/local

If you have a previous version of PROJ.4 installed alongside the current
version of PROJ.4 (6.0.0), the best way to avoid conflicts is to:

    1. Remove the previous PROJ.4 from PATH & unset old PROJ_LIB environment variable (temporarily)
    2. Install PROJ.4 to the internal PROJ.4 directory (pyproj/proj_dir)
    3. Set the environment variable PROJ_DIR to point to the internal PROJ.4 directory
    4. Set the environment variable PROJ_WHEEL=true
    5. Build pyproj

Setup pyproj
------------

The data directory
~~~~~~~~~~~~~~~~~~

The order of preference for the data directory is:

1. The one set by pyproj.datadir.set_data_dir (if exists & valid)
2. The internal proj directory (if exists & valid)
3. The directory in the PROJ_LIB environment variable (if exists & valid)

Install pyproj
~~~~~~~~~~~~~~

.. note:: `Cython <http://cython.org/>`_ or pip>=10.0.1 is required for the installation.

.. note:: You may need to run pip with administrative privileges (e.g. `sudo pip`) or
          perform a user only installation (e.g. `pip install --user`).


From pypi:
^^^^^^^^^^

.. code-block:: bash
    
    pip install pyproj --no-binary


From GitHub with `pip`:
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install git+https://github.com/pyproj4/pyproj.git

From cloned GitHub repo for development:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install -e .
