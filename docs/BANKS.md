# Vocabulary Banks Documentation

All prompt vocabulary lives in `banks/*.json`.  
The compiler never embeds tag lists; it only loads and validates these files.

## Bank Files

| File | keyed_by | Purpose |
|------|----------|---------|
| GENRE_BY_CHARACTER.json | character | 2 genres drawn per prompt |
| MOOD_BY_ENV.json | envelope | 2 moods |
| TEXTURE_BY_WAVE.json | wave | 2 textures |
| TEMPO_BY_CHARACTER.json | character | BPM range → integer BPM |
| ERA_TAGS.json | era | 1 era tag |
| PRODUCTION_TAGS.json | none | 2 production tags |
| INSTRUMENT_FLAVOURS.json | none | 1 drum/instrument flavour |
| STRUCTURE_HINTS.json | none | 1 structure hint |
| TITLE_BANKS.json (opt) | none | Title templates |
| LYRIC_BANKS.json (opt) | none | Lyric seeds |

## Closed Sets (must match classifier)

- character (18): bass, acid, perc, glitch, ambient, pad, drone, bell, theremin, formant, strings, brass, pluck, sub, arp, lead, hoover, fx
- envelope (6): padded, percussive, plucky, droning, stabbing, sustained
- wave (5): sine, saw, square, triangle, noise
- era (3): lo-fi analog, acid analog, analog

## Adding a Tag

1. Add the lowercase ASCII tag (no commas) to the appropriate `values` list.
2. If it participates in coherence, update the `coherence` object of that bank.
3. Run `python -m lfs.semantic.bank_loader` or the `--validate-only` CLI flag.
4. Add a snapshot or coherence test if the new tag affects rules C1–C9.

## Coherence Rules Implemented

- C1  lo-fi analog drum restriction
- C2  acid analog production preference
- C3  low BPM excludes four-on-floor
- C4  droning excludes percussive instruments
- C5  envelope → structure exclusions
- C6  drone/ambient exclude hardcore/drill
- C7  sub prefers low-tempo genre subset
- C8  exclusive pairs
- C9  audio-rate modulation adjusts production tags

All rules live in data under each bank’s `coherence` key; the engine only interprets them.

## Paper Defects Fixed

| § | Defect | Fix |
|---|--------|-----|
| 8.1 | Dead data / unreachable keys | Closed-set validation; hoover & fx wired |
| 8.2 | Drone unreachable | Rule order: drone before ambient, droning before padded |
| 8.3 | Boundary ambiguity | Explicit >= / <= documented in killer_bridge |
| 8.5 | Matrix ignored | Full matrix summary + audio_rate_mod |
| 8.6 | Wave collision | Accumulate levels → argmax; noise > 0.4 wins |
| 8.7 | No coherence | Full C1–C9 engine with waivers |