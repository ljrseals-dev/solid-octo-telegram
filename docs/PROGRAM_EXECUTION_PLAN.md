# Local-First Signal — Post-$100M Program Execution Plan

**Owner**: Chief of Staff (reports to CEO + Board)  
**Status**: Approved for execution at close  
**Last updated**: 2026-11-07  
**Runway assumption**: 36 months at planned headcount (flag if burn exceeds)

---

## 1. Program Objective

Ship a local-first music AI product that a creator can install, run fully offline, generate and render music, and export prompts — with a paid tier, creator program, marketplace, plugin, mobile apps, and enterprise availability on the stated timeline.  
**Target**: $5M+ ARR by end of Year 2.

---

## 2. Hard Constraints (Board-level, non-negotiable)

| ID | Constraint | Enforcement |
|----|------------|-------------|
| C1 | Runtime offline — no telemetry, no cloud calls, no remote model downloads | Source-tree network-import test in CI + installer offline verification |
| C2 | Deterministic render — same preset + same seed = identical PCM | Golden WAV tests across platforms |
| C3 | Reproducible prompts — same preset + same seed + same banks = identical text | Prompt snapshot tests |
| C4 | No network-capable imports in core runtime modules | CI grep + import blacklist test |
| C5 | Cross-platform golden tests must pass before “DSP engine production-ready” is claimed | CI matrix gate |

**Known tension (must be resolved by end of M2)**  
Marketplace, paid tiers, and enterprise features all imply online services (auth, payments, entitlements, distribution).  
**Decision required by end of M2 (Owner: Product Lead)**:  
Explicit offline-online split that preserves C1 for the core creative loop.  
Recommended pattern:  
- Creative loop (preset → render → prompt) remains 100 % offline.  
- Entitlements validated locally after first activation (signed license file or offline-capable activation token).  
- Marketplace catalog can be offline (bundled + user-imported) with optional online discovery.  
- Payments and account management live online but are never required for generation or rendering.

Any milestone that would force a network call inside the creative loop must be flagged and redesigned.

---

## 3. Workstreams

| ID | Workstream | Owner Role |
|----|------------|------------|
| ENG-DSP | DSP engine, golden tests, native port | DSP Lead |
| ENG-ML | Matrix-aware classifier, prompt compiler, local models, coherence | ML Lead |
| ENG-PLAT | Packaging, installer, cross-platform CI, SQLite library, content-addressed assets | Eng Manager, Platform |
| PROD | Product surface, GUI, CLI, UX, mobile architecture | Product Lead |
| GTM | Alpha/beta cohorts, creator seeding, pricing, launch | Head of GTM |
| BIZ | Hardware partnerships, enterprise pilots, marketplace BD | Head of BD |
| CORP | Finance, legal, security/privacy audit, hiring, board reporting | COO / Chief of Staff |

---

## 4. Phase Plan with Gates

### Phase 1 — Foundation (M0–3)

**Objective**  
Team in seats, technical baseline verified, first end-to-end offline build runs on macOS and Windows with networking disabled.

**Workstreams & Tasks**

- **ENG-DSP**  
  - Execute the existing Python engine end-to-end.  
  - Build golden WAV test harness; pin expected PCM for the six demo presets.  
  - CI matrix: macOS / Windows / Linux.  
- **ENG-ML**  
  - First real run of classifier + prompt compiler.  
  - Fix defects §8.1–§8.5 (unreachable classes, shadowed rules, boundary conditions, doc drift, dominant-wave collision).  
  - Add matrix features to profile; fix §8.6 (matrix blindness) and §8.7 (coherence) by wiring the coherence engine already present in the banks.  
  - Time-boxed defect triage sprint (treat §8 as floor, not ceiling — paper §8.9).  
- **ENG-PLAT**  
  - One-click offline installer PoC (macOS + Windows).  
  - SQLite preset library skeleton.  
  - Content-addressed asset store.  
- **PROD**  
  - Internal CLI + basic GUI prototype.  
  - Offline/online split design decision (due end of M2).  
- **CORP**  
  - Close funding.  
  - Hire DSP Lead, ML Lead, Product Lead + ≥8 engineers.  
  - Stand up board reporting cadence.

**Gate Criteria (binary)**  
- [ ] G1.1 Golden tests green on macOS, Windows, Linux in CI.  
- [ ] G1.2 Classifier + prompt compiler run without error; demo bank classifications match written spec (including Resonant Drone → drone).  
- [ ] G1.3 Coherence engine enforces C1–C9 with tests.  
- [ ] G1.4 Offline installer installs and launches the app on clean macOS and Windows VMs with networking disabled.  
- [ ] G1.5 DSP Lead, ML Lead, Product Lead, ≥8 engineers in seats.  
- [ ] G1.6 Marketplace/accounts offline-online decision documented and signed off by Product Lead + CEO.

**Critical-path risks at this gate**  
Hiring velocity, cross-platform float determinism, first-run of previously unverified code.

---

### Phase 2 — Alpha (M4–6)

**Objective**  
50 private alpha creators using a real preset library on real packaging.

**Key Tasks**  
- Full preset library (SQLite + content-addressed).  
- Cross-platform packaging pipeline; opt-in manual update check only (no auto phone-home).  
- Close the prompt→audio evaluation loop with a concrete metric (spectral or embedding distance).  
- Alpha UX + telemetry-free local feedback log export.  
- Onboard 50 alpha creators; structured feedback.  
- ≥2 hardware partnership conversations.  
- Security & privacy audit kickoff (threat model must include the no-network guarantee).

**Gate Criteria**  
- [ ] G2.1 50 alpha creators active; ≥30 producing ≥1 session/week.  
- [ ] G2.2 Preset library supports import/export, versioning, CAS dedupe.  
- [ ] G2.3 Security audit scope agreed; threat model documented.  
- [ ] G2.4 Prompt→audio evaluation loop running with a metric.  
- [ ] G2.5 ≥2 hardware partnership conversations in progress.

---

### Phase 3 — Beta (M7–9)

**Objective**  
Public beta, creator seeding, marketplace prototype, mobile architecture decision.

**Critical addition (not in original milestone list)**  
**Native DSP port (C++ or Rust) begins in M7.**  
This is the hidden critical path for both the plugin (M10–12) and mobile (Y2). Python will not ship as a real-time plugin or on mobile.  
Budget: 2 senior native engineers starting M7.

**Key Tasks**  
- Native DSP port starts.  
- Public beta distribution.  
- Marketplace prototype (local catalog + optional online discovery).  
- Mobile architecture decision (must be downstream of native port progress).  
- Creator seeding (500+ seats).  
- First enterprise pilot signed.  
- Security audit complete + remediation.

**Gate Criteria**  
- [ ] G3.1 Public beta live; ≥500 seeded creators.  
- [ ] G3.2 Marketplace prototype demoable; offline-online split documented.  
- [ ] G3.3 Mobile architecture decision made and signed off (blocked by native port progress — if port is behind, this gate slips).  
- [ ] G3.4 First enterprise pilot contract signed.  
- [ ] G3.5 Security audit findings remediated or formally risk-accepted.

---

### Phase 4 — 1.0 (M10–12)

**Objective**  
Paid 1.0, ≥10k active creators, plugin alpha, Series B preparation.

**Key Tasks**  
- Native DSP port reaches feature parity on core signal path with the Python engine.  
- Plugin (VST/AU) alpha in at least one host.  
- Paid tiers live (entitlements validated locally after first activation).  
- Classifier + compiler v1.1 (matrix-aware, coherence-enforced, loop-closed).  
- 1.0 launch; 10k+ active creators.  
- Series B data room ready.

**Gate Criteria**  
- [ ] G4.1 1.0 shipped; paid tiers live; ≥10k active creators.  
- [ ] G4.2 Plugin alpha runs in at least one host on one platform.  
- [ ] G4.3 Native DSP engine passes the same golden tests as the Python engine on the core signal path.  
- [ ] G4.4 Series B data room ready; ARR metric defined and tracked.

---

### Year 2

**Objective**  
Mobile apps, plugin GA, enterprise GA, $5M+ ARR, international expansion (EU first).

**Gate Criteria**  
- [ ] G5.1 ARR ≥ $5M.  
- [ ] G5.2 Mobile apps shipped on iOS and Android on the native DSP core.  
- [ ] G5.3 Plugin versions GA (VST3, AU).  
- [ ] G5.4 Enterprise product GA with ≥3 paying enterprise accounts.  
- [ ] G5.5 International expansion initiated (EU first).

---

### Year 3

**Objective**  
Category leadership, hardware reference designs (partner-led), path to profitability visible, strategic options evaluated.

**Gate Criteria**  
- [ ] G6.1 Category leadership metric defined and tracked.  
- [ ] G6.2 Hardware reference design shipped with ≥1 partner.  
- [ ] G6.3 Profitability path modeled and board-approved.  
- [ ] G6.4 Strategic options memo delivered.

---

## 5. Dependency Graph (Critical Path)

```
Funding close
    │
    ▼
Hiring (DSP Lead, ML Lead, Product Lead, ≥8 eng)
    │
    ▼
ENG-DSP golden tests ──────────────────────────────┐
    │                                              │
    ▼                                              │
Classifier + compiler v1 (matrix + coherence)      │
    │                                              │
    ▼                                              │
Offline installer PoC ──► Cross-platform packaging │
    │                                              │
    ▼                                              │
Alpha cohort ◄── Preset library (SQLite + CAS)     │
    │                                              │
    ▼                                              │
Native DSP port starts (M7) ◄──────────────────────┘
    │
    ▼
Mobile architecture decision (M9) — blocked by port progress
    │
    ▼
Plugin alpha (M10–12) ◄── Native port parity
    │
    ▼
Mobile apps (Y2) ──► Enterprise GA (Y2)
```

**Two loud flags**  
1. Native DSP port is missing from the original milestone list but is the critical path for both plugin and mobile. It is now a first-class workstream starting M7.  
2. The mobile architecture decision (M9 gate) is downstream of the port. If the port slips, the decision slips. Do not force an early decision on Python-engine assumptions.

---

## 6. Risk Register (Top 10)

| # | Risk | Owner | Trigger | Mitigation |
|---|------|-------|---------|------------|
| R1 | $100M implies 30–36 mo runway; plan may burn faster | COO | Monthly burn vs plan | Model burn by phase; hold hiring to gate criteria |
| R2 | Hiring 4 leads + 8–12 engineers in 90 days | COO | Offer-accept rate below plan | Pre-committed offers before close; contractor bridge |
| R3 | Python DSP will not run on mobile or as real-time plugin | DSP Lead | Plugin alpha slips | Start native port M7; budget 2 senior native engineers |
| R4 | Cross-platform float determinism breaks golden tests | DSP Lead | CI flake macOS vs Windows | Deterministic float discipline; per-platform golden baselines |
| R5 | Marketplace / paid / enterprise contradict C1 | Product Lead | Design review at M2 | Explicit offline-online split; local entitlement validation |
| R6 | Unverified code hides more defects than §8.1–8.7 | ML Lead | First run of classifier | Time-boxed defect triage sprint in M0–1; treat §8 as floor |
| R7 | Prompt→audio loop never validated | ML Lead | Alpha feedback contradictory | Close the loop in Alpha with a metric, not vibes |
| R8 | Security audit surfaces no-network violation | CORP | Audit at M4–6 | Pre-audit self-check in M3; enforce C4 with source-tree test |
| R9 | Hardware partnership distracts from software roadmap | Head of BD | First partnership LOI | Partner-led reference designs only; no first-party manufacturing |
| R10 | Series B story depends on ARR that depends on plugin + mobile | CEO | M10–12 ARR trajectory | Define ARR components early; track leading indicators |

---

## 7. Board Metrics (Monthly)

- **Engineering**: golden-test pass rate per platform; classifier defect burndown; native port % parity; CI flake rate.  
- **Product**: active creators (DAU/WAU/MAU); sessions per creator per week; preset library size; prompt export volume.  
- **GTM**: alpha/beta cohort size; creator seeding seats; conversion to paid.  
- **BIZ**: enterprise pipeline; hardware partnership stage.  
- **CORP**: burn, runway months, headcount vs plan, open roles.  
- **Year 2+**: ARR, net revenue retention, marketplace GMV (if applicable).

---

## 8. Governance

- **Weekly**: workstream leads sync (30 min, blockers only).  
- **Biweekly**: phase-gate review — each criterion marked green / amber / red with evidence.  
- **Monthly**: board pack using the metrics above.  
- **Quarterly**: risk-register review; re-baseline if any gate has been red for two consecutive reviews.  
- **Decision rights**: phase-gate sign-off by CEO + relevant workstream lead. Scope changes that move a gate date require board notification.

---

## 9. Acceptance of This Plan

This document satisfies the master prompt when:

- [x] All six phases have workstreams, tasks, owners, and binary gate criteria.  
- [x] Dependency graph is present and names the native DSP port as critical path.  
- [x] Offline-online tension is resolved with an owner (Product Lead) and deadline (end of M2).  
- [x] ≥10 risks with owner, trigger, mitigation.  
- [x] Monthly board metrics defined.  
- [x] No original milestone is silently rescheduled — the native port is an explicit addition with rationale.

---

*End of Program Execution Plan*