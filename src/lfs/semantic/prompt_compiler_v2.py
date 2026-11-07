"""Deterministic, coherence-aware prompt compiler (full bank-driven)."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from lfs.semantic.bank_loader import BankSet, load_all
from lfs.semantic.coherence import CoherenceEngine
from lfs.semantic.killer_bridge import extract_profile
from lfs.core.preset import Preset


def _seed_for_variant(global_seed: int, preset_name: str, variant_i: int) -> int:
    raw = f"{global_seed}|{preset_name}|{variant_i}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def compile_variants(
    preset: Preset,
    banks: BankSet,
    n_variants: int = 3,
    global_seed: int = 0,
    with_lyrics: bool = False,
) -> List[Dict[str, Any]]:
    profile = extract_profile(preset)
    engine = CoherenceEngine(banks)
    results = []

    for i in range(n_variants):
        engine.reset_waivers()
        seed_i = _seed_for_variant(global_seed, preset.name, i)
        rng = random.Random(seed_i)

        def draw(pool: List[str], k: int = 1) -> List[str]:
            if not pool:
                return []
            return rng.sample(pool, min(k, len(pool)))

        chosen: List[str] = []

        # 1. Genres
        g_pool = banks.bank("GENRE_BY_CHARACTER").for_key(profile["character"])
        g_pool = engine.filter_pool(g_pool, profile, 100, chosen, "genre")
        genres = draw(g_pool, 2)
        chosen.extend(genres)

        # 2. Moods
        m_pool = banks.bank("MOOD_BY_ENV").for_key(profile["envelope"])
        moods = draw(m_pool, 2)
        chosen.extend(moods)

        # 3. Textures
        t_pool = banks.bank("TEXTURE_BY_WAVE").for_key(profile["wave"])
        t_pool = engine.filter_pool(t_pool, profile, 100, chosen, "texture")
        textures = draw(t_pool, 2)
        chosen.extend(textures)

        # 4. Era tag
        e_pool = banks.bank("ERA_TAGS").for_key(profile["era"])
        era_tag = draw(e_pool, 1)
        chosen.extend(era_tag)

        # Tempo first (needed for later filters)
        tempo_range = banks.bank("TEMPO_BY_CHARACTER").for_key(profile["character"])
        bpm = rng.randint(int(tempo_range[0]), int(tempo_range[1]))

        # 5. Production
        p_pool = banks.bank("PRODUCTION_TAGS").for_key("all")
        p_pool = engine.filter_pool(p_pool, profile, bpm, chosen, "production")
        production = draw(p_pool, 2)
        chosen.extend(production)

        # 6. Instrument flavour
        i_pool = banks.bank("INSTRUMENT_FLAVOURS").for_key("all")
        i_pool = engine.filter_pool(i_pool, profile, bpm, chosen, "instrument")
        instrument = draw(i_pool, 1)
        chosen.extend(instrument)

        # 7. Structure
        s_pool = banks.bank("STRUCTURE_HINTS").for_key("all")
        s_pool = engine.filter_pool(s_pool, profile, bpm, chosen, "structure")
        structure = draw(s_pool, 1)
        chosen.extend(structure)

        # Conditional appends
        extras = []
        if profile["reverb"] > 0.3:
            extras.append("cavernous reverb")
        if profile["killer_mode"]:
            extras.append("raw analog imperfection")
        if profile["matrix"]["modulated"]:
            extras.append("modulated filter")

        # Title
        title = preset.name
        if "TITLE_BANKS" in banks.names():
            tb = banks.bank("TITLE_BANKS").values
            tmpl = rng.choice(tb["templates"])
            title = tmpl.format(
                adjective=rng.choice(tb["adjectives"]),
                noun=rng.choice(tb["nouns"]),
                place=rng.choice(tb["places"]),
                time=rng.choice(tb["times"]),
                verb=rng.choice(tb["verbs"]),
                abstract=rng.choice(tb["abstracts"]),
                number=rng.choice(tb["numbers"]),
            ).title()

        # Style assembly (fixed order)
        style_parts = (
            genres
            + era_tag
            + moods
            + textures
            + instrument
            + [f"{bpm} BPM"]
            + production
            + structure
            + extras
        )
        # Unique, preserve order, proper-case a few known terms
        seen = set()
        style_clean = []
        for t in style_parts:
            if t not in seen:
                seen.add(t)
                if t.startswith("with tr-"):
                    style_clean.append(t.replace("tr-808", "TR-808").replace("tr-909", "TR-909"))
                else:
                    style_clean.append(t)
        style = ", ".join(style_clean)

        description = (
            f"{profile['era']} {profile['character']} with a {profile['envelope']} "
            f"envelope and {profile['wave']} tone, cutoff {profile['cutoff']} Hz, "
            f"resonance {profile['resonance']}%, {structure[0] if structure else 'loop-based'}."
        )

        lyrics = None
        if with_lyrics and "LYRIC_BANKS" in banks.names():
            lb = banks.bank("LYRIC_BANKS").values
            v1, v2 = rng.sample(lb["verse_lines"], 2)
            ch = rng.choice(lb["chorus_lines"])
            lyrics = f"[Verse]\n{v1}\n{v2}\n\n[Chorus]\n{ch}"

        results.append({
            "title": title,
            "style": style,
            "description": description,
            "lyrics": lyrics,
            "exclude": "cloud references, festival EDM drop, generic pop vocal, internet/network SFX, corporate tech anthem, bright supersaw trance",
            "seed": seed_i,
            "variant": i,
            "source_preset": preset.name,
            "character": profile["character"],
            "envelope": profile["envelope"],
            "wave": profile["wave"],
            "era": profile["era"],
            "bpm": bpm,
            "structure": structure[0] if structure else None,
            "rule_fired": profile["rule_fired"],
            "coherence_waivers": list(engine.waivers),
            "matrix_summary": {
                "pin_count": profile["matrix"]["pin_count"],
                "total_depth": profile["matrix"]["total_depth"],
                "audio_rate_mod": profile["matrix"]["audio_rate_mod"],
            },
            "banks_hash": banks.banks_hash,
        })

    return results


def export_prompts(
    prompts: List[Dict[str, Any]],
    out_dir: Path,
    formats: List[str] = None,
) -> None:
    formats = formats or ["json", "txt", "csv"]
    out_dir.mkdir(parents=True, exist_ok=True)

    if "json" in formats:
        payload = {
            "schema_version": "1.0.0",
            "seed": prompts[0]["seed"] if prompts else 0,
            "banks_hash": prompts[0]["banks_hash"] if prompts else "",
            "prompts": prompts,
        }
        (out_dir / "suno_prompts.json").write_text(json.dumps(payload, indent=2))

    if "txt" in formats:
        blocks = []
        for p in prompts:
            block = [
                f"TITLE: {p['title']}",
                "",
                "STYLE:",
                p["style"],
                "",
                "DESCRIPTION:",
                p["description"],
            ]
            if p.get("lyrics"):
                block.extend(["", "LYRICS:", p["lyrics"]])
            block.extend(["", "EXCLUDE:", p["exclude"], "", "---", ""])
            blocks.append("\n".join(block))
        (out_dir / "suno_prompts.txt").write_text("\n".join(blocks))

    if "csv" in formats:
        import csv
        with open(out_dir / "suno_prompts.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "title", "style", "source_preset", "character", "envelope",
                    "wave", "era", "bpm", "structure", "description",
                ],
            )
            w.writeheader()
            for p in prompts:
                w.writerow({k: p.get(k) for k in w.fieldnames})