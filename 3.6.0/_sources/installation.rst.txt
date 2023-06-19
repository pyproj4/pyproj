.. highlight:: shell

============
Installation
============

The easiest methods for installing pyproj are:

1. Use pip to install the binary wheels on `PyPI <https://pypi.org/project/pyproj/>`__:

  .. code-block:: bash

      pip install pyproj

  .. note:: Linux (manylinux2014) wheels require pip 19.3+

  .. note:: pyproj 3+ wheels do not include transformation grids.
            For migration assistance see: :ref:`transformation_grids`


  - The MacOS and Linux wheels are powered by
    `cibuildwheel <https://github.com/pypa/cibuildwheel>`__
    & `multibuild <https://github.com/multi-build/multibuild>`__
  - The Windows wheels versions <= 3.3.x were built by `Christoph Gohlke <https://www.lfd.uci.edu/~gohlke/pythonlibs/>`__


2. Use `conda <https://conda.io/en/latest/>`__ with the `conda-forge <https://conda-forge.org/>`__ channel:

  .. code-block:: bash

      conda config --prepend channels conda-forge
      conda config --set channel_priority strict
      conda create -n pyproj_env pyproj
      conda activate pyproj_env

  .. note::
      "... we recommend always installing your packages inside a
      new environment instead of the base environment from
      anaconda/miniconda. Using envs make it easier to
      debug problems with packages and ensure the stability
      of your root env."
      -- https://conda-forge.org/docs/user/tipsandtricks.html

  .. warning::
      Avoid using `pip install` with a conda environment. If you encounter
      a python package that isn't in conda-forge, consider submitting a
      recipe: https://github.com/conda-forge/staged-recipes/


  - `pyproj` is maintained by the `pyproj-feedstock maintainers <http://github.com/conda-forge/pyproj-feedstock>`__
  - `PROJ` is maintained by the `proj.4-feedstock maintainers <http://github.com/conda-forge/proj.4-feedstock>`__

If these installation methods do not meet your needs, the section below provides further instructions
for getting setup.

Transformation Grids
=====================

See: :ref:`transformation_grids`


Installing from source
======================

Version compatibility matrix:

============   ============
pyproj         PROJ
============   ============
<= 1.9.6       <= 5.2
2.0-2.1        6.0-7
2.2-2.3        6.1-7
2.4-2.6        6.2-7
3.0.0          7.2
3.0.1-3.2      7.2-9.1
3.3            8.0-9.1
3.4+           8.2+
3.5+           9+
============   ============

Setup PROJ
------------

PROJ is required when building from source.

:ref:`PROJ Installation Instructions <install>`

You can also download PROJ from:

-  https://download.osgeo.org/proj
-  https://github.com/OSGeo/PROJ


pyproj Build Environment Variables
-----------------------------------

.. envvar:: PROJ_VERSION

    .. versionadded:: 3.0

    This sets the version of PROJ when building pyproj. This
    enables installing pyproj when the PROJ executables are not
    present but the header files exist.

.. envvar:: PROJ_DIR

    This is the path to the base directory for PROJ.
    Examples of how to set the PROJ_DIR environment variable:

    Windows::

        set PROJ_DIR=C:\OSGeo4W\

    Linux::

        export PROJ_DIR=/usr/local

.. envvar:: PROJ_LIBDIR

    This is the path to the directory containing the PROJ libraries.
    If not set, it searches the `lib` and `lib64` directories inside
    the PROJ directory.

.. envvar:: PROJ_INCDIR

    This is the path to the PROJ include directory. If not set, it assumes
    it is the `includes` directory inside the PROJ directory.

.. envvar:: PROJ_WHEEL

    This is a boolean value used when building a wheel. When true
    it includes the contents of the `pyproj/proj_dir/proj/share`
    directory if present.

.. envvar:: PYPROJ_FULL_COVERAGE

    Boolean that sets the compiler directive for cython to include
    the test coverage.


Setup pyproj
------------

In the setup.py, the order for searching for PROJ is:

    1. The :envvar:`PROJ_DIR` environment variable
    2. The internal PROJ directory (pyproj/proj_dir)
    3. The `proj` executable in sys.prefix
    4. The `proj` executable on the PATH

For best results, set the :envvar:`PROJ_DIR` environment variable to
point to location of PROJ installation before running setup.py.

If you have a previous version of PROJ installed alongside the current
version of PROJ, the best way to avoid conflicts is to:

    1. Remove the previous PROJ from `PATH` & unset the `PROJ_DATA`` (PROJ 9.1+) | `PROJ_LIB` (PROJ<9.1) environment variables (temporarily)
    2. Install PROJ to the internal PROJ directory (pyproj/proj_dir)
    3. Set the environment variable :envvar:`PROJ_DIR` to point to the internal PROJ directory
    4. Set the environment variable :envvar:`PROJ_WHEEL` to true
    5. Build pyproj


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
