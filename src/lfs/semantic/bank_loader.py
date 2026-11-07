"""Load and validate external vocabulary banks. Offline only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REQUIRED_BANKS = [
    "GENRE_BY_CHARACTER",
    "MOOD_BY_ENV",
    "TEXTURE_BY_WAVE",
    "TEMPO_BY_CHARACTER",
    "ERA_TAGS",
    "PRODUCTION_TAGS",
    "INSTRUMENT_FLAVOURS",
    "STRUCTURE_HINTS",
]

CHARACTER_KEYS = {
    "bass", "acid", "perc", "glitch", "ambient", "pad", "drone", "bell",
    "theremin", "formant", "strings", "brass", "pluck", "sub", "arp",
    "lead", "hoover", "fx",
}
ENVELOPE_KEYS = {"padded", "percussive", "plucky", "droning", "stabbing", "sustained"}
WAVE_KEYS = {"sine", "saw", "square", "triangle", "noise"}
ERA_KEYS = {"lo-fi analog", "acid analog", "analog"}


class BankValidationError(Exception):
    pass


class Bank:
    def __init__(self, data: Dict[str, Any], path: Path):
        self.data = data
        self.path = path
        self.name = data["bank"]
        self.keyed_by = data["keyed_by"]
        self.values = data["values"]
        self.coherence = data.get("coherence", {})
        self.notes = data.get("notes", "")

    def for_key(self, key: str) -> List[Any]:
        if self.keyed_by == "none":
            return list(self.values.get("all", []))
        if key not in self.values:
            raise KeyError(f"Bank {self.name} has no key '{key}'")
        return list(self.values[key])

    def pool(self) -> List[Any]:
        if self.keyed_by == "none":
            return list(self.values.get("all", []))
        out: List[Any] = []
        for v in self.values.values():
            out.extend(v)
        return out


class BankSet:
    def __init__(self, banks: Dict[str, Bank], banks_hash: str):
        self._banks = banks
        self.banks_hash = banks_hash

    def bank(self, name: str) -> Bank:
        if name not in self._banks:
            raise KeyError(f"Bank not loaded: {name}")
        return self._banks[name]

    def names(self) -> List[str]:
        return sorted(self._banks.keys())


def _validate_bank(data: Dict[str, Any], path: Path) -> None:
    if data.get("schema_version") != "1.0.0":
        raise BankValidationError(f"{path}: schema_version must be 1.0.0")
    if data.get("bank") != path.stem:
        raise BankValidationError(f"{path}: bank field must equal filename stem '{path.stem}'")
    keyed = data.get("keyed_by")
    if keyed not in ("character", "envelope", "wave", "era", "none"):
        raise BankValidationError(f"{path}: invalid keyed_by '{keyed}'")
    values = data.get("values")
    if not isinstance(values, dict) or not values:
        raise BankValidationError(f"{path}: values must be non-empty object")

    # Closed-set coverage
    expected = None
    if keyed == "character":
        expected = CHARACTER_KEYS
    elif keyed == "envelope":
        expected = ENVELOPE_KEYS
    elif keyed == "wave":
        expected = WAVE_KEYS
    elif keyed == "era":
        expected = ERA_KEYS

    if expected is not None:
        actual = set(values.keys())
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            raise BankValidationError(
                f"{path}: key coverage mismatch. missing={missing} extra={extra}"
            )

    # No empty lists, no duplicate tags, charset
    for k, v in values.items():
        if not isinstance(v, list) or len(v) == 0:
            raise BankValidationError(f"{path}: values['{k}'] must be non-empty list")
        if keyed != "none" and isinstance(v[0], str):
            if len(v) != len(set(v)):
                raise BankValidationError(f"{path}: duplicate tags in values['{k}']")
            for tag in v:
                if not isinstance(tag, str) or "," in tag or not tag.isascii() or tag != tag.lower():
                    raise BankValidationError(
                        f"{path}: tag '{tag}' must be lowercase ASCII without commas"
                    )


def load_all(banks_dir: Path | str) -> BankSet:
    banks_dir = Path(banks_dir)
    if not banks_dir.is_dir():
        raise BankValidationError(f"Banks directory not found: {banks_dir}")

    loaded: Dict[str, Bank] = {}
    hash_parts: List[str] = []

    for name in REQUIRED_BANKS:
        path = banks_dir / f"{name}.json"
        if not path.exists():
            raise BankValidationError(f"Required bank missing: {path}")
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        _validate_bank(data, path)
        loaded[name] = Bank(data, path)
        hash_parts.append(f"{name}:{hashlib.sha256(raw.encode()).hexdigest()}")

    # Optional banks
    for opt in ("TITLE_BANKS", "LYRIC_BANKS"):
        path = banks_dir / f"{opt}.json"
        if path.exists():
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            _validate_bank(data, path)
            loaded[opt] = Bank(data, path)
            hash_parts.append(f"{opt}:{hashlib.sha256(raw.encode()).hexdigest()}")

    banks_hash = hashlib.sha256("|".join(sorted(hash_parts)).encode()).hexdigest()
    return BankSet(loaded, banks_hash)