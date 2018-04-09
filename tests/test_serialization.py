from __future__ import print_function
import os
import sys
import tempfile

import pytest
from yamicache import Cache

try:
    import cPickle as pickle
except ImportError:
    import pickle   # noqa: F401


if sys.version_info[0] == 2:
    range = xrange

c = Cache(prefix='myapp', hashing=False, debug=False)


class MyApp(object):
    @c.cached()
    def test1(self, argument, power):
        '''running test1'''
        return argument ** power

    @c.cached()
    def test2(self):
        '''running test2'''
        return 1

    @c.cached(key='asdf')
    def test3(self, argument, power):
        '''running test3'''
        return argument ** power

    def test4(self):
        '''running test4'''
        return 4

    @c.cached()
    def cant_cache(self):
        print("here")


@pytest.fixture
def cache_obj():
    m = MyApp()
    return m


def test_serialization(cache_obj):
    for _ in range(10):
        cache_obj.test1(8, 0)

    assert len(c) == 1
    assert cache_obj.test1(8, 0) == 1

    for _ in range(10):
        cache_obj.test2()

    assert cache_obj.test2() == 1
    assert len(c) == 2

    # Dump the cache to a file
    temp_handle, filepath = tempfile.mkstemp()
    os.close(temp_handle)

    c.serialize(filepath)

    # Store the current obj for comparison
    orig = c._data_store.copy()

    c.clear()
    assert len(c) == 0

    c.deserialize(filepath)

    assert len(c)
    assert c._data_store == orig

    os.unlink(filepath)


def main():
    test_serialization(MyApp())


if __name__ == '__main__':
    main()
