from src.client_by_ahmed.main import add, is_even, reverse_string


def test_add() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_is_even() -> None:
    assert is_even(4) is True
    assert is_even(7) is False


def test_reverse_string() -> None:
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""
