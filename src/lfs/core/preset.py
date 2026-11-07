"""Preset data model and schema validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


Waveform = Literal["sine", "saw", "square", "triangle"]
NoiseType = Literal["white", "pink", "red"]
FilterMode = Literal["lp", "bp", "hp"]
LFOWave = Literal["sine", "tri", "square", "s&h"]


class OscillatorParams(BaseModel):
    waveform: Waveform = "saw"
    fine: float = 0.0
    level: float = Field(0.7, ge=0.0, le=1.0)
    pwm: float = Field(0.5, ge=0.0, le=1.0)


class NoiseParams(BaseModel):
    type: NoiseType = "pink"
    level: float = Field(0.1, ge=0.0, le=1.0)


class FilterParams(BaseModel):
    cutoff: float = Field(0.5, ge=0.0, le=1.0)
    resonance: float = Field(0.3, ge=0.0, le=1.0)
    mode: FilterMode = "lp"


class EnvelopeParams(BaseModel):
    attack: float = Field(0.1, ge=0.0, le=2.0)
    decay: float = Field(0.3, ge=0.0, le=2.0)
    sustain: float = Field(0.7, ge=0.0, le=1.0)
    release: float = Field(0.5, ge=0.0, le=5.0)


class LFOParams(BaseModel):
    rate: float = Field(0.2, ge=0.01, le=20.0)
    depth: float = Field(0.3, ge=0.0, le=1.0)
    waveform: LFOWave = "sine"


class ReverbParams(BaseModel):
    size: float = Field(0.5, ge=0.0, le=1.0)
    damping: float = Field(0.4, ge=0.0, le=1.0)
    mix: float = Field(0.3, ge=0.0, le=1.0)


class ImperfectionParams(BaseModel):
    drift: float = Field(0.15, ge=0.0, le=1.0)
    crosstalk: float = Field(0.1, ge=0.0, le=1.0)
    wobble: float = Field(0.1, ge=0.0, le=1.0)
    jitter: float = Field(0.05, ge=0.0, le=1.0)


class Panel(BaseModel):
    osc1: OscillatorParams = Field(default_factory=OscillatorParams)
    osc2: OscillatorParams = Field(default_factory=OscillatorParams)
    osc3: OscillatorParams = Field(default_factory=OscillatorParams)
    noise: NoiseParams = Field(default_factory=NoiseParams)
    filter: FilterParams = Field(default_factory=FilterParams)
    env: EnvelopeParams = Field(default_factory=EnvelopeParams)
    lfo: LFOParams = Field(default_factory=LFOParams)
    reverb: ReverbParams = Field(default_factory=ReverbParams)
    imperfection: ImperfectionParams = Field(default_factory=ImperfectionParams)


class Metadata(BaseModel):
    created: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    bpm: float = 96.0
    length_sec: float = 60.0


class Preset(BaseModel):
    """Canonical preset contract shared by Audio and Semantic branches."""

    name: str
    panel: Panel = Field(default_factory=Panel)
    matrix: List[List[float]] = Field(
        default_factory=lambda: [[0.0] * 16 for _ in range(16)]
    )
    seed: int = 42
    metadata: Metadata = Field(default_factory=Metadata)

    @field_validator("matrix")
    @classmethod
    def validate_matrix(cls, v: List[List[float]]) -> List[List[float]]:
        if len(v) != 16:
            raise ValueError("matrix must be 16x16")
        for row in v:
            if len(row) != 16:
                raise ValueError("matrix must be 16x16")
            for x in row:
                if not (0.0 <= x <= 1.0):
                    raise ValueError("matrix values must be in [0.0, 1.0]")
        return v

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Preset":
        return cls.model_validate(data)


def example_local_first_signal() -> Preset:
    """Factory for the flagship 'Local-First Signal' preset."""
    matrix = [[0.0] * 16 for _ in range(16)]
    # Osc1, Osc2, Noise → Filter (row 4)
    matrix[4][0] = 0.72
    matrix[4][1] = 0.48
    matrix[4][3] = 0.22
    # LFO → Filter cutoff / PWM (simplified)
    matrix[0][4] = 0.55

    return Preset(
        name="Local-First Signal",
        panel=Panel(
            osc1=OscillatorParams(waveform="saw", fine=-0.07, level=0.68, pwm=0.42),
            osc2=OscillatorParams(waveform="square", fine=0.11, level=0.51, pwm=0.63),
            osc3=OscillatorParams(waveform="triangle", fine=0.03, level=0.39, pwm=0.0),
            noise=NoiseParams(type="pink", level=0.18),
            filter=FilterParams(cutoff=0.34, resonance=0.61, mode="lp"),
            env=EnvelopeParams(attack=0.22, decay=0.41, sustain=0.55, release=0.78),
            lfo=LFOParams(rate=0.19, depth=0.47, waveform="sine"),
            reverb=ReverbParams(size=0.72, damping=0.38, mix=0.41),
            imperfection=ImperfectionParams(drift=0.28, crosstalk=0.15, wobble=0.21, jitter=0.09),
        ),
        matrix=matrix,
        seed=19840915,
        metadata=Metadata(
            tags=["offline", "modular", "local-first", "heartbeat", "tape"],
            bpm=96.0,
            length_sec=60.0,
        ),
    )