from src.plot.utilities.padding import pad


def test_pad_with_shorter_list():
    lst = [1, 2, 3]
    length = 5
    padded_list = pad(lst, length)
    assert len(padded_list) == length
    assert padded_list[: len(lst)] == lst

    # Check that the padded values are NaN
    assert all(isinstance(x, float) and x != x for x in padded_list[len(lst) :])


def test_pad_with_equal_length():
    lst = [1, 2, 3]
    length = 3
    expected = [1, 2, 3]
    assert pad(lst, length) == expected


def test_pad_with_longer_list():
    lst = [1, 2, 3, 4, 5]
    length = 3
    expected = [1, 2, 3, 4, 5]
    assert pad(lst, length) == expected
