import pytest

import iterator

def test_into_iter():
    iterator.into_iter([1, 2, 3])

def test_into_iter_2():
    assert iterator.into_iter([1, 2, 3]).collect() == [1, 2, 3]


def test_count():
    assert iterator.into_iter([1, 2, 3]).count() == 3

def test_last():
    assert iterator.into_iter([1, 2, 3]).last() == 3

def test_last_err():
    with pytest.raises(LookupError):
        iterator.into_iter([]).last()

