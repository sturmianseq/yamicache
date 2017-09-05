from __future__ import print_function
import sys
import time
import pytest
import random
import threading
from functools import partial
from yamicache import Cache

if sys.version_info[0] == 2:
    range = xrange
    from Queue import Queue, Empty
else:
    from queue import Queue, Empty


DEBUG_PRINT = False


def debug_print(text):
    if DEBUG_PRINT:
        print(text)


c = Cache(debug=False)


@pytest.fixture
def cache_obj():
    m = MyApp()
    return m


class ExcThread(threading.Thread):
    '''This class is used to capture exceptions during the threaded run.'''
    def __init__(self, bucket, target):
        threading.Thread.__init__(self, target=target)
        self.bucket = bucket
        self.target = target

    def run(self):
        try:
            super(ExcThread, self).run()
        except Exception:
            self.bucket.put((self.target, sys.exc_info()))


class MyApp(object):
    @c.cached()
    def test1(self, argument, power):
        '''running test1'''
        return argument ** power


def _cache(cache_obj):
    '''Cache the result of a function'''
    time.sleep(random.randint(0, 2))
    debug_print("caching")
    cache_obj.test1(3, 0)


def _pop():
    '''Pop a *random* item from cache'''
    time.sleep(random.randint(0, 2))
    try:
        c.popitem()
    except KeyError:
        pass

    assert True


def _iter():
    '''Iterate through the cached items using ``iter()``'''
    time.sleep(random.randint(0, 2))
    debug_print("iter")
    list(iter(c))
    assert True


def _items():
    '''Iterate through the cahced items using ``items()``'''
    time.sleep(random.randint(0, 2))
    debug_print("items")
    c.items()
    assert True


def _keys():
    '''Iterate through the cached item keys'''
    time.sleep(random.randint(0, 2))
    debug_print("keys")
    c.keys()
    assert True


def _values():
    '''Iterate through the cached item values'''
    time.sleep(random.randint(0, 2))
    debug_print("values")
    c.values()
    assert True


def _clear():
    '''Clear the cache'''
    time.sleep(random.randint(0, 2))
    debug_print("clearing")
    c.clear()
    assert True


def _collect():
    '''Manually GC the cache'''
    time.sleep(random.randint(0, 2))
    debug_print("collecting")
    c.collect()
    assert True


def test_multithreading(cache_obj):
    '''Test for thread blocking on Lock()'''
    threads = []
    counts = {}
    q = Queue()

    fcache = partial(_cache, cache_obj)
    choices = [fcache, _pop, _items, _clear, _values, _keys, _iter, _collect]

    # Create some random threads to see what happens ##########################
    for _ in range(10000):
        f = random.choice(choices)

        if f in counts:
            counts[f] += 1
        else:
            counts[f] = 1

        threads.append(ExcThread(q, target=f))

    # Spin them all up ########################################################
    tstart = time.time()
    [x.start() for x in threads]
    debug_print("all started")

    # Wait until all threads have completed ###################################
    [x.join() for x in threads]
    debug_print("all joined")
    debug_print("test took: %s" % (time.time() - tstart))

    # Print the counts of each function #######################################
    for func, count in counts.items():
        if func is fcache:
            debug_print("%8s: %i" % ("_cache", count))
        else:
            debug_print("%8s: %i" % (func.__name__, count))

    # Check the queue to make sure no Exceptions were raised ##################
    something_in_queue = False
    try:
        for item in q.get_nowait():
            something_in_queue = True
            print(item)
    except Empty:
        pass

    assert not something_in_queue


def main():
    test_multithreading(MyApp())


if __name__ == '__main__':
    main()
