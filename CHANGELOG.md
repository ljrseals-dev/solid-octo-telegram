# Changelog

## [0.2.0] — Vocabulary Bank Prompt Compiler

### Fixed (paper §8.1–§8.7)

- **§8.1** Dead / unreachable keys removed from banks; closed-set validation enforced at load time. `hoover` and `fx` are now reachable via explicit classifier rules.
- **§8.2** Rule ordering corrected: `drone` evaluated before `ambient`; `droning` evaluated before `padded`.
- **§8.3** All numeric boundaries now use documented non-strict comparisons (`>=` / `<=`) with the chosen side recorded in `rule_fired`.
- **§8.5 / §8.6** Matrix features fully extracted (pin_count, total_depth, targets, sources, modulated, audio_rate_mod). Wave energy is accumulated; dominant wave is argmax with noise override.
- **§8.7** Coherence engine (C1–C9) filters candidate pools *before* the seeded draw. Empty pools fall back with an explicit `coherence_waiver`.

### Added

- External JSON banks under `banks/` (8 required + 2 optional).
- `bank_loader.py` with schema + closed-set validation.
- `coherence.py` implementing rules C1–C9.
- `killer_bridge.py` (profile extractor with explainability via `rule_fired`).
- `prompt_compiler_v2.py` fully bank-driven, deterministic, multi-variant.
- `schemas/bank.schema.json`.
- `docs/BANKS.md` and this CHANGELOG entry.

### Compatibility

- Original minimal compiler remains available for migration.
- DSP / render path is untouched.
- Fully offline; no network imports.