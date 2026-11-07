"""Matrix-aware profile extractor (fixes paper §8.1–§8.6)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from lfs.core.preset import Preset


# Closed character set (must match banks)
CHARACTERS = [
    "bass", "acid", "perc", "glitch", "ambient", "pad", "drone", "bell",
    "theremin", "formant", "strings", "brass", "pluck", "sub", "arp",
    "lead", "hoover", "fx",
]


def _wave_energy(panel) -> Dict[str, float]:
    energy = {"sine": 0.0, "saw": 0.0, "square": 0.0, "triangle": 0.0, "noise": 0.0}
    for osc in (panel.osc1, panel.osc2, panel.osc3):
        energy[osc.waveform] = energy.get(osc.waveform, 0.0) + osc.level
    energy["noise"] += panel.noise.level
    return energy


def _matrix_summary(matrix: List[List[float]]) -> Dict[str, Any]:
    """Convert 16×16 weighted matrix into the profile matrix block."""
    # Simplified source/target names for the 16 slots
    sources = [
        "OSC1", "OSC2", "OSC3", "NOISE", "ENV", "LFO", "RING", "S&H",
        "JOY_X", "JOY_Y", "MOD_WHEEL", "PITCH_WHEEL", "KEY_CV",
        "TRIGGER", "FILTER", "REVERB",
    ]
    targets = [
        "FILTER_FREQ", "FILTER_RES", "VCA1", "VCA2", "REVERB_MIX", "PAN",
        "OUT_L", "OUT_R", "ENV_TRIG", "ENV_GATE", "LFO_RESET",
        "OSC1_PWM", "OSC2_PWM", "OSC3_PWM", "FM", "AUX",
    ]

    pin_count = 0
    total_depth = 0.0
    src_acc = {s: 0.0 for s in sources}
    tgt_acc = {t: 0.0 for t in targets}
    modulated = []
    audio_rate = False

    for d, row in enumerate(matrix):
        for s, level in enumerate(row):
            if level > 0.01:
                pin_count += 1
                total_depth += level
                if s < len(sources):
                    src_acc[sources[s]] += level
                if d < len(targets):
                    tgt_acc[targets[d]] += level
                    if targets[d] not in modulated:
                        modulated.append(targets[d])
                # Heuristic: LFO or ENV → filter/pitch is audio-rate-ish
                if s in (4, 5) and d < 4:
                    audio_rate = True

    return {
        "pin_count": pin_count,
        "total_depth": round(total_depth, 4),
        "targets": tgt_acc,
        "sources": src_acc,
        "modulated": modulated,
        "audio_rate_mod": audio_rate,
    }


def extract_profile(preset: Preset) -> Dict[str, Any]:
    """
    Stage 1 profile extraction.
    Fixes:
      §8.1 – closed sets only, no dead keys
      §8.2 – drone / droning ordered before ambient / padded
      §8.3 – non-strict boundaries documented
      §8.5 / §8.6 – matrix features + wave_energy accumulation
    """
    p = preset.panel
    energy = _wave_energy(p)
    # Dominant wave: argmax, noise wins if level > 0.4
    if p.noise.level > 0.4:
        wave = "noise"
    else:
        wave = max(
            ("sine", "saw", "square", "triangle"),
            key=lambda w: energy[w],
        )

    # Envelope – order matters (drone before pad)
    # Boundaries use >= / <= as documented
    att = p.env.attack
    rel = p.env.release
    sus = p.env.sustain
    if att >= 0.6 and rel >= 0.8 and sus >= 0.7:          # §8.3: >= side
        envelope = "droning"                               # evaluated first
        rule = "droning:att>=0.6,rel>=0.8,sus>=0.7"
    elif att <= 0.08 and rel <= 0.25:                     # §8.3: <= side
        envelope = "percussive"
        rule = "percussive:att<=0.08,rel<=0.25"
    elif att <= 0.12 and sus <= 0.4:
        envelope = "plucky"
        rule = "plucky:att<=0.12,sus<=0.4"
    elif att <= 0.05 and sus <= 0.3:
        envelope = "stabbing"
        rule = "stabbing:att<=0.05,sus<=0.3"
    elif att >= 0.25 and sus >= 0.6:
        envelope = "padded"
        rule = "padded:att>=0.25,sus>=0.6"
    else:
        envelope = "sustained"
        rule = "sustained:fallback"

    # Character – order matters; hoover & fx wired explicitly (before lead)
    res = p.filter.resonance
    noise = p.noise.level
    lfo_rate = p.lfo.rate
    lfo_wave = p.lfo.waveform
    reverb = p.reverb.mix
    cutoff = p.filter.cutoff

    # fx first (high noise + S&H or slow LFO + reverb)
    if noise > 0.3 and (lfo_wave == "s&h" or lfo_rate < 0.5) and reverb > 0.5:
        character = "fx"
        rule_c = "fx:noise>0.3 + (s&h or rate<0.5) + reverb>0.5"
    # hoover: multi-saw + high resonance + mid LFO
    elif (
        p.osc1.waveform == "saw"
        and p.osc2.waveform == "saw"
        and p.osc3.waveform == "saw"
        and res > 0.6
        and 5.0 <= lfo_rate <= 9.0
    ):
        character = "hoover"
        rule_c = "hoover:3x saw + res>0.6 + lfo 5-9"
    # drone before ambient (fix §8.2)
    elif cutoff < 0.35 and reverb > 0.55 and att >= 0.4:
        character = "drone"
        rule_c = "drone:cutoff<0.35 + reverb>0.55 + att>=0.4"
    elif cutoff < 0.45 and reverb > 0.4:
        character = "ambient"
        rule_c = "ambient:cutoff<0.45 + reverb>0.4"
    elif noise > 0.25:
        character = "glitch"
        rule_c = "glitch:noise>0.25"
    elif res > 0.7 and p.osc1.waveform in ("saw", "square"):
        character = "acid"
        rule_c = "acid:res>0.7 + saw/square"
    elif p.osc1.level > 0.7 and p.osc1.waveform == "sine" and cutoff < 0.3:
        character = "sub"
        rule_c = "sub:sine + low cutoff"
    elif energy["saw"] > 0.9 and lfo_rate > 4:
        character = "arp"
        rule_c = "arp:high saw energy + fast lfo"
    else:
        character = "lead"
        rule_c = "lead:fallback"

    # Era
    if p.imperfection.drift > 0.2 and p.reverb.size > 0.55:
        era = "lo-fi analog"
    elif res > 0.65 and p.osc1.waveform in ("saw", "square"):
        era = "acid analog"
    else:
        era = "analog"

    matrix = _matrix_summary(preset.matrix)

    return {
        "character": character,
        "envelope": envelope,
        "wave": wave,
        "era": era,
        "cutoff": round(20 + cutoff * 8000, 1),  # Hz approx
        "resonance": round(res * 100, 1),
        "attack": att,
        "release": rel,
        "reverb": reverb,
        "lfo_rate": lfo_rate,
        "drift": p.imperfection.drift,
        "killer_mode": p.imperfection.drift > 0.2 or p.imperfection.wobble > 0.15,
        "wave_energy": {k: round(v, 3) for k, v in energy.items()},
        "matrix": matrix,
        "rule_fired": f"{rule_c} | {rule}",
        "name": preset.name,
        "seed": preset.seed,
    }