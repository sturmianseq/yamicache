from __future__ import print_function
import pytest
from yamicache import Cache

c = Cache(prefix='myapp', hashing=False, debug=False)


class App1(object):
    @c.cached()
    def test1(self, argument, power):
        '''running test1'''
        return argument ** power

    @c.cached(key='test')
    def test2(self):
        return 0


class App2(object):
    @c.cached()
    def test1(self, argument, power):
        '''running test1'''
        return argument ** power


def test_avoid_collision():
    '''Make sure cache keys don't collide'''
    a1 = App1()
    a2 = App2()

    assert len(c) == 0

    a1.test1(1, 2)
    assert len(c) == 1

    a2.test1(1, 2)
    assert len(c) == 2
    print(c.dump())


def test_raises():
    '''Ensure same key raises ValueError'''

    with pytest.raises(ValueError):
        @c.cached(key='test')
        def test2(self):
            return 0


def main():
    test_raises()


if __name__ == '__main__':
    main()
