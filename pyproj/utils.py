"""
Utility functions used within pyproj
"""
from array import array
from typing import Any, Tuple


def _copytobuffer_return_scalar(xx: Any) -> Tuple[array, bool, bool, bool]:
    """
    Parameters
    -----------
    xx: float or 0-d numpy array
    """
    try:
        # inx,isfloat,islist,istuple
        return array("d", (float(xx),)), True, False, False
    except Exception:
        raise TypeError("input must be a scalar")


def _copytobuffer(xx: Any) -> Tuple[Any, bool, bool, bool]:
    """
    return a copy of xx as an object that supports the python Buffer
    API (python array if input is float, list or tuple, numpy array
    if input is a numpy array). returns copyofx, isfloat, islist,
    istuple (islist is True if input is a list, istuple is true if
    input is a tuple, isfloat is true if input is a float).
    """
    # make sure x supports Buffer API and contains doubles.
    isfloat = False
    islist = False
    istuple = False
    # first, if it's a numpy array scalar convert to float
    # (array scalars don't support buffer API)
    if hasattr(xx, "shape"):
        if xx.shape == ():
            return _copytobuffer_return_scalar(xx)
        else:
            try:
                # typecast numpy arrays to double.
                # (this makes a copy - which is crucial
                #  since buffer is modified in place)
                xx.dtype.char
                # Basemap issue
                # https://github.com/matplotlib/basemap/pull/223/files
                # (deal with input array in fortran order)
                inx = xx.copy(order="C").astype("d")
                # inx,isfloat,islist,istuple
                return inx, False, False, False
            except Exception:
                try:  # perhaps they are Numeric/numarrays?
                    # sorry, not tested yet.
                    # i don't know Numeric/numarrays has `shape'.
                    xx.typecode()
                    inx = xx.astype("d")
                    # inx,isfloat,islist,istuple
                    return inx, False, False, False
                except Exception:
                    raise TypeError("input must be an array, list, tuple or scalar")
    else:
        # perhaps they are regular python arrays?
        if hasattr(xx, "typecode"):
            # xx.typecode
            inx = array("d", xx)
        # try to convert to python array
        # a list.
        elif type(xx) == list:
            inx = array("d", xx)
            islist = True
        # a tuple.
        elif type(xx) == tuple:
            inx = array("d", xx)
            istuple = True
        # a scalar?
        else:
            return _copytobuffer_return_scalar(xx)
    return inx, isfloat, islist, istuple


def _convertback(isfloat: bool, islist: bool, istuple: bool, inx: Any) -> Any:
    # if inputs were lists, tuples or floats, convert back to original type.
    if isfloat:
        return inx[0]
    elif islist:
        return inx.tolist()
    elif istuple:
        return tuple(inx)
    else:
        return inx
