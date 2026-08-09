# create a test that test main function in src/client_medcherif/main.py
from src.client_medcherif.main import add, func


def test_func() -> None:
    assert func("salamou alaykom ahabia2i") == "salamou alaykom ahabia2i"


def test_add() -> None:
    assert add(2, 6) == 8
