# Technical Architecture — Local-First Signal

## Design Principles

1. **Offline-first by default** — no network calls after installation.
2. **Deterministic** — same preset + same seed = identical audio and prompts.
3. **Matrix-aware** — the classifier never ignores patch routing.
4. **Dual independent branches** — Audio (DSP) and Semantic (prompt) can be tested and versioned separately.
5. **Content-addressed assets** + SQLite local library.
6. **CPU-first with optional GPU/NPU acceleration**.

## System Overview

```
Preset JSON ──┬──► DSP Engine ──► WAV / MIDI / JSON
              │
              └──► Feature Extractor (matrix-aware)
                        │
                        ▼
                  Sonic Profile
                        │
                        ▼
                  Vocabulary Banks + Coherence Rules
                        │
                        ▼
                  Prompt Compiler ──► Suno-style JSON/TXT/CSV
```

## Core Components

### 1. Preset Schema
Shared contract used by both branches. See `src/lfs/core/preset.py`.

### 2. DSP Engine (`src/lfs/dsp/`)
- 3 oscillators (sine/saw/square/triangle) + fine, level, PWM
- Noise (white/pink/red)
- 16×16 weighted switch matrix
- Modules: ring mod, sample-and-hold, LFO, ADSR, state-variable filter, VCA, Schroeder reverb
- Imperfection stage: drift, tracking error, crosstalk, wobble, jitter
- Fully deterministic render loop

### 3. Semantic Branch (`src/lfs/semantic/`)
- Matrix-aware feature extraction (modulation depth, targets, pin activity)
- Rule-based + optional tiny ONNX classifier
- Vocabulary banks (genre, mood, texture, tempo, era, production, instruments, structure)
- Coherence constraints
- Seeded prompt compiler

### 4. Storage
- SQLite for library metadata
- Content-addressed files for presets, renders, models
- Crash-safe project files with autosave

### 5. UI
- CLI (Typer) for batch and scripting
- Local GUI (Dear PyGui or Qt) for matrix editing, audition, prompt preview

### 6. Packaging
- One-click offline installers (macOS .dmg, Windows .msi, Linux AppImage)
- All models and assets bundled and checksummed
- No post-install network requirement

## Model Strategy

| Component            | Approach                          | Size Target |
|----------------------|-----------------------------------|-------------|
| Core synthesis       | Pure DSP                          | < 5 MB code |
| Optional embedder    | Quantized CLAP / OpenL3 ONNX      | 10–30 MB    |
| Classifier           | Rules + tiny MLP ONNX             | < 5 MB      |
| Optional lyric polish| Tiny GGUF (Phi / Gemma quantized) | 1–3 GB (optional download later) |

All core functionality works with zero neural models.

## Security & Privacy

- No telemetry
- No analytics
- Optional LAN sync only (user-initiated)
- Models and assets verified by SHA-256 at startup

## Testing Strategy

- Golden WAV hash tests
- Classifier fixture tests
- Prompt snapshot tests
- Full integration test with network interface disabled
- Determinism tests across platforms

See `tests/` and the two-week MVP plan in the original design document.