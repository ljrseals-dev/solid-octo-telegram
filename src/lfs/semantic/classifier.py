"""Matrix-aware sonic profile classifier (rule-based skeleton)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from lfs.core.preset import Preset


@dataclass
class SonicProfile:
    character: str
    envelope_shape: str
    wave_family: str
    era: str
    features: Dict[str, float] = field(default_factory=dict)
    matrix_mod_depth: float = 0.0
    matrix_targets: List[str] = field(default_factory=list)
    seed: int = 0
    name: str = ""


def _matrix_activity(matrix: List[List[float]]) -> tuple[float, List[str]]:
    total = 0.0
    targets = []
    dest_names = [
        "osc1_pitch", "osc2_pitch", "osc3_pitch", "noise",
        "filter", "vca", "reverb", "lfo", "env", "pwm1", "pwm2",
        "fm", "ring", "aux1", "aux2", "feedback"
    ]
    for d, row in enumerate(matrix):
        row_sum = sum(row)
        if row_sum > 0.05:
            total += row_sum
            if d < len(dest_names):
                targets.append(dest_names[d])
    return total, targets


def classify(preset: Preset) -> SonicProfile:
    """Extract a sonic profile that drives the prompt compiler."""
    p = preset.panel
    mod_depth, targets = _matrix_activity(preset.matrix)

    # Character heuristics
    if mod_depth > 1.5 and p.imperfection.drift > 0.2:
        character = "mechanical_warm"
    elif p.filter.cutoff < 0.4 and p.reverb.mix > 0.35:
        character = "dark_ambient"
    elif p.noise.level > 0.25:
        character = "glitchy_fragile"
    else:
        character = "focused_resilient"

    # Envelope shape
    if p.env.attack > 0.3 and p.env.release > 0.6:
        env_shape = "slow_bloom"
    elif p.env.attack < 0.1:
        env_shape = "percussive"
    else:
        env_shape = "balanced"

    # Wave family
    waves = {p.osc1.waveform, p.osc2.waveform, p.osc3.waveform}
    if "saw" in waves and "square" in waves:
        wave_family = "analog_hybrid"
    elif "sine" in waves or "triangle" in waves:
        wave_family = "soft_harmonic"
    else:
        wave_family = "digital_edge"

    # Era
    if p.imperfection.drift > 0.2 and p.reverb.size > 0.6:
        era = "1970s_analog_modern"
    else:
        era = "contemporary_modular"

    features = {
        "cutoff": p.filter.cutoff,
        "resonance": p.filter.resonance,
        "attack": p.env.attack,
        "release": p.env.release,
        "reverb_mix": p.reverb.mix,
        "lfo_depth": p.lfo.depth,
        "drift": p.imperfection.drift,
        "noise": p.noise.level,
    }

    return SonicProfile(
        character=character,
        envelope_shape=env_shape,
        wave_family=wave_family,
        era=era,
        features=features,
        matrix_mod_depth=mod_depth,
        matrix_targets=targets,
        seed=preset.seed,
        name=preset.name,
    )