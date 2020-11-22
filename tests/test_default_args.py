from __future__ import print_function
from pprint import pprint as pp
from yamicache import Cache


c = Cache(hashing=False)


@c.cached()
def function1(argument, power=4, addition=0, division=2):
    return argument ** power + addition / division


def test_main():
    """use default args"""

    # `function1` uses default arguments.  These calls are all equivalent, so
    # there should only be 1 item in cache.
    function1(1)
    function1(1, 4)
    function1(1, 4, 0)
    function1(1, 4, addition=0, division=2)

    assert len(c) == 1

    pp(c._data_store)


def main():
    test_main()


if __name__ == "__main__":
    main()
