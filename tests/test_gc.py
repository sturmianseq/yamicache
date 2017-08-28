from __future__ import print_function
import sys
import time
import pytest
from yamicache.yamicache import Cache, override_timeout

if sys.version_info[0] == 2:
    range = xrange

c = Cache(prefix='myapp', hashing=False, debug=False, default_timeout=1, gc_thread_wait=0.5)


@pytest.fixture
def cache_obj():
    m = MyApp()
    return m


class MyApp(object):
    @c.cached()
    def test1(self, argument, power):
        '''running test1'''
        return argument ** power


def test_gc(cache_obj):
    for _ in range(10):
        cache_obj.test1(8, 0)

    assert len(c) == 1

    # Let the GC thread collect the single cached item
    time.sleep(2)

    assert len(c) == 0


def test_gc2(cache_obj):
    '''Make sure the GC doesn't constantly run'''
    c.clear()

    with override_timeout(c, 3):
        cache_obj.test1(8, 0)

    item_added = c._from_timestamp(list(c.values())[0].time_added)

    # Should be cached...
    assert len(c) == 1

    time.sleep(1)
    # Should still be cached...
    assert len(c) == 1

    # Wait for the GC thread to do its thing
    t_start = time.time()
    t_end = t_start + 5
    while time.time() < t_end:
        if not len(c):
            print("took %s to clear" % (time.time() - t_start))
            break

        time.sleep(0.5)

    # Should be cleared
    assert len(c) == 0

    # Make sure it's been at least 3 seconds since the item was added
    assert time.time() - item_added >= 3


def main():
    test_gc2(MyApp())


if __name__ == '__main__':
    main()
