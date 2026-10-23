# CHANGELOG v47 (2026-10-23, user kept v46 and ordered continuation)

v46 preserved unchanged. v47 is a new file.

## 1000-agent audit (Section 5.2, Section 4.5, Section 6.4 limitation 9)
- Correction: comparison policy is (T=0.55, s=0.20), not (T=0.45, s=0.40). Source script: archive/stress_control_optimal.py, now in the replication pack as experiments/stress/stress_control_optimal.py. The JSON records no threshold/severity, so the old attribution was unsupported.
- Seed pairing: episodes run with seed=ep (0,1,2) for both policies on the same env object. Episodes 1-2 are paired; episode 0 is unpaired because ECOSControlEnv.reset treats seed=0 as falsy and draws a random seed each time. Near-zero variance (std < 1e-5) means this flaw does not change the result; it is disclosed in Section 5.2.
- The 374% figure is therefore NOT seed-confounded in the same way as the 30-agent grid, but it remains a 3-episode point estimate.

## Correctly parameterized p/S sweep (Section 5.3)
- Script: experiments/robustness/ps_sweep.py; output: results/robustness/ps_sweep.json (copied from dao Temp run). Focused zone check: experiments/robustness/ps_zone45.py. Isolated-agent check: experiments/robustness/iso_check.py.
- Method: p rebuilt after reset with common random numbers (RandomState(seed), edge iff rand < p); S set as a common initial stability on all three FSRS lessons after reset (documented: not the default bank's 5/3/2). Fixed policy T=0.30, s=0.60; 30 agents; 300 ticks; seeds 1,2,3.
- Results (mean return, RL reward, not PnL): p=0.05: 1737/1534/1316 for S=30/45/60, zone 27.8/25.0/22.2%, std ~2600-3300; p=0.10: -263/-205/-164, zone 0%, std ~90; p=0.20: -202/-142/-100, zone 0%, std 0. Interventions 0.0 in all 27 episodes.
- Mechanism verified: _compute_obs gives an agent with no predecessors perceived R = 0.4 * true R. Isolated counts: p=0.05 seeds 1-3: 4,3,10; p=0.10: 1,0,0; p=0.20: 0,0,0. Focused p=0.05, S=45: per-episode zone 0%, 0%, 75%; seed-3 return +5735 vs about -600 for the others. The p effect is largely an isolated-agent artifact; no policy recommendation is drawn from it until the fallback-to-true-R fix is in.
- S effect is p-dependent (monotonic increasing at p>=0.10, decreasing at p=0.05 driven by the isolated episode). No clean S claim is made.

## Figure 5 replacement (Section 3.3, Section 6.4 limitation 7)
- New file: figures/fig5_grade_impact_v47.png (132 KB, generated on dao with matplotlib 3.10.9, script experiments/figure_generation/fig5_v47.py). Formula S' = S * exp(w17*(G-3+w18)*S^(-w19)); multipliers match the Section 3.3 table exactly (S=45: 0.145/0.546/2.050/7.703). The v43 figure remains withdrawn; this is a new file, the old file is untouched.
- Sandbox matplotlib is broken (NumPy 1.x-compiled matplotlib vs NumPy 2.5.4), so the figure was generated on dao; note for future figure work.

## Word-count locale trap (found while fixing the header)
- wc -w is locale-dependent for this manuscript (non-ASCII symbols): POSIX/C locale gives 8850 for v47, C.UTF-8 gives 8908. All v43-v47 headers use the POSIX count. Use LC_ALL=POSIX wc -w for future headers.

## Still open
- Appendix A: needs a real code/data link or DOI (requires a public-repo/DOI decision; not done unilaterally).
- tex sync to v47 (after md is approved).
- Independent re-review of v47 (not yet run).
- User keep/rollback decision for v47.
- Isolated-agent fallback fix in ECOSControlEnv (future work, disclosed in Section 5.3; not implemented, as it would change the environment and all prior numbers).
