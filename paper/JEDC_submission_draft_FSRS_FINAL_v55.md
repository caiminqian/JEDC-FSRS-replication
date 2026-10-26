# Long Memory in Agent-Based Markets: FSRS Power-Law Forgetting vs Ebbinghaus Decay, and Why Control Fails to Bite

**Authors**: MinQian Cai  
**Target Journal**: *Journal of Economic Dynamics and Control* (JEDC)  
**Submission Date**: v55 draft, 2026-10-26 (v43, v44, v45, v46, v47, v48, v49, v50, v51, v52, v53 and v54 preserved unchanged for provenance)
**Word Count**: 19166 (wc -w, including headings and tables; v54 was 17321)

---

## Abstract

We introduce FSRS (Free Spaced Repetition Scheduler), a power-law forgetting model, into agent-based economic modeling, and contrast it with the classical Ebbinghaus exponential forgetting curve (hereafter EE). The paper's central result is a memory-model contest: in a head-to-head 100-agent comparison over 500 ticks (Section 5.1), FSRS retrievability at tick 500 is approximately 47,000 times EE's (R(500) = 0.7185 vs 0.000015), demonstrating that exponential decay severely underestimates market persistence. Section 5.7 (v55) reports the same contest under a second caliber: a true homogeneous FSRS cell set against a heterogeneous EE cell (lognormal $S_0$, $\sigma=2$) gives a tick-500 gap of 5.4$\times$ ($\overline{R}(500)$ = 0.55548 vs 0.10201, $G$ = 0.7360), so the published 47,000$\times$ and the new 5.4$\times$ are reported side by side as two calibers of one contest, not as competing estimates. The adjudication is mixed: tier T2 for the lognormal and two-point distributions, tier T3 for the uniform distribution (Section 5.7); the main caliber stays T2. Agents equipped with FSRS exhibit realistic panic-complacency cycles, with retrievability decaying slowly over years, mirroring the fat-tailed volatility clustering in post-crisis markets. We model risk memory contagion via network diffusion of perceived retrievability. The simulation parameter set uses an initial stability of $S_0 = 45$ days, taken from the synthetic five-crisis calibration exercise; a real-data recalibration attempt (v51, Section 6.4, limitation 12) could not identify $S$ from market data, so 45 days is retained as a simulation convention, not a calibrated estimate (see Section 3.1 for why this is not a half-life). Two control probes were run against this memory engine and both returned negative results: PPO-based reinforcement learning fails due to sparse delayed rewards, and grid search over intervention parameters cannot identify an optimal threshold on 30-agent populations — the S=45 grid rerun (Section 5.7, A-grid C1) gives identical outcomes for (T=0.45, s=0.40) and (T=0.30, s=0.60) (2209.38 vs 2209.38; interventions 0.0, target zone 28.67% in both), because neither threshold triggers under the recalibrated FSRS kernel at S=45; only the 0.65 threshold triggers, in the final ~11 ticks, and it reduces return. The original 15.0% gap (3947 vs 3434) was measured under the default memory bank (initial stabilities 5/3/2, not S=45) and is a seed/network artifact; it is retained in Section 5.2 for audit only. The effective policy on 30 agents is non-intervention. The 1,000-agent run rerun at S=45 (Section 5.3; v49 pre-fix, v50 post-fix identical) gives identical returns for both policies (-1065.35, interventions 0.0), so the v47/v48 374% figure does not survive at S=45 and is retained in Section 5.3 for audit only (see Section 6.4, limitation 11). Our work bridges cognitive psychology and computational finance: the primary implication is about model choice — memory kernels, not policy levers, decide how long markets remember.

**Keywords:** spaced repetition, cognitive memory, agent-based modeling, FSRS, power-law forgetting, POMDP

**JEL codes:** G01, G17, C63

---
## 1. Introduction

Agent-based models (ABM) have become a cornerstone of modern financial economics, offering a bottom-up approach to understanding complex phenomena that defy equilibrium analysis—bubbles, crashes, herding, and emergent volatility clusters (Lux & Marchesi, 1999; Kirman, 1993). By simulating heterogeneous agents with bounded rationality, ABM captures the nonlinear feedback loops and path dependencies inherent in financial markets. However, a critical component remains underdeveloped: **cognitive memory**. Most agent-based models treat agents as either fully rational expectations agents or as boundedly rational entities using simple heuristics (e.g., technical vs. fundamentalist strategies). When memory is included, it is typically implemented as a short-term moving average of past prices or a slowly-decaying sentiment score—a far cry from the rich, structured memory processes documented in cognitive psychology.

In actual financial markets, participants vividly recall crises shortly after they occur, but those memories fade with time. The 2008 Global Financial Crisis (GFC) triggered sweeping regulatory reforms—Dodd-Frank, Basel III, stress testing regimes. Yet a decade later, as markets boomed, calls for deregulation grew louder. This pattern—crisis → reform → complacency → new crisis—suggests a systematic **memory decay** at the institutional level. Behavioral finance has long recognized this: Guttentag and Herring (1986), in their Princeton essay *Disaster Myopia in International Banking*, argue that lenders systematically discount low-probability disasters whose most recent occurrence has receded from memory, so that the perceived probability of a crisis erodes as the interval since the last one lengthens. Odean (1998) shows investors hold losing stocks too long, a form of selective memory. Shefrin & Statman (1985) describe the "disposition effect" as a cognitive bias rooted in memory asymmetry.

What drives this decay? Cognitive psychology provides a precise mathematical framework: the **forgetting curve**. Hermann Ebbinghaus (1885) discovered that retention of learned material decays exponentially without reinforcement: R(t) = exp(-t/S), where R is retrievability (memory strength), t is time, and S is stability (a measure of how long memory lasts). Crucially, Ebbinghaus also identified the **spacing effect**: information reviewed at optimally spaced intervals is retained far more effectively than massed practice. This principle powers modern spaced repetition systems like SuperMemo (Woźniak, 1990) and Anki. SuperMemo's published **SM-2** algorithm (Woźniak, 1990) adjusts the review interval based on the quality of each recall attempt, creating adaptive, personalized learning schedules. One point of terminology must be fixed at the outset: SuperMemo's later commercial algorithms (SM-3 onward, including SM-20) are proprietary and their forgetting-curve formulas have never been publicly disclosed, so they cannot be independently implemented or audited. The exponential baseline implemented in this paper is therefore the **classical Ebbinghaus curve**, which we denote **EE** (Ebbinghaus-exponential)—not SuperMemo SM-20.

Despite this robust cognitive science, **agent-based economic models have rarely incorporated quantitative memory engines**. A few exceptions exist: Lux (1997) included a simple exponential decay of sentiment; Brock & Hommes (1997) used switching between forecasting strategies based on relative payoffs, which indirectly captures memory through performance weighting. However, none use the mathematically precise FSRS/EE framework. This gap is striking given that memory dynamics lie at the heart of market psychology—fear and greed are not static traits but evolving states shaped by experience and its decay.

Furthermore, memory is not purely individual. In financial networks, information (and misinformation) spreads rapidly through news, social media, and peer networks. An agent's perception of risk is influenced not only by their own memory but by what they hear from others—a phenomenon known as **social amplification of risk** (Kasperson et al., 1988). In agent-based terms, this creates a **memory contagion effect**: even agents with strong personal memory may perceive heightened risk if their neighbors are panicking. Prior work on informational cascades (Bikhchandani et al., 1992) and complex contagion (Centola & Macy, 2007) models how behaviors spread; we extend this to *memory states* spreading.

This paper addresses these gaps by integrating a **cognitive memory engine**—based on FSRS (power-law) versus EE (exponential)—into a multi-agent trading environment. Agents develop retrievability scores R(t) representing their risk awareness; R decays after shocks and consolidates through interventions. We then model **memory contagion**: agents influence each other's perceived R via an information-flow network, mimicking how fear propagates through social and professional ties. The result is a dynamic system where collective memory emerges from individual cognition and network diffusion.

Our contributions are fivefold:

1. **Cognitive Memory Engine**: We implement FSRS (power-law forgetting) and EE (exponential forgetting) within economic agents, creating a mathematically precise model of how risk memories form, decay, and consolidate. This bridges cognitive psychology and computational finance. SuperMemo's SM-2 is discussed only as published historical background in Section 2; it is not an experimental engine in this paper.

2. **Memory Contagion Mechanism**: We introduce a network-based diffusion process where agents' perceived retrievability is a weighted average of their own memory and neighbors' memories, with contagion strength α set to 0.6 from the synthetic calibration exercise (not re-identified on real data; Section 6.4, limitation 12).

3. **Parameter Setting and the Real-Data Calibration Gap**: We set three key parameters—initial stability $S_0$, contagion strength α, and intervention severity mapping—from a synthetic five-event calibration exercise (1987 Black Monday, 2000 Dot-com Bubble, 2008 GFC, 2020 COVID Crash, 2022 Inflation Shock) using an analytical simulator and grid search. The resulting initial stability is **$S_0 = 45$ days**; a real-data recalibration attempt (v51) could not identify $S$ from market data (Section 6.4, limitation 12), so 45 days is retained as a simulation convention, not a calibrated estimate.

4. **Control Probes, Not Control Design**: We test two control approaches against the FSRS engine — PPO reinforcement learning and grid search over threshold-severity parameters — and both return negative results (Sections 5.2, 5.5): PPO fails on sparse delayed rewards, and no threshold-severity optimum is identified because thresholds never trigger under FSRS. These probes are reported as findings about the memory regime, not as a policy design.

5. **Robustness and Sensitivity Analysis**: We systematically vary network density and initial stability, and scale to 1000 agents. Results show the memory contrast is robust (Section 5.1) while the control probes stay negative across scales: in the paired rerun neither configuration outperforms the other, and at S=45 the 1000-agent rerun under the v55 kernel separates the two policies (comparison intervenes once per episode, +80.6%), so the self-stabilizing reading holds only where avg_R never falls below the threshold, and any threshold must be validated in a regime where avg_R actually falls below it.

The paper proceeds as follows. Section 2 reviews related work in spaced repetition, behavioral finance memory, contagion, and the control approaches tested here as probes. Section 3 details the cognitive memory engine (FSRS versus EE), contagion mechanism, control-probe setup, and reward formulation. Section 4 describes our experimental setup: environment, baselines, parameter setting and its calibration status, and control-probe designs (RL and grid search). Section 5 presents results: the FSRS-vs-EE contrast first, then the control probes, scale robustness, the robustness sweep, extended validation, the heterogeneity adjudication (Section 5.7), and Tier-1 empirical validation (Section 5.8). Section 6 discusses what the memory contest implies, why the control probes failed, limitations, and future directions. Section 7 concludes.

**Keywords**: spaced repetition; cognitive memory; agent-based modeling; FSRS; POMDP
**JEL Codes**: G01 (Financial Crises), G17 (Financial Forecasting), C63 (Computational Techniques)

---


---

## 2. Related Work

Our work bridges cognitive psychology, behavioral finance, network science, and computational control. We position each contribution.

### 2.1 Spaced Repetition: From Ebbinghaus to FSRS

Ebbinghaus (1885) discovered the forgetting curve: retention decays exponentially, R(t) = exp(-t/S). Woźniak (1990) operationalized *scheduling* via Algorithm SM-2 (adaptive intervals): SM-2 updates the E-Factor after each review based on recall quality $q$, determining the next interval $I(n) = \mathrm{round}(I(n-1) \times EF)$. SM-2 is the last SuperMemo algorithm whose specification was published in full; subsequent versions, including SM-20, remain proprietary and undisclosed. Together with the Ebbinghaus curve these mechanisms power modern educational software (Anki, Mnemosyne). Our innovation: repurposing the power-law FSRS curve and the exponential EE curve as *competing cognitive engines* for economic agents, where market shocks serve as "reviews" of risk memories. SM-2 is historical background only; it is not an experimental engine in this paper.

### 2.2 Memory in Financial Decision-Making

Behavioral finance documents memory-related biases:
- **Disaster myopia** (Guttentag & Herring, 1986): banks forget past crises, underestimating tail risk.
- **Disposition effect** (Odean, 1998): investors hold losers too long, partly due to memory asymmetry.
- **Recency bias**: over-weighting recent events (Tversky & Kahneman, 1973).

Agent-based models have incorporated simple memory decay (Lux, 1997; Brock & Hommes, 1997), but none employ a rigorous cognitive model like FSRS. Our engine provides a quantitative, parameterizable approach. Long memory in financial markets has also been derived in the heterogeneous-agent literature from agents switching between behavioral forecasting rules (Zheng, Liu, & Li, 2018); that mechanism produces long memory at the aggregate level through rule dynamics, whereas our contribution is a cognitive memory kernel operating inside each agent, so the two approaches are complementary rather than competing.

### 2.3 Contagion via Information Networks

Information diffusion drives herd behavior (Bikhchandani et al., 1992). Complex contagion (Centola & Macy, 2007) requires multiple exposures—captured via our α parameter (mean of neighbors' R). Social amplification of risk (Kasperson et al., 1988) describes how hazards gain attention through media; we implement this as continuous-state diffusion on an Erdős–Rényi graph.

### 2.4 Control Approaches Tested as Probes

Macroprudential tools (countercyclical buffers, stress tests) aim to curb systemic risk (Borio, 2003). In this paper the regulator is treated as a central planner with partial observability (POMDP formulation), but only as a probe: two control approaches were tested against the FSRS engine — model-free RL (PPO), which failed due to sparse/delayed rewards, and direct policy search, which did not identify an optimal threshold on 30 agents (see Section 5.2). This reflects a general pattern rather than an anomaly: when the delay between an intervention and its measurable effect exceeds the effective credit-assignment horizon of an on-policy RL algorithm, direct search over a low-dimensional policy parameterization is the more tractable choice for this problem, not a successful optimisation (see Section 6.3 for a full diagnosis). The control results are therefore reported as negative findings about the regime, not as a policy prescription.

---


## 3. Model

### 3.1 Agent Cognitive Memory (FSRS-Style Power-Law Forgetting)

The forgetting curve in cognitive psychology is traditionally modeled as exponential decay: $R(t) = \exp(-t/S)$ (Ebbinghaus, 1885). However, extensive data from millions of learners using spaced repetition systems reveals that **real-world forgetting follows a power-law distribution with a fat tail**—memories once consolidated persist for extremely long periods with slow decay. The power-law form has a long pedigree in the experimental memory literature, where it is known as the Wickelgren power law and its relation to the Ebbinghaus savings function is examined by Wixted & Carpenter (2007). This paper implements a **FSRS-style power-law model** in the FSRS family. The implementation in `fsrs_memory.py` is a simplified tick-based model with parameters $w_{17}$–$w_{20}$ as listed below; it is not the official FSRS-6 scheduler, and the widely cited 500-million-review figure describes the FSRS literature, not a training run performed for this code. Parameter names here follow the code, not the official FSRS-6 21-parameter indexing, and no claim is made that this implementation equals official FSRS-6.

> **Terminology note (EE vs. SuperMemo SM-20).** In parts of the spaced-repetition literature the exponential curve above is loosely attributed to SuperMemo. We do not follow that usage, and we do not implement SM-20. SuperMemo published its early algorithms in full—**Algorithm SM-2** (Woźniak, 1990) is the last of these—whereas the later commercial releases, **SM-3 through SM-20**, are proprietary and their forgetting-curve formulas have never been publicly disclosed. A model whose specification is unavailable can be neither implemented nor independently audited, and therefore cannot serve as a reproducible scientific baseline. Accordingly, the exponential baseline used throughout this paper is the **classical Ebbinghaus curve** $R(t)=\exp(-t/S)$, which we denote **EE** (Ebbinghaus-exponential). All comparisons labelled "FSRS vs. EE" contrast a power-law model against this classical exponential curve; the contribution is a comparison of *forgetting-curve functional forms*, not a benchmark of any commercial product.

Each agent maintains a **CognitiveMemoryBank** consisting of multiple lessons (e.g., `leverage_risk`, `liquidity_crisis`, `bull_market_complacency`). Each lesson has three core state variables:

- **Retrievability** $R(t)$: probability of recalling the memory at tick $t$. Under FSRS:
  $$
  R(t) = \left(1 + \frac{\text{factor} \cdot t}{S}\right)^{-w_{20}}
  $$
  where $t$ is ticks since last review (market shock), $S$ is stability (in days), and $\text{factor} = (0.9^{-1/w_{20}} - 1)$ encodes the target post-review retrievability (0.9). This produces a **power-law decay** $R \sim t^{-w_{20}}$ at long times, in contrast to EE's exponential $e^{-t/S}$.

- **Stability** $S$: measures how long the memory lasts (days). Initially $S_0 = 45$ (synthetic-exercise value, see Section 4.3; not re-identified on real data, see Section 6.4, limitation 12). $S$ grows when the agent experiences market shocks, representing institutionalized risk controls.

- **Difficulty** $D \in [1,10]$: complexity of the lesson. Harder concepts decay faster. $D$ maps to financial instrument complexity (e.g., plain equity $D=4$, structured products $D=9$).

FSRS stability update after a shock of grade $G$:

$$
S' = S \cdot \exp\left( w_{17} \cdot (G - 3 + w_{18}) \cdot S^{-w_{19}} \right)
$$

Parameters (values used in `fsrs_memory.py`, recalibrated in v55 by a joint fit to 12 VIX/VXO events; see Section 4.3): $w_{17}=0.6096$, $w_{18}=0.0496$, $w_{19}=0.1841$, $w_{20}=0.4$ (factor $= 0.3013$).

**Economic interpretation:**
- $S^{-w_{19}}$ implements **marginal diminishing**: large $S$ → smaller growth. This is the mathematical origin of the fat tail.
- $G=1$ (systemic collapse) yields negative exponent → $S$ collapses, at $S=45$ to 55.4% of its value (41.3% at $S=5$, 71.7% at $S=1000$), modeling a Minsky Moment where institutional memory is sharply reduced but not wiped out.
- $G=4$ (minor corrections) yields large positive exponent → $S$ multiplies by $1.37\times$ at $S=45$ (1.61\times at $S=5$, 1.20\times at $S=1000$), capturing "Great Moderation" complacency at a much smaller gain than the Anki-parameter version.

FSRS produces **fat-tailed forgetting**: in the 100-agent simulation of Section 5.1, $R(500) = 0.7185$ vs EE's $0.000015$—an approximately **47,000\times difference** (the archived rounded inputs 0.718491 / 0.00001528 give 47,022, but the last digits are not significant). This aligns with empirical market memory: post-2008 risk aversion persisted for years, not months. (The closed-form single-memory values at $S=45$ are different—FSRS 0.55548, EE $1.5 \times 10^{-5}$—because the simulation includes shocks, leverage feedback, and contagion; do not mix the two sets.)



### 3.2 Memory Contagion

Agents are nodes in an undirected graph `G = (V, E)` where edges represent information-flow relationships (e.g., social networks, professional ties). Each agent i has true retrievability R_true,i(t) from their memory bank. Perceived retrievability is:

R_perceived,i(t) = (1 - α) · R_true,i(t) + α · mean_{j ∈ N(i)} (R_true,j(t))

where α ∈ [0,1] is the contagion strength (set to α = 0.6 in the synthetic exercise; not re-identified on real data, see Section 6.4, limitation 12). Agents use R_perceived for decision-making (trading behavior). This creates a **memory contagion effect**: a panic in one cluster raises neighbors' perceived risk even if their own memory hasn't decayed.

### 3.3 Control Probe Setup: Governance and Intervention

This section documents the intervention machinery used by the control probes in Sections 5.2 and 5.5; it is a probe setup, not a policy proposal — in the 30-agent FSRS regime the machinery never activates (see Section 5.2).

A **GovernanceManager** observes the population's average retrievability \(\text{avg}_R = \text{mean}_i(R_{\text{perceived},i})\) and variance \(R_{\text{std}}\). When \(\text{avg}_R\) drops below a threshold \(T\), the regulator intervenes with severity \(s \in [0,1]\), which maps to a **shock grade** \(G\) under FSRS in the implementation (`HumanAgent.process_market_shock`, severity thresholds 0.8 / 0.5 / 0.2):

| Severity \(s\) | Grade \(G\) in code | Economic Interpretation |
|-----------------|---------------|------------------------|
| 0.0–0.19       | —             | No intervention |
| 0.2–0.49       | \(G=3\) (Good)  | Moderate intervention |
| 0.5–0.79       | \(G=2\) (Hard)  | Stronger severity, but a *negative* stability update under the formula below |
| 0.8–1.0        | \(G=1\)    | Extreme (system reset; large negative update) |

The intervention triggers `process_market_shock` for all agents. Crucially, only $G=3$ and $G=4$ increase $S$; $G=1$ and $G=2$ decrease it. The mapping above is the code mapping (severity thresholds 0.8 / 0.5 / 0.2), not the v43 table, which had the 0.2–0.79 range reversed. In the 30-agent grid, interventions were 0.0 for both the baseline and the (T=0.45, s=0.40) configuration, so this mapping does **not** affect Table 2; it matters only where interventions actually occur (notably the T=0.65 grid configurations and the 1000-agent scaling run).

| Grade \(G\) | Multiplier at $S=5$ | Multiplier at $S=45$ | Multiplier at $S=1000$ |
|---------------|----------------------|----------------------|------------------------|
| $G=1$ | 0.413 (−58.7%) | 0.554 (−44.6%) | 0.717 (−28.3%) |
| $G=2$ | 0.650 (−35.0%) | 0.750 (−25.0%) | 0.850 (−15.0%) |
| $G=3$ | 1.023 (+2.3%) | 1.015 (+1.5%) | 1.009 (+0.9%) |
| $G=4$ | 1.609 (+60.9%) | 1.374 (+37.4%) | 1.196 (+19.6%) |

Example: the same severity $s=0.2$ maps in code to $G=3$, giving +2.3% at $S=5$ and +0.9% at $S=1000$—not the v43 claim of +25% / +0.1%, which used the wrong grade and the wrong sign. *Regulatory measures matter most when institutions are fragile* is now weak for $G=3$ (+1.5% at $S=45$) and moderate only for $G=4$ (+37.4% at $S=45$), and it remains false for $G=2$: a Hard intervention shrinks stability, it does not consolidate it.

### 3.4 Reward Formulation (v4)

We define the regulator's reward at each tick:

```
r_t = 10·avg_R                                    # Dense term
      + 1·[avg_R > 0.2]                           # Survival bonus
      + 20·[0.5 ≤ avg_R ≤ 0.7]                    # Stability zone (+20)
      - 20·[avg_R < 0.5]                          # Danger zone (-20)
      - 10·[avg_R > 0.7]                          # Complacency zone (-10)
      - (2·severity + 5·R_std)                    # Intervention cost
      + (severity·5)·[severity>0.01 ∧ pre_avg_R<0.5]  # Intervention bonus
```

This reward encourages maintaining avg_R in [0.5, 0.7] while penalizing both danger and complacency zones. The **intervention bonus** directly incentivizes acting when risk perception is already low (pre_avg_R < 0.5), overcoming the RL exploration trap.

**Table: grade impact (formula values).** The table in Section 3.3 above gives the exact multipliers. Figure 5 in v43 is withdrawn in v44: its generation script used the parameter list $[w_{17}, w_{18}, w_{19}, w_{20}]$ indexed by grade as the exponent, which is not the stability-update formula, so neither the figure nor its caption can be retained. Replacement figure (v55):

![Correct FSRS grade impact](figures/fig5_grade_impact_v55.png){#fig:grade_impact_v55 width=90%}

**Figure 5 (v55).** Correct stability update $S' = S \cdot \exp(w_{17} \cdot (G - 3 + w_{18}) \cdot S^{-w_{19}})$ with $w_{17}=0.6096$, $w_{18}=0.0496$, $w_{19}=0.1841$. Panel (a): multiplier $S'/S$ vs initial $S$ (log scale); panel (b): multiplier vs grade $G$ at $S=5, 45, 1000$. Values match the table exactly (at $S=45$: 0.554 / 0.750 / 1.015 / 1.374 for $G=1$ to $4$). Regenerated under v55 from the J1 parameters (script `experiments/figure_generation/fig5_v55.py`). The v43 figure remains withdrawn; this is a new figure, not a correction of the old file.

---


---



---

## 4. Experiments

### 4.1 Environment (ECOSControlEnv)

We implement a Gymnasium-compatible environment:

- **State space** (6-dimensional continuous): [avg_R, R_std, crisis_prob, tick_norm, last_severity, time_since_inter]
- **Action space**: intervention_severity ∈ [0,1] (continuous)
- **Episodes**: 300 ticks (simulation horizon)
- **Agents**: 30 (default), 300, 1000 (scaling tests)

Agents' cognitive memories start with $S_0 = 45$ in the v48 grid and paired rerun, where S is set explicitly to 45.0 on every lesson after reset (scripts `grid_s45.py`, `paired_s45.py`), and in the v49 1000-agent rerun and Section 5.6 reruns (S set explicitly to 45.0 on every lesson after reset, or after agent creation where the script builds agents directly; see Sections 5.3 and 5.6). The v50 reruns use the fixed environment (isolated-agent fallback, Section 5.4); the Section 5.6 scripts do not use ECOSControlEnv and are unaffected by the fix. Correction (v48 audit): the original grid and the v45 paired rerun did not set S at all and therefore ran the default memory bank (initial stabilities 5/3/2 for the three default lessons); their numbers are retained for audit only and are superseded by Section 5.2. EF is a legacy SM-2 parameter and is not used in FSRS runs. The info_flow network is Erdős–Rényi with p=0.1 in the grid environment (the robustness sweep in v43 did not actually vary p; see Section 5.4).

### 4.2 Baselines

1. **Fixed Threshold**: intervene if avg_R < T, with severity S. Default T=0.3, S=0.6.
2. **Random**: random severity every 10 ticks. (Defined here for completeness; no Random-baseline results are reported in Section 5 and no claim in v44 depends on it.)
3. **RL Baselines**: PPO agents trained on v3/v4 rewards (reported for completeness; they underperformed).

### 4.3 Parameter Setting (Synthetic Calibration Exercise)

Before control optimization, we set three environment parameters from a synthetic five-event exercise (see limitation 12 for the real-data status):

- **S_initial**: initial stability (days)
- **α**: contagion strength
- **severity**: mapping from regulator's action to memory consolidation

Using a grid search over a 5-event synthetic simulator (1987, 2000, 2008, 2020, 2022), we obtain:

- **S_initial = 45 days** (initial stability; for comparison, an EE curve with $S=45$ would have half-life $45 \cdot \ln 2 \approx 31$ days, whereas the FSRS power-law curve has no comparable half-life—under the paper's own FSRS formula with the v55 parameters, $R=0.5$ would take about 695 days at $S=45$, so $S$ must not be read as a half-life)
- **α = 0.6** (strong contagion)
- **severity_crisis = 0.5** (baseline intervention impact)

These values are the simulation parameter set (v51: retained as convention, not as real-data-calibrated estimates; see Section 6.4, limitation 12).

**v55 recalibration (J1 joint fit).** The FSRS kernel parameters $w_{17}$−$w_{20}$ used in v55 (0.6096/0.0496/0.1841/0.4, factor 0.3013) replace the Anki defaults: they are the joint fit to 12 VIX/VXO events (1987, 2000, 2008, 2020, 2022 plus 7 further VIX peak days), mean total loss 0.0360 across the 12 events, with post-shock stability $S_0^* = 0.5$ weakly identified (roughly 0.5–1.1). The default memory bank is rescaled by $k = 6.7$ (loaded mean 3.33 / 0.5) to retail 0.75/0.45/0.30 (unloaded 0.60/2.25; institution leverage 7.5 via the ×10 multiplier). Only two v55 families consume the default bank (the original-protocol grid in Section 5.2 and the end-to-end run in Section 5.6.1); all other v55 families set $S$ explicitly or force $S=45$, so they test the kernel, not the bank scale. The $k$ robustness check (Section 5.2) covers $k = 3.3$–$6.7$; $k$ itself is not identified, only bracketed (see Section 6.4, limitation 19). In v49 they are actually applied in the grid, the paired rerun, the p/S sweep, the 1000-agent rerun, and the Section 5.6 reruns (S set explicitly after reset, or after agent creation where the script builds agents directly; see Sections 5.3 and 5.6 for the as-run settings). In v50 the grid, the paired rerun, the p/S sweep, and the 1000-agent rerun are repeated with the fixed environment (Section 5.4); the Section 5.6 reruns need no repetition because they do not use ECOSControlEnv. The original runs used the default memory bank (initial stabilities 5/3/2) and are retained for audit only.

### 4.4 Control Probes (Design)

We explore two approaches:

#### 4.4.1 Reinforcement Learning (PPO)

We train PPO agents with MLP policies on the ECOS environment using rewards v1–v4. Despite architectural adjustments (reward shaping, entropy regularization), PPO fails to converge to a deterministic policy that beats the fixed threshold baseline. The learned policies either:
- Output mean ≈ 0 and rely on stochasticity during training (v3, v4)
- Learn to never intervene (v1)

We attribute failure to **sparse and delayed rewards**: an intervention's positive effect manifests after 30–50 ticks, making credit assignment difficult for on-policy algorithms with short rollouts (2048 steps). Value function estimates have near-zero explained variance, leading to poor policy gradients.

#### 4.4.2 Grid Search over Threshold Policies

Given RL's poor performance, we perform an exhaustive grid search over discrete threshold-severity pairs:

- Thresholds T ∈ {0.25, 0.35, 0.45, 0.55, 0.65}, plus the baseline T=0.30 appended by the script (6 thresholds x 4 severities = 24 configurations; this reconciles the 20-configuration list with the 24-configuration count in Section 5.2)
- Severities S ∈ {0.2, 0.4, 0.6, 0.8}

Each configuration is evaluated over 10 episodes (mean return). No optimal policy is discovered (see the paired rerun in Section 5.2):

- **No identifiable optimum**: the paired same-seed rerun in Section 5.2 gives identical outcomes for (T=0.45, s=0.40) and (T=0.30, s=0.60); thresholds never trigger under FSRS.

![Grid search heatmap](figures/fig2_grid_search.png){#fig:grid_search width=90%}

**Figure 2.** Grid search heatmap over threshold $T$ and severity $s$ (original run, seed-confounded; see Section 5.2 for the paired rerun that supersedes the optimum claim). Original means: (T=0.45, s=0.40) ~3947; baseline (T=0.30, s=0.60) ~3434. The 15.0% gap is a seed/network artifact, not a policy effect.

Original grid means were **3947 ± 1177** vs **3434 ± 1181**, but the two configurations were evaluated on different seed sets (seed_offset 9 vs 22), so this gap is not evidence of a policy effect; see the paired rerun in Section 5.2.

### 4.5 Stress Tests and Robustness

We validate the threshold configurations on:

1. **1000-agent populations** (network effects)
2. **Varied network densities** $p \in \{0.05, 0.10, 0.20\}$
3. **Varied memory decay rates** $S \in \{30, 45, 60\}$

The 1000-agent test uses the fixed parameters (T=0.55, s=0.20) against baseline (T=0.30, s=0.60) (corrected in v47; see Section 5.3), i.e., no re-optimization. The network-density / initial-stability sweep is reported with correctly parameterized results in Section 5.4 (v47 pre-fix, v50 post-fix).

The grid search heatmap (**Figure 2**) is retained for audit; it does not identify an optimal pair (see Section 5.2).

---

## 5. Results

Reading guide: the main result is the FSRS-vs-EE contrast in Section 5.1. Sections 5.2 and 5.5 report control probes (threshold grid; PPO) whose finding is negative; Sections 5.3, 5.4, and 5.6 report scale robustness, the robustness sweep, and extended validation of the memory engine.

### 5.1 FSRS vs EE: A Contrastive Analysis

To quantify the impact of switching from exponential (EE) to power-law (FSRS) forgetting, we ran a head-to-head comparison with 100 agents (55 FSRS, 45 EE) over 500 ticks, from `results/comparison/fsrs_vs_ee.json` (where the EE group is keyed `sm20` in the file—a legacy label for the EE baseline, not commercial SM-20). Figure 4 shows the average retrievability $\overline{R}$ trajectories.

**Key empirical differences:**

| Metric | EE (Exponential) | FSRS (Power-Law) | Ratio |
|--------|--------------------|-----------------|-------|
| $R(100)$ | 0.1108 | 0.7968 | 7.19\times |
| $R(300)$ | 0.0013 | 0.7427 | 571\times |
| $R(500)$ | **0.000015** | **0.7185** | **~47,000\times** |
| Final leverage | 10.00\times | 6.35\times | 0.64\times |
| Crisis events ($R<0.3$) | 45 of 45 EE agents (100% of the EE group) | 0 agents (0%) | — |

The contrast is stark. EE's exponential decay causes **catastrophic forgetting**: by tick 100, average $R$ has already fallen to 0.111; by tick 300 to 0.0013; by tick 500 to 0.000015—all 45 EE agents are below the crisis threshold and levered to the maximum 10.00\times. FSRS's power-law decay retains $R=0.719$ at tick 500, keeping leverage at a sane 6.35\times. The fat tail—$R \sim t^{-0.4}$—means memory persists for years of simulated time. Ratios in the table are rounded to the nearest thousand; the archived inputs 0.718491 / 0.00001528 give 47,022, but the last digits of the archived values are not significant, so the ratio is reported as approximately 47,000.

**Caliber note (v55).** The table above is the published-caliber result: its FSRS group carries agent-type multipliers (mean initial stability 19.70), while its EE group is uniform at 45.0, so the two groups are not homogeneous in the same sense (see Section 5.7 and Section 6.4, limitation 13). The published figures (0.7185 / 0.000015 / ~47,000$\times$) are retained unchanged. Table 5.1b below reports the same tick-500 contest under the new homogeneous and heterogeneous calibers defined in Section 5.7; the two calibers are not interchangeable.

| $S_0$ caliber (v54) | FSRS $\overline{R}(500)$ | EE $\overline{R}(500)$ |
|---|---|---|
| Homogeneous (all agents, all lessons $S_0 = 45$) | 0.55548 (C1) | 0.00001 (C3) |
| Lognormal, median 45, $\sigma=1$ | 0.55912 (C2) | 0.01894 (C4) |
| Lognormal, median 45, $\sigma=1.5$ | 0.56036 (C2) | 0.05733 (C4) |
| Lognormal, median 45, $\sigma=2$ | 0.55990 (C2) | 0.10201 (C4) |
| Two-point 11.68 / 173.34 | — (not run; see Section 5.7) | 0.02674 (C4′) |
| Uniform [0.89, 2268] | — (not run; see Section 5.7) | 0.54191 (C4″) |

Table 5.1b (v55): tick-500 mean retrievability $\overline{R}(500)$ by $S_0$ caliber, 10 seeds per cell. FSRS is nearly insensitive to heterogeneity (0.55548 → 0.55990); EE rises monotonically with heterogeneity (0.00001 → 0.10201 at $\sigma=2$, 0.54191 under the uniform stress test).

Figure 4 visualizes this divergence. The EE curve (dashed red) plunges exponentially, crossing the danger threshold ($R=0.5$) between tick 30 (0.525) and tick 40 (0.420) and approaching zero by tick 300. The FSRS curve (solid blue) decays in the first 100 ticks then flattens dramatically, staying above 0.7 throughout (0.909 at tick 10 to 0.719 at tick 500)—that is, above the reward target zone $[0.5, 0.7]$, not inside it.

![FSRS vs EE comparison](figures/fig4_fsrs_vs_ee.png){#fig:fsrs_vs_ee width=90%}

**Economic interpretation.** The EE model implies that market participants fully forget a crisis on a short scale: under the EE curve, $3S = 135$ days is 0.37 years, not 1–2 years. Empirically, post-2008 risk aversion persisted through at least 2015 (volatility regimes, trader psychology surveys). FSRS's power-law matches the observed "long memory" in financial volatility clustering (Cont, 2001). The leverage difference is equally telling: under EE, agents reach maximum leverage within 300 ticks—mirroring pre-2008 behavior where risk controls evaporated. FSRS's more gradual leverage increase (6.35\times at tick 500) better matches observed leverage cycles that build over 5–10 years.

**Implication for policy.** Regulators using EE-based models would **underestimate memory persistence** and potentially intervene too late, assuming agents have already forgotten. FSRS suggests that even at tick 300, $R = 0.743$—agents are still quite risk-aware. No intervention threshold is identified by the 30-agent grid (Section 5.2); a pre-emptive trigger — act while memory is still strong enough that a mild intervention consolidates it — is a hypothesis for future work with environments in which thresholds actually trigger, not a finding of this experiment.

---

### 5.2 Control Probe I: Threshold Grid

**Figure 1** displays avg_R trajectories for the two threshold configurations (labels retained from the original run; trajectories are identical in the paired rerun) under FSRS.

![Baseline vs optimal avg_R trajectories](figures/fig1_trajectory.png){#fig:baseline_optimal width=90%}

Quantitatively (**Table 2, original grid, seed-confounded and run under the default bank 5/3/2, not S=45 — retained for audit only; superseded by the paired tables below**, 30 agents, 300 ticks, 10 episodes):

| Policy | Return | Interventions | Target Zone % | Crisis Steps |
|--------|--------|---------------|---------------|--------------|
| Baseline (T=0.30, s=0.60) | 3434 ± 1181 | 0.0 | 45.0% | 0 |
| (T=0.45, s=0.40) [labelled 'Optimal' in the original run] | 3947 ± 1177 | 0.0 | 51.3% | 0 |

**Paired same-seed rerun (v45, supersedes Table 2 as policy evidence).** Same networks per episode (seed_offset 10 and 110, 10 episodes each, 30 agents, 300 ticks; script `same_seed.py`, output `same_seed.json` in the replication pack):

| Seed set | (T=0.45, s=0.40) return | (T=0.30, s=0.60) return | Interventions (both) | Target zone (both) |
|---|---|---|---|---|
| 10 | 3836.30 ± 1126.90 | 3836.30 ± 1126.90 | 0.0 | 49.97% |
| 110 | 3725.26 ± 1063.03 | 3725.26 ± 1063.03 | 0.0 | 48.63% |

Outcomes are identical to the cent within each seed set, and per-episode returns are identical, because neither threshold ever triggers: avg_R never falls below 0.30 or 0.45 under FSRS in these runs, so the intervention code path is never entered and the threshold/severity parameters cannot affect the trajectory. The original Table 2 gap (3947 vs 3434, target zone 51.3% vs 45.0%) is therefore a seed/network artifact: in the original grid each configuration was evaluated on a different seed set (`seed_offset=i` in `grid_search_control.py`), and `ECOSControlEnv.reset` uses the seed to draw the p=0.1 information network, so different seeds mean different contagion topologies. **Revised claim: under FSRS on 30 agents the effective policy is non-intervention, and no threshold-severity optimum is identified by this experiment.** This is a statement about identifiability in this regime, not a proof that thresholds could never matter: in a regime where avg_R falls below threshold, the intervention code path would be entered and the parameters could matter. FSRS agents naturally maintain risk awareness; interventions are not merely rare, they do not occur in these runs.

**Paired same-seed rerun at S=45 (v48, pre-fix; superseded by the v50 post-fix rerun below).** Same design as v45, plus S set explicitly to 45.0 on every lesson after reset (script `paired_s45.py`, output `paired_s45.json` in the replication pack):

| Seed set | (T=0.45, s=0.40) return | (T=0.30, s=0.60) return | Interventions (both) | Target zone (both) |
|---|---|---|---|---|
| 10 | -314.71 +/- 128.20 | -314.71 +/- 128.20 | 0.0 | 0.0% |
| 110 | -304.23 +/- 122.01 | -304.23 +/- 122.01 | 0.0 | 0.0% |

Outcomes are again identical within each seed set, and per-episode returns are identical, because neither threshold ever triggers at S=45 either: avg_R stays above the target zone, so the reward is dominated by the -10 per-tick out-of-zone penalty and the target-zone time is 0%. The v45 paired numbers (+3836/+3725, zone ~49%) were the same comparison run under the default bank, not under S=45; the conclusion (no optimum identified, effective policy non-intervention) is unchanged, but the absolute returns and zone times are not comparable across S settings.

**Paired same-seed rerun at S=45, post-fix environment (v50) — superseded by the v55 A-grid rerun.** The v50 paired tables are superseded by the v55 A-grid C1 rerun in Section 5.7, which uses the recalibrated kernel: the two paired configurations (T=0.45, s=0.40) and (T=0.30, s=0.60) both return 2209.38 with 0.0 interventions and 28.67% target-zone time, so the paired conclusion (no optimum identified, effective policy non-intervention for thresholds up to 0.55) is confirmed under the new kernel; the paired protocol itself was not rerun in v55. The pre-fix S=45 numbers (-314.71 on seed set 10, -304.23 on seed set 110) remain audit-only.

**Full grid at S=45 (v48).** Script `grid_s45.py`, output `grid_s45.json`: all 24 configurations (6 thresholds including baseline 0.30, 4 severities, 10 episodes each, seed_offset by configuration as in the original grid), returns from -325.19 (T=0.45, s=0.40) to -247.56 (T=0.30, s=0.80), baseline (T=0.30, s=0.60) -266.45 +/- 136.30, interventions 0.0 and target zone 0.0% in every configuration, crisis steps 0 throughout. As in the original grid, configurations still use different seed sets, so the spread across configurations is not a policy comparison; the paired table above is the controlled comparison. The v44/v45 statement that interventions were 0.0 except at T=0.65 applied to the default-bank grid only and does not hold at S=45 under the new kernel, where the 0.65 threshold does trigger (Section 5.7). **Full grid at S=45, post-fix environment (v50) — superseded by v55.** The v50 full-grid table is superseded by the v55 A-grid C1 rerun in Section 5.7: 20 configurations tie at 2209.38 with 0.0 interventions, and only the 0.65 threshold triggers (about 1 intervention per episode, returns about 1941–1943). The pre-fix spread (-325.19 to -247.56) remains audit-only; under the new kernel the threshold/severity parameters are inert up to 0.55, not up to 0.65.

**Original-protocol grid rerun (v55, new kernel + recalibrated bank).** Script `grid_search_control_v55.py`, output `grid_search_control_v55.json`: the original 24-configuration protocol (seed_offset by configuration, audit caliber — see Section 6.4, limitation 21) under the v55 kernel and default bank gives optimal configuration (0.65/0.60) mean 7585.39 (interventions 295.0 per episode) and baseline (0.30/0.60) mean −2618.76 (interventions 36.0 per episode); the original-label 'optimal' (0.45/0.40) gives 2625.33. Interventions run 4.0–296.0 per episode across configurations (vs 0.0 in the old-kernel S=45 runs, because the recalibrated bank's small stabilities and the faster kernel let avg_R fall below thresholds frequently). The clean policy evidence remains the paired S=45 rerun (2209.38 for both configurations, Section 5.7) and the A-grid C1 grid. **Bank sensitivity (k=3.3).** Rerunning the original-protocol grid on the k=3.3 bank gives optimal 7459.13 (−1.7%), baseline −2514.18, the same optimal and baseline configurations, the same top 4 ranking, and total interventions 1347 vs 1516 (−11.1%, in the theoretically expected direction: larger initial S decays more slowly and trips thresholds less often). The grid policy conclusion is therefore robust to k in 3.3–6.7. **End-to-end sensitivity.** The E2E run is bit-identical under k=3.3 and k=6.7 except agent UUIDs (Section 5.6.1), so the E2E reversal is driven by the kernel, not by the bank scale.

**Figure 2** shows the grid search heatmap over threshold-severity space (original default-bank run, retained for audit). No optimum is claimed from this heatmap (see the paired reruns above).

Robustness across network density and initial stability is discussed in Section 5.4, where the v43 robustness table is withdrawn for the reasons stated there; the verified grid summary above is the robustness evidence retained in v44.

### 5.3 Scale Robustness (1000 Agents)

Scaling to 1000 agents: baseline (T=0.30, s=0.60) return **2197**, comparison policy (T=0.55, s=0.20) return **10402**, a **373.6% improvement** (374% rounded). Correction (v47 audit): the paper previously labelled the comparison policy as (T=0.45, s=0.40); the archived script that produced the JSON, `archive/stress_control_optimal.py` (now in the replication pack as `experiments/stress/stress_control_optimal.py`), actually runs (T=0.55, s=0.20) against baseline (T=0.30, s=0.60), and the JSON itself records no threshold/severity, so the (0.45, 0.40) attribution was unsupported. Both policies avoid crises, but the comparison policy maintains **39.6%** time in target zone vs baseline **30.1%**. Interventions are 5.0 per episode for baseline and 15.0 per episode for the comparison policy, over 1000 ticks per episode (the script's max_ticks=1000; this is the run the Section 6.2 'over 1000 ticks' phrase refers to, distinct from the 300-tick grid default in Section 4.1). Seed pairing: the script runs episodes with seed=ep (0, 1, 2) for both policies on the same env object, so episodes 1 and 2 are paired; episode 0 is not paired because `ECOSControlEnv.reset` treats seed=0 as falsy and draws a random seed each time. Given the near-zero variance (std below $10^{-5}$, min/max within $10^{-5}$ of the mean), the episode-0 flaw does not change the result, but it is disclosed here. The near-zero variance is not inconsistent with the 30-agent seed sensitivity: with 1000 agents, per-episode means average over 1000 agents and network variation largely cancels, whereas 30-agent means do not. Scope (v49): the run above used the default memory bank, so its 2197/10402 numbers are not S=45 numbers and must not be compared directly with the S=45 grid numbers in Section 5.2. The 373.6% figure is withdrawn as a policy claim in v49 (see the S=45 rerun below) and is retained above for audit only; it was in any case a point estimate from only 3 episodes, not a robust effect size.

**S=45 rerun (v49).** Script: `experiments/stress/stress_s45.py`; output: `results/stress/stress_1000a_s45.json`. Method: same environment and policies as the original run, with S set explicitly to 45.0 on every FSRS lesson after every reset, followed by an observation recompute. Design change, disclosed: the rerun uses seeds 1, 2, 3 for both policies (paired), avoiding seed 0, which `ECOSControlEnv.reset` treats as falsy and replaces with a random seed (the flaw in the original run's episode 0). Results, 1000 agents, 1000 ticks per episode, 3 episodes per policy:

| Policy | Mean return | Std | Mean interventions | Mean zone % |
|---|---|---|---|---|
| Baseline (T=0.30, s=0.60) | -1065.35 | 0.00 | 0.0 | 0.0 |
| Comparison (T=0.55, s=0.20) | -1065.35 | 0.00 | 0.0 | 0.0 |

Improvement: **0.0%**. Per-episode returns are bit-identical across all three seeds and both policies (-1065.3521728515625 in every episode); per-episode interventions are 0 and zone time 0.0% throughout. Runtimes: baseline 425 s, comparison 486 s. Interpretation: at S=45, avg_R never falls below either threshold even at 1000 agents, so neither policy ever triggers and the two policies are the same policy in effect — hence identical returns are expected for the policy comparison. The cross-seed identity (network realisations differ: 50195, 50389, 50027 undirected edges across seeds 1–3) is recorded here as an observed property of this run, not a claimed mechanism: with zero interventions, the return depends only on the true-R trajectory, which does not move across these seeds in this run. The v47/v48 374% figure therefore does not survive at S=45. The rerun is likewise only 3 episodes per policy, so the 0.0% is a statement about this regime, not a general scaling law — but unlike 373.6%, it is not a sampling artifact in the same way, since the returns are bit-identical rather than merely close.

**Post-fix rerun (v50).** Same script and design, run against the fixed environment (output `stress_1000a_fix.json`): baseline and comparison both -1065.3521728515625 in every episode, interventions 0, zone 0.0%, improvement 0.0% — bit-identical to the v49 pre-fix rerun, including the same network realisations (50195/50389/50027 undirected edges across seeds 1–3). Runtimes: baseline 469 s, comparison 600 s. The fix is a no-op at 1000 agents, as expected: with roughly 50,000 edges over 1000 agents, isolated nodes essentially never occur, so no agent's perceived R changes. The 0.0% conclusion is therefore unchanged by the fix.

**v55 rerun — 0.0% superseded, comparison intervenes.** Same script and design (script `experiments/stress/stress_s45_v55.py`, output `stress_1000a_s45_v55.json`; protocol code identical to `stress_s45.py`, only the output path changed), run against the recalibrated kernel and the fixed environment:

| Policy | Mean return | Std | Mean interventions | Mean zone % |
|---|---|---|---|---|
| Baseline (T=0.30, s=0.60) | 8356.24 | 0.0 | 0.0 | 48.1 |
| Comparison (T=0.55, s=0.20) | 15090.35 | 0.0 | 1.0 | 56.8 |

Improvement: **+80.6%** (+6734.11). Per-episode returns are bit-identical across all three seeds within each policy (8356.240234375 baseline, 15090.353515625 comparison); per-episode interventions are 0 for baseline and 1 for comparison in every episode; zone time 48.1% baseline, 56.8% comparison; crisis steps 0.0 throughout. Runtimes: baseline 643.85 s, comparison 657.76 s. Network realisations are identical to v49/v50 (50195, 50389, 50027 undirected edges across seeds 1–3). Findings. (1) The v49/v50 0.0% improvement does not survive: under the v55 kernel, retrievability decays through the target zone (both policies zone% > 0, vs 0.0% under the old kernel) and crosses the comparison threshold 0.55 but not the baseline threshold 0.30, so only the comparison policy intervenes — confirming the qualitative prediction of the former v55 caveat (homogeneous R(1000) ≈ 0.44 by closed form, below 0.55 but above 0.30). (2) The cross-policy identity is broken while within-policy seed identity holds: the two policies are no longer the same policy in effect. (3) The 3-episode-per-policy limitation from v49 carries over: the +80.6% is a statement about this regime, not a general scaling law — but as in v49, it is not a sampling artifact in the same way, since the returns are bit-identical rather than merely close. The homogeneous R(1000) ≈ 0.44 figure is not directly verified by this run (the script outputs no trajectories) and is not restated as a measured value. The 300-tick non-intervention finding is unaffected (homogeneous R(300) ≈ 0.64, above 0.55; Section 5.7).

The 1000-agent system-stability test in the replication pack (`results/stress/stress_1000a_output.txt`: 1000 agents, 1000 ticks, 2,332,508 trades, 90.80 ms/tick, peak memory 1085.7 MB, 0 errors) is a separate stability run and is not the source of the 2197 → 10402 returns above.

### 5.4 Robustness Analysis (v55: p/S sweep rerun under the recalibrated kernel)

The robustness table and Figure 3 reported in v43 are **withdrawn in v44** and are not reproduced here. Two archived scripts contradict the v43 description: the September robustness script (`experiments/robustness/run.py`) accepts $p$ and $S_{initial}$ as arguments but never passes them to the environment, so identical rows across $p$ cannot be evidence that $p$ has no effect; the April robustness script uses different policies (baseline T=0.75, optimal T=0.80 by default), 300 agents, and 200 ticks, not the paper's stated 30 agents, 300 ticks, and optimal policy (T=0.45, s=0.40). The v43 claim that network density has negligible effect, and the contrast claim that an EE policy improves returns by >1000%, have no archived source in the replication pack and are therefore also withdrawn in v44.

Verified robustness evidence retained in v44 is the grid itself (Section 5.2): across all 24 threshold-severity configurations, returns range from 3288 to 3947, crisis steps are 0 throughout, and interventions are 0.0 except at T=0.65 (0.1–0.6 per episode). A correctly parameterized $p$/$S$ sweep is reported below (v47, pre-fix), rerun post-fix in v50, and rerun under the recalibrated kernel in v55; the v44 open item is closed by that sweep, and the artifact is now fixed and its effect measured.

**Correctly parameterized sweep (v47).** Script: `experiments/robustness/ps_sweep.py`; output: `results/robustness/ps_sweep.json`. Method, stated explicitly because the v43 script did not do it: $p$ is applied by rebuilding the info_flow network after `reset` with common random numbers (`RandomState(seed)`, edge iff rand $< p$, so networks are nested across $p$ for a given seed); $S$ is a common initial stability set on all three FSRS lessons after `reset` (this is the paper's claimed $S$ parameterisation, not the default bank's 5/3/2). Fixed reference policy (T=0.30, s=0.60), 30 agents, 300 ticks, seeds 1, 2, 3 (seed 0 avoided, as it is treated as falsy). Returns below are RL rewards (Section 3.4), not market PnL.

| $p$ | $S$ | Mean return | Std | Mean zone % | Mean interventions |
|---|---|---|---|---|---|
| 0.05 | 30 | 1737 | 3329 | 27.8 | 0.0 |
| 0.05 | 45 | 1534 | 2971 | 25.0 | 0.0 |
| 0.05 | 60 | 1316 | 2614 | 22.2 | 0.0 |
| 0.10 | 30 | -263 | 87 | 0.0 | 0.0 |
| 0.10 | 45 | -205 | 89 | 0.0 | 0.0 |
| 0.10 | 60 | -164 | 91 | 0.0 | 0.0 |
| 0.20 | 30 | -202 | 0 | 0.0 | 0.0 |
| 0.20 | 45 | -142 | 0 | 0.0 | 0.0 |
| 0.20 | 60 | -100 | 0 | 0.0 | 0.0 |

Findings. (1) Network density is **not** negligible, contradicting the v43 claim: target-zone time falls from 22–28% at $p=0.05$ to 0% at $p \geq 0.10$, and mean reward changes sign. (2) At low $p$, seed dominates: at $p=0.05$, $S=30$, per-episode returns are -656, -577, +6445 (std 3329), so 3-episode means at $p=0.05$ are unreliable. (3) Mechanism, verified: in `ECOSControlEnv._compute_obs`, an agent with no predecessors gets perceived $R = (1-\alpha) \times$ true $R = 0.4 \times$ true $R$, not true $R$. Isolated-agent counts (script `experiments/robustness/iso_check.py`): at $p=0.05$, seeds 1–3 have 4, 3, 10 isolated agents; at $p=0.10$, 1, 0, 0; at $p=0.20$, 0, 0, 0. Focused check ($p=0.05$, $S=45$): per-episode zone 0%, 0%, 75% — the seed-3 episode, with 10 isolated agents, has mean perceived $R$ dragged from ~0.78 (true) toward ~0.62, into the target zone, earning +20/tick instead of -10/tick, for a return of +5735 vs about -600 for the other seeds. The $p$ effect in this environment is therefore largely an isolated-agent artifact of the contagion formula, not a genuine contagion benefit; the fix — fall back to true $R$ when an agent has no neighbours — is implemented in v50 (commit 7ee820c) and the post-fix rerun below measures its effect; no policy recommendation is drawn from the pre-fix $p$ sweep. (4) The $S$ effect is $p$-dependent: at $p \geq 0.10$, higher $S$ gives higher (less negative) reward monotonically; at $p=0.05$, higher $S$ gives lower mean reward, driven by the isolated seed-3 episode (6445 → 5735 → 5012 as $S$ rises). No clean '$S$ improves returns' claim is made. (5) Interventions are 0.0 in all 27 episodes, so this sweep tests reward sensitivity to $p$/$S$ through the $R$ trajectory, not intervention policy.

**Post-fix rerun (v50) — numbers superseded, qualitative findings retained.** Same script and design, run against the fixed environment (script `ps_sweep.py`, output `ps_sweep_fix.json`): post-fix, the three $p$ rows are identical at every $S$, so network density has exactly zero effect in this regime — the v47 finding that density is not negligible is withdrawn; the low-$p$ seed dominance is gone with the artifact; and the $S$ effect is clean and $p$-independent (higher $S$ gives higher, less negative reward monotonically). No mechanism is claimed for the exact $p$-identity; it is recorded as an observed property of this run. The v50 numeric table is old-kernel; the S=45 column was already superseded by the v55 A-grid C1 rerun in Section 5.7. The v55 rerun below replaces the pending item.

**v55 rerun — numbers replaced, $S$ direction reversed.** Same script and design (script `experiments/robustness/ps_sweep_v55.py`, output `ps_sweep_v55.json`; protocol code identical to `ps_sweep.py`, only the output path changed), run against the recalibrated kernel and the fixed environment:

| $p$ | $S$ | Mean return | Std | Mean zone % | Mean interventions |
|---|---|---|---|---|---|
| 0.05 | 30 | 4168.23 | 0.0 | 52.33 | 0.0 |
| 0.05 | 45 | 2209.38 | 0.0 | 28.67 | 0.0 |
| 0.05 | 60 | 159.71 | 0.0 | 4.67 | 0.0 |
| 0.10 | 30 | 4168.23 | 0.0 | 52.33 | 0.0 |
| 0.10 | 45 | 2209.38 | 0.0 | 28.67 | 0.0 |
| 0.10 | 60 | 159.71 | 0.0 | 4.67 | 0.0 |
| 0.20 | 30 | 4168.23 | 0.0 | 52.33 | 0.0 |
| 0.20 | 45 | 2209.38 | 0.0 | 28.67 | 0.0 |
| 0.20 | 60 | 159.71 | 0.0 | 4.67 | 0.0 |

Findings. (1) $p$-identity holds exactly: the three $p$ rows are identical at every $S$ (full-precision means equal), reproducing the v50 property under the new kernel. (2) Seed-invariance is observed: within each configuration the three seeds give identical per-episode returns (std 0.0), so the sweep collapses to a curve in $S$ only; no mechanism for this invariance is claimed. (3) The $S$ effect reverses the v50 direction: mean return strictly decreases in $S$ (4168.23 → 2209.38 → 159.71), and mean zone % decreases with $S$ (52.33 → 28.67 → 4.67). The v50 sentence that higher $S$ gives higher reward does not survive the recalibration and is superseded by this table. (4) Interventions are 0.0 in all 27 episodes and crisis steps are 0.0, so as in v47/v50 this sweep tests reward sensitivity to $p$/$S$ through the $R$ trajectory, not intervention policy; no policy conclusion is drawn. (5) Cross-validation: the $S=45$ row (2209.38, zone 28.67%, interventions 0.0) matches the v55 A-grid C1 baseline in Section 5.7 exactly, from an independent script. A mechanism consistent with the $S$ direction — higher $S$ slows $R$ decay, so avg_R spends more time above the 0.7 complacency bound and less time in the [0.5, 0.7] target zone — is offered as interpretation only: the sweep outputs no trajectories, so it is not directly verified.
### 5.5 Control Probe II: Why RL Failed

We document the complete failure of PPO across three reward variants:

| Version | Timesteps | Eval Return | Interventions | Diagnosis |
|---------|-----------|-------------|---------------|-----------|
| v1 (original) | 10k | -3421 | 0 | Learned no-op; intervention cost too high |
| v3 (dense shaping) | 50k | 124 | 0 | Stochastic gaming; deterministic mean ≈ 0 |
| v4 (intervention bonus) | 30k | -1440 | 3 | Poor timing; crisis still frequent |

Root causes:
- **Sparse/Delayed Rewards**: Intervention benefits appear after 30–50 ticks, but rollouts are 2048 steps; credit assignment is weak.
- **Value Function Failure**: Explained variance near 0; the critic cannot accurately forecast long-term intervention value.
- **Exploration Trap**: During training, stochasticity occasionally maintains avg_R, inflating rollout rewards (~1000) but deterministic evaluation reveals mean action ≈ 0.

A compounding factor, documented in the online-RL literature, is that this environment is non-stationary: retrievability and stability evolve endogenously within an episode, so the reward landscape the agent faces drifts over time, and online RL in non-stationary context-driven environments is known to suffer catastrophic forgetting of previously learned behavior (Hamadanian et al., 2025).

In contrast, grid search searches the deterministic policy space directly, bypassing sample inefficiency, but on 30 agents it still did not identify an optimal threshold (see Section 5.2).

---



### 5.6 Additional Validation with Extended Experiments

To further validate the FSRS engine under more realistic and longer-horizon conditions, we conducted three supplementary experiments: (1) end-to-end trading performance with HumanAgent, (2) Monte Carlo robustness over 30 independent runs, and (3) a 10-year (3650-tick) long-term memory persistence study. All experiments use the FSRS engine with α=0.6. Audit (v49): none of the three original scripts sets S or uses ECOSControlEnv; they build HumanAgent directly with the default memory bank (leverage_risk S=5.0, liquidity_crisis S=3.0, bull_market_complacency S=2.0; the LESSONS dict also defines panic_selling S=4.0 and regulation_change S=15.0, which the default bank does not load). The as-published numbers below are therefore default-bank numbers, not S=45 numbers. Each experiment was rerun at S=45 in v49 (S set to 45.0 on every FSRS lesson after agent creation); the rerun numbers are reported alongside the originals, and the originals are retained for audit. In v55 the three experiments are rerun again under the recalibrated kernel (Sections 5.6.1–5.6.3 report the v55 numbers); the original default-bank numbers are retained for audit where the protocol was not rerun, and the v54 S=45 numbers are superseded. The default bank in v55 carries the recalibrated stabilities (retail 0.75/0.45/0.30); only the end-to-end run consumes the bank among the three experiments (the Monte Carlo and 10-year reference protocols set S=45 explicitly), so bank-scale effects appear only in Section 5.6.1.

#### 5.6.1 End-to-End Trading Performance

We ran a full multi-agent trading simulation over 200 ticks across three markets (BTC, ETH, AAPL) with 10 agents (1 HumanAgent using FSRS, 5 RetailAgents, 2 InstitutionAgents, 2 MarketMakers). The HumanAgent achieved (v55, recalibrated kernel + recalibrated default bank):

- **Final value**: $150,520.34 (from $250,000)
- **Profit/Loss**: $−99,479.66 (−39.8% return)
- **Maximum drawdown**: 47.27%
- **Total trades**: 67 executions
- **Shocks experienced**: 9 market events (same 9 ticks and severities as the archived run, same seed)

The v55 result reverses the v54 profitability conclusion for this run (v54: +$7,091.30 (+2.8%), maximum drawdown 35.7%, 51 trades; v55: −$99,479.66 (−39.8%), 47.27%, 67 trades; full old→new table in CHANGELOG_v55). The shock sequence, seed, and RNG streams are identical to the archived run, so the reversal comes from the kernel and bank behavior change, not from a different random draw; the decision-level mechanism was not instrumented and is not claimed here. The other 9 agents record 0 trades and 0 PnL, as in the archived run. Run configuration: 200 ticks, seed 20260418, markets BTC/ETH/AAPL, shock probability 0.03. The full-run output records PnL, drawdown, trades, and final value, but not final retrievability; the S=45 R-only rerun (v55) gives final HumanAgent R = 0.98627 (same recording caliber as the archived rerun). The bank sensitivity rerun (k=3.3) reproduces the full run bit-for-bit except agent UUIDs (Section 5.2), so the reversal is driven by the kernel, not by the bank scale.

#### 5.6.2 Monte Carlo Robustness (30 Runs, 250 Ticks)

We ran 30 stochastic simulations with different seeds, comparing FSRS against EE (100 agents, 250 ticks each). The table below is the archived original-protocol result, retained for reference; v55 reruns are given in the paragraph following the table.

| Metric | EE (Exponential) | FSRS (Power-Law) | Difference |
|--------|--------------------|-----------------|------------|
| Final $R$ (mean ± std) | 0.6040 ± 0.2493 | 0.9421 ± 0.0581 | +56.0% mean |
| Final $R$ (median) | 0.7224 | 0.9671 | — |
| Final $R$ (min) | 0.0345 | 0.7824 | — |
| Final $R$ (max) | 0.9643 | 0.9996 | — |

FSRS shows **lower variance** (std 0.058 vs 0.249) and **higher minimum** retrievability. In the 30 runs, 19 EE runs exceeded R=0.5; all 30 FSRS runs exceeded R=0.5, and 27 exceeded R=0.85. Setup (fills the missing detail): 30 runs, seeds 0–29, 250 ticks, sample every 10 ticks, shock_prob 0.02, severity range [0.15, 0.4], markets BTC/ETH/AAPL/SPY. S=45 reference rerun (v55; 2-agent protocol, S set to 45.0 explicitly): FSRS final R mean 0.9094 ± 0.0609, median 0.9355, min 0.7316, max 0.9909; 25 of 30 FSRS runs exceed R=0.85 and all 30 exceed R=0.5. EE is unchanged (mean 0.6040 ± 0.2493, median 0.7224, min 0.0345, max 0.9643, 3 of 30 above 0.85). The FSRS–EE reference gap is 0.3054. The 100-agent population Monte Carlo (30 runs, 250 ticks) is reported in Section 5.7 (A-mc): FSRS homogeneous 0.9140 (24/30 above 0.85), EE homogeneous 0.6455 (8/30).

#### 5.6.3 Long-Term Memory Persistence (10-Year Horizon)

We extended simulation to **3650 ticks** (~10 years) with 8 runs per engine.

**Key findings (v55)**:

- **FSRS retention**: mean final $R$ = **0.9522** (reference protocol, 2 agents, S=45) and **0.9631** (population protocol, 100 agents per engine)
- **EE decay**: mean final $R$ = **0.9074** (reference) and **0.9351** (population)
- **Trajectory divergence**: by tick 3650 the reference gap is **0.0448** absolute (0.9522 − 0.9074) and the population gap is **0.0280** (0.9631 − 0.9351). Intermediate tick-500 values for the 10-year run are not in the archived summary file and are not claimed in v44. Setup (fills the missing detail): 8 runs, seeds 200–207, 3650 ticks, sample every 50 ticks, shock_prob 0.02, severity range [0.15, 0.4], markets BTC/ETH/AAPL/SPY. Reference detail (v55): FSRS mean 0.9522 ± 0.0587, range [0.8039, 0.9946]; EE mean 0.9074 ± 0.1222, range [0.6010, 0.9903]. Mechanism (v55, superseding the v54 saturation account): under the recalibrated kernel, FSRS stability no longer saturates the 10-year trajectories at the 36500-day cap, so the 10-year gap now discriminates the kernel; the v54 saturation qualifier is superseded. The two protocols must not be mixed.

![FSRS vs EE comparison (10-year horizon)](figures/fig6_fsrs_vs_ee_10year_v55.png){#fig:fsrs_vs_ee_10year width=90%}

**Figure 6.** FSRS vs EE retrievability over 3650 ticks. EE decays to R=0.907 by year 10 (reference protocol); FSRS maintains R=0.952 (reference) and 0.963 (population). Regenerated under v55 from the A-10y reference runs (script `experiments/figure_generation/fig6_v55.py`). The power-law fat tail keeps memory persistent, but under the recalibrated kernel it no longer saturates within the 10-year horizon.

The 10-year result still supports our core claim: **exponential forgetting underestimates long-term memory persistence**. Even after a decade, FSRS agents retain higher risk awareness (R=0.952 reference, 0.963 population) than EE agents (0.907 reference, 0.935 population). This gap has material implications for leverage cycles and crisis recurrence — with the v55 qualification that the gap is smaller than the saturated v54 figure and now discriminates the kernel rather than reflecting a cap artifact.

#### 5.6.4 Summary of Extended Validation

The additional experiments reinforce the main findings:

1. **End-to-end trading**: FSRS agents lose 39.8% with max DD 47.27% over 67 trades in the 200-tick multi-market run (Section 5.6.1) — the v54 profitability finding does not survive the kernel recalibration, and the run is reported as a simulation outcome, not as validation of trading performance.
2. **Monte Carlo stability**: FSRS final R has 0.23\times the EE standard deviation (0.058 vs 0.249) in the original run; in the v55 S=45 reference rerun the ratio is 0.24\times (0.061 vs 0.249), and in the v55 population protocol FSRS holds above 0.85 in 24/30 runs (EE homogeneous 8/30), demonstrating robust memory consolidation under the recalibrated kernel.
3. **10-year persistence**: FSRS retains 95.22% retrievability (mean final $R$ = 0.9522 reference, 0.9631 population); EE decays to 90.7% (reference) and 93.5% (population), confirming the fat-tail effect at economic timescales — with the v55 qualification that saturation no longer holds, so this experiment now discriminates the kernel (Section 5.6.3).

Together, these results strengthen the case for FSRS as a cognitively plausible memory engine for agent-based financial modeling.

---


### 5.7 Heterogeneity Adjudication: The Anderson & Tweney Test (v54, rerun v55)

Section 5.1's published-caliber result leaves one challenge open. Anderson & Tweney (1997) showed that averaging exponential forgetting curves over a heterogeneous population can produce an apparent power law: if the 47,000$\times$ gap were an artifact of pooling agents with different stabilities, the paper's central contrast would be overstated. A second, purely textual problem compounds this: Section 5.1's baseline is not homogeneous in the sense the contest requires (see the caliber note in Section 5.1 and Section 6.4, limitation 13). This section reports a dedicated adjudication experiment, run in v54 and rerun in v55 under the recalibrated kernel, that separates the two issues: a true homogeneous cell is run for the first time, and heterogeneity is then introduced under controlled distributions.

**Design.** Four cells are defined. C1 is FSRS-homogeneous: every agent, every lesson, $S_0 = 45$. C2 is FSRS-heterogeneous. C3 is EE-homogeneous, defined identically to C1. C4 is EE-heterogeneous and is the key cell: it is where the Anderson & Tweney mechanism, if real in this model, must show up. Two further EE cells run the A-500 family only: C4′ (two-point) and C4″ (uniform). Three candidate $S_0$ distributions, all quantile-matched to the 45-day convention (not mean-matched, so that the median agent is unchanged), are used. D1, lognormal, is the main caliber: $S_0 = 45 \cdot \exp(\sigma z)$, $z \sim N(0,1)$, with $\sigma \in \{0, 1, 1.5, 2\}$; $\sigma = 0$ reproduces the homogeneous cells. D1 is the main caliber because the model's stability update law is multiplicative, so lognormal dispersion is the model-endogenous shape. D2, two-point, is a lower-bound test: with probability 0.5 each, $S_0$ is 11.68 or 173.34, the 25% and 75% quantiles of D1 at $\sigma = 2$. D3, uniform on [0.89, 2268], is a stress test: it is the 2.5%–97.5% range of D1 at $\sigma = 2$ spread flat, and therefore the sensitivity upper bound. All three families share an $S_0$ floor of 0.1 days, symmetric with the FSRS stability clamp; this is a stated convention, not a fitted value. Each agent draws one $S_0$ used for all three of its lessons, so that lesson-averaging cannot confound the distribution effect. Contagion strength $\alpha = 0.6$ is not heterogenized: it is a single global scalar in the environment code, and per-agent $\alpha$ would require core-code changes, which are frozen for v54. Common random numbers are used throughout: for a given family and run index, the FSRS and EE cells share the same $S_0$ realization and the same network/environment realization, so the engine is the only difference. The governance automatic-intervention monitor is disabled in all v54 and v55 runs (see Section 6.4, limitation 15) and the choice is recorded in every output file.

**Run families.** Four families, aligned to the v53 protocols. A-500: 100-agent single-engine populations, 500 ticks, markets BTC/ETH/AAPL at the Section 5.1 parameters, no shocks (matching the archived Section 5.1 run, which contains no shock injection). A-grid: the Section 5.2 threshold grid on 30-agent populations, 300 ticks, 24 configurations $\times$ 10 episodes. A-mc: 30 runs $\times$ 250 ticks with the archived shock protocol (shock probability 0.02, severity in [0.15, 0.4], markets BTC/ETH/AAPL/SPY). A-10y: 8 runs $\times$ 3650 ticks, sampled every 50 ticks, seeds 200–207, same shock protocol. For A-mc and A-10y, the archived 2-agent dual-engine protocol is rerun for C1 and C3 as a consistency reference only; all heterogeneous cells use a new 100-agent-per-engine population protocol, whose figures are not comparable to the v53 Monte Carlo and 10-year figures (see Section 6.4, limitation 14).

| Cell | Engine | $S_0$ caliber | Families |
|---|---|---|---|
| C1 | FSRS | Homogeneous (all 45) | A-500, A-grid, A-mc, A-10y |
| C2 ($\sigma$ = 1, 1.5, 2) | FSRS | Lognormal, median 45 | A-500, A-grid, A-mc, A-10y |
| C3 | EE | Homogeneous (all 45) | A-500, A-grid, A-mc, A-10y |
| C4 ($\sigma$ = 1, 1.5, 2) | EE | Lognormal, median 45 | A-500, A-grid, A-mc, A-10y |
| C4′ | EE | Two-point 11.68 / 173.34 | A-500 only |
| C4″ | EE | Uniform [0.89, 2268] | A-500 only |

**A-500 results (tick-500 mean retrievability, 10 seeds per cell).** FSRS is nearly insensitive to heterogeneity, while EE rises monotonically with it — the Anderson & Tweney mechanism in its direct form. All A-500 runs record zero interventions.

| Cell | $\overline{R}(500)$ mean | Std. dev. |
|---|---|---|
| C1 (FSRS homogeneous) | 0.55548 | 0.00000 |
| C2, $\sigma=1$ | 0.55912 | 0.00965 |
| C2, $\sigma=1.5$ | 0.56036 | 0.01285 |
| C2, $\sigma=2$ | 0.55990 | 0.01509 |
| C3 (EE homogeneous) | 0.00001 | 0.00000 |
| C4, $\sigma=1$ | 0.01894 | 0.00470 |
| C4, $\sigma=1.5$ | 0.05733 | 0.01205 |
| C4, $\sigma=2$ | 0.10201 | 0.01927 |
| C4′ (two-point) | 0.02674 | 0.00206 |
| C4″ (uniform) | 0.54191 | 0.01778 |

The homogeneous comparison (C1 vs C3) reproduces the published-caliber order of magnitude in level terms but with a different ratio: 0.55548 vs 0.00001. Heterogeneity moves only the EE side. At $\sigma=2$ the EE pooled mean reaches 0.10201, and under the uniform stress test 0.54191 — the gap is extremely distribution-shape-sensitive (same quantile range, three shapes: two-point 21$\times$, lognormal 5.4$\times$, uniform 1.025$\times$ against the homogeneous FSRS cell). The design-phase analytic budget (roughly 10–13% of agents with $S_0$ in the 1000–2000-day range suffices to compress the gap to 10$\times$) is superseded by these run ratios and is not carried forward.

**A-grid results (return is the RL reward, not economic PnL; 24 configurations $\times$ 10 episodes).** The FSRS cells record near-zero interventions (homogeneous 0.17 per episode, all from the 0.65 threshold; heterogeneous 0.13–0.46 per episode, almost all from the 0.65 threshold with trace 0.55 triggering at $\sigma=1.5$–$2$), confirming that no FSRS agent's retrievability can fall to the 0.30/0.45/0.55 thresholds within the 300-tick grid horizon (homogeneous R(300) ≈ 0.64); only the 0.65 threshold triggers, in the final ~11 ticks. The EE cells, by contrast, show intervention-driven returns.

| Cell | Return mean (all configs) | Std. dev. | Interventions / episode | Target-zone % |
|---|---|---|---|---|
| C1 (FSRS homogeneous) | 2164.81 | 99.66 | 0.17 | 28.11 |
| C2, $\sigma=1$ | 2208.66 | 1098.05 | 0.13 | 30.09 |
| C2, $\sigma=1.5$ | 2489.56 | 1469.62 | 0.15 | 34.12 |
| C2, $\sigma=2$ | 2848.93 | 1752.47 | 0.46 | 39.01 |
| C3 (EE homogeneous) | +1413.53 | 1137.23 | 4.42 | 30.22 |
| C4, $\sigma=1$ | +1220.25 | 1425.26 | 4.46 | 31.68 |
| C4, $\sigma=1.5$ | +1059.46 | 1774.17 | 4.52 | 32.61 |
| C4, $\sigma=2$ | +902.87 | 2096.11 | 4.48 | 33.64 |

At the baseline configuration (0.30/0.60): C1 2209.38 (interventions 0.00, target zone 28.67%), C3 +190.97 (interventions 3.00), C4 $\sigma=1$ −166.09, C4 $\sigma=1.5$ −418.07, C4 $\sigma=2$ −908.85. FSRS homogeneous baselines rise with $\sigma$ (C2 baselines 2586.01/3082.96/3528.35, all with 0.00 interventions). Two facts matter. First, the EE baseline return deteriorates with $\sigma$ and its variance explodes, so the EE "optimum" configuration is itself unstable. Second, the EE cells' positive returns are intervention-driven (shocks consolidate retrievability back into the target zone), not evidence that EE memory is better; the FSRS cells' high, nearly intervention-free returns are the same non-intervention finding as Section 5.2, now shown to survive heterogeneity (with the 0.65-threshold exception above).

**A-mc results (30 runs, 250 ticks; final retrievability).** The population protocol (100 agents per engine) and the archived-protocol reference (2 agents per run) are reported separately and are not comparable.

| Cell | Population mean | Population final $R > 0.85$ | Reference mean |
|---|---|---|---|
| C1 (FSRS homogeneous) | 0.9140 | 24/30 | 0.9094 |
| C2, $\sigma=2$ | 0.8568 | 17/30 | — |
| C3 (EE homogeneous) | 0.6455 | 8/30 | 0.6040 |
| C4, $\sigma=2$ | 0.6202 | 6/30 | — |
| C4″ (uniform) | 0.9351 | 28/30 | — |

The reference means are 0.9094 (FSRS) and 0.6040 (EE) under the v55 kernel. Under the population protocol, FSRS holds above 0.85 in 24/30 runs homogeneous and 17/30 at $\sigma=2$, while EE-heterogeneous lognormal cells collapse to 6/30; only the uniform stress test lifts EE back to 28/30. The Monte Carlo family therefore supports the gap surviving, not closing, under lognormal heterogeneity — with FSRS population retention lower than in v54 under the faster-decaying kernel.

**A-10y results (8 runs, 3650 ticks; final retrievability).** The reference-protocol gap is 0.0448 (0.9522 − 0.9074). Under the population protocol the gap is 0.0280 (0.9631 − 0.9351): FSRS no longer saturates at the 36500-day stability cap under the recalibrated kernel, while EE rises from 0.9351 (homogeneous) to 0.9364 ($\sigma=2$) and 0.9745 (uniform). The long-horizon gap persists but is smaller than the published-caliber figure, and the two protocols must not be mixed.

**Shape test (pooled $\overline{R}(t)$, power vs exponential fit).** The level test alone cannot adjudicate the Anderson & Tweney claim, because a mixture of exponentials can match a level while differing in shape. Fitting $\log \overline{R}$ against $\log t$ (power law) and against $t$ (exponential) on the A-500 pooled trajectories gives:

| Cell | Apparent exponent $b$ | Power $R^2$ | Exponential $R^2$ | $\Delta$AIC (power − exponential) |
|---|---|---|---|---|
| C1 (FSRS homogeneous) | 0.1735 | 0.9287 | 0.9680 | +40.1 |
| C4, $\sigma=1$ | 1.0935 | 0.9460 | 0.9577 | +12.3 |
| C4, $\sigma=1.5$ | 0.7256 | 0.9675 | 0.9341 | −35.4 |
| C4, $\sigma=2$ | 0.5330 | 0.9784 | 0.9169 | −67.4 |
| C4′ (two-point) | 0.9092 | 0.8669 | 0.9955 | +169.1 |
| C4″ (uniform) | 0.1780 | 0.8825 | 0.9928 | +139.7 |

Fits use the window [10, 500]. The FSRS homogeneous exponent (0.1735) sits below the kernel's $w_{20} = 0.4$; the deficit is the closed form's curvature at small $t$, and the estimate rises to 0.2198 on [50, 500] and 0.2455 on [100, 500]. On [10, 500] the exponential fit wins for the FSRS cell ($\Delta$AIC +40.1); on the later windows the power fit wins ($\Delta$AIC −11.0 and −34.1). For the key cell C4 $\sigma=2$, the power fit wins decisively ($\Delta$AIC −67.4, strengthening to −98.4 on [50, 500] and −100.4 on [100, 500]) with $R^2$ 0.9784 on [10, 500] and 0.995–0.998 on the later windows: the Anderson & Tweney mechanism is confirmed in shape for lognormal heterogeneity at $\sigma \geq 1.5$, while at $\sigma=1$ and under two-point and uniform shapes the exponential fit still wins. The mechanism is therefore real but shape-dependent, not universal.

| Window | C1 b (R²) | C4 σ=2 b (R², ΔAIC) | Distance | Threshold (0.5·b_FSRS) |
| [10, 500] | 0.1735 (0.9287) | 0.5330 (0.9784, −67.4) | 0.3595 | 0.0868 |
| [50, 500] | 0.2198 (0.9818) | 0.6090 (0.9948, −98.4) | 0.3893 | 0.1099 |
| [100, 500] | 0.2455 (0.9933) | 0.6467 (0.9978, −100.4) | 0.4013 | 0.1227 |

Window-specific shape fits for the tier verdict: for the main caliber (C4 $\sigma=2$) the distance exceeds its threshold on all three windows, so the exponent criterion fails there; for the uniform cell (C4″) the distance is below its threshold on all three windows (0.0045/0.0173/0.0342 against 0.0868/0.1099/0.1227), so the exponent criterion holds there. The tier verdict below is therefore mixed, not uniform.

**Level test and tier verdict.** Define $G = \log_{10}(\overline{R}_{\mathrm{FSRS,C1}} / \overline{R}_{\mathrm{EE,cell}})$ at tick 500:

| EE cell | $G$ |
|---|---|
| C4, $\sigma=1$ | 1.4672 |
| C4, $\sigma=1.5$ | 0.9863 |
| C4, $\sigma=2$ | 0.7360 |
| C4′ (two-point) | 1.3175 |
| C4″ (uniform) | 0.0107 |

The pre-registered decision rule (Section 5.7 design) is: $G \geq 3$ gap survives; $2 \leq G < 3$ tier T1; $1 \leq G < 2$ tier T2; $G < 1$ tier T3 only if the exponent criterion also holds ($|b_{\mathrm{EE}} - b_{\mathrm{FSRS}}| \leq 0.5 \cdot b_{\mathrm{FSRS}}$). The main-caliber value $G = 0.7360$ passes the level bar for T3, but the exponent distance is 0.3595 on [10, 500] (0.3893 on [50, 500], 0.4013 on [100, 500]) against thresholds of 0.0868, 0.1099 and 0.1227 respectively — several times too large, on every window. **The verdict is therefore mixed: tier T2 for the lognormal and two-point distributions, tier T3 for the uniform distribution.** The main caliber stays T2: the gap narrows sharply under heterogeneity (47,000$\times$ → 5.4$\times$ at the main caliber) but does not vanish, and the two kernels remain distinguishable in shape at $\sigma=2$. The lognormal $\sigma=1$ cell (1.4672) and the two-point cell (1.3175) fall in the T2 band by level alone; the lognormal $\sigma=1.5$ cell (0.9863) fails the exponent criterion as well (distance 0.5521 > 0.0868). The uniform cell (0.0107) passes both bars: its level is within 1.025$\times$ of the FSRS cell and its exponent distance (0.0045 on [10, 500]) is well inside the threshold, on all three windows. No distribution returns to T1. Under a mixed tier the title is unchanged (the main caliber remains T2); the abstract reports the mixed verdict and both calibers; Section 5.1's table carries caliber labels; and the limitations below record the adjudication. Caveat: the FSRS and uniform cells agree on the exponent but disagree on functional form (FSRS $\Delta$AIC +40.1 on [10, 500], i.e. exponential favoured, turning to power on later windows; uniform $\Delta$AIC +139.7, exponential favoured throughout) — the pre-registered rule does not gate on form, so the T3 verdict stands, but the form disagreement is disclosed here and in Section 6.4, limitation 23.

**Intervention qualification.** The v53 conclusion that "thresholds never trigger" was established in the FSRS regime (Sections 5.2–5.4) and survives there under heterogeneity for thresholds up to 0.55: FSRS grid cells record zero interventions below 0.65, and only the 0.65 threshold triggers (about 1 per episode homogeneous, 0.78–2.67 per episode heterogeneous), where it reduces return. In the EE regime, however, grid identifiability is restored under heterogeneity (about 4.5 interventions per episode, with distinguishable returns across configurations). The non-intervention finding is therefore a property of the power-law regime below the 0.65 threshold, not a universal property of the environment, and any future control design must be validated in the regime where thresholds actually trigger.

### 5.8 Empirical Validation, Tier 1 (v54, rerun v55)

This section reports the first empirical-validation tier: real VIX-derived shock sequences are injected into the agent-based model, and the simulated series are checked against stylized facts and long-memory estimates. The scope is deliberately narrow. Only data already in hand are used; the kernel parameters are the v55 recalibration (Section 4.3), which supersedes the 949-day wall of Section 6.4, limitation 12 (see the v55 update there); no simulator formula beyond the parameter values is changed; the PPO experiments are not rerun. The governance monitor is disabled in all runs (Section 6.4, limitation 15). The GPH log-periodogram estimator (Geweke & Porter-Hudak, 1983) and the local Whittle estimator (Robinson, 1995; Künsch, 1987) are cited in Appendix B.

**Data and injection caliber.** Inputs are FRED VIXCLS daily closes, 1990-01-02 to 2026-10-22 (9,301 valid observations plus 302 holiday blanks, blanks skipped), with FRED VXOCLS for 1987 (peak 150.19 on 1987-10-19) as a sensitivity input. The main grade mapping, taken from the v51 calibration specification (the same source as limitation 12's figures), is: peak VIX $\geq 80 \rightarrow G=1$; 40–80 $\rightarrow G=2$; 25–40 $\rightarrow G=3$; otherwise $G=4$. A second, inconsistent four-band mapping from an earlier proposal draft is used only as a sensitivity dimension. The main timing caliber applies a shock only on days when the grade changes (408 shock days), so that the level is not pegged at 1 by daily shocking; sensitivities apply shocks daily and on upward boundary crossings only. Populations share cells and seeds with Section 5.7's C1/C2/C4 families, so the B-line runs reuse the A-line infrastructure.

**B-1a: injection-pipeline fidelity (return side).** Real-VIX-derived price jumps are superimposed on the model's exogenous price process (drift plus Gaussian noise), and three statistics of the simulated return series $r_t$ are computed. These statistics test whether the injection pipeline transmits the shape of real shocks into the model; because agent trades do not feed back into prices (see Section 6.4, limitation 5 and the B-1b discussion below), they are not evidence about the memory kernel. All 8 main-caliber runs pass all three criteria.

| Statistic | Simulated $r_t$ (8 runs) | Benchmark: $\Delta\log$ VIX, same caliber | Pass criterion |
|---|---|---|---|
| Fat tails: Pearson kurtosis; Hill index (90% / 95% thresholds) | Kurtosis 105.29–112.16; Hill 1.54–1.59 / 1.15–1.18 | Kurtosis 9.68; Hill 2.89 / 3.11 | Kurtosis > 3 and Hill < 4 |
| Volatility clustering: ACF of $\|r_t\|$ and $r_t^2$, lags 1–20 | ACF$\|r\|$(1) 0.184–0.203; 9–10 of lags 1–10 significantly positive | ACF(1) 0.200 | ACF$\|r\|$(1) > 0.1 and at least 5 of lags 1–10 significantly positive |
| $\|r\|$ autocorrelation decay: exponential fit ACF$(k) = A e^{-k/\tau}$ | $\tau$ 3.9–4.6, $R^2$ 0.86–0.92 | $\tau$ 9.4 | Finite $\tau$, $R^2 \geq 0.8$, 95% CI excluding 0 |

One difference must be reported plainly: the simulated return tails are far more extreme than the benchmark's (kurtosis above 100 against 9.68). This is a mixture effect — a Gaussian core with daily volatility near 0.0125 plus jumps averaging about 0.10 — not a failure of the pass criteria, but it means the pipeline amplifies tail mass relative to the volatility-change-rate benchmark, and the two objects (returns vs volatility changes) are not the same quantity. The clustering and decay statistics, by contrast, line up: ACF(1) nearly equals the benchmark's, and the $\tau$ ratio (about 2.1–2.4) sits inside the pre-registered 3$\times$ soft band. Sensitivities: daily shocking (FSRS cell) nearly reproduces the benchmark (kurtosis 9.41, $\tau$ 9.1, all three criteria pass); the EE daily cell fails deterministically (see Section 6.4, limitation 18); the second grade mapping passes all three (kurtosis 54.24); the VXO input passes all three (kurtosis 297.19); only upward-crossing-day injection fails clustering and decay (ACF(1) 0.040, $R^2$ 0.44), showing that the main-caliber clustering is driven by the full grade-change sequence, not by fear-rising days alone.

**Correction record (B-1a).** The first-produced return series excluded the jumps: the previous price was captured after the jump had been applied, so the recorded $r$ contained only the Gaussian component, and the first summary (all runs failing) was a product of that bug and is discarded. The fix moves the previous-price capture before the jump; all 71 output files (of 72 planned runs; the 72nd, the sens_daily EE cell, failed deterministically — see Section 6.4, limitation 18) were corrected by exact reconstruction (on shock days, corrected $r$ = recorded $r$ + $\log(\mathrm{mult})$; unchanged otherwise), and the correction was validated by rerunning the fixed script (maximum return difference $10^{-6}$, pure rounding; cross-sectional dispersions bit-identical). The pre-fix series are preserved inside each output file, and the pre-fix files are archived separately. Only $r$ was affected; the B-1b and B-2 simulation-side series do not depend on prices and are unaffected.

**B-1b: memory-side endogenous series (engine side).** For each tick, the cross-sectional standard deviation of retrievability across agents, and of leverage tendency, are computed, and a 20-tick rolling standard deviation gives a simulated realized-volatility series. This series is sensitive to the engine and to the $S_0$ distribution, unlike B-1a. Two qualifications apply throughout. First, leverage tendency is an affine function of retrievability (FSRS slope 19, EE slope 9), so the standardized leverage statistics are mathematically identical to the retrievability statistics and carry no independent information. Second, the two engines' leverage scales differ (FSRS maximum 20, EE maximum 9), so absolute values are never compared across engines.

Homogeneous cells (C1, C3) are degenerate: with identical agents, the cross-sectional dispersion is identically zero, and this is recorded as degenerate, not as zero. The FSRS heterogeneous cells are now measurable: under grade-change-day shocks, the cross-sectional dispersion is nonzero on 28.7–29.4% of days (C2 $\sigma=1$ 28.7%, $\sigma=1.5$ 29.1%, $\sigma=2$ 29.4%), the last nonzero day falling on day 2784–2849 — saturation is delayed about 19-fold relative to v54 but not eliminated, as stability still reaches the 36500-day cap by about day 2850. An early summary that reported clustering and decay passes for these cells was an artifact of zero-dominated series and is overturned here (in v54 the cells were not applicable at all; in v55 they are measurable but with a different morphology, see below). Level statistics for the FSRS heterogeneous cells show no fat tails (kurtosis 4.40–4.86, $\tau$ about 978–1071, extremely slow variation), while their 20-tick rolling standard deviations pass fat-tail, clustering, and $\tau$ criteria 8/8 — so the rolling volatility is stylized-fact-like but the dispersion level itself is not, and the v54 EE-type 'stylized facts pass' phrasing must not be copied onto the FSRS cells. The EE heterogeneous cells are genuine pressure series (dispersion zero only on shock days, 4.40% of ticks): clustering and decay pass 8/8 (ACF(1) about 0.98, $\tau$ about 86–97, $R^2$ 0.99), but fat tails fade with $\sigma$ (6/8 at $\sigma=1$, 0/8 at $\sigma=1.5$ and $\sigma=2$).

**B-2: long-memory estimation.** The estimation target is log VIXCLS on the real side and the log of the B-1b simulated realized volatility on the simulation side, so that both sides are in logs. Estimators are GPH (log-periodogram regression) and local Whittle (constrained to $d \in (-0.5, 0.5)$), reported together as a robustness pair. The main window is the full sample (9,301 real observations); robustness windows are 1990–2007, 2008–2026, and the sample excluding 2020. Bandwidths are $m = T^{0.5}$ and $T^{0.6}$, plus a sweep over {20, 50, 100, 150, 200, 300, 400}. Confidence intervals are computed two ways: the estimators' own asymptotic distributions, and a parametric block bootstrap (1000 resamples, block length 20). **No cell passes.** The reason is not confined to the simulation side: the real side itself is outside the pre-registered pass band.

| Side | GPH (main bandwidth) | Local Whittle | Bandwidth drift | Verdict |
|---|---|---|---|---|
| Real log VIX, full sample (T = 9301) | 0.580, asymptotic 95% CI [0.452, 0.709] | 0.499, boundary-censored | 0.260 (sweep 0.53 → 0.79) | Fail (outside [0.2, 0.5]; drift > 0.1) |
| Simulated EE (T = 9282) | 0.642–0.752 | 0.499, boundary-censored, all runs | Mostly > 0.1 | Fail |
| Simulated FSRS | 0.79–0.86 (T = 2850, estimable) | 0.499, boundary-censored, all runs | 0.17–0.20 (not robust, drift > 0.1) | Fail (further from band than the real side) |
| B-1a return rolling volatility (sensitivity) | 0.296 | 0.313 | 0.261 / 0.237 | No conclusion (drift > 0.1) |

Sample-size arithmetic: the simulated series length is 9282, not 9301, because the 20-tick rolling standard deviation drops the first 19 observations (9301 − 19 = 9282). The FSRS series is now measurable over an effective window of 2850 days (last nonzero dispersion day 2849).

The pre-registered benchmark $d \approx 0.3$–$0.4$ does not hold for log VIX: the GPH point estimate (0.580) and the local Whittle pile-up at the 0.5 boundary jointly indicate $d \geq 0.5$, outside the stationary long-memory framework the pass band assumes. Sub-window GPH estimates (0.597–0.770) and boundary-censored local Whittle estimates on every sub-window confirm this. The block-bootstrap intervals are not usable here: with block length 20, resampling destroys the long memory, so bootstrap distributions center near 0 (real-side bootstrap mean 0.013, 95% interval [−0.127, 0.141], excluding the point estimate); the asymptotic intervals are therefore the operative basis, as pre-registered for exactly this contingency. The directional reporting obligation is discharged as follows: the simulated EE side's estimates are slightly higher than the real side's, but both sides sit above 0.5 with bandwidth instability, so no "excess long memory" distinction can be drawn within the pre-registered band. B-2 is reported as a validation result — the model's volatility process and the real volatility process share strong persistence, but neither fits the assumed band — not as a failure of the paper's core contest, which does not depend on $d$.
## 6. Discussion

### 6.1 Economic Interpretation
The economic content of this paper is a claim about memory kernels, not about policy levers. Under FSRS, retrievability decays as a power law with a fat tail: at tick 500 FSRS agents retain R = 0.7185 against EE's 0.000015 (Section 5.1). That difference — roughly 47,000-fold — is the mechanism behind everything else reported here. It is why avg_R never falls below the 0.30/0.45/0.55 thresholds in the 30-agent regime, why the S=45 grid rerun in Section 5.7 gives identical outcomes for both paired configurations, and why the original grid's modest return gap (3434 vs 3947) is a seed/network artifact (Section 5.2), not a policy effect. The regime cannot discriminate between thresholds — which does not prove thresholds would be irrelevant in a regime where avg_R does fall below them, but it does show that in a power-law-memory regime the threshold question is downstream of the memory question: get the kernel wrong by orders of magnitude and any control design built on it inherits the error.

In this regime FSRS agents are intrinsically self-stabilizing: both paired configurations record zero interventions across 10 episodes, as avg_R never falls below either paired threshold in these runs. The near-equivalence of the two paired configurations underscores that the best policy is often no policy when the underlying cognitive model captures long memory naturally — but that statement is a property of this regime, not a general prescription.

The kernel contest at the center of this paper is itself contested in the memory literature, and we present both sides of that contest rather than only the side favorable to our engine. Anderson and Tweney (1997) show that pooling individually exponential forgetting curves with heterogeneous decay rates produces an aggregate curve that is well approximated by a power law: the power-law appearance can be an artifact of aggregation. That is a direct challenge to readings of pooled data, including in principle the group-level FSRS–EE contrast of Section 5.1, which averages over agents. Wixted and Ebbesen (1997), in the immediately following pages of the same journal issue (*Memory & Cognition*, 25(5), 724–730 and 731–739 respectively), analyze forgetting at the individual level and report genuine power curves, so the aggregate artifact and the individual power law can coexist. The synthesis consistent with both papers is that the functional form is level-dependent and that heterogeneity in decay rates across agents can amplify the apparent divergence between power-law and exponential fits—a mechanism that would widen the gap we measure rather than narrow it, while simultaneously warning that a pooled contrast is not by itself evidence about any individual agent's kernel. We therefore read the Section 5.1 contrast as a statement about fitted aggregate kernels, not as an individual-level claim. A further complication comes from a recent, not-yet-peer-reviewed EdArXiv preprint (Kannan and Ravi, 2026), which evaluates decay models on individual-level Anki spaced-repetition data and finds that a stretched exponential—neither the pure power law implemented here nor the pure exponential of EE—fits best in 76% of individuals, with adaptive scheduling inducing rate–delay coupling and the Anderson–Tweney heterogeneity mechanism alone insufficient to account for the observed curvature. We report that finding as a complication of the power-law story rather than as support for it: on individual data the contest may be won by an intermediate functional family, and the preprint does not endorse the aggregate persistence contrast reported here. Section 5.7 now tests this mechanism directly: introducing S0 heterogeneity on the EE side only narrows the gap from 47,000 times to 5.4 times at the main caliber (Tier T2; the uniform distribution reaches T3), so the pooled contrast is level-dependent in the Anderson–Tweney sense, but the gap does not close at the main caliber.

### 6.2 Implications: Model Choice First
Our findings reorder the usual policy discussion. Because agents retain long-term risk awareness under FSRS, the first-order implication is about model choice: an exponential memory kernel understates persistence by orders of magnitude (Section 5.1), so any control design calibrated on it will mistime interventions — intervening too late, assuming memory has faded when it has not. Before prescribing triggers and severities, a control design must first get the memory timescale right; the v51 calibration result (Section 6.4, limitation 12) shows that timescale is not yet identified from market data, which bounds how far any prescription from this paper can go.

Within those bounds, the probe results support a restrained stance:
- **Monitor, do not micromanage**: in the 30-agent regime no threshold up to 0.55 ever triggers and no threshold-severity optimum is identified (Sections 5.2, 6.1), so a fixed trigger/severity prescription is not supported by this experiment; any trigger must be validated in a regime where avg_R actually falls below it,
- **Reserve intervention for genuinely fragile states**: interventions at scale occur in the original default-bank 1000-agent run, where the comparison policy (T=0.55, s=0.20) intervened more mildly and more frequently than baseline (15.0 vs 5.0 per episode), not more strongly and less frequently; at S=45 under the old kernel both policies record 0.0 interventions, while under the v55 kernel the comparison policy intervenes once per episode and baseline never does (Section 5.3),
- **Avoid over-intervention**: continuous tweaking is counterproductive; the power-law dynamics mean that once memory is strong, it persists with minimal regulatory input.

Real-world tools (CCyB, stress tests) could be set to activate only when systemic risk perception falls below thresholds aligned with the FSRS initial stability $S_0 = 45$ days used in the simulations (a convention value, not a real-data-calibrated threshold; Section 6.4, limitation 12). Interventions in the 30-agent grid were zero except at the 0.65 threshold (about 1 per episode, reducing return); in the original default-bank 1000-agent scaling run they averaged 15.0 per episode for the comparison policy (T=0.55, s=0.20) over 1000 ticks, and in the S=45 reruns (v49 pre-fix, v50 post-fix) they are 0.0 for both policies (Section 5.3). Macroprudential authorities should therefore **reserve major actions for genuinely fragile states**, rather than frequent fine-tuning — with the caveat that this stance inherits the calibration gap in limitation 12.

### 6.3 Why Reinforcement Learning Failed

The failure of PPO to learn a viable policy deserves deeper analysis, as it highlights challenges in applying standard RL to economic control problems:

1. **Credit Assignment Horizon**: Intervention effects manifest after 30–50 ticks, but PPO rollouts are 2048 steps. With discount factor γ=0.99, the effective horizon is ~100 ticks, still shorter than the intervention-to-reward delay. TD(λ) with eligibility traces could help, but on-policy methods struggle with such long gaps.

2. **Value Function Collapse**: The critic's explained variance was near zero. This occurs when the reward signal is dominated by dense terms (avg_R×10) that are hard to predict from state, making the value estimate noisy. Actor-critic methods rely on accurate critics; poor value estimates degrade policy gradients.

3. **Exploration–Evaluation Mismatch**: During training, Gaussian exploration (std≈0.66) occasionally produced positive actions that maintained avg_R, inflating rollout returns (~1000). However, the *mean policy* at evaluation (deterministic) output ≈0, revealing that the agent learned to rely on noise rather than a consistent strategy. This "stochastic policy failure" is known in RL; solutions include entropy regularization (we used ent_coef=0.01) or deterministic policy gradients (SAC, DDPG).

4. **Sparse Binary Signal**: Despite v4's intervention bonus, the reward landscape contains flat regions where avg_R changes slowly. Policy gradient updates become tiny when the advantage function is near zero. Dense shaping (avg_R×10) helped but still didn't make intervention *immediately* rewarding in danger zones (avg_R<0.5 yields negative net reward even with bonus).

Alternative approaches that could work:
  - **Soft Actor-Critic (SAC)**: Off-policy, better for continuous action spaces, maximizes entropy to avoid premature collapse.
  - **Model Predictive Control (MPC)**: Use analytical simulator to roll out candidate actions and pick best (random shooting or CEM).
  - **Bayesian Optimization**: Directly optimize threshold-severity parameters (as we did) or higher-dimensional policy families.

### 6.4 Limitations
v52 scope note: in v52 the paper's framing changed from macroprudential control design to a memory-model contest with control probes. The limitations below are unchanged, but limitation items concerning control (notably 6, 9, and 11) should now be read as limits on probe findings, not as limits on a policy proposal. No data, code, or result numbers changed in v52.


1. **Simplified memory model**: We use a single retrievability score per agent per lesson; real memory is multi-dimensional (episodic, semantic, procedural).
2. **Homogeneous agents (v54 update)**: Section 5.7 introduces heterogeneity in S0 across agents (lognormal, two-point, and uniform distributions), but α and the lesson structure remain uniform; future work should introduce heterogeneity in α and in lesson-specific stabilities.
3. **Exogenous shocks (v54 update)**: Section 5.8 injects 408 real VIX-derived exogenous shocks, so the environment is no longer shock-free; what remains missing is endogenous news generation and price feedback from agent trades.
4. **Grid search scalability**: While effective for 2D threshold-severity, higher-dimensional control (e.g., targeting specific agent subgroups) would require more advanced optimization (Bayesian optimization, MPC).
5. **Real-world validation attempted, not achieved (v54 update)**: Calibration used synthetic VIX-proxy curves. A v51 real-data recalibration attempt (Section 6.4, limitation 12) could not identify $S$ from market data; the synthetic values are retained as simulation convention. Section 5.8 attempts Tier-1 validation with real VIX shock sequences, but no B-2 cell passes because the long-memory benchmark itself falls outside the pre-registered band.
6. **Robustness sweep (v47) and isolated-agent defect**: the v43 sweep is withdrawn (see Section 5.4); a correctly parameterized $p$/$S$ sweep is now reported in Section 5.4, with the isolated-agent artifact disclosed (an agent with no predecessors gets perceived R = 0.4 x true R, dragging mean perceived R into the target zone). The sweep does not support a '$p$ negligible' or '$S$ improves returns' claim, and the defect is fixed in v50 (commit 7ee820c; Section 5.4): the post-fix sweep shows the $p$ effect was entirely the artifact, and the replication pack environment now runs with the fix.
7. **Figure 5 replaced (v47)**: see Section 3.3; the v43 figure used an incorrect exponent and remains withdrawn, and a new figure from the correct formula is now included.
8. **PPO training script not archived**: Section 5.5 reports training outcomes from archived logs and model files, not a rerunnable training script in the replication pack.
9. **Grid optimum unidentified (v45); 1000-agent audit (v47)**: the original 30-agent grid evaluated each configuration on a different seed set, and the paired same-seed rerun in Section 5.2 gives identical outcomes for both threshold configurations; no threshold-severity optimum is claimed. The 1000-agent run is now audited in Section 5.3: its comparison policy is (T=0.55, s=0.20), not (T=0.45, s=0.40), episodes 1–2 are paired and episode 0 is unpaired due to the falsy-seed bug, and the near-zero variance means that flaw does not change the result. The 373.6% figure is withdrawn as a policy claim in v49: the S=45 rerun gives 0.0% (see Section 5.3); 373.6% remains audit-only for the original default-bank run, and was in any case a point estimate from only 3 episodes, not a robust effect size.
10. **v45 pi-review adjudication (fixed in v46)**: pi (gpt-oss:120b) returned VERDICT: FAIL on a HIGH claim that Table 2 mismatches same_seed.json. Adjudication: not sustained — the paired table in v45 matches same_seed.json exactly (3836.30 ± 1126.90, 3725.26 ± 1063.03, 49.97%, 48.63%), and the HIGH compared the audit-labelled original Table 2 against the paired rerun. Two genuine MEDs from that review are fixed in v46: the Section 6.1 paragraph still called the policy 'optimal … derived from grid search' and quoted the original gap without an artifact qualifier, and Table 2's row label 'Optimal' and intro lacked an audit label. Pi's word-count and 374% rounding points are not sustained (word count verified by wc -w; 373.6% rounds to 374% and the small-sample caveat is present).

11. **S parameterisation scope (v50)**: the grid, the paired rerun, the p/S sweep, and the 1000-agent run have now been rerun at S=45 with the fixed environment (Sections 5.2-5.4); the Section 5.6 experiments need no post-fix rerun because they do not use ECOSControlEnv._compute_obs and are therefore unaffected by the fix. All three Section 5.6 experiments were rerun at S=45 in v49 (Section 5.6). What remains not S=45-verified: the E2E P&L, drawdown, and trade-count figures (from `full_trading_simulation.json`, not rerun), and the PPO training outcomes (Section 5.5, script not archived). The 10-year S=45 result is bit-identical to the original by S-cap saturation (Section 5.6.3), so it does not discriminate S; the E2E and Monte Carlo reruns do show S effects (Sections 5.6.1, 5.6.2). (v55 update) The E2E figures are now the v55 recalibrated-kernel-plus-bank numbers (Section 5.6.1); the Monte Carlo and 10-year S=45 reference figures are the v55 numbers (Sections 5.6.2, 5.6.3). Rerun in v55: the 1000-agent S=45 run (Section 5.3) and the p/S sweep (Section 5.4) now carry v55-kernel numbers, and their scale/sweep conclusions are reasserted on the v55 tables in those sections.
12. **Real-data calibration unidentified (v51)**: Step 2 of the strengthening plan attempted to replace the synthetic VIX proxy with real data. Data route: FRED VIXCLS daily closes 1990-01-02 to 2026-10-22 (9,603 rows: 9,301 trading-day observations plus 302 holiday blanks) plus FRED VXOCLS for 1987 (peak 150.19 on 1987-10-19); both archived in the replication pack (`data/`). The original calibration script is lost and its loss is not reproducible: the surviving reports give per-event losses whose MSE component implies an undocumented additive term of about 0.45 for four events and about 0.157 for 2022, and the old best loss 0.5604 sits on a grid boundary (S=45 is the largest grid value; loss still falling at the boundary), so the synthetic exercise never genuinely identified S=45 or α=0.6 either. Under a new fully documented loss (mean squared error between the simulated FSRS retrievability trajectory after a single peak-day shock and a VIX-derived reference curve, plus a recovery-days error), the grid over S = 5 to 75 is monotone: total loss 1.3413 at S=5 rising to 1.5162 at S=75, with no interior optimum. The mechanism is structural, not a fitting failure: in every event and at every S, the simulated retrievability never falls below 0.5 within the 780-day window, while the VIX reference halves in 2 to 14 days; from the pack's own FSRS formula, the half-life is 9,491 x S' days (S' = post-shock stability), and the code clamps S at 0.1 days, so the minimum achievable half-life is 949 trading days—any market observable that normalizes faster cannot be fit by construction. The same arithmetic defeats price-recovery days as a target: at S0=1 the mean relative error against the reported historical recovery days (1987: 520, 2000: 2555, 2008: 1460, 2020: 153 days) is already 174%, and at S0=45 the G=1 half-life is 62,050 days. The old and new losses are on different definitions and are not comparable. Consequence: S, α, and severity are **not** real-data-calibrated quantities in this paper; S=45 is retained solely as the synthetic-era simulation convention so that Sections 5.1-5.6 remain mutually comparable. Refitting the FSRS decay exponent w20 (borrowed from Anki spaced-repetition data) rather than S alone is the remaining lever that could match market timescales, and is left as a separately designed study. (v55 update) That study has now been done as the J1 joint fit (Section 4.3): w20 is refit to 0.4 (with w17 = 0.6096, w18 = 0.0496, w19 = 0.1841) against 12 VIX/VXO events, mean loss 0.0360. The 949-day wall is broken: the new kernel's half-life is about 15.45 × S′ days (about 1.6 days at the 0.1-day clamp, about 695 days at S = 45), so market-timescale observables are no longer un-fittable by construction. What remains unidentified is the post-shock stability S0* itself (fit value 0.5, weakly identified over roughly 0.5–1.1) and hence the LESSONS scale k (see limitation 19).
13. **Published-caliber baseline not homogeneous (v54)**: Section 5.1's FSRS group carries agent-type multipliers (mean initial stability 19.70) while its EE group is uniform at 45.0, so the 47,000$\times$ figure is a mixed-population-caliber statement, retained unchanged, and must not be read as a homogeneous-cell comparison. Section 5.7 runs the true homogeneous cells and reports both calibers side by side.
14. **Monte Carlo "100 agents" wording unsupported (v54)**: Section 5.6.2 writes "(100 agents, 250 ticks each)", but no archived script or output file runs a 100-agent Monte Carlo; the archived protocol is 2 agents per run (dual-engine), and the 27/30 and 30/30 figures come from that protocol. Section 5.7's population Monte Carlo (100 agents per engine) is a new protocol whose figures are not comparable to v53's.
15. **Governance automatic-intervention path latent crash (v54)**: `governance_manager.tick()` references `summary` before assignment when collective average retrievability falls below 0.25 with monitoring enabled, which would raise UnboundLocalError (and the monitor's own shock trigger would already have fired first). It never fired in archived runs because the collective mean over all agents stayed above 0.25 (about 0.395 at tick 500 in Section 5.1). All v54 runs disable the monitor and record that choice; the bug itself is not fixed (core code frozen for v54). (v55 update) All v55 runs likewise disable the monitor and record that choice; the bug is still not fixed (core code frozen for v55).
16. **Long-memory benchmark out of band; bootstrap caveat (v54)**: Section 5.8's $d$-estimation premise ($d \approx 0.3$–$0.4$) does not hold for log VIX (GPH 0.580, local Whittle at the 0.5 boundary), so no B-2 cell can pass the pre-registered criteria; block bootstrap with block length 20 destroys long memory and centers near 0, so asymptotic intervals are the operative basis. (v55 update) Still no B-2 cell passes in v55; the FSRS side is now estimable (effective T = 2850, GPH 0.79–0.86) but further from the band than the real side.
17. **FSRS saturation voids the memory-side pressure series (v54)**: under real-VIX grade-change-day shocks, FSRS stabilities hit the 36500-day cap after about 10 shocks, so the cross-sectional retrievability dispersion dies (nonzero on only a small fraction of days in v54); Section 5.8's FSRS B-1b cells were therefore not applicable, not zero, in v54. (v55 update) In v55 the FSRS B-1b cells are measurable (nonzero on 28.7–29.4% of days, last nonzero day 2784–2849): saturation is delayed about 19-fold but not eliminated, and the morphology differs from the EE-type stylized facts (see Section 5.8 and limitation 23).
18. **Daily-shock sensitivity cell fails deterministically (v54)**: the sens_daily EE cell (9300 consecutive shocks) raises OverflowError in `cognitive_memory.py` (`int(interval_days * EF)` compounding to infinity); the failure is deterministic and the cell is reported as failed, not retried; fixing the interval bound is a core-code change, frozen for v54; the main-caliber B-1 cells (408 shocks) are unaffected. (v55 update) The sens_daily EE cell fails deterministically in v55 as well (same OverflowError, same root cause); the main-caliber B-1 cells are unaffected.

19. **Post-shock stability weakly identified; LESSONS scale bracketed, not identified (v55)**: the J1 joint fit identifies the kernel shape (w17–w20) but S0* only weakly (fit 0.5 over roughly 0.5–1.1), so the LESSONS rescale k = 6.7 (loaded mean 3.33 / 0.5) is a convention anchored to a weakly identified point. Robustness was checked at two points, k = 3.3 and k = 6.7 (Section 5.2): the grid policy conclusion is unchanged and the E2E run is bit-identical, but two points are not an identification of k, and no other experiment consumes the bank (only the original-protocol grid and the end-to-end run do), so k-robustness elsewhere is vacuous, not demonstrated.

20. **End-to-end reversal; simulation, not validation (v55)**: the v55 end-to-end run loses 39.8% (Section 5.6.1), reversing the v54 profitability conclusion for the same protocol, seed, and shock sequence. The reversal is attributed to the kernel and bank behavior change (RNG streams identical), but the decision-level mechanism was not instrumented and is not claimed. More generally, the trading run is a simulation outcome under one seed and one shock sequence, not validation of trading performance; the grid returns throughout are RL rewards, not economic PnL, except where a section states otherwise.

21. **Original-protocol grid is seed-confounded audit caliber (v55)**: the v55 original-protocol grid numbers (Section 5.2) use different seed sets per configuration, as in the original run, so their cross-configuration spread is not a policy comparison. The clean policy evidence is the paired S=45 rerun and the A-grid C1 grid (Section 5.7), where configurations share seeds or are otherwise controlled.

22. **EE floating-point noise at 1e-8 (v55)**: EE cells rerun across processes differ at full precision by up to 2.5e-08 in R500 (A-500) — numerical noise, not an engine change. EE figures are therefore reported to 5 decimals, and full-precision EE comparisons across versions should not be over-read.

23. **FSRS B-1b morphology differs from EE stylized facts (v55)**: the now-measurable FSRS heterogeneous dispersion levels show no fat tails and extremely slow variation (τ about 978–1071), while only their rolling volatilities pass the stylized-fact criteria 8/8. The H1 claim for v55 is therefore 'measurable and delayed', not 'stylized facts pass' in the EE sense; copying the EE phrasing onto the FSRS cells would misstate the result.

### 6.5 Future Research Directions

Three items listed in earlier versions are now completed: the isolated-agent fix (v50, Section 5.4), S0 heterogeneity (v54, Section 5.7), and exogenous shocks (v54, Section 5.8). The remaining items are:

- **Multi-lesson coupling**: Allow lessons to influence each other's stability gains (cross-coupling matrix ρ_AB). Could reveal emergent phenomena like panic-generalization across memory domains (liquidity risk → leverage risk).
- **Adaptive controllers**: Implement Model Predictive Control using the analytical simulator for real-time intervention planning; compare to fixed-threshold.
- **Real-data calibration (v51 status: unidentified)**: the v51 attempt (Section 6.4, limitation 12) could not identify S from VIX/VXO data; refitting the FSRS decay exponent w20, rather than S alone, is the remaining lever that could match market timescales, and is left as a separately designed study. (v55: the w20 refit is now done — J1 joint fit, Section 4.3; what remains open is S0* identification and the LESSONS scale k, see limitation 19.)


---

## 7. Conclusion
We have introduced a cognitive memory engine based on FSRS power-law forgetting, contrasted with the classical Ebbinghaus exponential forgetting curve, into agent-based economic modeling. Agents equipped with spaced repetition exhibit realistic forgetting dynamics: retrievability decays as a power law after market shocks. Crucially, we demonstrated that memory is not purely private—agents influence each other's perceived risk via information-flow networks, creating systemic amplification of fear and greed (contagion effect).

The paper's main result is the memory-model contest (Section 5.1): in a 100-agent head-to-head comparison over 500 ticks, FSRS retrievability at tick 500 is approximately 47,000 times EE's (R(500) = 0.7185 vs 0.000015). Under a second, homogeneous-vs-heterogeneous caliber (Section 5.7), the gap is 5.4 times (0.55548 vs 0.10201, G = 0.7360), so the two figures are two calibers of one contest, not competing estimates. Exponential memory understates market persistence by orders of magnitude; that single difference drives the rest of the paper's findings.

Two v55 chapters qualify that headline. Section 5.7 adjudicates the contest under homogeneous-vs-heterogeneous calibers and lands on a mixed tier (T2 for the lognormal and two-point distributions, T3 for the uniform distribution): the gap narrows to 5.4 times at the main caliber but does not close there, and the exponent-closure criterion fails on every window for the main caliber. Section 5.8 attempts Tier-1 empirical validation with real VIX shock sequences: the B-1a injection pipeline reproduces clustering and decay, but no B-2 cell passes because the long-memory benchmark itself sits outside the pre-registered band.

Through a synthetic five-event calibration exercise (Black Monday 1987, Dot-com Bubble 2000, Global Financial Crisis 2008, COVID Crash 2020, Inflation 2022), we set initial stability $S_0 = 45$ days; a v51 real-data recalibration attempt could not identify $S$ from market data (Section 6.4, limitation 12), so 45 days is retained as a simulation convention. Under EE this would imply a 31-day half-life, but under FSRS the power-law tail keeps retrievability high for years, so the 45-day figure must not be read as a forgetting half-life. This distinction matters for the behavioral claim: market participants' risk awareness does not decay on a monthly timescale under FSRS; it is the EE counterfactual that does.

Two control probes were run against this memory engine and both returned negative results. The regulator's intervention problem, formulated as a POMDP with partially observable agent states, proved challenging for standard RL (PPO) due to sparse and delayed rewards (Section 5.5). Direct parameter optimization via grid search did **not** identify an optimal control strategy on 30-agent populations: a paired same-seed rerun (Section 5.2) gives identical outcomes for (T=0.45, s=0.40) and (T=0.30, s=0.60) (3836.30 vs 3836.30 on seed set 10; 3725.26 vs 3725.26 on seed set 110; interventions 0.0 in both), because thresholds never trigger under FSRS in the default-bank regime. The S=45 grid rerun (Section 5.7, A-grid C1) gives 2209.38 vs 2209.38 for the same two configurations, with 0.0 interventions and 28.67% target-zone time in both. The original 15.0% gap (3947 vs 3434) and target-zone gap (51.3% vs 45.0%) are seed/network artifacts and are retained in Section 5.2 for audit only. The 1000-agent result at S=45 (Section 5.3) gives identical returns for both policies (-1065.35, interventions 0.0), so the v47/v48 374% figure (10402 vs 2197, default bank) is withdrawn as a policy claim and retained for audit only; on 1000 agents at S=45, as on 30 agents, the effective policy is non-intervention in this regime.

The effective policy is **non-intervention** under FSRS on 30 agents: both paired configurations record zero interventions across all episodes, because avg_R never falls below either paired threshold; only the 0.65 threshold triggers, and it reduces return. This indicates that **FSRS agents are intrinsically self-stabilizing** and do not require active regulatory control to maintain risk awareness in this regime.

From a methodological perspective, our work demonstrates that **control problems with long-delayed effects may be better served by direct policy search than by model-free RL** when the parameter space is low-dimensional. The failure of PPO here aligns with recent critiques of applying standard RL to economic domains with sparse feedback. But the larger methodological point is prior to control: when the memory kernel is wrong by orders of magnitude, control results inherit the error, and a calibration that cannot be identified from market data (Section 6.4, limitation 12) bounds what any policy conclusion from this paper can claim.

**Limitations** remain. Our memory model is a single scalar retrievability; real cognition involves multi-dimensional episodic and semantic memory. Agents are heterogeneous in S0 (Section 5.7) but uniform in α; the environment now includes real VIX-derived exogenous shocks (Section 5.8) but generates no news endogenously and has no price feedback from trades. Finally, calibration used a synthetic VIX proxy, and a v51 real-data recalibration attempt could not identify the stability parameter from market data (Section 6.4, limitation 12); in v55 the kernel parameters are jointly fit to 12 VIX/VXO events (Section 4.3), but the post-shock stability $S_0^*$ remains weakly identified and the LESSONS scale $k$ is robustness-checked, not identified (Section 6.4, limitation 19), so the real-data calibration remains partly open.

**Future research directions** include: (1) multi-lesson memory coupling, where different risk types (liquidity, leverage, contagion) cross-influence; (2) adaptive MPC controllers using the analytical simulator; (3) heterogeneity in α and lesson-specific stabilities (S0 heterogeneity is reported in Section 5.7); (4) deployment of the non-intervention baseline as a benchmark for real-world macroprudential stress testing frameworks.

In sum, this paper establishes a **cognitive foundation for agent-based financial modeling**, linking the psychology of spaced repetition to systemic risk dynamics. Its contribution is a contest, not a controller: power-law memory beats exponential memory by orders of magnitude on persistence, control probes return negative in the power-law regime, and the calibration that would tie the winning kernel to market data remains unidentified. We hope this work inspires further cross-pollination between cognitive science, control theory, and computational economics.

## Acknowledgments

The author thanks the ECOS development community for infrastructure support.

---


## Appendix A: Data Availability

All code, data, and results are available in the replication pack archived on Zenodo: https://doi.org/10.5281/zenodo.23594010 (version DOI for v48; concept DOI: https://doi.org/10.5281/zenodo.23594009). The living repository is https://github.com/caiminqian/JEDC-FSRS-replication. The simulation environment is built on the ECOS framework; configuration files and random seeds are included for reproducibility. v52 changes no data or code; the v51 archive (version DOI 10.5281/zenodo.23602707) contains the data used through v53. v54 adds 2,547 JSON result files for Sections 5.7–5.8, included in the replication pack; a v54 version DOI will be added on release. v55 adds 2,554 JSON result files for the recalibrated reruns of Sections 5.7–5.8 (plus 100 A-500 sensitivity files and 4 bank-sensitivity files: 2 JSON + 2 dao run logs); a v55 version DOI will be added when the pack is released.


## Appendix B: References

## Core Memory & Spaced Repetition
- Anderson, J. R., & Schooler, L. J. (1991). Reflections of the environment in memory. *Psychological Science*, 2(6), 396–408. https://doi.org/10.1111/j.1467-9280.1991.tb00174.x
- Ebbinghaus, H. (1885/1913). *Memory: A contribution to experimental psychology* (H. A. Ruger & C. E. Bussenius, Trans.). New York: Teachers College, Columbia University. https://doi.org/10.1037/10011-000
- Pavlik, P. I., & Anderson, J. R. (2005). Practice and forgetting effects on vocabulary memory: An activation-based model of the spacing effect. *Cognitive Science*, 29(4), 559–586. https://doi.org/10.1207/s15516709cog0000_14
- Schooler, L. J., & Anderson, J. R. (1997). The role of process in the rational analysis of memory. *Cognitive Psychology*, 32(3), 219–250. https://doi.org/10.1006/cogp.1997.0652
- Woźniak, P. A. (1990). *Optimization of learning* (Master's thesis). University of Technology in Poznań. https://super-memory.com/english/ol.htm — Algorithm SM-2 (§3.2, adapted for the web May 10, 1998): https://super-memory.com/english/ol/sm2.htm
- Anderson, R. B., & Tweney, R. D. (1997). Artifactual power curves in forgetting. *Memory & Cognition*, 25(5), 724–730. https://doi.org/10.3758/BF03211315
- Wixted, J. T., & Ebbesen, E. B. (1997). Genuine power curves in forgetting: A quantitative analysis of individual subject forgetting functions. *Memory & Cognition*, 25(5), 731–739. https://doi.org/10.3758/BF03211316
- Wixted, J. T., & Carpenter, S. K. (2007). The Wickelgren power law and the Ebbinghaus savings function [Comment]. *Psychological Science*, 18(2), 133–134. https://doi.org/10.1111/j.1467-9280.2007.01862.x
- Kannan, V., & Ravi, N. (2026). *Evaluation of memory decay models in spaced repetition data* (EdArXiv preprint). Center for Open Science. https://doi.org/10.35542/osf.io/5hqc9_v1

## Behavioral Finance & Memory
- Guttentag, J. M., & Herring, R. J. (1986). *Disaster myopia in international banking* (Essays in International Finance No. 164). International Finance Section, Department of Economics, Princeton University. https://ies.princeton.edu/pdf/E164.pdf
- Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. *Econometrica*, 47(2), 263–292. https://doi.org/10.2307/1914185
- Odean, T. (1998). Are investors reluctant to realize their losses? *The Journal of Finance*, 53(5), 1775–1798. https://doi.org/10.1111/0022-1082.00072
- Shefrin, H., & Statman, M. (1985). The disposition to sell winners too early and ride losers too long: Theory and evidence. *The Journal of Finance*, 40(3), 777–790. https://doi.org/10.1111/j.1540-6261.1985.tb05002.x
- Cont, R. (2001). Empirical properties of asset returns: stylized facts and statistical issues. *Quantitative Finance*, 1(2), 223–236. https://doi.org/10.1080/713665670
- Tversky, A., & Kahneman, D. (1973). Availability: A heuristic for judging frequency and probability. *Cognitive Psychology*, 5(2), 207–232. https://doi.org/10.1016/0010-0285(73)90033-9

## Agent-Based Modeling
- Brock, W. A., & Hommes, C. H. (1997). A rational route to randomness. *Econometrica*, 65(5), 1059–1095. https://doi.org/10.2307/2171879
- Kirman, A. (1993). Ants, rationality, and recruitment. *The Quarterly Journal of Economics*, 108(1), 137–156. https://doi.org/10.2307/2118498
- Lux, T. (1997). Time variation of second moments from a noise trader/infection model. *Journal of Economic Dynamics and Control*, 22(1), 1–38. https://doi.org/10.1016/S0165-1889(97)00061-4
- Lux, T., & Marchesi, M. (1999). Scaling and criticality in a stochastic multi-agent model of a financial market. *Nature*, 397(6719), 498–500. https://doi.org/10.1038/17290
- Tesfatsion, L., & Judd, K. L. (Eds.). (2006). *Handbook of computational economics: Agent-based computational economics* (Vol. 2). Elsevier. ISBN 978-0-444-51253-6. https://doi.org/10.1016/S1574-0021(05)X0200-3
- Zheng, M., Liu, R., & Li, Y. (2018). Long memory in financial markets: A heterogeneous agent model perspective. *International Review of Financial Analysis*, 58, 38–51. https://doi.org/10.1016/j.irfa.2018.04.001

## Contagion & Social Influence
- Bikhchandani, S., Hirshleifer, D., & Welch, I. (1992). A theory of fads, fashion, custom, and cultural change as informational cascades. *Journal of Political Economy*, 100(5), 992–1026. https://doi.org/10.1086/261849
- Centola, D., & Macy, M. (2007). Complex contagions and the weakness of long ties. *American Journal of Sociology*, 113(3), 702–734. https://doi.org/10.1086/521848
- Kasperson, R. E., Renn, O., Slovic, P., Brown, H. S., Emel, J., Goble, R., Kasperson, J. X., & Ratick, S. (1988). The social amplification of risk: A conceptual framework. *Risk Analysis*, 8(2), 177–187. https://doi.org/10.1111/j.1539-6924.1988.tb01168.x

## Macroprudential Policy & Control
- Borio, C. (2003). Towards a macroprudential framework for financial supervision and regulation? *BIS Working Papers No. 128*. Bank for International Settlements. (No DOI assigned; RePEc handle: `RePEc:bis:biswps:128`.) Also published as: *CESifo Economic Studies*, 49(2), 181–215. https://doi.org/10.1093/cesifo/49.2.181
- Gaffard, J.-L., & Napoletano, M. (Eds.). (2012). Agent-based models and economic policy [Special issue]. *Revue de l'OFCE*, No. 124. https://doi.org/10.3917/reof.124.0007
- Timmermann, A. (2006). Chapter 4: Forecast combinations. In G. Elliott, C. W. J. Granger, & A. Timmermann (Eds.), *Handbook of economic forecasting* (Vol. 1, pp. 135–196). Elsevier. https://doi.org/10.1016/S1574-0706(05)01004-9
- Varian, H. R. (Ed.). (1996). *Computational economics and finance: Modeling and analysis with Mathematica®*. Springer. ISBN 978-1-4612-2340-5. https://doi.org/10.1007/978-1-4612-2340-5

## Reinforcement Learning & POMDP
- Kaelbling, L. P., Littman, M. L., & Cassandra, A. R. (1998). Planning and acting in partially observable stochastic domains. *Artificial Intelligence*, 101(1–2), 99–134. https://doi.org/10.1016/S0004-3702(98)00023-X
- Sutton, R. S., & Barto, A. G. (2018). *Reinforcement learning: An introduction* (2nd ed.). MIT Press. ISBN 978-0-262-03924-6. (No DOI assigned.)
- Wiering, M., & van Otterlo, M. (Eds.). (2012). *Reinforcement learning: State-of-the-art* (Adaptation, Learning, and Optimization, Vol. 12). Springer. ISBN 978-3-642-27644-6. https://doi.org/10.1007/978-3-642-27645-3
- Hamadanian, P., Nasr-Esfahany, A., Schwarzkopf, M., Sen, S., & Alizadeh, M. (2025). Online reinforcement learning in non-stationary context-driven environments. In *International Conference on Learning Representations (ICLR)* (Spotlight). arXiv:2302.02182. https://openreview.net/forum?id=l6QnSQizmN

## Long-Memory Econometrics
- Geweke, J., & Porter-Hudak, S. (1983). The estimation and application of long memory time series models. *Journal of Time Series Analysis*, 4(4), 221–238. https://doi.org/10.1111/j.1467-9892.1983.tb00371.x
- Künsch, H. R. (1987). Statistical aspects of self-similar processes. In *Probability Theory and Applications*, 67–74. https://doi.org/10.1515/9783112314227-005
- Robinson, P. M. (1995). Gaussian semiparametric estimation of long range dependence. *The Annals of Statistics*, 23(5), 1630–1661. https://doi.org/10.1214/aos/1176324317
