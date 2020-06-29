.. _global_context:

Global Context
==============

If you have a single-threaded application that generates many objects,
enabling the use of the global context can provide performance enhancements.

.. warning:: The global context is not thread safe.
.. warning:: The global context does not autoclose the database.

How to enable:

- Using :func:`pyproj.set_use_global_context`.
- Using the environment variable `PYPROJ_GLOBAL_CONTEXT`.


pyproj.set_use_global_context
-----------------------------

.. autofunction:: pyproj.set_use_global_context


pyproj.set_global_context_network
-----------------------------------

.. autofunction:: pyproj.set_global_context_network


pyproj.is_global_context_network_enabled
------------------------------------------

.. autofunction:: pyproj.is_global_context_network_enabled
