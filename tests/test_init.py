from __future__ import print_function
from yamicache import Cache
from yamicache.yamicache import INIT_CACHE_VALUE

c = Cache(hashing=False)


class MyApp(object):
    @c.cached(key="test1")
    def test1(self, argument, power):
        """running test1"""
        return argument ** power

    @c.cached(key="test2")
    def test2(self):
        """running test2"""
        return 1

    @c.cached(key="test3")
    def test3(self, argument, power):
        """running test3"""
        return argument ** power


def test_init_cache():
    a = MyApp()

    for _ in range(10):
        a.test1(8, 0)
        a.test2()

    assert a.test2() == 1

    print(c.dump())
    assert len(c) == 2

    # test3 should be initialized, but not cached
    assert c._data_store["test3"] == INIT_CACHE_VALUE
    assert len(c._data_store) == 3
    assert "test3" not in c


def main():
    test_init_cache()


if __name__ == "__main__":
    main()
