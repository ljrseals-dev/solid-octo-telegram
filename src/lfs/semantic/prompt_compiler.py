"""Seeded prompt compiler that turns a SonicProfile into Suno-style text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from lfs.core.seed import SeededRNG
from lfs.semantic.classifier import SonicProfile


# Simplified vocabulary banks (full banks would live in assets/vocab/)
GENRE_BY_CHARACTER = {
    "mechanical_warm": ["ambient techno", "IDM", "modular synth", "lo-fi analog"],
    "dark_ambient": ["dark ambient", "drone", "cinematic ambient"],
    "glitchy_fragile": ["glitch", "IDM", "experimental electronica"],
    "focused_resilient": ["ambient techno", "IDM", "focused electronica"],
}

MOOD_BY_ENV = {
    "slow_bloom": ["warm", "mysterious", "resilient", "focused"],
    "percussive": ["mechanical", "driving", "precise"],
    "balanced": ["balanced", "steady", "hypnotic"],
}

TEXTURE_BY_WAVE = {
    "analog_hybrid": ["tape-saturated", "raw analog imperfection", "buzzing", "granular"],
    "soft_harmonic": ["harmonic", "warm", "smooth"],
    "digital_edge": ["bit-crushed", "glitchy", "digital"],
}

ERA_TAGS = {
    "1970s_analog_modern": ["1970s analog", "modern hybrid", "cavernous reverb"],
    "contemporary_modular": ["modular", "contemporary", "clean digital"],
}

PRODUCTION = ["glued", "TR-808 drums", "soft spoken-word vocal"]
EXCLUDE_BASE = [
    "cloud references", "festival EDM drop", "generic pop vocal",
    "internet/network SFX", "corporate tech anthem", "bright supersaw trance"
]


@dataclass
class SunoPrompt:
    title: str
    style: str
    description: str
    lyrics: Optional[str]
    exclude: str
    seed: int
    source_preset: str


def compile_prompt(profile: SonicProfile, lyric_seed: Optional[str] = None) -> SunoPrompt:
    rng = SeededRNG(profile.seed)

    genres = GENRE_BY_CHARACTER.get(profile.character, ["ambient techno", "IDM"])
    moods = MOOD_BY_ENV.get(profile.envelope_shape, ["focused", "warm"])
    textures = TEXTURE_BY_WAVE.get(profile.wave_family, ["granular", "tape-saturated"])
    eras = ERA_TAGS.get(profile.era, ["modern hybrid"])

    style_parts = genres + moods + textures + eras + PRODUCTION
    # deterministic shuffle-ish selection
    selected = []
    for part in style_parts:
        if rng.random() > 0.25 or len(selected) < 8:
            selected.append(part)
    style = ", ".join(dict.fromkeys(selected))  # unique, order-preserving

    # Title
    titles = [
        profile.name or "Untitled Patch",
        "Closed-Loop Heartbeat",
        "Local Weights",
        "Switch Matrix Breathing",
        "Private Universe",
        "Offline Signal",
    ]
    title = rng.choice(titles)

    description = (
        f"A warm, glitchy instrumental about a music AI that runs entirely on-device: "
        f"closed-loop synthesis, local presets, no network, private and resilient. "
        f"Built from modular pulses, tape haze, granular texture, and a steady machine heartbeat."
    )

    # Fixed flagship lyrics for the example preset; otherwise None or generated
    lyrics = None
    if "Local-First" in (profile.name or ""):
        lyrics = """[Verse 1]
No signal in the wire, but the room still sings
Local weights in the dark, folded into strings
Every patch is a promise, every seed is a home
The machine keeps a heartbeat when the network is gone

[Chorus]
Offline, offline, let the loop run free
Private little universe that only listens to me
Offline, offline, warm against the cold
A synthesizer story in a circuit I hold

[Verse 2]
No cloud in the morning, no queue in the night
Just a switch matrix breathing in the analog light
Render me a memory, render me a code
The song stays inside me when the world goes cold"""

    exclude = ", ".join(EXCLUDE_BASE)

    return SunoPrompt(
        title=title,
        style=style,
        description=description,
        lyrics=lyrics,
        exclude=exclude,
        seed=profile.seed,
        source_preset=profile.name,
    )


def prompt_to_text(p: SunoPrompt) -> str:
    lines = [
        f"TITLE: {p.title}",
        "",
        "STYLE:",
        p.style,
        "",
        "DESCRIPTION:",
        p.description,
        "",
    ]
    if p.lyrics:
        lines.extend(["LYRICS:", p.lyrics, ""])
    lines.extend(["EXCLUDE:", p.exclude])
    return "\n".join(lines)