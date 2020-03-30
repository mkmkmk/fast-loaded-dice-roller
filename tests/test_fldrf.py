# Released under Apache 2.0; refer to LICEaE.txt.

from itertools import product
from random import getrandbits
from random import random

import pytest

from fldr.fldrf import align_mantissa

def linspace(start, stop, n):
    if n == 1:
        yield stop
        return
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i

def bits_to_int(a):
    return int(''.join(map(str, a)), 2) if a else 0

xs \
    = list(linspace(0, 1, 100)) \
    + list(linspace(1, 10, 100)) \
    + list(map(float, range(0,10)))

@pytest.mark.parametrize('x', xs)
def test_as_integer_ratio_py(x):
    from fldr.fldrf import as_integer_ratio_py
    a = x.as_integer_ratio()
    b = as_integer_ratio_py(x)
    assert a == b

@pytest.mark.parametrize('x', xs)
def test_as_integer_ratio_c(x):
    from fldr.fldrf import as_integer_ratio_c
    a = x.as_integer_ratio()
    (mantissa, exponent) = as_integer_ratio_c(x)
    assert mantissa[0][mantissa[1]-1] is not 0 or x == 0.0
    mantissa_bits = align_mantissa(mantissa, mantissa[1]+mantissa[2])
    numerator = bits_to_int(mantissa_bits)
    denominator = 2**exponent
    assert a == (numerator, denominator)

ms = [
    (([0,0,0,0,0,0,0], 0, 0), []),
    (([0,1,0,0,0,0,0], 3, 0), [0,1,0]),
    (([1,1,0,0,0,0,0], 3, 0), [0,1,1]),
    (([1,1,0,0,0,0,0], 3, 4), [0,1,1,0,0,0,0]),
    (([1,1,0,1,1,0,0], 5, 3), [1,1,0,1,1,0,0,0]),
]
@pytest.mark.parametrize('m', ms)
def test_align_mantissa(m):
    k = m[0][1]
    offset = m[0][2]
    assert align_mantissa(m[0], k+offset) == m[1]

bits_list = [(0,), (0,1,), (1,),(1, 0), (0,1,1), (1,1,1), (1,1,0,1,1,0)]
@pytest.mark.parametrize('a, b', product(bits_list, bits_list))
def test_binary_add(a, b):
    from fldr.fldrf import binary_add
    int_a = bits_to_int(a)
    int_b = bits_to_int(b)
    solution = bin(int_a + int_b)
    answer = '0b%s' % (''.join(map(str, binary_add(a, b))))
    try:
        assert answer == solution
    except AssertionError:
        # Case 0b011 == 0b11, happens when a starts with 0.
        assert answer[2] == '0'
        assert answer[3:] == solution[2:]

@pytest.mark.parametrize('a, b', product(bits_list, bits_list))
def test_binary_subtract(a, b):
    from fldr.fldrf import binary_subtract
    int_a = bits_to_int(a)
    int_b = bits_to_int(b)
    if (int_a < int_b) or len(a) < len(b):
        return True
    solution = bin(int_a - int_b)
    answer = '0b%s' % (''.join(map(str, binary_subtract(a, b))))
    assert answer == solution

max_dims = 11
rep_dims = 10
a_list_int = [
    [getrandbits(10) + 1. for i in range(n)]
    for n in range(2, max_dims)
    for k in range(rep_dims)
]
a_list_float = [
    [getrandbits(10) + random() for i in range(n)]
    for n in range(2, max_dims)
    for k in range(rep_dims)
]
@pytest.mark.parametrize('a', a_list_int + a_list_float)
def test_normalize_floats_equivalent_py_pyc(a):
    from fldr.fldrf import normalize_floats_py
    from fldr.fldrf import normalize_floats_c
    integers = normalize_floats_py(a)
    mantissas = normalize_floats_c(a)
    arrays = [align_mantissa(m, m[1] + m[2]) for m in mantissas]
    for i, j in zip(integers, arrays):
        assert i == bits_to_int(j)

@pytest.mark.parametrize('a', a_list_int + a_list_float)
def test_preprocess_identical_py_pyc(a):
    from fldr.fldrf import fldr_preprocess_float_py
    from fldr.fldrf import fldr_preprocess_float_c
    x_py = fldr_preprocess_float_py(a)
    x_c = fldr_preprocess_float_c(a)

    assert x_py.m == bits_to_int(x_c.m)
    assert x_py.k == x_c.k
    assert x_py.r == bits_to_int(x_c.r)
    assert x_py.h == x_c.h
    assert x_py.H == x_c.H
