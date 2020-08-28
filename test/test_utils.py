from array import array

import numpy
import pytest
from pandas import Series
from xarray import DataArray

from pyproj.utils import _copytobuffer, _copytobuffer_return_scalar


@pytest.mark.parametrize("in_data", [numpy.array(1), 1])
def test__copytobuffer_return_scalar(in_data):
    assert _copytobuffer_return_scalar(in_data) == (array("d", [1]), True, False, False)


def test__copytobuffer_return_scalar__invalid():
    with pytest.raises(TypeError):
        _copytobuffer_return_scalar("invalid")


@pytest.mark.parametrize(
    "in_data, is_float, is_list, is_tuple",
    [
        (numpy.array(1), True, False, False),
        (DataArray(numpy.array(1)), True, False, False),
        (1, True, False, False),
        ([1], False, True, False),
        ((1,), False, False, True),
    ],
)
def test__copytobuffer(in_data, is_float, is_list, is_tuple):
    assert _copytobuffer(in_data) == (array("d", [1]), is_float, is_list, is_tuple)


@pytest.mark.parametrize(
    "in_arr", [numpy.array([1]), DataArray(numpy.array([1])), Series(numpy.array([1]))]
)
def test__copytobuffer__numpy_array(in_arr):
    assert _copytobuffer(in_arr) == (
        in_arr.astype("d").__array__(),
        False,
        False,
        False,
    )


def test__copytobuffer__invalid():
    with pytest.raises(TypeError):
        _copytobuffer("invalid")
