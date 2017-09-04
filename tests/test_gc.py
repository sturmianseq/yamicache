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

    @c.cached(timeout=2)
    def test2(self):
        '''running test2'''
        return 3


def test_deco_timeout(cache_obj):
    '''Test custom decorator timeout'''
    c.clear()

    # Cache the result, which should use a 2s timeout, as opposed to the
    # default of 1s.
    tstart = time.time()
    cache_obj.test2()

    # Wait up to 5s for the GC thread to clear `test2()`.
    while len(c) and ((time.time() - tstart) < 5):
        time.sleep(0.1)  # Give GC a chance to run

    tend = time.time()

    # The defined timeout is 2, and gc_thread_wait is 0.5, so the max we
    # should really be waiting is 2.5 (ish).  The mininum is 2-ish.
    # NOTE: I've had a hell of time with duration variance on Travis-CI, which
    # is why the range is so big.
    time_diff = tend - tstart
    print('actual time: %s' % time_diff)
    assert 1.5 < time_diff < 3.5


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
    test_deco_timeout(MyApp())


if __name__ == '__main__':
    main()
