# create a test that test main function in src/client_example/main.py
from src.client_example.main import func, multiply


def test_func() -> None:
    assert func("hello") == "hello"


def test_multiply() -> None:
    assert multiply(2, 3) == 6
