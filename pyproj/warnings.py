class PyProjWarning(UserWarning):
    """
    This is a warning for pyproj
    """


class PyProjDeprecationWarning(PyProjWarning):
    """
    This is a deprecation warning for pyproj
    """


class ProjDeprecationWarning(PyProjDeprecationWarning):
    """
    This is a deprecation warning for PROJ
    """
