import pytest

import locations

if __name__ == "__main__":
    pytest.main([__file__, '-s', "-v"])


def test_combine():
    assert locations.combine([], 1) == []
    assert locations.combine([], 0) == [[]]
    assert locations.combine([1], 1) == [[1]]
    assert locations.combine([1, 2], 1) == [[1], [2]]
    assert locations.combine([1, 2], 2) == [[1, 2]]
    assert locations.combine([1, 2, 3], 2) == [[1, 2], [2, 3]]
    assert locations.combine([1, 2, 3, 4, 5], 3) == [[1, 2, 3], [2, 3, 4], [3, 4, 5]]


def test_string_combinations():
    assert locations.string_combinations("", 0) == None
    assert locations.string_combinations("1", 0) == None
    assert locations.string_combinations("1", 1) == ["1"]
    assert locations.string_combinations("1 2", 1) == ['1', '2']
    assert locations.string_combinations("1 2", 2) == ['1 2']
    assert locations.string_combinations("1 2 3", 1) == ["1", "2", "3"]
    assert locations.string_combinations("1 2 3", 2) == ["1 2", "2 3"]
    assert locations.string_combinations("1 2 3", 3) == ["1 2 3"]


def test_string_found():
    assert locations.string_found("asdf", "asdf g") == True
    assert locations.string_found("asdf", "as") == False
