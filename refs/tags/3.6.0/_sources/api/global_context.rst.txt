.. _global_context:

Global Context
==============

If you have a single-threaded application that generates many objects,
enabling the use of the global context can provide performance enhancements.

.. warning:: The global context is not thread safe.
.. warning:: The global context maintains a connection to the database
             through the duration of each python session and is closed
             once the program terminates.

How to enable:

- Using :func:`pyproj.set_use_global_context`.
- Using the environment variable `PYPROJ_GLOBAL_CONTEXT`.


pyproj.set_use_global_context
-----------------------------

.. autofunction:: pyproj.set_use_global_context
