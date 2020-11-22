"""
Just a quick test to make sure there's no ``cls`` or ``self`` odness.
"""
from __future__ import print_function
import sys
import time
from yamicache import Cache

c = Cache(prefix="myapp", hashing=False, debug=False)


@c.cached()
def my_func(argument, power):
    """running my_func"""
    return argument ** power


@c.cached()
def return_list(index):
    mylists = {0: [1, 2, 3], 1: [4, 5, 6]}
    return mylists[index]


def test_main():
    assert len(c) == 0

    for _ in [0, 1, 2, 3, 4, 5]:
        my_func(2, 3)

    assert len(c) == 1


def test_lists():
    """Make sure lists are returned"""
    assert return_list(0) == [1, 2, 3]
    assert return_list(0) == [1, 2, 3]
    assert return_list(1) == [4, 5, 6]
    assert return_list(1) == [4, 5, 6]


class MyObject(object):
    def __init__(self, number):
        self.number = number


@c.cached(timeout=1)
def return_object_list():
    return [MyObject(0), MyObject(1), MyObject(2)]


def test_object_list():
    """Test a result with a timeout & objects are returned"""
    result = return_object_list()
    assert result[0].number == 0
    assert result[1].number == 1
    assert result[2].number == 2
    time.sleep(2)
    result = return_object_list()
    assert result[0].number == 0
    assert result[1].number == 1
    assert result[2].number == 2


if __name__ == "__main__":
    test_main()
