'''
Just a quick test to make sure there's no ``cls`` or ``self`` odness.
'''
from __future__ import print_function
import sys
from yamicache.yamicache import Cache

if sys.version_info[0] == 2:
    range = xrange

c = Cache(prefix='myapp', hashing=False, debug=False)


@c.cached()
def my_func(argument, power):
    '''running my_func'''
    return argument ** power


def test_main():
    assert len(c) == 0

    for _ in [0, 1, 2, 3, 4, 5]:
        my_func(2, 3)

    assert len(c) == 1


if __name__ == '__main__':
    test_main()
