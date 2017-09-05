# pylint: skip-file
from yamicache import Cache

c = Cache()

class App1(object):
    @c.cached()
    def test1(self, argument, power):
        '''running test1'''
        return argument ** power

    @c.clear_cache()
    def test2(self):
        return 0


def test_clear():
    '''Make sure cache gets cleared'''
    a1 = App1()

    assert len(c) == 0

    assert a1.test1(1, 2) == 1
    assert a1.test1(1, 2) == 1
    assert a1.test1(1, 2) == 1
    assert len(c) == 1

    a1.test2()
    assert len(c) == 0


def main():
    test_clear()


if __name__ == '__main__':
    main()
