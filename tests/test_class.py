from __future__ import print_function
import sys
import time
import pytest
from yamicache import Cache, nocache, override_timeout

c = Cache(prefix="myapp", hashing=False, debug=False)


class MyApp(object):
    @c.cached()
    def test1(self, argument, power):
        """running test1"""
        return argument ** power

    @c.cached()
    def test2(self):
        """running test2"""
        return 1

    @c.cached(key="asdf")
    def test3(self, argument, power):
        """running test3"""
        return argument ** power

    def test4(self):
        """running test4"""
        return 4

    @c.cached()
    def cant_cache(self):
        print("here")


@pytest.fixture
def cache_obj():
    m = MyApp()
    return m


def test_cached(cache_obj):
    c.clear()
    for _ in range(10):
        cache_obj.test1(8, 0)

    assert len(c) == 1
    assert cache_obj.test1(8, 0) == 1

    for _ in range(10):
        cache_obj.test2()

    assert cache_obj.test2() == 1
    assert len(c) == 2

    c.clear()
    assert len(c) == 0

    # Make sure the cached function is properly wrapped
    assert cache_obj.test2.__doc__ == "running test2"


def test_keyed_cached(cache_obj):
    for _ in range(10):
        cache_obj.test3(8, 0)

    cache_obj.test4()  # Shouldn't be cached

    assert len(c) == 1

    key = list(c.keys())[0]
    assert key == "asdf"

    c.clear()
    assert len(c) == 0

    # Make sure the cached function is properly wrapped
    assert cache_obj.test3.__doc__ == "running test3"


def test_utility(cache_obj):
    for _ in range(10):
        cache_obj.test1(8, 0)
        cache_obj.test1(8, 2)
        cache_obj.test1(8, 2)  # Already cached
        cache_obj.test2()
        cache_obj.test3(8, 2)

    assert len(c) == 4

    assert c.dump() != "{}"

    key = list(c.keys())[0]
    c.pop(key)
    assert len(c) == 3
    assert key not in c

    assert len(c.keys()) == 3
    assert len(c.values()) == 3

    assert c.items()

    c.clear()

    assert not c.items()
    assert not c.keys()
    assert not c.values()
    assert not len(c)
    assert c.dump() == "{}"


def test_counters(cache_obj):
    c.clear()
    c._debug = True

    for _ in range(10):
        cache_obj.test3(8, 2)

    assert len(c.counters) == 1
    assert c.counters["asdf"] == 9

    print(c.dump())
    c.counters.clear()
    c.clear()


def test_nocache(cache_obj):
    c.clear()
    c._debug = False

    assert len(c.counters) == 0
    assert len(c) == 0

    with nocache(c):
        for _ in range(10):
            cache_obj.test3(8, 2)
            cache_obj.test4()

    assert len(c.counters) == 0
    assert len(c) == 0


def test_timeout(cache_obj):
    c.clear()
    c._debug = True

    cache_obj.test3(8, 2)
    cache_obj.test3(8, 2)

    time.sleep(1)

    c.collect()
    assert len(c) == 1

    c.collect(since=time.time() - 20)
    assert len(c) == 0

    with override_timeout(c, 1):
        cache_obj.test3(8, 2)
        cache_obj.test3(8, 2)

    assert len(c) == 1

    time.sleep(1.5)
    c.collect()
    assert len(c) == 0

    c.clear()

    # Test a call where the cache has timed out.
    # For this test, we want to load the cache with our specified timeout
    # value.  Then wait longer than the timeout, and run the function again.
    # The hit counter should remain the same, since we didn't read the value
    # from cache.
    with override_timeout(c, 1):
        cache_obj.test3(8, 2)
        cache_obj.test3(8, 2)

    assert len(c.counters) == 1
    before_count = list(c.counters.values())[0]
    assert len(c) == 1
    time.sleep(1.5)
    cache_obj.test3(8, 2)  # should be a new cache w/o the counter incrementing
    assert len(c) == 1

    assert list(c.counters.values())[0] == before_count


def test_prefix(cache_obj):
    c.clear()
    cache_obj.test1(8, 0)
    key = list(c.keys())[0]
    assert key.startswith("myapp|")


def main():
    # test_utility(MyApp())
    # test_nocache(MyApp())
    # test_cached(MyApp())
    test_timeout(MyApp())


if __name__ == "__main__":
    main()
