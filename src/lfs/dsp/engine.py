"""Core deterministic DSP render engine (simplified but functional skeleton)."""

from __future__ import annotations

import numpy as np
from typing import Optional

from lfs.core.preset import Preset
from lfs.core.seed import SeededRNG


def _oscillator(t: np.ndarray, freq: float, waveform: str, pwm: float = 0.5) -> np.ndarray:
    phase = (2 * np.pi * freq * t) % (2 * np.pi)
    if waveform == "sine":
        return np.sin(phase)
    elif waveform == "saw":
        return 2.0 * (phase / (2 * np.pi)) - 1.0
    elif waveform == "square":
        return np.where((phase / (2 * np.pi)) < pwm, 1.0, -1.0)
    elif waveform == "triangle":
        p = phase / (2 * np.pi)
        return 1.0 - 4.0 * np.abs(p - 0.5)
    return np.sin(phase)


def _pink_noise(n: int, rng: SeededRNG) -> np.ndarray:
    """Very simple pink-ish noise approximation."""
    white = np.array([rng.normal() for _ in range(n)])
    # crude 1/f filter
    b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
    a = np.array([1, -2.494956002, 2.017265875, -0.522189400])
    from scipy.signal import lfilter
    return lfilter(b, a, white).astype(np.float32)


def render(
    preset: Preset,
    length_sec: Optional[float] = None,
    sample_rate: int = 44100,
) -> np.ndarray:
    """
    Deterministic render of a preset to mono float32 PCM.

    Same preset + same seed → identical samples (within float32 tolerance).
    """
    length_sec = length_sec or preset.metadata.length_sec
    n_samples = int(length_sec * sample_rate)
    t = np.arange(n_samples, dtype=np.float64) / sample_rate

    rng = SeededRNG(preset.seed)
    panel = preset.panel

    # Base frequencies (A3-ish + detune)
    base_freq = 220.0
    f1 = base_freq * (2 ** (panel.osc1.fine / 12.0))
    f2 = base_freq * 1.5 * (2 ** (panel.osc2.fine / 12.0))
    f3 = base_freq * 0.5 * (2 ** (panel.osc3.fine / 12.0))

    o1 = _oscillator(t, f1, panel.osc1.waveform, panel.osc1.pwm) * panel.osc1.level
    o2 = _oscillator(t, f2, panel.osc2.waveform, panel.osc2.pwm) * panel.osc2.level
    o3 = _oscillator(t, f3, panel.osc3.waveform, panel.osc3.pwm) * panel.osc3.level

    if panel.noise.level > 0:
        noise = _pink_noise(n_samples, rng) * panel.noise.level
    else:
        noise = np.zeros(n_samples)

    mix = o1 + o2 + o3 + noise

    # Simple one-pole lowpass as stand-in for state-variable filter
    cutoff = panel.filter.cutoff
    alpha = np.exp(-2 * np.pi * (20 + cutoff * 8000) / sample_rate)
    filtered = np.zeros_like(mix)
    z = 0.0
    for i in range(n_samples):
        z = alpha * z + (1 - alpha) * mix[i]
        filtered[i] = z

    # Simple exponential envelope
    attack = max(panel.env.attack, 1e-4)
    release = max(panel.env.release, 1e-4)
    env = np.ones(n_samples)
    att_samples = int(attack * sample_rate)
    rel_samples = int(release * sample_rate)
    if att_samples > 0:
        env[:att_samples] = np.linspace(0, 1, att_samples)
    if rel_samples > 0 and rel_samples < n_samples:
        env[-rel_samples:] = np.linspace(1, 0, rel_samples)

    out = filtered * env * panel.env.sustain

    # Very light imperfection (deterministic)
    if panel.imperfection.drift > 0:
        drift = 1.0 + panel.imperfection.drift * 0.01 * np.sin(2 * np.pi * 0.07 * t)
        out = out * drift

    # Soft clip
    out = np.tanh(out * 1.2)

    # Normalize
    peak = np.max(np.abs(out)) + 1e-9
    out = (out / peak * 0.89).astype(np.float32)

    return out


def render_to_wav(preset: Preset, path: str, length_sec: float = 60.0, sr: int = 44100) -> None:
    import soundfile as sf
    audio = render(preset, length_sec=length_sec, sample_rate=sr)
    sf.write(path, audio, sr)