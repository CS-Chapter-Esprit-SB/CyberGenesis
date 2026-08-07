from src.data_management_by_malek import normalize_label, total_values


def test_normalize_label() -> None:
    assert normalize_label("  Data  ") == "data"


def test_total_values() -> None:
    assert total_values([1, 2, 3]) == 6
