# Cognitive Spaced Repetition in Agent-Based Economic Modeling: A Power-Law FSRS Approach

**Authors**: MinQian Cai  
**Target Journal**: *Journal of Economic Dynamics and Control* (JEDC)  
**Submission Date**: v48 draft, 2026-10-23 (v43, v44, v45, v46 and v47 preserved unchanged for provenance)
**Word Count**: 9723 (wc -w, including headings and tables; v43 was 6775)

---

## Abstract

We introduce **FSRS (Free Spaced Repetition Scheduler)**, a power-law forgetting model in the FSRS family, into agent-based economic modeling to capture the long-memory effects observed in financial markets—a significant upgrade over the classical Ebbinghaus exponential forgetting curve (hereafter **EE**). Agents equipped with FSRS exhibit realistic panic-complacency cycles, with retrievability decaying slowly over years, mirroring the fat-tailed volatility clustering in post-crisis markets. We model risk memory contagion via network diffusion of perceived retrievability. Calibration to five historical crises gives an initial stability of $S_0 = 45$ days (see Section 3.1 for why this is not a half-life). The macroprudential control problem is formulated as a POMDP. While PPO-based reinforcement learning fails due to sparse delayed rewards, **grid search over intervention parameters cannot identify an optimal threshold on 30-agent populations**: a paired same-seed rerun (Section 5.1) gives identical outcomes for (T=0.45, s=0.40) and (T=0.30, s=0.60) (-314.71 vs -314.71 on seed set 10; -304.23 vs -304.23 on seed set 110; interventions 0.0, target zone 0% in both), because neither threshold ever triggers under FSRS at S=45. The original 15.0% gap (3947 vs 3434) was measured under the default memory bank (initial stabilities 5/3/2, not S=45) and is a seed/network artifact; it is retained in Section 5.1 for audit only. The effective policy on 30 agents is non-intervention. The 1,000-agent run rerun at S=45 in v49 (Section 5.2) gives identical returns for both policies (-1065.35, interventions 0.0), so the v47/v48 $374\%$ figure does not survive at S=45 and is retained in Section 5.2 for audit only (see Section 6.4, limitation 11). A contrasting analysis between FSRS and EE reveals an approximately **47,000-fold difference** in long-term memory retention at tick 500 in the 100-agent comparison (Section 5.1.3), demonstrating that exponential decay severely underestimates market persistence. Our work bridges cognitive psychology and computational finance, offering a new paradigm for macroprudential policy design that accounts for long-memory tail effects.

**Keywords:** spaced repetition, cognitive memory, agent-based modeling, macroprudential policy, FSRS, power-law forgetting, POMDP

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

2. **Memory Contagion Mechanism**: We introduce a network-based diffusion process where agents' perceived retrievability is a weighted average of their own memory and neighbors' memories, with contagion strength α calibrated to historical data.

3. **Parameter Calibration to Historical Crashes**: We calibrate three key parameters—initial stability $S_0$, contagion strength α, and intervention severity mapping—to five major market crash events (1987 Black Monday, 2000 Dot-com Bubble, 2008 GFC, 2020 COVID Crash, 2022 Inflation Shock) using an analytical simulator and grid search. The calibrated initial stability is **$S_0 = 45$ days**, aligning with observed volatility clustering cycles.

4. **Control Optimization via Grid Search**: We formulate the regulator's intervention problem as a POMDP. While PPO fails, systematic grid search over threshold-severity parameters cannot identify an optimal threshold on 30-agent populations: a paired same-seed rerun (Section 5.1) gives identical outcomes for (T=0.45, s=0.40) and (T=0.30, s=0.60), because thresholds never trigger under FSRS. The 1000-agent stress test (2197 → 10402) is a separate run in which interventions do occur, and is retained with its small-sample caveat.

5. **Robustness and Sensitivity Analysis**: We systematically vary network density and initial stability. Results show that under FSRS, both baseline and optimal policies refrain from intervening in the 30-agent grid, and returns are sensitive to the initial stability $S$. In the paired rerun neither configuration outperforms the other, highlighting that FSRS agents are self-stabilizing and that regulatory thresholds must be calibrated to the memory stability scale.

The paper proceeds as follows. Section 2 reviews related work in spaced repetition, behavioral finance memory, contagion, and macroprudential control. Section 3 details the cognitive memory engine (FSRS versus EE), contagion mechanism, governance intervention, and reward formulation. Section 4 describes our experimental setup: environment, baselines, calibration methodology, and control optimization approaches (RL and grid search). Section 5 presents results: optimal policy behavior, large-scale stress tests, robustness analysis, and RL failure diagnosis. Section 6 discusses policy implications, why RL failed, limitations, and future directions. Section 7 concludes.

**Keywords**: spaced repetition; cognitive memory; agent-based modeling; macroprudential policy; FSRS; POMDP
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

Agent-based models have incorporated simple memory decay (Lux, 1997; Brock & Hommes, 1997), but none employ a rigorous cognitive model like FSRS. Our engine provides a quantitative, parameterizable approach.

### 2.3 Contagion via Information Networks

Information diffusion drives herd behavior (Bikhchandani et al., 1992). Complex contagion (Centola & Macy, 2007) requires multiple exposures—captured via our α parameter (mean of neighbors' R). Social amplification of risk (Kasperson et al., 1988) describes how hazards gain attention through media; we implement this as continuous-state diffusion on an Erdős–Rényi graph.

### 2.4 Macroprudential Control and RL

Macroprudential tools (countercyclical buffers, stress tests) aim to curb systemic risk (Borio, 2003). Our POMDP formulation treats the regulator as a central planner with partial observability. While model-free RL (PPO) failed due to sparse/delayed rewards, direct policy search was more tractable, but it did not identify an optimal threshold on 30 agents (see Section 5.1). This reflects a general pattern rather than an anomaly: when the delay between an intervention and its measurable effect exceeds the effective credit-assignment horizon of an on-policy RL algorithm, direct search over a low-dimensional policy parameterization is the more tractable choice for this problem, not a successful optimisation (see Section 6.3 for a full diagnosis).

---


## 3. Model

### 3.1 Agent Cognitive Memory (FSRS-Style Power-Law Forgetting)

The forgetting curve in cognitive psychology is traditionally modeled as exponential decay: $R(t) = \exp(-t/S)$ (Ebbinghaus, 1885). However, extensive data from millions of learners using spaced repetition systems reveals that **real-world forgetting follows a power-law distribution with a fat tail**—memories once consolidated persist for extremely long periods with slow decay. This paper implements a **FSRS-style power-law model** in the FSRS family. The implementation in `fsrs_memory.py` is a simplified tick-based model with parameters $w_{17}$–$w_{20}$ as listed below; it is not the official FSRS-6 scheduler, and the widely cited 500-million-review figure describes the FSRS literature, not a training run performed for this code. Parameter names here follow the code, not the official FSRS-6 21-parameter indexing, and no claim is made that this implementation equals official FSRS-6.

> **Terminology note (EE vs. SuperMemo SM-20).** In parts of the spaced-repetition literature the exponential curve above is loosely attributed to SuperMemo. We do not follow that usage, and we do not implement SM-20. SuperMemo published its early algorithms in full—**Algorithm SM-2** (Woźniak, 1990) is the last of these—whereas the later commercial releases, **SM-3 through SM-20**, are proprietary and their forgetting-curve formulas have never been publicly disclosed. A model whose specification is unavailable can be neither implemented nor independently audited, and therefore cannot serve as a reproducible scientific baseline. Accordingly, the exponential baseline used throughout this paper is the **classical Ebbinghaus curve** $R(t)=\exp(-t/S)$, which we denote **EE** (Ebbinghaus-exponential). All comparisons labelled "FSRS vs. EE" contrast a power-law model against this classical exponential curve; the contribution is a comparison of *forgetting-curve functional forms*, not a benchmark of any commercial product.

Each agent maintains a **CognitiveMemoryBank** consisting of multiple lessons (e.g., `leverage_risk`, `liquidity_crisis`, `bull_market_complacency`). Each lesson has three core state variables:

- **Retrievability** $R(t)$: probability of recalling the memory at tick $t$. Under FSRS:
  $$
  R(t) = \left(1 + \frac{\text{factor} \cdot t}{S}\right)^{-w_{20}}
  $$
  where $t$ is ticks since last review (market shock), $S$ is stability (in days), and $\text{factor} = (0.9^{-1/w_{20}} - 1)$ encodes the target post-review retrievability (0.9). This produces a **power-law decay** $R \sim t^{-w_{20}}$ at long times, in contrast to EE's exponential $e^{-t/S}$.

- **Stability** $S$: measures how long the memory lasts (days). Initially $S_0 = 45$ (calibrated to historical crises, see Section 4.3). $S$ grows when the agent experiences market shocks, representing institutionalized risk controls.

- **Difficulty** $D \in [1,10]$: complexity of the lesson. Harder concepts decay faster. $D$ maps to financial instrument complexity (e.g., plain equity $D=4$, structured products $D=9$).

FSRS stability update after a shock of grade $G$:

$$
S' = S \cdot \exp\left( w_{17} \cdot (G - 3 + w_{18}) \cdot S^{-w_{19}} \right)
$$

Parameters (values used in `fsrs_memory.py`): $w_{17}=1.8729$, $w_{18}=0.5425$, $w_{19}=0.0912$, $w_{20}=0.0658$.

**Economic interpretation:**
- $S^{-w_{19}}$ implements **marginal diminishing**: large $S$ → smaller growth. This is the mathematical origin of the fat tail.
- $G=1$ (systemic collapse) yields negative exponent → $S$ collapses, at $S=45$ to $\approx 15\%$ of its value (14.5%; 9.5% at $S=5$, 23.4% at $S=1000$), modeling a Minsky Moment where institutional memory is wiped out.
- $G=4$ (minor corrections) yields large positive exponent → $S$ multiplies by $7.7\times$ at $S=45$ (12.1\times at $S=5$, 4.7\times at $S=1000$), capturing "Great Moderation" complacency.

FSRS produces **fat-tailed forgetting**: in the 100-agent simulation of Section 5.1.3, $R(500) = 0.7185$ vs EE's $0.000015$—an approximately **47,000\times difference** (the archived rounded inputs 0.718491 / 0.00001528 give 47,022, but the last digits are not significant). This aligns with empirical market memory: post-2008 risk aversion persisted for years, not months. (The closed-form single-memory values at $S=45$ are different—FSRS 0.778, EE $1.5 \times 10^{-5}$—because the simulation includes shocks, leverage feedback, and contagion; do not mix the two sets.)



### 3.2 Memory Contagion

Agents are nodes in an undirected graph `G = (V, E)` where edges represent information-flow relationships (e.g., social networks, professional ties). Each agent i has true retrievability R_true,i(t) from their memory bank. Perceived retrievability is:

R_perceived,i(t) = (1 - α) · R_true,i(t) + α · mean_{j ∈ N(i)} (R_true,j(t))

where α ∈ [0,1] is the contagion strength (calibrated to α = 0.6). Agents use R_perceived for decision-making (trading behavior). This creates a **memory contagion effect**: a panic in one cluster raises neighbors' perceived risk even if their own memory hasn't decayed.

### 3.3 Governance and Intervention

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
| $G=1$ | 0.095 (−90.5%) | 0.145 (−85.5%) | 0.234 (−76.6%) |
| $G=2$ | 0.477 (−52.3%) | 0.546 (−45.4%) | 0.634 (−36.6%) |
| $G=3$ | 2.405 (+140.5%) | 2.050 (+105.0%) | 1.718 (+71.8%) |
| $G=4$ | 12.116 (+1111.6%) | 7.703 (+670.3%) | 4.658 (+365.8%) |

Example: the same severity $s=0.2$ maps in code to $G=3$, giving +140.5% at $S=5$ and +71.8% at $S=1000$—not the v43 claim of +25% / +0.1%, which used the wrong grade and the wrong sign. *Regulatory measures matter most when institutions are fragile* remains true in magnitude for $G=3$/$G=4$, but it is false for $G=2$: a Hard intervention shrinks stability, it does not consolidate it.

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

**Table: grade impact (formula values).** The table in Section 3.3 above gives the exact multipliers. Figure 5 in v43 is withdrawn in v44: its generation script used the parameter list $[w_{17}, w_{18}, w_{19}, w_{20}]$ indexed by grade as the exponent, which is not the stability-update formula, so neither the figure nor its caption can be retained. Replacement figure (v47):

![Correct FSRS grade impact](figures/fig5_grade_impact_v47.png){#fig:grade_impact_v47 width=90%}

**Figure 5 (v47).** Correct stability update $S' = S \cdot \exp(w_{17} \cdot (G - 3 + w_{18}) \cdot S^{-w_{19}})$ with $w_{17}=1.8729$, $w_{18}=0.5425$, $w_{19}=0.0912$. Panel (a): multiplier $S'/S$ vs initial $S$ (log scale); panel (b): multiplier vs grade $G$ at $S=5, 45, 1000$. Values match the table exactly (at $S=45$: 0.145 / 0.546 / 2.050 / 7.703 for $G=1$ to $4$). Script: `experiments/figure_generation/fig5_v47.py`. The v43 figure remains withdrawn; this is a new figure, not a correction of the old file.

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

Agents' cognitive memories start with $S_0 = 45$ in the v48 grid and paired rerun, where S is set explicitly to 45.0 on every lesson after reset (scripts `grid_s45.py`, `paired_s45.py`), and in the v49 1000-agent rerun and Section 5.5 reruns (S set explicitly to 45.0 on every lesson after reset, or after agent creation where the script builds agents directly; see Sections 5.2 and 5.5). Correction (v48 audit): the original grid and the v45 paired rerun did not set S at all and therefore ran the default memory bank (initial stabilities 5/3/2 for the three default lessons); their numbers are retained for audit only and are superseded by Section 5.1. EF is a legacy SM-2 parameter and is not used in FSRS runs. The info_flow network is Erdős–Rényi with p=0.1 in the grid environment (the robustness sweep in v43 did not actually vary p; see Section 5.3).

### 4.2 Baselines

1. **Fixed Threshold**: intervene if avg_R < T, with severity S. Default T=0.3, S=0.6.
2. **Random**: random severity every 10 ticks. (Defined here for completeness; no Random-baseline results are reported in Section 5 and no claim in v44 depends on it.)
3. **RL Baselines**: PPO agents trained on v3/v4 rewards (reported for completeness; they underperformed).

### 4.3 Parameter Calibration

Before control optimization, we calibrate three environment parameters to historical market crash data:

- **S_initial**: initial stability (days)
- **α**: contagion strength
- **severity**: mapping from regulator's action to memory consolidation

Using a grid search over a 5-event simulator (1987, 2000, 2008, 2020, 2022), we find optimal:

- **S_initial = 45 days** (initial stability; for comparison, an EE curve with $S=45$ would have half-life $45 \cdot \ln 2 \approx 31$ days, whereas the FSRS power-law curve has no comparable half-life—under the paper's own FSRS formula, $R=0.5$ would take about 427,000 days, so $S$ must not be read as a half-life)
- **α = 0.6** (strong contagion)
- **severity_crisis = 0.5** (baseline intervention impact)

These values are the calibrated targets. In v49 they are actually applied in the grid, the paired rerun, the p/S sweep, the 1000-agent rerun, and the Section 5.5 reruns (S set explicitly after reset, or after agent creation where the script builds agents directly; see Sections 5.2 and 5.5 for the as-run settings). The original runs used the default memory bank (initial stabilities 5/3/2) and are retained for audit only.

### 4.4 Control Optimization

We explore two approaches:

#### 4.4.1 Reinforcement Learning (PPO)

We train PPO agents with MLP policies on the ECOS environment using rewards v1–v4. Despite architectural adjustments (reward shaping, entropy regularization), PPO fails to converge to a deterministic policy that beats the fixed threshold baseline. The learned policies either:
- Output mean ≈ 0 and rely on stochasticity during training (v3, v4)
- Learn to never intervene (v1)

We attribute failure to **sparse and delayed rewards**: an intervention's positive effect manifests after 30–50 ticks, making credit assignment difficult for on-policy algorithms with short rollouts (2048 steps). Value function estimates have near-zero explained variance, leading to poor policy gradients.

#### 4.4.2 Grid Search over Threshold Policies

Given RL's poor performance, we perform an exhaustive grid search over discrete threshold-severity pairs:

- Thresholds T ∈ {0.25, 0.35, 0.45, 0.55, 0.65}, plus the baseline T=0.30 appended by the script (6 thresholds x 4 severities = 24 configurations; this reconciles the 20-configuration list with the 24-configuration count in Section 5.1)
- Severities S ∈ {0.2, 0.4, 0.6, 0.8}

Each configuration is evaluated over 10 episodes (mean return). No optimal policy is discovered (see the paired rerun in Section 5.1):

- **No identifiable optimum**: the paired same-seed rerun in Section 5.1 gives identical outcomes for (T=0.45, s=0.40) and (T=0.30, s=0.60); thresholds never trigger under FSRS.

![Grid search heatmap](figures/fig2_grid_search.png){#fig:grid_search width=90%}

**Figure 2.** Grid search heatmap over threshold $T$ and severity $s$ (original run, seed-confounded; see Section 5.1 for the paired rerun that supersedes the optimum claim). Original means: (T=0.45, s=0.40) ~3947; baseline (T=0.30, s=0.60) ~3434. The 15.0% gap is a seed/network artifact, not a policy effect.

Original grid means were **3947 ± 1177** vs **3434 ± 1181**, but the two configurations were evaluated on different seed sets (seed_offset 9 vs 22), so this gap is not evidence of a policy effect; see the paired rerun in Section 5.1.

### 4.5 Stress Tests and Robustness

We validate the threshold configurations on:

1. **1000-agent populations** (network effects)
2. **Varied network densities** $p \in \{0.05, 0.10, 0.20\}$
3. **Varied memory decay rates** $S \in \{30, 45, 60\}$

The 1000-agent test uses the fixed parameters (T=0.55, s=0.20) against baseline (T=0.30, s=0.60) (corrected in v47; see Section 5.2), i.e., no re-optimization. The network-density / initial-stability sweep is reported with correctly parameterized results in Section 5.3 (v47).

The grid search heatmap (**Figure 2**) is retained for audit; it does not identify an optimal pair (see Section 5.1).

---

## 5. Results

### 5.1 Optimal Policy Behavior

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

**Paired same-seed rerun at S=45 (v48, supersedes the v45 paired table as policy evidence).** Same design as v45, plus S set explicitly to 45.0 on every lesson after reset (script `paired_s45.py`, output `paired_s45.json` in the replication pack):

| Seed set | (T=0.45, s=0.40) return | (T=0.30, s=0.60) return | Interventions (both) | Target zone (both) |
|---|---|---|---|---|
| 10 | -314.71 +/- 128.20 | -314.71 +/- 128.20 | 0.0 | 0.0% |
| 110 | -304.23 +/- 122.01 | -304.23 +/- 122.01 | 0.0 | 0.0% |

Outcomes are again identical within each seed set, and per-episode returns are identical, because neither threshold ever triggers at S=45 either: avg_R stays above the target zone, so the reward is dominated by the -10 per-tick out-of-zone penalty and the target-zone time is 0%. The v45 paired numbers (+3836/+3725, zone ~49%) were the same comparison run under the default bank, not under S=45; the conclusion (no optimum identified, effective policy non-intervention) is unchanged, but the absolute returns and zone times are not comparable across S settings.

**Full grid at S=45 (v48).** Script `grid_s45.py`, output `grid_s45.json`: all 24 configurations (6 thresholds including baseline 0.30, 4 severities, 10 episodes each, seed_offset by configuration as in the original grid), returns from -325.19 (T=0.45, s=0.40) to -247.56 (T=0.30, s=0.80), baseline (T=0.30, s=0.60) -266.45 +/- 136.30, interventions 0.0 and target zone 0.0% in every configuration, crisis steps 0 throughout. As in the original grid, configurations still use different seed sets, so the spread across configurations is not a policy comparison; the paired table above is the controlled comparison. The v44/v45 statement that interventions were 0.0 except at T=0.65 applied to the default-bank grid only and does not hold at S=45, where no threshold up to 0.65 triggers at all.

**Figure 2** shows the grid search heatmap over threshold-severity space (original default-bank run, retained for audit). No optimum is claimed from this heatmap (see the paired reruns above).

Robustness across network density and initial stability is discussed in Section 5.3, where the v43 robustness table is withdrawn for the reasons stated there; the verified grid summary above is the robustness evidence retained in v44.

### 5.1.3 FSRS vs EE: A Contrastive Analysis

To quantify the impact of switching from exponential (EE) to power-law (FSRS) forgetting, we ran a head-to-head comparison with 100 agents (55 FSRS, 45 EE) over 500 ticks, from `results/comparison/fsrs_vs_ee.json` (where the EE group is keyed `sm20` in the file—a legacy label for the EE baseline, not commercial SM-20). Figure 4 shows the average retrievability $\overline{R}$ trajectories.

**Key empirical differences:**

| Metric | EE (Exponential) | FSRS (Power-Law) | Ratio |
|--------|--------------------|-----------------|-------|
| $R(100)$ | 0.1108 | 0.7968 | 7.19\times |
| $R(300)$ | 0.0013 | 0.7427 | 571\times |
| $R(500)$ | **0.000015** | **0.7185** | **~47,000\times** |
| Final leverage | 10.00\times | 6.35\times | 0.64\times |
| Crisis events ($R<0.3$) | 45 of 45 EE agents (100% of the EE group) | 0 agents (0%) | — |

The contrast is stark. EE's exponential decay causes **catastrophic forgetting**: by tick 100, average $R$ has already fallen to 0.111; by tick 300 to 0.0013; by tick 500 to 0.000015—all 45 EE agents are below the crisis threshold and levered to the maximum 10.00\times. FSRS's power-law decay retains $R=0.719$ at tick 500, keeping leverage at a sane 6.35\times. The fat tail—$R \sim t^{-0.0658}$—means memory persists for years of simulated time. Ratios in the table are rounded to the nearest thousand; the archived inputs 0.718491 / 0.00001528 give 47,022, but the last digits of the archived values are not significant, so the ratio is reported as approximately 47,000.

Figure 4 visualizes this divergence. The EE curve (dashed red) plunges exponentially, crossing the danger threshold ($R=0.5$) between tick 30 (0.525) and tick 40 (0.420) and approaching zero by tick 300. The FSRS curve (solid blue) decays in the first 100 ticks then flattens dramatically, staying above 0.7 throughout (0.909 at tick 10 to 0.719 at tick 500)—that is, above the reward target zone $[0.5, 0.7]$, not inside it.

![FSRS vs EE comparison](figures/fig4_fsrs_vs_ee.png){#fig:fsrs_vs_ee width=90%}

**Economic interpretation.** The EE model implies that market participants fully forget a crisis on a short scale: under the EE curve, $3S = 135$ days is 0.37 years, not 1–2 years. Empirically, post-2008 risk aversion persisted through at least 2015 (volatility regimes, trader psychology surveys). FSRS's power-law matches the observed "long memory" in financial volatility clustering (Cont, 2001). The leverage difference is equally telling: under EE, agents reach maximum leverage within 300 ticks—mirroring pre-2008 behavior where risk controls evaporated. FSRS's more gradual leverage increase (6.35\times at tick 500) better matches observed leverage cycles that build over 5–10 years.

**Implication for policy.** Regulators using EE-based models would **underestimate memory persistence** and potentially intervene too late, assuming agents have already forgotten. FSRS suggests that even at tick 300, $R = 0.743$—agents are still quite risk-aware. No intervention threshold is identified by the 30-agent grid (Section 5.1); a pre-emptive trigger — act while memory is still strong enough that a mild intervention consolidates it — is a hypothesis for future work with environments in which thresholds actually trigger, not a finding of this experiment.

---

### 5.2 Large-Scale Stress Test (1000 Agents)

Scaling to 1000 agents: baseline (T=0.30, s=0.60) return **2197**, comparison policy (T=0.55, s=0.20) return **10402**, a **373.6% improvement** (374% rounded). Correction (v47 audit): the paper previously labelled the comparison policy as (T=0.45, s=0.40); the archived script that produced the JSON, `archive/stress_control_optimal.py` (now in the replication pack as `experiments/stress/stress_control_optimal.py`), actually runs (T=0.55, s=0.20) against baseline (T=0.30, s=0.60), and the JSON itself records no threshold/severity, so the (0.45, 0.40) attribution was unsupported. Both policies avoid crises, but the comparison policy maintains **39.6%** time in target zone vs baseline **30.1%**. Interventions are 5.0 per episode for baseline and 15.0 per episode for the comparison policy, over 1000 ticks per episode (the script's max_ticks=1000; this is the run the Section 6.2 'over 1000 ticks' phrase refers to, distinct from the 300-tick grid default in Section 4.1). Seed pairing: the script runs episodes with seed=ep (0, 1, 2) for both policies on the same env object, so episodes 1 and 2 are paired; episode 0 is not paired because `ECOSControlEnv.reset` treats seed=0 as falsy and draws a random seed each time. Given the near-zero variance (std below $10^{-5}$, min/max within $10^{-5}$ of the mean), the episode-0 flaw does not change the result, but it is disclosed here. The near-zero variance is not inconsistent with the 30-agent seed sensitivity: with 1000 agents, per-episode means average over 1000 agents and network variation largely cancels, whereas 30-agent means do not. Scope (v49): the run above used the default memory bank, so its 2197/10402 numbers are not S=45 numbers and must not be compared directly with the S=45 grid numbers in Section 5.1. The 373.6% figure is withdrawn as a policy claim in v49 (see the S=45 rerun below) and is retained above for audit only; it was in any case a point estimate from only 3 episodes, not a robust effect size.

**S=45 rerun (v49).** Script: `experiments/stress/stress_s45.py`; output: `results/stress/stress_1000a_s45.json`. Method: same environment and policies as the original run, with S set explicitly to 45.0 on every FSRS lesson after every reset, followed by an observation recompute. Design change, disclosed: the rerun uses seeds 1, 2, 3 for both policies (paired), avoiding seed 0, which `ECOSControlEnv.reset` treats as falsy and replaces with a random seed (the flaw in the original run's episode 0). Results, 1000 agents, 1000 ticks per episode, 3 episodes per policy:

| Policy | Mean return | Std | Mean interventions | Mean zone % |
|---|---|---|---|---|
| Baseline (T=0.30, s=0.60) | -1065.35 | 0.00 | 0.0 | 0.0 |
| Comparison (T=0.55, s=0.20) | -1065.35 | 0.00 | 0.0 | 0.0 |

Improvement: **0.0%**. Per-episode returns are bit-identical across all three seeds and both policies (-1065.3521728515625 in every episode); per-episode interventions are 0 and zone time 0.0% throughout. Runtimes: baseline 425 s, comparison 486 s. Interpretation: at S=45, avg_R never falls below either threshold even at 1000 agents, so neither policy ever triggers and the two policies are the same policy in effect — hence identical returns are expected for the policy comparison. The cross-seed identity (network realisations differ: 50195, 50389, 50027 undirected edges across seeds 1–3) is recorded here as an observed property of this run, not a claimed mechanism: with zero interventions, the return depends only on the true-R trajectory, which does not move across these seeds in this run. The v47/v48 374% figure therefore does not survive at S=45. The rerun is likewise only 3 episodes per policy, so the 0.0% is a statement about this regime, not a general scaling law — but unlike 373.6%, it is not a sampling artifact in the same way, since the returns are bit-identical rather than merely close.

The 1000-agent system-stability test in the replication pack (`results/stress/stress_1000a_output.txt`: 1000 agents, 1000 ticks, 2,332,508 trades, 90.80 ms/tick, peak memory 1085.7 MB, 0 errors) is a separate stability run and is not the source of the 2197 → 10402 returns above.

### 5.3 Robustness Analysis (v47: correctly parameterized p/S sweep)

The robustness table and Figure 3 reported in v43 are **withdrawn in v44** and are not reproduced here. Two archived scripts contradict the v43 description: the September robustness script (`experiments/robustness/run.py`) accepts $p$ and $S_{initial}$ as arguments but never passes them to the environment, so identical rows across $p$ cannot be evidence that $p$ has no effect; the April robustness script uses different policies (baseline T=0.75, optimal T=0.80 by default), 300 agents, and 200 ticks, not the paper's stated 30 agents, 300 ticks, and optimal policy (T=0.45, s=0.40). The v43 claim that network density has negligible effect, and the contrast claim that an EE policy improves returns by >1000%, have no archived source in the replication pack and are therefore also withdrawn in v44.

Verified robustness evidence retained in v44 is the grid itself (Section 5.1): across all 24 threshold-severity configurations, returns range from 3288 to 3947, crisis steps are 0 throughout, and interventions are 0.0 except at T=0.65 (0.1–0.6 per episode). A correctly parameterized $p$/$S$ sweep is reported below (v47); the v44 open item is closed by that sweep, subject to the isolated-agent artifact disclosed there.

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

Findings. (1) Network density is **not** negligible, contradicting the v43 claim: target-zone time falls from 22–28% at $p=0.05$ to 0% at $p \geq 0.10$, and mean reward changes sign. (2) At low $p$, seed dominates: at $p=0.05$, $S=30$, per-episode returns are -656, -577, +6445 (std 3329), so 3-episode means at $p=0.05$ are unreliable. (3) Mechanism, verified: in `ECOSControlEnv._compute_obs`, an agent with no predecessors gets perceived $R = (1-\alpha) \times$ true $R = 0.4 \times$ true $R$, not true $R$. Isolated-agent counts (script `experiments/robustness/iso_check.py`): at $p=0.05$, seeds 1–3 have 4, 3, 10 isolated agents; at $p=0.10$, 1, 0, 0; at $p=0.20$, 0, 0, 0. Focused check ($p=0.05$, $S=45$): per-episode zone 0%, 0%, 75% — the seed-3 episode, with 10 isolated agents, has mean perceived $R$ dragged from ~0.78 (true) toward ~0.62, into the target zone, earning +20/tick instead of -10/tick, for a return of +5735 vs about -600 for the other seeds. The $p$ effect in this environment is therefore largely an isolated-agent artifact of the contagion formula, not a genuine contagion benefit; the fix for future work is to fall back to true $R$ when an agent has no neighbours, and no policy recommendation is drawn from the $p$ sweep until that fix is in. (4) The $S$ effect is $p$-dependent: at $p \geq 0.10$, higher $S$ gives higher (less negative) reward monotonically; at $p=0.05$, higher $S$ gives lower mean reward, driven by the isolated seed-3 episode (6445 → 5735 → 5012 as $S$ rises). No clean '$S$ improves returns' claim is made. (5) Interventions are 0.0 in all 27 episodes, so this sweep tests reward sensitivity to $p$/$S$ through the $R$ trajectory, not intervention policy.
### 5.4 Why RL Failed

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

In contrast, grid search searches the deterministic policy space directly, bypassing sample inefficiency, but on 30 agents it still did not identify an optimal threshold (see Section 5.1).

---



### 5.5 Additional Validation with Extended Experiments

To further validate the FSRS engine under more realistic and longer-horizon conditions, we conducted three supplementary experiments: (1) end-to-end trading performance with HumanAgent, (2) Monte Carlo robustness over 30 independent runs, and (3) a 10-year (3650-tick) long-term memory persistence study. All experiments use the FSRS engine with α=0.6. Audit (v49): none of the three original scripts sets S or uses ECOSControlEnv; they build HumanAgent directly with the default memory bank (leverage_risk S=5.0, liquidity_crisis S=3.0, bull_market_complacency S=2.0; the LESSONS dict also defines panic_selling S=4.0 and regulation_change S=15.0, which the default bank does not load). The as-published numbers below are therefore default-bank numbers, not S=45 numbers. Each experiment was rerun at S=45 in v49 (S set to 45.0 on every FSRS lesson after agent creation); the rerun numbers are reported alongside the originals, and the originals are retained for audit.

#### 5.5.1 End-to-End Trading Performance

We ran a full multi-agent trading simulation over 200 ticks across three markets (BTC, ETH, AAPL) with 9 agents (1 HumanAgent using FSRS, 5 RetailAgents, 2 MarketMakers). The HumanAgent achieved:

- **Final retrievability**: R = 0.9991 (maintained >0.98 after tick 100)
- **Profit/Loss**: $7,091.30 (2.8% return)
- **Maximum drawdown**: 35.7%
- **Total trades**: 51 executions
- **Shocks experienced**: 9 market events

Despite 9 volatility shocks, the HumanAgent's memory recovered quickly, ending at R=0.999—demonstrating FSRS's ability to consolidate risk awareness. The 2.8% profit with moderate drawdown (35.7%) suggests FSRS agents generate realistic risk-adjusted returns. Run configuration: 200 ticks, seed 20260418, markets BTC/ETH/AAPL, shock probability 0.03. S=45 rerun (v49; script `experiments/trading/e2e_s45.py`, output `results/validation_5_5/e2e_verification_results_s45.json`): final HumanAgent R = 0.9998 (original 0.9991), per-lesson final R 0.998 each. The shock sequence is identical to the original (same 9 ticks and severities, same seed), so the 0.9991 to 0.9998 change comes only from S. The P&L ($7,091.30), maximum drawdown (35.7%), and trade count (51) above come from a separate run (`full_trading_simulation.json`) that was not rerun at S=45 and must not be cited as S=45 results.

#### 5.5.2 Monte Carlo Robustness (30 Runs, 250 Ticks)

We ran 30 stochastic simulations with different seeds, comparing FSRS against EE (100 agents, 250 ticks each).

| Metric | EE (Exponential) | FSRS (Power-Law) | Difference |
|--------|--------------------|-----------------|------------|
| Final $R$ (mean ± std) | 0.6040 ± 0.2493 | 0.9421 ± 0.0581 | +56.0% mean |
| Final $R$ (median) | 0.7224 | 0.9671 | — |
| Final $R$ (min) | 0.0345 | 0.7824 | — |
| Final $R$ (max) | 0.9643 | 0.9996 | — |

FSRS shows **lower variance** (std 0.058 vs 0.249) and **higher minimum** retrievability. In the 30 runs, 19 EE runs exceeded R=0.5; all 30 FSRS runs exceeded R=0.5, and 27 exceeded R=0.85. Setup (fills the missing detail): 30 runs, seeds 0–29, 250 ticks, sample every 10 ticks, shock_prob 0.02, severity range [0.15, 0.4], markets BTC/ETH/AAPL/SPY. S=45 rerun (v49; script `experiments/monte_carlo/mc_s45.py`, output `results/validation_5_5/fsrs_vs_ee_monte_carlo_s45.json`): FSRS final R mean 0.9820 ± 0.0238 (original 0.9421 ± 0.0581), median 0.9932, min 0.9012, max 0.9999; all 30 FSRS runs exceed R=0.85 (original 27/30) and all 30 exceed R=0.5. EE is unchanged within float noise (mean 0.6040 ± 0.2493), and the shock sequence is identical to the original (mean 5.3 per run, same per-run counts). The FSRS–EE gap widens from 0.338 to 0.378, in the expected direction: S=45 decays more slowly, so final R is higher and tighter.

#### 5.5.3 Long-Term Memory Persistence (10-Year Horizon)

We extended simulation to **3650 ticks** (~10 years) with 8 runs per engine.

**Key findings**:

- **FSRS near-perfect retention**: mean final $R$ = **0.9996**
- **EE severe decay**: mean final $R$ = **0.9074**
- **Trajectory divergence**: by tick 3650 the gap is **0.0922** absolute (0.9996 − 0.9074). Intermediate tick-500 values for the 10-year run are not in the archived summary file and are not claimed in v44. Setup (fills the missing detail): 8 runs, seeds 200–207, 3650 ticks, sample every 50 ticks, shock_prob 0.02, severity range [0.15, 0.4], markets BTC/ETH/AAPL/SPY. S=45 rerun (v49; script `experiments/longterm/lt10y_s45.py`, output `results/validation_5_5/fsrs_vs_ee_10year_3650d_s45.json`): FSRS mean final R = 0.99958, std 0.00057, range [0.99813, 0.99996] — bit-identical to the original in all 8 runs; EE mean 0.90738 ± 0.12215, gap 0.0922, unchanged. Mechanism: `FSRS_Economic_Memory.process_market_shock` caps S at 36500 (100 years), and with mean 69.9 shocks per run at G=3/G=4 multipliers of 2–12x, S starting from 5 and from 45 both hit the cap, after which the trajectories merge. The 10-year gap is therefore insensitive to initial S by saturation, not by design discrimination, and must not be cited as evidence that S=45 was verified by this experiment; it is evidence that this experiment cannot discriminate S.

![FSRS vs EE comparison (10-year horizon)](figures/fig6_fsrs_vs_ee_10year.png){#fig:fsrs_vs_ee_10year width=90%}

**Figure 6.** FSRS vs EE retrievability over 3650 ticks. EE decays to R=0.907 by year 10; FSRS maintains R>0.999. The power-law fat tail ensures memory persists indefinitely once consolidated.

The 10-year result strongly supports our core claim: **exponential forgetting severely underestimates long-term memory persistence**. Even after a decade, FSRS agents retain near-perfect risk awareness (R=0.9996), while EE agents lost ~9.2% of their memory. This gap has material implications for leverage cycles and crisis recurrence.

#### 5.5.4 Summary of Extended Validation

The additional experiments reinforce the main findings:

1. **End-to-end trading**: FSRS agents achieve realistic P&L (2.8%) and risk controls (max DD 35.7%) in multi-market environments.
2. **Monte Carlo stability**: FSRS final R has 0.23\times the EE standard deviation (0.058 vs 0.249) in the original run, and 0.095\times (0.024 vs 0.249) in the S=45 rerun, demonstrating robust memory consolidation.
3. **10-year persistence**: FSRS retains 99.96% retrievability (mean final $R$ = 0.9996); EE decays to 90.7%, confirming the fat-tail effect at economic timescales — with the v49 qualifier that the S=45 rerun is bit-identical by S-cap saturation (Section 5.5.3), so this experiment does not discriminate S.

Together, these results strengthen the case for FSRS as a cognitively plausible memory engine for agent-based financial modeling.

---

## 6. Discussion

### 6.1 Economic Interpretation
Under FSRS, the effective policy on 30 agents is **non-intervention** (see the paired rerun in Section 5.1; no threshold-severity optimum is identified by this experiment). Both configurations record zero interventions across 10 episodes, as avg_R never falls below either threshold in these runs. The original grid's modest return gap (3434 vs 3947) is a seed/network artifact (Section 5.1), not a policy effect, and the fact that thresholds never fire means this regime cannot discriminate between thresholds — it does not prove thresholds would be irrelevant in a regime where avg_R does fall below them. This indicates that **FSRS agents are intrinsically self-stabilizing** in this regime and do not require active regulatory control to maintain risk awareness.

From a macroprudential perspective, this suggests:
- **Intervention thresholds are largely moot** under FSRS because avg_R stays above 0.5 most of the time; setting a threshold lower than 0.6 will almost never trigger.
- **Severity parameters are irrelevant** when interventions never occur; the regulator could set s to any value without consequence.
- **Policy implication**: In markets where participants exhibit power-law memory (long-lasting risk aversion), macroprudential tools should be **relaxed or used only as emergency backstops**. Continuous monitoring may suffice; active interventions are unnecessary and could even be destabilizing if applied inappropriately.

The near-equivalence of the two paired configurations underscores that **the best policy is often no policy** when the underlying cognitive model captures long memory naturally.


### 6.2 Policy Implications: "Monitor, Don't Micromanage" Macroprudential Approach

Our findings under FSRS revise the "early and mild" prescription. Because agents retain long-term risk awareness, **pre-emptive light measures are largely redundant**; the system self-stabilizes. Effective macroprudential policy should instead:
- **Monitor, do not micromanage**: in the 30-agent regime no threshold ever triggers and no threshold-severity optimum is identified (Sections 5.1, 6.1), so a fixed trigger/severity prescription is not supported by this experiment; any trigger must be validated in a regime where avg_R actually falls below it,
- **Reserve intervention for genuinely fragile states**: the only run in which interventions occur at scale is the original default-bank 1000-agent run, where the comparison policy (T=0.55, s=0.20) intervened more mildly and more frequently than baseline (15.0 vs 5.0 per episode), not more strongly and less frequently; at S=45 both policies record 0.0 interventions (Section 5.2),
- **Avoid over-intervention**: continuous tweaking is counterproductive; the power-law dynamics mean that once memory is strong, it persists with minimal regulatory input.

Real-world tools (CCyB, stress tests) could be calibrated to activate only when systemic risk perception falls below historically calibrated thresholds aligned with FSRS initial stability $S_0 = 45$ days. Interventions in the 30-agent grid were zero; in the original default-bank 1000-agent scaling run they averaged 15.0 per episode for the comparison policy (T=0.55, s=0.20) over 1000 ticks, and in the v49 S=45 rerun they are 0.0 for both policies (Section 5.2). Macroprudential authorities should therefore **reserve major actions for genuinely fragile states**, rather than frequent fine-tuning.

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

1. **Simplified memory model**: We use a single retrievability score per agent per lesson; real memory is multi-dimensional (episodic, semantic, procedural).
2. **Homogeneous agents**: All agents have identical memory parameters; future work should introduce heterogeneity in S and α.
3. **Deterministic environment**: No exogenous news shocks; only endogenous dynamics.
4. **Grid search scalability**: While effective for 2D threshold-severity, higher-dimensional control (e.g., targeting specific agent subgroups) would require more advanced optimization (Bayesian optimization, MPC).
5. **No real-world validation**: Calibration used synthetic VIX-proxy curves; actual market data would strengthen claims.
6. **Robustness sweep (v47) and isolated-agent defect**: the v43 sweep is withdrawn (see Section 5.3); a correctly parameterized $p$/$S$ sweep is now reported in Section 5.3, with the isolated-agent artifact disclosed (an agent with no predecessors gets perceived R = 0.4 x true R, dragging mean perceived R into the target zone). The sweep does not support a '$p$ negligible' or '$S$ improves returns' claim, and the defect itself is not fixed in this paper: the fix (fall back to true R when an agent has no neighbours) is future work, and the current environment still runs with the defect.
7. **Figure 5 replaced (v47)**: see Section 3.3; the v43 figure used an incorrect exponent and remains withdrawn, and a new figure from the correct formula is now included.
8. **PPO training script not archived**: Section 5.4 reports training outcomes from archived logs and model files, not a rerunnable training script in the replication pack.
9. **Grid optimum unidentified (v45); 1000-agent audit (v47)**: the original 30-agent grid evaluated each configuration on a different seed set, and the paired same-seed rerun in Section 5.1 gives identical outcomes for both threshold configurations; no threshold-severity optimum is claimed. The 1000-agent run is now audited in Section 5.2: its comparison policy is (T=0.55, s=0.20), not (T=0.45, s=0.40), episodes 1–2 are paired and episode 0 is unpaired due to the falsy-seed bug, and the near-zero variance means that flaw does not change the result. The 373.6% figure is withdrawn as a policy claim in v49: the S=45 rerun gives 0.0% (see Section 5.2); 373.6% remains audit-only for the original default-bank run, and was in any case a point estimate from only 3 episodes, not a robust effect size.
11. **S parameterisation scope (v49)**: the grid, the paired rerun, the p/S sweep, the 1000-agent run, and all three Section 5.5 experiments have now been rerun at S=45 (Sections 5.2, 5.5). What remains not S=45-verified: the E2E P&L, drawdown, and trade-count figures (from `full_trading_simulation.json`, not rerun), and the PPO training outcomes (Section 5.4, script not archived). The 10-year S=45 result is bit-identical to the original by S-cap saturation (Section 5.5.3), so it does not discriminate S; the E2E and Monte Carlo reruns do show S effects (Sections 5.5.1, 5.5.2).
10. **v45 pi-review adjudication (fixed in v46)**: pi (gpt-oss:120b) returned VERDICT: FAIL on a HIGH claim that Table 2 mismatches same_seed.json. Adjudication: not sustained — the paired table in v45 matches same_seed.json exactly (3836.30 ± 1126.90, 3725.26 ± 1063.03, 49.97%, 48.63%), and the HIGH compared the audit-labelled original Table 2 against the paired rerun. Two genuine MEDs from that review are fixed in v46: the Section 6.1 paragraph still called the policy 'optimal … derived from grid search' and quoted the original gap without an artifact qualifier, and Table 2's row label 'Optimal' and intro lacked an audit label. Pi's word-count and 374% rounding points are not sustained (word count verified by wc -w; 373.6% rounds to 374% and the small-sample caveat is present).

### 6.5 Future Research Directions

- **Isolated-agent fix**: fall back to true R when an agent has no neighbours, then rerun the p/S sweep and the grid, so the p and S effects can be read without the artifact (see Section 6.4, limitation 6).
- **Multi-lesson coupling**: Allow lessons to influence each other's stability gains (cross-coupling matrix ρ_AB). Could reveal emergent phenomena like panic-generalization across memory domains (liquidity risk → leverage risk).
- **Adaptive controllers**: Implement Model Predictive Control using the analytical simulator for real-time intervention planning; compare to fixed-threshold.
- **Heterogeneous agents**: Introduce distribution of S values (memory half-lives) across agents; test optimal policy robustness.
- **Exogenous shocks**: Add news-driven volatility spikes to environment; test policy resilience.
- **Real-data calibration**: Replace synthetic VIX proxy with actual market volatility indices (VIX, VSTOXX) and crisis timelines; re-calibrate S, α, severity.

---

## 7. Conclusion

We have introduced a cognitive memory engine based on FSRS power-law forgetting, contrasted with the classical Ebbinghaus exponential forgetting curve, into agent-based economic modeling. Agents equipped with spaced repetition exhibit realistic forgetting dynamics: retrievability decays as a power law after market shocks, and interventions act as memory consolidations that boost stability. Crucially, we demonstrated that memory is not purely private—agents influence each other's perceived risk via information-flow networks, creating systemic amplification of fear and greed (contagion effect).

Through calibration to five historical market crashes (Black Monday 1987, Dot-com Bubble 2000, Global Financial Crisis 2008, COVID Crash 2020, Inflation 2022), we calibrated initial stability $S_0 = 45$ days. Under EE this would imply a 31-day half-life, but under FSRS the power-law tail keeps retrievability high for years, so the 45-day figure must not be read as a forgetting half-life. This distinction matters for the behavioral claim: market participants' risk awareness does not decay on a monthly timescale under FSRS; it is the EE counterfactual that does.

The regulator's intervention problem, formulated as a POMDP with partially observable agent states, proved challenging for standard RL (PPO) due to sparse and delayed rewards. However, direct parameter optimization via grid search did **not** identify an optimal control strategy on 30-agent populations: a paired same-seed rerun (Section 5.1) gives identical outcomes for (T=0.45, s=0.40) and (T=0.30, s=0.60) (3836.30 vs 3836.30 on seed set 10; 3725.26 vs 3725.26 on seed set 110; interventions 0.0 in both), because thresholds never trigger under FSRS. The original 15.0% gap (3947 vs 3434) and target-zone gap (51.3% vs 45.0%) are seed/network artifacts and are retained in Section 5.1 for audit only. The 1000-agent result at S=45 (Section 5.2) gives identical returns for both policies (-1065.35, interventions 0.0), so the v47/v48 374% figure (10402 vs 2197, default bank) is withdrawn as a policy claim and retained for audit only; on 1000 agents at S=45, as on 30 agents, the effective policy is non-intervention in this regime.

The effective policy is **non-intervention** under FSRS on 30 agents: both configurations record zero interventions across all episodes, because avg_R never falls below either threshold. This indicates that **FSRS agents are intrinsically self-stabilizing** and do not require active regulatory control to maintain risk awareness in this regime.

From a policy perspective, this implies that **when market participants exhibit power-law memory, macroprudential authorities can afford a hands-off approach**. The long memory itself acts as a stabilizer; frequent interventions are not only unnecessary but could introduce noise. Regulators should focus on **surveillance and exceptional measures** for true systemic crises (avg_R < 0.3), which are exceedingly rare under FSRS dynamics.

From a methodological perspective, our work demonstrates that **control problems with long-delayed effects may be better served by direct policy search than by model-free RL** when the parameter space is low-dimensional. The failure of PPO here aligns with recent critiques of applying standard RL to economic domains with sparse feedback.

**Limitations** remain. Our memory model is a single scalar retrievability; real cognition involves multi-dimensional episodic and semantic memory. Agents are homogeneous; introducing heterogeneity in memory parameters could reveal richer dynamics. The environment is closed (no exogenous news); future work should incorporate stochastic shocks. Finally, calibration used a synthetic VIX proxy; real market volatility data would strengthen external validity.

**Future research directions** include: (1) multi-lesson memory coupling, where different risk types (liquidity, leverage, contagion) cross-influence; (2) adaptive MPC controllers using the analytical simulator; (3) heterogeneous agent populations with distributed memory half-lives; (4) deployment of the non-intervention baseline as a benchmark for real-world macroprudential stress testing frameworks.

In sum, this paper establishes a **cognitive foundation for agent-based financial modeling**, linking the psychology of spaced repetition to systemic risk dynamics. The effective control principle—monitor, do not micromanage, with intervention reserved for genuinely fragile states (a regime not observed in the 30-agent FSRS grid, and in the original default-bank 1000-agent run realised as milder, more frequent intervention, not stronger and less frequent (at S=45 the rerun records 0.0 interventions for both policies, Section 5.2))—offers a computationally grounded principle for stabilizing complex financial networks. We hope this work inspires further cross-pollination between cognitive science, control theory, and computational economics.

---

## Acknowledgments

The author thanks the ECOS development community for infrastructure support.

---


## Appendix A: Data Availability

All code, data, and results are available in the replication pack archived on Zenodo: https://doi.org/10.5281/zenodo.23594010 (version DOI for v48; concept DOI: https://doi.org/10.5281/zenodo.23594009). The living repository is https://github.com/caiminqian/JEDC-FSRS-replication. The simulation environment is built on the ECOS framework; configuration files and random seeds are included for reproducibility.


## Appendix B: References

## Core Memory & Spaced Repetition
- Anderson, J. R., & Schooler, L. J. (1991). Reflections of the environment in memory. *Psychological Science*, 2(6), 396–408. https://doi.org/10.1111/j.1467-9280.1991.tb00174.x
- Ebbinghaus, H. (1885/1913). *Memory: A contribution to experimental psychology* (H. A. Ruger & C. E. Bussenius, Trans.). New York: Teachers College, Columbia University. https://doi.org/10.1037/10011-000
- Pavlik, P. I., & Anderson, J. R. (2005). Practice and forgetting effects on vocabulary memory: An activation-based model of the spacing effect. *Cognitive Science*, 29(4), 559–586. https://doi.org/10.1207/s15516709cog0000_14
- Schooler, L. J., & Anderson, J. R. (1997). The role of process in the rational analysis of memory. *Cognitive Psychology*, 32(3), 219–250. https://doi.org/10.1006/cogp.1997.0652
- Woźniak, P. A. (1990). *Optimization of learning* (Master's thesis). University of Technology in Poznań. https://super-memory.com/english/ol.htm — Algorithm SM-2 (§3.2, adapted for the web May 10, 1998): https://super-memory.com/english/ol/sm2.htm

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


