# A Power-Law FSRS Approach — Replication Pack

Replication pack for the manuscript **"A Power-Law FSRS Approach"**
(submitted to the *Journal of Economic Dynamics and Control*),
which introduces a simplified FSRS-style, power-law forgetting model
into agent-based economic modeling and tests macroprudential
intervention policies in the ECOS simulation environment.

**Cite this pack:** version DOI for v48:
[10.5281/zenodo.23594010](https://doi.org/10.5281/zenodo.23594010);
concept DOI (all versions):
[10.5281/zenodo.23594009](https://doi.org/10.5281/zenodo.23594009).
Archived record: <https://zenodo.org/records/23594010>.

**Current manuscript:** `paper/JEDC_submission_draft_FSRS_FINAL_v48.md`
(v48; earlier drafts v43–v47 are kept in the same folder for audit).
The tex draft in `paper/` predates v48 and has not yet been fully
synchronised with it; its Data Availability section already carries
the v48 DOI.

## What is inside

| Path | Contents |
| --- | --- |
| `paper/` | Manuscript drafts (v43–v48), the tex draft, `references.bib`, `cover_letter.md`, and per-version changelogs |
| `src/ecos/` | The full ECOS package used by the experiments (control, agents including traders, governance, core, risk) |
| `experiments/` | Grid search, paired reruns, robustness and p/S sweeps, comparison, Monte Carlo, long-term, trading, and stress scripts |
| `results/` | Archived result JSONs behind the paper's tables, including the original grid, the same-seed and S=45 reruns |
| `figures/` | Figures, including the corrected Figure 5 (`fig5_grade_impact_v47.png`) |
| `data/` | Calibration parameters and the initial world state |
| `MANIFEST.txt` | File list with sizes and SHA-256 hashes (129 files, excluding the manifest itself and `__pycache__`) |

`src/ecos/` is a complete copy of the source package, not a cherry-picked
subset: `ecos_env.py` imports `ecos.core.world_state`, and the governance
manager imports `ecos.core.metrics`, the ministries, and `ecos.risk.*`,
so a partial copy cannot run. The only generated file is the empty
`src/ecos/control/__init__.py` (the source directory never had one).

## Reproduce

The working directory must be `src/`; imports are written as
`from ecos.control.ecos_env import ECOSControlEnv` (never `src.ecos.*`).
For scripts under `experiments/`, set `PYTHONPATH` to `src/`.
See `REPRODUCE.md` for the full run layout, the exact commands, and
the known gaps.

## Headline results (v48, audited)

- **No threshold–severity optimum is identified.** The original grid
  (default memory bank, S = 5/3/2) reported an apparent optimum at
  threshold 0.45 / severity 0.40 (3947.33 vs baseline 3433.56), but
  each configuration ran a different seed set, so the gap is
  seed-confounded and is kept in the paper for audit only.
- **Paired reruns, same seeds, S = 45:** both the 0.45/0.40 and the
  0.30/0.60 configurations return exactly the same numbers
  (−314.71 ± 128.20 on seed set 10; −304.23 ± 122.01 on seed set 110),
  with zero interventions — average retrievability never falls below
  either threshold, so the effective policy in this regime is
  non-intervention. The full S = 45 grid spans −325.19 to −247.56,
  again with zero interventions throughout, and its cross-config
  spread is not a policy comparison (configurations still use
  different seed sets).
- **1000-agent scaling run (audit):** the comparison policy actually run
  was threshold 0.55 / severity 0.20 (not 0.45/0.40), returning 10402.47
  vs baseline 2196.53 over 3 episodes of 1000 ticks. This run used the
  default memory bank and was **not** rerun at S = 45, so its numbers
  must not be compared directly with the S = 45 grid.
- **p/S sweep:** the apparent effect of network density p is largely an
  isolated-agent artifact — an agent with no predecessors perceives
  only 0.4 × its true retrievability, which can drag the mean into the
  target zone and earn the zone bonus. The fix (fall back to true
  retrievability with no neighbours) is future work; applying it would
  change the environment and all prior numbers.
- **FSRS vs EE:** at tick 500 the archived inputs give FSRS/EE ≈ 47,000×
  (reported as an approximation; the v43 figure of 47,867× used rounded
  values). Note that the "EE" baseline in code is an exponential-decay
  curve, not the commercial SM-20 algorithm; legacy `sm20` file and key
  names are preserved for provenance.

## Known limitations (stated in the paper, §6.4)

1. The PPO training script was not located in the source archive — only
   `results/rl/results_v4.json` and the model zips are present.
2. The 1000-agent run and the §5.5 supplementary experiments were not
   re-audited at S = 45 in v48.
3. The isolated-agent perception defect in `ECOSControlEnv._compute_obs`
   is still present in this code.
4. The original v43 claims withdrawn in v44–v48 (the 48.1% target-zone
   figure, the Monte Carlo and 10-year misstatements, the §3.3 grade
   mapping, and the §5.3 robustness table) are documented in the
   changelogs, not silently edited away.

## License

Not yet assigned. Until a license file is added, reuse terms are to be
confirmed with the author.
