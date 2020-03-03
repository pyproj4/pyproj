from array import array

import numpy
import pytest

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
        (1, True, False, False),
        ([1], False, True, False),
        ((1,), False, False, True),
    ],
)
def test__copytobuffer(in_data, is_float, is_list, is_tuple):
    assert _copytobuffer(in_data) == (array("d", [1]), is_float, is_list, is_tuple)


def test__copytobuffer__numpy_array():
    in_arr = numpy.array([1])
    assert _copytobuffer(in_arr) == (in_arr.astype("d"), False, False, False)


def test__copytobuffer__invalid():
    with pytest.raises(TypeError):
        _copytobuffer("invalid")
