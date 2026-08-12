"""Collision-resistant Base62 short-code generation for the URL shortener.

Codes are drawn from the full Base62 alphabet using ``secrets`` (CSPRNG) so
they are unpredictable. Uniqueness is enforced at the database level with a
unique constraint; the CRUD layer retries with a fresh code when a collision
is detected.
"""

from __future__ import annotations

import secrets
import string

ALPHABET = string.ascii_letters + string.digits
BASE = len(ALPHABET)
DEFAULT_CODE_LENGTH = 7
MAX_CODE_LENGTH = 32


def encode(num: int) -> str:
    """Encode a non-negative integer as a Base62 string."""
    if num < 0:
        raise ValueError("num must be non-negative")
    if num == 0:
        return ALPHABET[0]
    chars: list[str] = []
    while num > 0:
        num, remainder = divmod(num, BASE)
        chars.append(ALPHABET[remainder])
    return "".join(reversed(chars))


def decode(code: str) -> int:
    """Decode a Base62 string back into an integer."""
    if not code:
        raise ValueError("code must not be empty")
    num = 0
    for char in code:
        num = num * BASE + ALPHABET.index(char)
    return num


def generate_short_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a random Base62 code of the given length."""
    if length <= 0 or length > MAX_CODE_LENGTH:
        raise ValueError("length must be between 1 and 32")
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
