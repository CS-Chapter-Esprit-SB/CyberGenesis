# create a test that test main function in src/client_example/main.py
from src.client_example.main import func


def test_func() -> None:
    assert func("hello") == "hello"
