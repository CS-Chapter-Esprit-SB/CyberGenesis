# create a test that test main function in src/client_youssefzou/main.py
from src.client_youssefzou.main import func, multiply


def test_func() -> None:
    assert func("hello") == "hello"


def test_multiply() -> None:
    assert multiply(2, 3) == 6
