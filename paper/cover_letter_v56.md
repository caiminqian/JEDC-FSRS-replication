# Cover Letter for JEDC Submission (v56 finalized — not sent)

**Date**: 2026-10-31
**To**: Editor, *Journal of Economic Dynamics and Control*
**From**: MinQian Cai
**Title**: "Long Memory in Agent-Based Markets: FSRS Power-Law Forgetting vs Ebbinghaus Decay, and Why Control Fails to Bite"
**Type**: Research Article

Dear Editor,

We submit our manuscript for consideration as a research article in the *Journal of Economic Dynamics and Control*. The paper's central claim is a contest over the functional form of memory, not a controller: in agent-based markets, a power-law forgetting kernel (FSRS) beats the classical exponential forgetting curve (Ebbinghaus, EE) at reproducing how long markets remember crises — and that kernel choice, rather than any policy lever, decides the dynamics that follow.

**The contest, in one paragraph**: in a head-to-head 100-agent comparison over 500 ticks, FSRS retrievability at tick 500 is approximately 47,000 times EE's (R(500) = 0.7185 vs 0.000015). Under a second, heterogeneity-adjusted caliber the gap narrows to 5.4 times (tier T2 for the lognormal and two-point distributions, T3 for the uniform distribution); both calibers are reported side by side, not as competing estimates. The same kernel that wins the persistence contest is then shown to defeat control: two control probes (PPO reinforcement learning and grid search over intervention parameters) both return negative results, because under the recalibrated FSRS kernel the intervention thresholds never trigger. The paper's implication is therefore about model choice first — memory kernels, not policy levers, decide how long markets remember — and about the limits of control in a long-memory regime second.

**What the paper does not claim** (stated here so the submission is judged on its actual content):

1. The external-moment evaluation of the kernel's scale parameter is **CONDITIONAL**: it reports **no identification conclusion**. The Route A span is 22.79% (break band; F8-corrected 2026-10-31 from the as-implemented 22.53%), but the null AND condition fails in all 6 window-by-reference combinations and the argmin sits at the grid endpoint 2.0, so the paper reports "boundary preference, no identification," with 9 caps disclosed in the manuscript (lower clip; common-mode bias; |G_valid| = 4 < 5; effective n = 2 after pair removal; endpoint argmin; w20 cross low-end failure; peak-window sensitivity; grade-boundary sensitivity; Route C lag-5 diagnostic flag). The S0* scale and the LESSONS rescale k remain admissible over [1.67, 11.11], not identified.
2. The genuine multi-shock engine validation (step 8) concludes **BORDERLINE**: on the 12 admitted forward events, the engine trajectory does not beat the single-shock closed form (mean log-ratio +0.295725) while beating a re-initialization baseline (mean log-ratio −0.064158, BCa upper bound inside the pre-registered ±0.01 borderline band), underpowered (10 exposures against 23 required at the reference cell), and sensitive to clip saturation. The honest summary is "multi-shock advantage unproven," not "engine invalid," and not a validation claim.
3. No trading-profitability claim is made: the trading backtest is a simulation outcome under one seed and one shock sequence, and the v54 profitability figure was withdrawn as irreproducible.

**Reproducibility**: all code, data, and figures are openly available in the replication pack at https://github.com/caiminqian/JEDC-FSRS-replication (release v56, archived at Zenodo: https://zenodo.org/records/23839771, DOI 10.5281/zenodo.23839771; concept DOI 10.5281/zenodo.23594009). No external funding was received. No conflicts of interest to declare.

We confirm this manuscript is original, not previously published, and not under consideration elsewhere. All authors have approved the manuscript.

We look forward to your consideration.

Sincerely,
MinQian Cai
