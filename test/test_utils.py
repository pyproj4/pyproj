from array import array

import numpy
import pytest

from pyproj.utils import DataType, _copytobuffer, _copytobuffer_return_scalar


@pytest.mark.parametrize("in_data", [numpy.array(1), 1])
def test__copytobuffer_return_scalar(in_data):
    assert _copytobuffer_return_scalar(in_data) == (array("d", [1]), DataType.FLOAT)


def test__copytobuffer_return_scalar__invalid():
    with pytest.raises(TypeError):
        _copytobuffer_return_scalar("invalid")


@pytest.mark.parametrize(
    "in_data, data_type",
    [
        (numpy.array(1), DataType.FLOAT),
        (1, DataType.FLOAT),
        ([1], DataType.LIST),
        ((1,), DataType.TUPLE),
    ],
)
def test__copytobuffer(in_data, data_type):
    assert _copytobuffer(in_data) == (array("d", [1]), data_type)


def test__copytobuffer__xarray_scalar():
    xarray = pytest.importorskip("xarray")
    assert _copytobuffer(xarray.DataArray(numpy.array(1))) == (
        array("d", [1]),
        DataType.FLOAT,
    )


@pytest.mark.parametrize("arr_type", ["numpy", "xarray", "pandas"])
def test__copytobuffer__array(arr_type):
    in_arr = numpy.array([1])
    if arr_type == "xarray":
        xarray = pytest.importorskip("xarray")
        in_arr = xarray.DataArray(in_arr)
    elif arr_type == "pandas":
        pandas = pytest.importorskip("pandas")
        in_arr = pandas.Series(in_arr)
    assert _copytobuffer(in_arr) == (
        in_arr.astype("d").__array__(),
        DataType.ARRAY,
    )


def test__copytobuffer__numpy_masked_array():
    in_arr = numpy.ma.array([1])
    out_arr, dtype = _copytobuffer(in_arr)

    assert isinstance(out_arr, numpy.ma.MaskedArray)


def test__copytobuffer__fortran_order():
    data = numpy.ones((2, 4), dtype=numpy.float64, order="F")
    converted_data, dtype = _copytobuffer(data)
    assert data.flags.f_contiguous
    assert not converted_data.flags.f_contiguous
    assert converted_data.flags.c_contiguous


def test__copytobuffer__invalid():
    with pytest.raises(TypeError):
        _copytobuffer("invalid")
