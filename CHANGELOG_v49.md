# CHANGELOG v49 (2026-10-23)

## Why v49 exists
v48 left two S=45 gaps: the 1000-agent run (Section 5.2) and the Section 5.5
supplementary experiments were never rerun at S=45, and Section 5.5's S settings
were never audited. v49 closes both: the Section 5.5 audit finds none of the
three original scripts sets S (they build HumanAgent directly on the default
bank 5/3/2), and all four runs are rerun at S=45 on dao.

## New runs (dao, S=45)
- 1000-agent rerun (`experiments/stress/stress_s45.py`,
  `results/stress/stress_1000a_s45.json`): seeds 1, 2, 3 paired for both
  policies (seed 0 avoided, dodging the original run's falsy-seed flaw).
  Baseline and comparison both return -1065.35 +- 0.00, interventions 0.0,
  zone 0.0%; per-episode returns bit-identical across seeds and policies.
  Improvement 0.0%. The v47/v48 373.6% figure is withdrawn as a policy claim
  and retained for audit only. Runtimes: baseline 425 s, comparison 486 s.
- E2E rerun (`experiments/trading/e2e_s45.py`,
  `results/validation_5_5/e2e_verification_results_s45.json`): final R
  0.9998 (original 0.9991), per-lesson final R 0.998 each, shock sequence
  identical to the original. P&L/drawdown/trades (from
  `full_trading_simulation.json`) were not rerun and are not S=45 results.
- Monte Carlo rerun (`experiments/monte_carlo/mc_s45.py`,
  `results/validation_5_5/fsrs_vs_ee_monte_carlo_s45.json`): FSRS mean
  0.9820 +- 0.0238 (original 0.9421 +- 0.0581), min 0.9012, 30/30 runs above
  R=0.85 (original 27/30); EE 0.6040 +- 0.2493 unchanged; shocks identical.
- 10-year rerun (`experiments/longterm/lt10y_s45.py`,
  `results/validation_5_5/fsrs_vs_ee_10year_3650d_s45.json`): FSRS mean
  0.99958, bit-identical to the original in all 8 runs. Cause: S is capped at
  36500 in `process_market_shock`, and mean 69.9 shocks push S from 5 and
  from 45 both into the cap, after which trajectories merge. The 10-year gap
  is therefore saturation-robust, not S-discriminating.

## Text changes (v48 -> v49, no other data changed)
- Abstract, Sections 4.1, 4.3, 5.2, 6.2, 6.4 (limitation 9), 7: 374% figure
  withdrawn as a policy claim; S=45 1000-agent result (-1065.35, 0.0%)
  reported; 1000-agent intervention claims qualified as original
  default-bank run only.
- Section 5.5 intro: audit result stated (default bank 5/3/2, no S set, no
  ECOSControlEnv in any of the three original scripts).
- Sections 5.5.1, 5.5.2, 5.5.3: S=45 rerun numbers alongside originals;
  setup details added (MC: seeds 0-29, 250 ticks, sample 10, shock_prob
  0.02, severity [0.15, 0.4], BTC/ETH/AAPL/SPY; 10-year: seeds 200-207, 3650
  ticks, sample 50, same shock settings).
- Section 5.5.4: Monte Carlo std ratio updated (0.23x original, 0.095x at
  S=45); 10-year item carries the saturation qualifier.
- Section 6.4 limitation 11 rewritten: everything except E2E P&L/drawdown/
  trades and PPO outcomes is now S=45-verified; 10-year result does not
  discriminate S.

## Still open (unchanged, narrowed)
- E2E P&L/drawdown/trades not rerun at S=45. PPO training script still not
  archived. Isolated-agent defect still unfixed (future work). Tex not yet
  synced to v49. No real-market-data validation (limitation 5).
