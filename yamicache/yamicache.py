#!/usr/bin/env python
# coding: utf-8
'''
yamicache : Yet another in-memory cache module ('yami' sounds better to me than
'yaim')

This module provides a simple in-memory interface for caching results from
function calls.
'''

# Imports #####################################################################
from __future__ import print_function
import json
import time
import contextlib
import collections
from hashlib import sha224
from functools import wraps
from threading import Lock, Thread


# Globals #####################################################################
__all__ = ['Cache', 'nocache', 'override_timeout']


@contextlib.contextmanager
def override_timeout(cache_obj, timeout):
    old = cache_obj._default_timeout
    cache_obj._default_timeout = timeout

    try:
        yield
    finally:
        cache_obj._default_timeout = old


@contextlib.contextmanager
def nocache(cache_obj):
    '''
    Use this context manager to temporarily disable all caching for an
    object.

    Example:

        >>> from yamicache import Cache, nocache
        >>> c = Cache()
        >>> @c.cached
        ... def test():
        ...     return 4
        ...
        >>> with nocache(c):
        ...     test()
        ...
        4
        >>> print c.data_store
        {}
        >>>

    '''
    cache_obj._cache = False

    try:
        yield
    finally:
        cache_obj._cache = True


CachedItem = collections.namedtuple('CachedItem', 'value timeout time_added')


class Cache(collections.MutableMapping):
    '''
    A class for caching and retreiving returns from function calls.

    :param bool hashing: Whether or not to hash the function inputs when
        calculating the key.  This helps keep the keys *readable*, especially
        for functions with many inputs.
    :param str key_join: The character used to join the different parts that
        make up the hash key.
    :param bool debug: When ``True``, ``Cache.counters`` will be enabled and
        cache hits will produce output on ``stdout``.
    :param str prefix: All cache keys will use this prefix.  Since the current
        implementation is instance-based, this is only helpful if dumping or
        comparing the cache to another instance.
    :param bool quiet: Don't print during ``debug`` cache hits
    :param int default_timeout: If > 0, all cached items will be considered
        stale this many seconds after they are cached.  In that case, the
        function will be run again, cached, and a new timeout value will be
        created.
    :param int gc_thread_wait: The number of seconds in between cache
        *garbage collection*.  The default, ``None``, will disable the garbage
        collection thread.  This parameter is only valid if ``default_timeout``
        is > 0 (``ValueError`` is raised otherwise).
    '''
    def __init__(
        self, hashing=True, key_join='|', debug=False, prefix=None,
        quiet=False, default_timeout=0, gc_thread_wait=None
    ):
        self._prefix = prefix or ''
        self._hashing = hashing
        self._key_join = key_join
        self._debug = debug
        self._quiet = quiet
        self._cache = True  # Allow for ``nocache``
        self._data_store = {}
        self._default_timeout = default_timeout
        self._gc_thread_wait = gc_thread_wait
        self._gc_thread = None
        self._do_gc_thread = False
        self._gc_lock = Lock()
        self.counters = {}  # Only enabled with ``debug``

        if self._gc_thread_wait:
            self._do_gc_thread = True
            self._gc_thread = Thread(target=self._gc)
            self._gc_thread.daemon = True
            self._gc_thread.start()

    # Default stuff to override MutableMapping ABC ############################
    def __len__(self):
        return len(self._data_store)

    def __getitem__(self, key):
        with self._gc_lock:
            return self._data_store[key]

    def __setitem__(self, key, value):
        with self._gc_lock:
            self._data_store[key] = value

    def __delitem__(self, key):
        with self._gc_lock:
            del self._data_store[key]

    def __iter__(self):
        '''
        Override ``iter()``.  This can make things slow, but it's the only
        way to prevent the underlying object from changing during iteration.
        '''
        with self._gc_lock:
            for x in self._data_store.keys():
                yield x

    # Override some of the *normal* methods to include the lock ###############
    def clear(self):
        '''Override `MutableMapping.clear()` to also clear `self.counters`'''
        with self._gc_lock:
            self._data_store.clear()
            self.counters.clear()

    def keys(self):
        with self._gc_lock:
            return self._data_store.keys()

    def items(self):
        with self._gc_lock:
            return self._data_store.items()

    def values(self):
        with self._gc_lock:
            return self._data_store.values()

    def pop(self, key):
        with self._gc_lock:
            return self._data_store.pop(key)

    def popitem(self):
        with self._gc_lock:
            return self._data_store.popitem()
    ###########################################################################

    def _from_timestamp(self, timestamp):
        '''Convert a timestamp string to an epoch value'''
        return time.mktime(time.strptime(timestamp))

    def _to_timestamp(self, epoch=None):
        '''Convert an epoch value to a timestamp string'''
        if epoch:
            return time.asctime(time.localtime(epoch))

        return time.asctime()

    def _debug_print(self, *args):
        if self._debug:
            print(*args)

    def dump(self):
        '''Dump the entire cache as a JSON object'''
        return json.dumps(self._data_store, indent=4, separators=(',', ': '))

    def _calculate_key(self, func, cached_key=None, *args, **kwargs):
        '''
        Calculates the cache key based on the function, inputs, and object
        settings.

        :param code func: The function being cached
        :param str cached_key: The `keyed_cache`, if any
        :param *args: Any ``*args`` used to call the function
        :param *kwargs: Any ``*kwargs`` used to call the function
        '''
        key = cached_key
        if not key:
            key = dict(kwargs)
            key.update(dict(zip(func.__code__.co_varnames, args)))

        return "{prefix}{name}{join}{formatted_key}".format(
            join=self._key_join,
            prefix=(self._prefix + self._key_join) if self._prefix else '',
            name=func.__name__,
            formatted_key=sha224(str(key).encode('utf-8')).hexdigest() if self._hashing else str(key)
        )

    def _update_counter(self, key):
        '''Keeps track of cache hits'''
        if not self._debug:
            return

        with self._gc_lock:
            if key in self.counters:
                self.counters[key] += 1
            else:
                self.counters[key] = 1

    def _gc(self):
        '''
        This is the garbage collection thread that periodically calls our
        collect method.
        '''
        tnext = time.time() + self._gc_thread_wait
        while self._do_gc_thread:
            if time.time() > tnext:
                self.collect()
                tnext = time.time() + self._gc_thread_wait

            time.sleep(1)

    def collect(self, since=None):
        '''
        Clear any item from the cache that has timed out.
        '''
        remove_keys = []
        for key, item in self.items():
            if (
                (item.timeout and (time.time() > self._from_timestamp(item.timeout))) or
                (since and (self._from_timestamp(item.time_added) > since))
            ):
                self._debug_print('collecting : %s' % key)
                remove_keys.append(key)

        for key in remove_keys:
            if key in self:
                del self[key]

    def cached(self, key=None, timeout=None):
        '''
        A decorator used to memoize the return of a function call.
        '''
        def real_decorator(function):

            @wraps(function)
            def wrapper(*args, **kwargs):
                # Check the timeout here, since this is the call and not the
                # instantiation.
                timeout = self._default_timeout

                if not self._cache:
                    return function(*args, **kwargs)

                cache_key = self._calculate_key(function, key, *args, **kwargs)

                try:
                    if cache_key in self:
                        result = self[cache_key]
                        if (not result.timeout) or (result.timeout and (time.time() <= self._from_timestamp(result.timeout))):
                            self._debug_print('cache hit : %s' % cache_key)
                            self._update_counter(cache_key)
                            return result.value
                        elif result.timeout and (time.time() > self._from_timestamp(result.timeout)):
                            self._debug_print('cache timeout: %s' % cache_key)
                            result = CachedItem(
                                value=function(*args, **kwargs),
                                timeout=self._to_timestamp(time.time() + timeout) if timeout else 0,
                                time_added=self._to_timestamp())
                            self[cache_key] = result
                            return self[cache_key]
                except KeyError:  # pragma: nocover
                    # Workaround for threading issues, as opposed to a potential
                    # lock block.  A thread may have deleted this key, and
                    # that's fine.  We simply need to cache it again.
                    # We won't always hit this, so we disable code coverage.
                    self._debug_print('KeyError %s' % cache_key)

                self._debug_print('caching %s' % cache_key)

                result = CachedItem(
                    value=function(*args, **kwargs),
                    timeout=self._to_timestamp(time.time() + timeout) if timeout else None,
                    time_added=self._to_timestamp())
                self[cache_key] = result
                return result.value

            return wrapper

        return real_decorator
