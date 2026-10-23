# CHANGELOG v45 (2026-10-23, same-seed rerun)

v44 preserved unchanged. v45 is a new file.

## Paired same-seed rerun (dao, ECOSControlEnv, 30 agents, 300 ticks)
- Script: experiments/grid_search/same_seed.py (in replication pack); output: results/grid/same_seed.json
- Seed set 10: (T=0.45, s=0.40) 3836.30 +/- 1126.90, (T=0.30, s=0.60) 3836.30 +/- 1126.90, interventions 0.0 both, target zone 49.97% both, per-episode returns identical.
- Seed set 110: 3725.26 +/- 1063.03 both, interventions 0.0 both, target zone 48.63% both.
- Conclusion: outcomes identical because neither threshold ever triggers under FSRS; the intervention code path is never entered. The original Table 2 gap (3947 vs 3434, zone 51.3% vs 45.0%) is a seed/network artifact: original grid used seed_offset=i per configuration, and ECOSControlEnv.reset draws the p=0.1 network from the seed.
- Note: ECOSControlEnv.reset treats seed=0 as falsy and draws a random seed instead; the rerun therefore uses seed_offset 10 and 110 (all episodes > 0), and the first same_seed run failed on a float32 JSON serialization bug in the script (fixed by float() conversion).

## Text changes in v45
- Abstract, Section 1 contribution 4, Section 4.4.2, Section 5.1 (new paired Table 2b), Section 5.1.3 implication, Section 6.4 limitation 9, Section 7 conclusion: the "optimal policy (T=0.45, s=0.40), +15.0%" claim is withdrawn and replaced by "effective policy is non-intervention; no threshold-severity optimum is identified on 30 agents".
- Original Table 2 numbers are retained in Section 5.1 for audit, explicitly labelled as seed-confounded.
- 1000-agent result (10402 vs 2197, 374%) is retained with its small-sample caveat; its seed pairing has not yet been audited (open item).

## Still open (unchanged from v44, plus one new item)
- Figure 5 replacement figure (correct formula).
- Correctly parameterized p/S robustness rerun.
- Appendix A real code/data link or DOI.
- tex sync to v45 (after md is approved).
- Independent review of v45 (agy cross-model), then user keep/rollback decision.
- Audit seed pairing of the 1000-agent scaling run.
