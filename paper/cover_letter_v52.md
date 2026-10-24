# Cover Letter for JEDC Submission

**Date**: 2026-10-24
**To**: Editor, *Journal of Economic Dynamics and Control*
**From**: MinQian Cai
**Title**: "Long Memory in Agent-Based Markets: FSRS Power-Law Forgetting vs Ebbinghaus Decay, and Why Control Fails to Bite"
**Type**: Research Article

Dear Editor,

I submit the manuscript above for consideration as a research article in the
*Journal of Economic Dynamics and Control*. The paper asks a model-choice
question that sits squarely in the journal's computational-economics remit:
when agents in a market model remember past shocks, does the functional form
of forgetting change anything that matters?

**What the paper does.** It implements a power-law forgetting engine
(FSRS-style) in an agent-based trading environment and contrasts it
head-to-head with classical Ebbinghaus exponential decay. In a 100-agent,
500-tick comparison, FSRS retrievability at tick 500 is approximately
47,000 times the exponential baseline (0.7185 vs 0.000015). The paper then
reports, with equal weight, two negative results from control probes run
against that engine: PPO-based reinforcement learning fails to learn an
intervention policy, and grid search over intervention thresholds cannot
identify an optimal threshold at the simulation stability (a paired
same-seed rerun gives identical outcomes for both candidate policies), so
the effective policy on 30 agents is non-intervention. A real-data
recalibration attempt is reported in full and also fails: the stability
parameter cannot be identified from market volatility data, for a
structural reason (the model's minimum achievable memory half-life exceeds
any observed market recovery timescale). The simulation stability of 45 days
is therefore retained explicitly as a simulation convention, not a
calibrated estimate, and the limitation is stated in the paper rather than
buried.

**Why JEDC.** The contribution is a contest between memory kernels, not a
policy proposal: it shows that memory-kernel choice, not policy levers,
decides how long simulated markets remember. That claim is directly
relevant to computational work on agent-based markets, volatility
clustering, and macroprudential modeling, and it is presented with a full
audit trail: every superseded claim in earlier drafts is retained in the
manuscript labeled as audit-only, with the rerun that superseded it.

**Reproducibility.** All code, data, and results are archived in a
replication pack (GitHub: caiminqian/JEDC-FSRS-replication; Zenodo concept
DOI 10.5281/zenodo.23594009, v52 DOI 10.5281/zenodo.23614971).

I confirm this manuscript is original, not previously published, and not
under consideration elsewhere. No external funding was received. No
conflicts of interest to declare.

I look forward to your consideration.

Sincerely,
MinQian Cai
