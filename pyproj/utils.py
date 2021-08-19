"""
Utility functions used within pyproj
"""
import json
from array import array
from enum import Enum, auto
from typing import Any, Tuple


def is_null(value: Any) -> bool:
    """
    Check if value is NaN or None
    """
    return value != value or value is None


class NumpyEncoder(json.JSONEncoder):
    """
    Handle numpy types when dumping to JSON
    """

    def default(self, obj):
        try:
            return obj.tolist()
        except AttributeError:
            pass
        try:
            # numpy scalars
            if obj.dtype.kind == "f":
                return float(obj)
            elif obj.dtype.kind == "i":
                return int(obj)
        except AttributeError:
            pass
        return json.JSONEncoder.default(self, obj)


class DataType(Enum):
    """
    Data type for copy to buffer and convertback operations
    """

    FLOAT = auto()
    LIST = auto()
    TUPLE = auto()
    ARRAY = auto()


def _copytobuffer_return_scalar(xx: Any) -> Tuple[array, DataType]:
    """
    Parameters
    -----------
    xx: float or 0-d numpy array
    """
    try:
        return array("d", (float(xx),)), DataType.FLOAT
    except Exception:
        raise TypeError("input must be a scalar")


def _copytobuffer(xx: Any) -> Tuple[Any, DataType]:
    """
    return a copy of xx as an object that supports the python Buffer
    API (python array if input is float, list or tuple, numpy array
    if input is a numpy array). returns copyofx, isfloat, islist,
    istuple (islist is True if input is a list, istuple is true if
    input is a tuple, isfloat is true if input is a float).
    """
    # check for pandas.Series, xarray.DataArray or dask.array.Array
    if hasattr(xx, "__array__") and callable(xx.__array__):
        xx = xx.__array__()

    # if it's a numpy array scalar convert to float
    # (array scalars don't support buffer API)
    if hasattr(xx, "shape"):
        if xx.shape == ():
            return _copytobuffer_return_scalar(xx)
        else:
            # typecast numpy arrays to double.
            # (this makes a copy - which is crucial
            #  since buffer is modified in place)
            xx.dtype.char
            # Basemap issue
            # https://github.com/matplotlib/basemap/pull/223/files
            # (deal with input array in fortran order)
            inx = xx.copy(order="C").astype("d", copy=False)
            # inx,isfloat,islist,istuple
            return inx, DataType.ARRAY
    else:
        data_type = DataType.ARRAY
        # perhaps they are regular python arrays?
        if hasattr(xx, "typecode"):
            # xx.typecode
            inx = array("d", xx)
        # try to convert to python array
        # a list.
        elif isinstance(xx, list):
            inx = array("d", xx)
            data_type = DataType.LIST
        # a tuple.
        elif isinstance(xx, tuple):
            inx = array("d", xx)
            data_type = DataType.TUPLE
        # a scalar?
        else:
            return _copytobuffer_return_scalar(xx)
    return inx, data_type


def _convertback(data_type: DataType, inx: Any) -> Any:
    # if inputs were lists, tuples or floats, convert back to original type.
    if data_type == DataType.FLOAT:
        return inx[0]
    elif data_type == DataType.LIST:
        return inx.tolist()
    elif data_type == DataType.TUPLE:
        return tuple(inx)
    else:
        return inx
