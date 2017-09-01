import pytest
from yamicache.yamicache import Cache


def test_object_creation():
    with pytest.raises(ValueError):
        Cache(default_timeout=0.5)


def test_function():
    c = Cache()

    with pytest.raises(ValueError):

        @c.cached(timeout=0.5)
        def t1():
            pass
