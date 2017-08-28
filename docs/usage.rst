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
