# CHANGELOG v46 (2026-10-23, pi-review adjudication)

v45 preserved unchanged. v46 is a new file.

## Review
- Reviewer: pi, model gpt-oss:120b, read v45, v44, CHANGELOG_v45, same_seed.py, same_seed.json in full.
- Reviewer verdict: VERDICT: FAIL, with one HIGH (Table 2 vs same_seed.json mismatch), plus MED/LOW items.

## Adjudication (by main agent, on the record)
- HIGH not sustained: the paired table in v45 matches same_seed.json exactly (seed 10: 3836.30 +/- 1126.90, 49.97%; seed 110: 3725.26 +/- 1063.03, 48.63%; interventions 0.0 both). The HIGH compared the audit-labelled original Table 2 against the paired rerun, not the paired table itself.
- Genuine MEDs accepted and fixed in v46:
  1. Section 6.1 still called the policy "optimal control policy derived from grid search" and quoted the original gap (3434 vs 3947) without an artifact qualifier.
  2. Table 2's row label "Optimal" and its intro lacked an explicit audit label.
- LOW/scoping point accepted: added the sentence that "no optimum identified" means this regime cannot discriminate thresholds, not that thresholds could never matter in a regime where avg_R falls below them.
- Not sustained: word-count point (header verified by wc -w: v45 7900, v46 8124); 374% rounding point (373.6% rounds to 374%, small-sample caveat present); Figure 5 point (v45 states Figure 5 withdrawn, replacement pending, which is disclosure, not a false reference).

## Text changes in v46
- Section 5.1 Table 2 intro and row label now explicitly say original grid, seed-confounded, retained for audit only, superseded by the paired table below.
- Section 5.1 revised-claim sentence gains the identifiability scoping sentence.
- Section 6.1 paragraph rewritten with artifact qualifier and scoping.
- Section 6.4 adds limitation 10 recording this adjudication.

## Still open
- Independent re-review of v46 (not yet run; reviewer routes agy and codex are both down today, pi was the reviewer for v45).
- Figure 5 replacement figure, p/S rerun, Appendix A real link, tex sync, 1000-agent seed-pairing audit.
- User keep/rollback decision for v46 (v45 remains preserved).
