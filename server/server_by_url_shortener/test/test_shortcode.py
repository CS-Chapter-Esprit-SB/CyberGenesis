"""Unit tests for the Base62 short-code utilities."""

from __future__ import annotations

import pytest
from server_by_url_shortener.shortcode import (
    ALPHABET,
    DEFAULT_CODE_LENGTH,
    MAX_CODE_LENGTH,
    decode,
    encode,
    generate_short_code,
)


@pytest.mark.parametrize(
    "num",
    [0, 1, 61, 62, 63, 3844, 2**31 - 1, 2**63 - 1],
)
def test_encode_decode_roundtrip(num: int) -> None:
    assert decode(encode(num)) == num


def test_encode_zero() -> None:
    assert encode(0) == ALPHABET[0]


def test_encode_sixty_two() -> None:
    assert encode(62) == ALPHABET[1] + ALPHABET[0]


def test_encode_negative_raises() -> None:
    with pytest.raises(ValueError):
        encode(-1)


def test_decode_empty_raises() -> None:
    with pytest.raises(ValueError):
        decode("")


def test_generate_short_code_default_length() -> None:
    code = generate_short_code()
    assert len(code) == DEFAULT_CODE_LENGTH
    assert all(char in ALPHABET for char in code)


def test_generate_short_code_uses_full_alphabet() -> None:
    assert len(ALPHABET) == 62


def test_generate_short_code_produces_distinct_codes() -> None:
    codes = {generate_short_code() for _ in range(2000)}
    assert len(codes) == 2000


def test_generate_short_code_invalid_length_raises() -> None:
    with pytest.raises(ValueError):
        generate_short_code(0)
    with pytest.raises(ValueError):
        generate_short_code(MAX_CODE_LENGTH + 1)
