# CHANGELOG v48 (2026-10-23)

## Why v48 exists
Four independent reviews of v47 (pi PASS, Gemini Flash FAIL, Gemini 4 Argon FAIL, Qwen3.8-Max deep PASS) converged on wording contradictions, and Argon found a methods error: the original grid and the v45 paired rerun never set S, so they ran the default memory bank (initial stabilities 5/3/2), not the calibrated S0=45 claimed in Sections 4.1/4.3. v48 reruns the grid at S=45 (user-approved scope B) and fixes the wording.

## New runs (dao, 30 agents, 300 ticks)
- Paired rerun at S=45 (`experiments/grid_search/paired_s45.py`, `results/grid/paired_s45.json`): seed set 10: -314.71 +/- 128.20 both configs, interventions 0.0, zone 0.0%; seed set 110: -304.23 +/- 122.01 both, interventions 0.0, zone 0.0%. Per-episode returns identical within each seed set. Conclusion unchanged (no optimum, effective policy non-intervention); absolute returns and zone times are not comparable with the default-bank numbers.
- Full grid at S=45 (`experiments/grid_search/grid_s45.py`, `results/grid/grid_s45.json`): 24 configurations (6 thresholds including baseline 0.30, 4 severities, 10 episodes each, seed_offset by configuration as in the original grid), returns -325.19 to -247.56, baseline (0.30, 0.60) -266.45 +/- 136.30, interventions 0.0 and zone 0.0% in every configuration, crisis 0. Configurations still use different seed sets, so the spread is not a policy comparison; the paired table is the controlled comparison.

## Text changes (v47 -> v48, no other data changed)
- Abstract, Section 1 contribution 5, Section 4.1, Section 4.3, Section 5.1: S=45 paired numbers; original 3947/3434 gap explicitly labelled default-bank and audit-only; 24-configuration count reconciled (5 listed thresholds + baseline 0.30 appended by the script).
- Section 2.4, Section 5.4, Section 6.1, Section 6.2, Section 7: "direct policy search succeeded" and "optimal policy" labels removed; Section 6.2 no longer prescribes (0.45, 0.40); it now says monitor, reserve intervention for fragile states, and notes the 1000-agent comparison policy was milder and more frequent (0.20, 15.0/ep), not stronger and less frequent.
- Section 5.2: 1000-agent run stated as 1000 ticks/episode; near-zero variance explained (1000-agent averaging); scope stated: not rerun at S=45, default-bank numbers, not comparable with v48 grid numbers.
- Section 5.3: v44 stale "open item" sentence replaced with the v47 sweep closing that item.
- Section 6.4 limitation 6: isolated-agent defect explicitly unfixed, fix is future work. Limitation 9: 3-episode point-estimate caveat added. New limitation 11: S scope of v48 (only grid, paired rerun, p/S sweep are S=45-verified; 1000-agent and Section 5.5 runs are not).
- Section 6.5: isolated-agent fix added as a future-work item.
- Precision: Section 3.3 G=3/S=5 +140.4% corrected to +140.5%; 47,018x corrected to approximately 47,000x (archived inputs give 47,022, last digits not significant).

## Still open (unchanged from v47)
- 1000-agent run not rerun at S=45. Section 5.5 supplementary experiments' S settings not re-audited. PPO training script still not archived. Appendix A still a placeholder. Tex not yet synced to v48.
