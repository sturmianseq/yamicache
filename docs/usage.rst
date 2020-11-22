=====
Usage
=====

To use yamicache in a project:

.. code-block:: python

    from yaimcache import Cache

    app_cache = Cache()


    @app_cache.cached
    def square(var):
        return var ** 2


    square(2)  # Will cache the first time
    square(2)  # Cache hit
    square(2)  # Cache hit
    square(3)  # New cached item
    square(3)  # Cache hit
    app_cache.clear()
    square(3)  # New cached item

.. caution::
    You probably shouldn't indefinitely store really large objects if you don't
    really need to.

Object Creation
---------------

In order to enable caching, you must first create a ``Cache`` object:

.. code-block:: python

    from yamicache import Cache
    c = Cache()

The caching object has the following parameters available during object creation:

    * ``hashing (bool)``: This controls how default cache ``keys`` are created.  By default, they key will hashed to make things a bit more *readable*.
    * ``key_join (str)``: This is the character used to join the different parts that make up the default key.
    * ``debug (bool)``: When ``True``, ``Cache.counters`` will be enabled and cache hits will produce output on ``stdout``.
    * ``prefix (str)``: All cache keys will use this prefix.  Since the current implementation is instance-based, this is only helpful if dumping or comparing the cache to another instance.
    * ``quiet (bool)``: Don't print during ``debug`` cache hits
    * ``default_timeout (int)``: If > 0, all cached items will be considered stale this many seconds after they are cached.  In that case, the function will be run again, cached, and a new timeout value will be created.
    * ``gc_thread_wait (int)``: The number of seconds in between cache *garbage collection*.  The default, ``None``, will disable the garbage collection thread. This parameter is only valid if ``default_timeout`` is > 0 (``ValueError`` is raised otherwise).

Decorators
----------

`@Cache.cached(key, timeout)`
+++++++++++++++++++++++++++++

This is the main decorator you use to cache the result from the function.
`Yamicache` stores the result of the function and the function's inputs.
Subsequent calls to this function, with the same inputs, will not call the
function's code.  `Yamicache` will return the function's result.

``key``: This input parameter can be used to specify the exact key you wish to
store in the cache.  This can make testing easier.  You would normally leave
this parameter blank.  This will allow ``yamicache`` to build a key based on
the function being called and the arguments being used.

.. warning::
    You cannot duplicate a key.  Attempts to instantiate a cached object with
    the same key will raise ``ValueError``.

``timeout``: You can use this parameter to override the default timeout value
used by the ``yamicache.Cache`` object.


`@Cache.clear_cache()`
++++++++++++++++++++++

This decorator can be used to force ``Cache.clear()`` whenever the function is
called.  This is handy when you call a function that should change the state of
the object and its cache (e.g. creating a directory after you already cached the
result of ``ls``).

Context Managers
----------------

`Yamicache` includes the following context managers to override default caching
behavior.

`override_timeout(cache_obj, timeout)`
++++++++++++++++++++++++++++++++++++++

This will override the timeout value set either by the ``Cache`` object or the
cached decorator.  For example:

.. code-block:: python

    from yamicache import Cache, override_timeout
    c = Cache()

    @c.cached(timeout=90)
    def long_op():
        return 1

    with override_timeout(c, timeout=5):
        long_op()

`nocache(cache_obj)`
++++++++++++++++++++

This will disable the default caching mechanism.  The cache will **not** be
modified when this context manager is used.  For example:

.. code-block:: python

    from yamicache import Cache, nocache
    c = Cache()

    @c.cached(key='test')
    def long_op(value):
        return value

    long_op(1)  # First time; result will be cached
    long_op(1)  # cached result will be returned

    with nocache(c):
        long_op(1)  # Function code will be run; value will not affect cache

Garbage Collection
------------------

You may want to periodically remove items from the cache that are no longer
*valid* or stale.  There are a few of ways to do this:

1.  Periodically call ``clear()``:  This removes everything from the cache.
2.  Periodically call ``collect()``:  This removes only items that exist and are *stale**
3.  Create the object with non-zero ``default_timeout`` and non-zero ``gc_thread_wait``: This will spawn a garbage collection thread that periodically calls ``collect()`` for you.

.. important::
    Calling ``collect()``, or using the garbage collection thread, is only valid when using a timeout value > 0
