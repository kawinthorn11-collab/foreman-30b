"""Checks two small functions; input must first be manually reviewed."""
import unittest

def check_functions(clamp, deduplicate):
    cases = [(-1, 0, 10, 0), (5, 0, 10, 5), (11, 0, 10, 10), (3, 3, 3, 3)]
    for value, low, high, expected in cases:
        assert clamp(value, low, high) == expected
    try:
        clamp(1, 5, 0)
    except ValueError:
        pass
    else:
        raise AssertionError('Reversed bounds must raise ValueError')
    for original, expected in [([], []), ([3, 1, 3, 2, 1], [3, 1, 2]), (['a', 'a', 'b'], ['a', 'b']), ([(1,), (1,), (2,)], [(1,), (2,)])]:
        before = original.copy()
        assert deduplicate(original) == expected
        assert original == before
    return 13
