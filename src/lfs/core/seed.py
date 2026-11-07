"""Deterministic seeded PRNG for reproducible audio and prompts."""

from __future__ import annotations

import hashlib
import struct
from typing import Iterator

import numpy as np


class SeededRNG:
    """Simple deterministic RNG based on a 64-bit seed.

    Guarantees: same seed → identical sequence on all platforms.
    """

    def __init__(self, seed: int):
        self.seed = int(seed) & 0xFFFFFFFFFFFFFFFF
        self._state = self.seed

    def _next(self) -> int:
        # xorshift64*
        x = self._state
        x ^= (x >> 12) & 0xFFFFFFFFFFFFFFFF
        x ^= (x << 25) & 0xFFFFFFFFFFFFFFFF
        x ^= (x >> 27) & 0xFFFFFFFFFFFFFFFF
        self._state = x & 0xFFFFFFFFFFFFFFFF
        return (x * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF

    def random(self) -> float:
        """Uniform [0, 1)."""
        return (self._next() >> 11) / float(1 << 53)

    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        return low + (high - low) * self.random()

    def randint(self, low: int, high: int) -> int:
        """Inclusive low, exclusive high."""
        return low + int(self.random() * (high - low))

    def choice(self, seq):
        return seq[self.randint(0, len(seq))]

    def normal(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        # Box-Muller
        u1 = max(self.random(), 1e-12)
        u2 = self.random()
        z = np.sqrt(-2.0 * np.log(u1)) * np.cos(2 * np.pi * u2)
        return mu + sigma * z

    def bytes(self, n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            out.extend(struct.pack("<Q", self._next()))
        return bytes(out[:n])


def seed_from_string(s: str) -> int:
    """Derive a stable 64-bit seed from a string."""
    h = hashlib.sha256(s.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "little")