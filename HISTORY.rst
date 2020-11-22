=======
History
=======

0.6.0 (2020-11-22)
------------------

* Remove support for Python 2.


0.5.1 (2018-04-10)
------------------

* Fix #8: Function default arguments were not handled.  There was also a
  potential cache miss if Python changed the order of `dict` keys.


0.5.0 (2018-03-23)
------------------

* Fix #7: Timed-out values are not returned when refreshed


0.4.0 (2017-10-09)
------------------

* Added ``serialize()`` and ``deserialize()``


0.3.0 (2017-09-05)
------------------

* Added ``@clear_cache()`` decorator
* Added imports to allow for ``from yamicache import Cache``


0.2.0 (2017-09-03)
------------------

* Added cache key collision checking


0.1.1 (2017-09-01)
------------------

* Fix #1: ``Cache.cached()`` ignores ``timeout`` parameter


0.1.0 (2017-08-28)
------------------

* First release on PyPI.
