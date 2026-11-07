"""Coherence constraint engine (rules C1–C9). Filters pools before draw."""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from lfs.semantic.bank_loader import BankSet


class CoherenceEngine:
    def __init__(self, banks: BankSet):
        self.banks = banks
        self.waivers: List[str] = []

    def reset_waivers(self) -> None:
        self.waivers = []

    def filter_pool(
        self,
        pool: List[str],
        profile: Dict[str, Any],
        bpm: int,
        already_chosen: List[str],
        context: str,
    ) -> List[str]:
        """Apply all applicable rules; return filtered pool (or original + waiver)."""
        original = list(pool)
        filtered = list(pool)

        # C8: exclusive pairs
        exclusive = self._collect_exclusive_pairs()
        for a, b in exclusive:
            if a in already_chosen and b in filtered:
                filtered = [t for t in filtered if t != b]
            if b in already_chosen and a in filtered:
                filtered = [t for t in filtered if t != a]

        # C1: lo-fi analog drum restriction
        if profile.get("era") == "lo-fi analog" and context == "instrument":
            lofi = set(
                self.banks.bank("ERA_TAGS").coherence.get("lofi_drums", [])
            )
            # Keep only flavours that mention allowed drums or are non-drum
            filtered = [
                t for t in filtered
                if any(d in t for d in lofi) or "drums" not in t
            ]

        # C2: acid analog requires acid production tags (handled at production draw)
        if profile.get("era") == "acid analog" and context == "production":
            required = set(
                self.banks.bank("ERA_TAGS").coherence.get("acid_era_production", [])
            )
            # Prefer tags that satisfy; if none left, waiver later
            preferred = [t for t in filtered if t in required]
            if preferred:
                filtered = preferred

        # C3: low BPM excludes four-on-floor
        if bpm < 70 and context == "instrument":
            filtered = [t for t in filtered if "four_on_floor" not in
                        self.banks.bank("INSTRUMENT_FLAVOURS").coherence.get("tags", {}).get(t, [])]

        # C4: droning excludes percussive instruments
        if profile.get("envelope") == "droning" and context == "instrument":
            excl = self.banks.bank("INSTRUMENT_FLAVOURS").coherence.get("droning_exclusions", [])
            filtered = [t for t in filtered if t not in excl]

        # C5: envelope exclusions for structure
        if context == "structure":
            env = profile.get("envelope", "")
            excl_map = self.banks.bank("STRUCTURE_HINTS").coherence.get("envelope_exclusions", {})
            excl = excl_map.get(env, [])
            filtered = [t for t in filtered if t not in excl]

        # C6: drone/ambient exclude hardcore/drill genres
        if context == "genre":
            char = profile.get("character", "")
            if char in ("drone", "ambient"):
                excl = self.banks.bank("GENRE_BY_CHARACTER").coherence.get(
                    f"{char}_excluded_genres", []
                )
                filtered = [t for t in filtered if t not in excl]

        # C7: sub requires low-tempo subset
        if context == "genre" and profile.get("character") == "sub":
            subset = (
                self.banks.bank("GENRE_BY_CHARACTER")
                .coherence.get("low_tempo_subset", {})
                .get("sub", [])
            )
            preferred = [t for t in filtered if t in subset]
            if preferred:
                filtered = preferred

        # C9: audio-rate mod
        if profile.get("matrix", {}).get("audio_rate_mod") and context == "production":
            adds = self.banks.bank("PRODUCTION_TAGS").coherence.get("audio_rate_mod_adds", [])
            removes = self.banks.bank("PRODUCTION_TAGS").coherence.get("audio_rate_mod_removes", [])
            filtered = [t for t in filtered if t not in removes]
            # Ensure at least one add is possible
            for a in adds:
                if a not in filtered and a in original:
                    filtered.append(a)

        if not filtered:
            self.waivers.append(f"{context}:empty_pool_after_filter")
            return original
        return filtered

    def _collect_exclusive_pairs(self) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for name in self.banks.names():
            coh = self.banks.bank(name).coherence
            for p in coh.get("exclusive_pairs", []):
                if len(p) == 2:
                    pairs.append((p[0], p[1]))
        return pairs