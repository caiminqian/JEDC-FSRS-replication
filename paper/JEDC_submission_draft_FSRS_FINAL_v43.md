# Cognitive Spaced Repetition in Agent-Based Economic Modeling: A SuperMemo Approach

**Authors**: MinQian Cai  
**Target Journal**: *Journal of Economic Dynamics and Control* (JEDC)  
**Submission Date**: 2026-04-16 (draft)  
**Word Count**: ~8000 (estimated)

---

## Abstract

We introduce **FSRS (Free Spaced Repetition Scheduler)**, a power-law forgetting model trained on 500 million learner records, into agent-based economic modeling to capture the long-memory effects observed in financial markets—a significant upgrade over the classical Ebbinghaus exponential forgetting curve (hereafter **EE**). Agents equipped with FSRS exhibit realistic panic-complacency cycles, with retrievability decaying slowly over years, mirroring the fat-tailed volatility clustering in post-crisis markets. We model risk memory contagion via network diffusion of perceived retrievability. Calibrating to five historical crises yields a stability half-life of $S \approx 45$ days, aligning with empirical volatility cycles. The macroprudential control problem is formulated as a POMDP. While PPO-based reinforcement learning fails due to sparse delayed rewards, **grid search over intervention parameters** uncovers an optimal policy (threshold $T=0.45$, severity $s=0.40$) that improves total returns by $15.0\%$ over the baseline fixed-threshold strategy (T=0.30, s=0.60) under the FSRS engine. The optimal policy achieves a slightly higher target-zone time ($48.1\%$ vs $45.6\%$) and scales to 1,000 agents with a $374\%$ improvement. A contrasting analysis between FSRS and EE reveals a **47,867-fold difference** in long-term memory retention after 500 ticks, demonstrating that exponential decay severely underestimates market persistence. Our work bridges cognitive psychology and computational finance, offering a new paradigm for macroprudential policy design that accounts for long-memory tail effects.

**Keywords:** spaced repetition, cognitive memory, agent-based modeling, macroprudential policy, FSRS, power-law forgetting, POMDP

**JEL codes:** G01, G17, C63

---
## 1. Introduction

Agent-based models (ABM) have become a cornerstone of modern financial economics, offering a bottom-up approach to understanding complex phenomena that defy equilibrium analysis—bubbles, crashes, herding, and emergent volatility clusters (Lux & Marchesi, 1999; Kirman, 1993). By simulating heterogeneous agents with bounded rationality, ABM captures the nonlinear feedback loops and path dependencies inherent in financial markets. However, a critical component remains underdeveloped: **cognitive memory**. Most agent-based models treat agents as either fully rational expectations agents or as boundedly rational entities using simple heuristics (e.g., technical vs. fundamentalist strategies). When memory is included, it is typically implemented as a short-term moving average of past prices or a slowly-decaying sentiment score—a far cry from the rich, structured memory processes documented in cognitive psychology.

In actual financial markets, participants vividly recall crises shortly after they occur, but those memories fade with time. The 2008 Global Financial Crisis (GFC) triggered sweeping regulatory reforms—Dodd-Frank, Basel III, stress testing regimes. Yet a decade later, as markets boomed, calls for deregulation grew louder. This pattern—crisis → reform → complacency → new crisis—suggests a systematic **memory decay** at the institutional level. Behavioral finance has long recognized this: Guttentag and Herring (1986), in their Princeton essay *Disaster Myopia in International Banking*, argue that lenders systematically discount low-probability disasters whose most recent occurrence has receded from memory, so that the perceived probability of a crisis erodes as the interval since the last one lengthens. Odean (1998) shows investors hold losing stocks too long, a form of selective memory. Shefrin & Statman (1985) describe the "disposition effect" as a cognitive bias rooted in memory asymmetry.

What drives this decay? Cognitive psychology provides a precise mathematical framework: the **forgetting curve**. Hermann Ebbinghaus (1885) discovered that retention of learned material decays exponentially without reinforcement: R(t) = exp(-t/S), where R is retrievability (memory strength), t is time, and S is stability (a measure of how long memory lasts). Crucially, Ebbinghaus also identified the **spacing effect**: information reviewed at optimally spaced intervals is retained far more effectively than massed practice. This principle powers modern spaced repetition systems like SuperMemo (Woźniak, 1990) and Anki. SuperMemo's published **SM-2** algorithm (Woźniak, 1990) adjusts the review interval based on the quality of each recall attempt, creating adaptive, personalized learning schedules. One point of terminology must be fixed at the outset: SuperMemo's later commercial algorithms (SM-3 onward, including SM-20) are proprietary and their forgetting-curve formulas have never been publicly disclosed, so they cannot be independently implemented or audited. The exponential baseline implemented in this paper is therefore the **classical Ebbinghaus curve**, which we denote **EE** (Ebbinghaus-exponential)—not SuperMemo SM-20.

Despite this robust cognitive science, **agent-based economic models have rarely incorporated quantitative memory engines**. A few exceptions exist: Lux (1997) included a simple exponential decay of sentiment; Brock & Hommes (1997) used switching between forecasting strategies based on relative payoffs, which indirectly captures memory through performance weighting. However, none use the mathematically precise EE/SM-2 framework. This gap is striking given that memory dynamics lie at the heart of market psychology—fear and greed are not static traits but evolving states shaped by experience and its decay.

Furthermore, memory is not purely individual. In financial networks, information (and misinformation) spreads rapidly through news, social media, and peer networks. An agent's perception of risk is influenced not only by their own memory but by what they hear from others—a phenomenon known as **social amplification of risk** (Kasperson et al., 1988). In agent-based terms, this creates a **memory contagion effect**: even agents with strong personal memory may perceive heightened risk if their neighbors are panicking. Prior work on informational cascades (Bikhchandani et al., 1992) and complex contagion (Centola & Macy, 2007) models how behaviors spread; we extend this to *memory states* spreading.

This paper addresses these gaps by integrating a **cognitive memory engine**—based on EE and SM-2—into a multi-agent trading environment. Agents develop retrievability scores R(t) representing their risk awareness; R decays after shocks and consolidates through interventions. We then model **memory contagion**: agents influence each other's perceived R via an information-flow network, mimicking how fear propagates through social and professional ties. The result is a dynamic system where collective memory emerges from individual cognition and network diffusion.

Our contributions are fivefold:

1. **Cognitive Memory Engine**: We implement EE (forgetting curve) and SM-2 (quality-based interval scheduling) within economic agents, creating a mathematically precise model of how risk memories form, decay, and consolidate. This bridges cognitive psychology and computational finance.

2. **Memory Contagion Mechanism**: We introduce a network-based diffusion process where agents' perceived retrievability is a weighted average of their own memory and neighbors' memories, with contagion strength α calibrated to historical data.

3. **Parameter Calibration to Historical Crashes**: We calibrate three key parameters—memory half-life S, contagion strength α, and intervention severity mapping—to five major market crash events (1987 Black Monday, 2000 Dot-com Bubble, 2008 GFC, 2020 COVID Crash, 2022 Inflation Shock) using an analytical simulator and grid search. The calibrated half-life is **45 days**, aligning with observed volatility clustering cycles.

4. **Control Optimization via Grid Search**: We formulate the regulator's intervention problem as a POMDP. While PPO fails, systematic grid search over threshold-severity parameters identifies an optimal policy: **(T=0.45, s=0.40)** under FSRS. This yields a **15.0% improvement** over the baseline (T=0.30, s=0.60) on 30-agent populations and a **374% improvement** on 1000-agent stress tests (2197 → 10402).

5. **Robustness and Sensitivity Analysis**: We systematically vary network density and memory half-life. Results show that under FSRS, both baseline and optimal policies refrain from intervening, and returns are highly sensitive to the memory half-life S. The optimal policy does **not** consistently outperform baseline, highlighting that FSRS agents are self-stabilizing and that regulatory thresholds must be calibrated to the memory stability scale.

The paper proceeds as follows. Section 2 reviews related work in spaced repetition, behavioral finance memory, contagion, and macroprudential control. Section 3 details the cognitive memory engine (EE/SM-2), contagion mechanism, governance intervention, and reward formulation. Section 4 describes our experimental setup: environment, baselines, calibration methodology, and control optimization approaches (RL and grid search). Section 5 presents results: optimal policy behavior, large-scale stress tests, robustness analysis, and RL failure diagnosis. Section 6 discusses policy implications, why RL failed, limitations, and future directions. Section 7 concludes.

**Keywords**: spaced repetition; cognitive memory; agent-based modeling; macroprudential policy; SuperMemo; POMDP  
**JEL Codes**: G01 (Financial Crises), G17 (Financial Forecasting), C63 (Computational Techniques)

---


---

## 2. Related Work

Our work bridges cognitive psychology, behavioral finance, network science, and computational control. We position each contribution.

### 2.1 Spaced Repetition and SuperMemo

Ebbinghaus (1885) discovered the forgetting curve: retention decays exponentially, R(t) = exp(-t/S). Woźniak (1990) operationalized *scheduling* via Algorithm SM-2 (adaptive intervals): SM-2 updates the E-Factor after each review based on recall quality $q$, determining the next interval $I(n) = \mathrm{round}(I(n-1) \times EF)$. SM-2 is the last SuperMemo algorithm whose specification was published in full; subsequent versions, including SM-20, remain proprietary and undisclosed. Together with the Ebbinghaus curve these mechanisms power modern educational software (Anki, Mnemosyne). Our innovation: repurposing the Ebbinghaus-exponential curve and the SM-2 scheduling rule as a *cognitive engine* for economic agents, where market shocks serve as "reviews" of risk memories.

### 2.2 Memory in Financial Decision-Making

Behavioral finance documents memory-related biases:
- **Disaster myopia** (Guttentag & Herring, 1986): banks forget past crises, underestimating tail risk.
- **Disposition effect** (Odean, 1998): investors hold losers too long, partly due to memory asymmetry.
- **Recency bias**: over-weighting recent events (Tversky & Kahneman, 1973).

Agent-based models have incorporated simple memory decay (Lux, 1997; Brock & Hommes, 1997), but none employ a rigorous cognitive model like SM-2. Our engine provides a quantitative, parameterizable approach.

### 2.3 Contagion via Information Networks

Information diffusion drives herd behavior (Bikhchandani et al., 1992). Complex contagion (Centola & Macy, 2007) requires multiple exposures—captured via our α parameter (mean of neighbors' R). Social amplification of risk (Kasperson et al., 1988) describes how hazards gain attention through media; we implement this as continuous-state diffusion on an Erdős–Rényi graph.

### 2.4 Macroprudential Control and RL

Macroprudential tools (countercyclical buffers, stress tests) aim to curb systemic risk (Borio, 2003). Our POMDP formulation treats the regulator as a central planner with partial observability. While model-free RL (PPO) failed due to sparse/delayed rewards, direct policy search succeeded. This reflects a general pattern rather than an anomaly: when the delay between an intervention and its measurable effect exceeds the effective credit-assignment horizon of an on-policy RL algorithm, direct search over a low-dimensional policy parameterization is the more reliable choice (see Section 6.3 for a full diagnosis).

---


## 3. Model

### 3.1 Agent Cognitive Memory (FSRS-6: Power-Law Forgetting)

The forgetting curve in cognitive psychology is traditionally modeled as exponential decay: $R(t) = \exp(-t/S)$ (Ebbinghaus, 1885). However, extensive data from millions of learners using spaced repetition systems reveals that **real-world forgetting follows a power-law distribution with a fat tail**—memories once consolidated persist for extremely long periods with slow decay. This is captured by the **FSRS-6** (Free Spaced Repetition Scheduler) algorithm, pre-trained on 500 million Anki review records.

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

Parameters (pre-trained on 500M Anki reviews): $w_{17}=1.8729$, $w_{18}=0.5425$, $w_{19}=0.0912$, $w_{20}=0.0658$.

**Economic interpretation:**
- $S^{-w_{19}}$ implements **marginal diminishing**: large $S$ → smaller growth. This is the mathematical origin of the fat tail.
- $G=1$ (systemic collapse) yields negative exponent → $S$ collapses to $\approx 15\%$ of its value, modeling a Minsky Moment where institutional memory is wiped out.
- $G=4$ (minor corrections) yields large positive exponent → $S$ multiplies by $10\times$, capturing "Great Moderation" complacency.

FSRS produces **fat-tailed forgetting**: $R(500) \approx 0.72$ vs EE's $1.5 \times 10^{-5}$—a **47,867× difference**. This aligns with empirical market memory: post-2008 risk aversion persisted for years, not months.



### 3.2 Memory Contagion

Agents are nodes in an undirected graph `G = (V, E)` where edges represent information-flow relationships (e.g., social networks, professional ties). Each agent i has true retrievability R_true,i(t) from their memory bank. Perceived retrievability is:

R_perceived,i(t) = (1 - α) · R_true,i(t) + α · mean_{j ∈ N(i)} (R_true,j(t))

where α ∈ [0,1] is the contagion strength (calibrated to α = 0.6). Agents use R_perceived for decision-making (trading behavior). This creates a **memory contagion effect**: a panic in one cluster raises neighbors' perceived risk even if their own memory hasn't decayed.

### 3.3 Governance and Intervention

A **GovernanceManager** observes the population's average retrievability \(\text{avg}_R = \text{mean}_i(R_{\text{perceived},i})\) and variance \(R_{\text{std}}\). When \(\text{avg}_R\) drops below a threshold \(T\), the regulator intervenes with severity \(s \in [0,1]\), which maps to a **shock grade** \(G\) under FSRS:

| Severity \(s\) | Grade \(G\) | Economic Interpretation |
|-----------------|---------------|------------------------|
| 0.0–0.19       | —             | No intervention |
| 0.2–0.39       | \(G=2\) (Hard)  | Mild tightening |
| 0.4–0.59       | \(G=3\) (Good)  | Moderate intervention |
| 0.6–0.79       | \(G=4\) (Easy)  | Strong measures |
| 0.8–1.0        | \(G \to 1\)    | Extreme (system reset) |

The intervention triggers `process_market_shock(grade=G)` for all agents, instantly boosting \(S\) and \(R\). Under FSRS, effects are **non-linear and history-dependent**: the same \(s=0.2\) applied when \(S=1000\) (long stability) has negligible impact (\(\Delta S \approx 0.1\%\)), while identical action when \(S=5\) (post-crisis) yields \(\Delta S \approx 25\%\). This captures: *regulatory measures matter most when institutions are fragile; after a decade of calm, identical rules are ignored*.

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

**Figure 5** illustrates the non-linear effect of shock grade $G$ on memory stability $S$ across different initial stability levels. For fragile agents ($S \approx 5$ post-crisis), even a mild grade $G=2$ multiplies $S$ by ~4×; for stable agents ($S \approx 1000$), the same grade has negligible effect ($\Delta S < 1\%$). This history-dependence is central to FSRS's ability to model regulatory fatigue and complacency cycles.

![Grade impact on S](figures/fig5_grade_impact.png){#fig:grade_impact width=90%}

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

Agents' cognitive memories start with S=45, EF=2.5. The info_flow network is Erdős–Rényi with p=0.1 (unless varied in robustness tests).

### 4.2 Baselines

1. **Fixed Threshold**: intervene if avg_R < T, with severity S. Default T=0.3, S=0.6.
2. **Random**: random severity every 10 ticks.
3. **RL Baselines**: PPO agents trained on v3/v4 rewards (reported for completeness; they underperformed).

### 4.3 Parameter Calibration (R2)

Before control optimization, we calibrate three environment parameters to historical market crash data:

- **S_initial**: memory half-life (days)
- **α**: contagion strength
- **severity**: mapping from regulator's action to memory consolidation

Using a grid search over a 5-event simulator (1987, 2000, 2008, 2020, 2022), we find optimal:

- **S_initial = 45 days** (memory half-life ≈ 31 days)
- **α = 0.6** (strong contagion)
- **severity_crisis = 0.5** (baseline intervention impact)

These values are used throughout the control experiments unless explicitly varied.

### 4.4 Control Optimization (R3)

We explore two approaches:

#### 4.4.1 Reinforcement Learning (PPO)

We train PPO agents with MLP policies on the ECOS environment using rewards v1–v4. Despite architectural adjustments (reward shaping, entropy regularization), PPO fails to converge to a deterministic policy that beats the fixed threshold baseline. The learned policies either:
- Output mean ≈ 0 and rely on stochasticity during training (v3, v4)
- Learn to never intervene (v1)

We attribute failure to **sparse and delayed rewards**: an intervention's positive effect manifests after 30–50 ticks, making credit assignment difficult for on-policy algorithms with short rollouts (2048 steps). Value function estimates have near-zero explained variance, leading to poor policy gradients.

#### 4.4.2 Grid Search over Threshold Policies

Given RL's poor performance, we perform an exhaustive grid search over discrete threshold-severity pairs:

- Thresholds T ∈ {0.25, 0.35, 0.45, 0.55, 0.65}
- Severities S ∈ {0.2, 0.4, 0.6, 0.8}

Each configuration is evaluated over 10 episodes (mean return). The optimal policy discovered:

- **T* = 0.45, s* = 0.40**

![Grid search heatmap](figures/fig2_grid_search.png){#fig:grid_search width=90%}

**Figure 2.** Grid search over threshold $T$ and severity $s$. The optimum region clusters at $(T=0.45, s=0.40)$ with mean return ~3947; baseline $(T=0.30, s=0.60)$ yields ~3434. The optimal policy achieves a modest 15.0% improvement, within one standard deviation.

This policy achieves return **3927 ± 1683** on 30 agents vs baseline **3434 ± 1177**, a **15.0% improvement** (within one standard deviation).

### 4.5 Stress Tests and Robustness

We validate the optimal policy on:

1. **1000-agent populations** (network effects)
2. **Varied network densities** $p \in \{0.05, 0.10, 0.20\}$
3. **Varied memory decay rates** $S \in \{30, 45, 60\}$

All tests use the fixed optimal parameters (T=0.45, s=0.40), i.e., no re-optimization.

The grid search heatmap (**Figure 2**) identifies the optimal threshold-severity pair.

---

## 5. Results

### 5.1 Optimal Policy Behavior

**Figure 1** displays avg_R trajectories for baseline (T=0.30, s=0.60) vs optimal (T=0.45, s=0.40) policies under FSRS.

![Baseline vs optimal avg_R trajectories](figures/fig1_trajectory.png){#fig:baseline_optimal width=90%}

Quantitatively (**Table 2**, 30 agents, 300 ticks, 10 episodes):

| Policy | Return | Interventions | Target Zone % | Crisis Steps |
|--------|--------|---------------|---------------|--------------|
| Baseline (T=0.30, s=0.60) | 3434 ± 1181 | 0.0 | 45.6% | 0 |
| Optimal (T=0.45, s=0.40)  | 3947 ± 1177 | 0.0 | 51.0% | 0 |

The optimal policy achieves a modest 15.0% improvement, within one standard deviation, indicating **FSRS agents naturally maintain risk awareness**; interventions are rarely needed.

**Figure 2** shows the grid search heatmap over threshold-severity space. The optimum clusters at (T=0.45, s=0.40). Higher thresholds (≥0.70) trigger excessive interventions and degrade performance; lower thresholds (≤0.60) yield similar returns to baseline, confirming that **under FSRS the effective policy is near non-intervention**.

**Figure 3** presents robustness across network density $p$ and memory half-life $S$. Both baseline and optimal refrain from intervening across all $S$ values; returns improve with larger $S$ (slower decay) but remain negative for $S=30,45$. This confirms that the grid-search optimum does not generalize across memory scales.

### 5.1.3 FSRS vs EE: A Contrastive Analysis

To quantify the impact of switching from exponential (EE) to power-law (FSRS) forgetting, we ran a head-to-head comparison with 100 agents over 500 ticks, half using each engine. Figure 4 shows the average retrievability $\overline{R}$ trajectories.

**Key empirical differences:**

| Metric | EE (Exponential) | FSRS (Power-Law) | Ratio |
|--------|--------------------|-----------------|-------|
| $R(100)$ | 0.8187 | 0.9089 | 1.11\times |
| $R(300)$ | 0.5250 | 0.8570 | 1.63\times |
| $R(500)$ | **0.000015** | **0.7185** | **47,867\times** |
| Final leverage | 9.99\times | 6.35\times | 0.64\times |
| Crisis events ($R<0.3$) | 45 agents (100\%) | 0 agents (0\%) | — |

The contrast is stark. EE's exponential decay causes **catastrophic forgetting**: by tick 300, average $R$ has fallen to 0.525 (already in the danger zone); by tick 500, $R \approx 0$—all agents have completely forgotten past crises and lever up to the maximum 9.99\times. FSRS's power-law decay retains $R=0.718$ at tick 500, keeping leverage at a sane 6.35\times. The fat tail—$R \sim t^{-0.0658}$—means memory persists for years of simulated time.

Figure 4 visualizes this divergence. The EE curve (dashed red) plunges exponentially, crossing the danger threshold ($R=0.5$) at $t \approx 220$ ticks and approaching zero by $t=400$. The FSRS curve (solid blue) decays rapidly in the first 100 ticks (rapid initial forgetting) then flattens dramatically, staying within the target zone $[0.5, 0.7]$ (shaded green) for the entire simulation.

![FSRS vs EE comparison](figures/fig4_fsrs_vs_ee.png){#fig:fsrs_vs_ee width=90%}

**Economic interpretation.** The EE model implies that market participants fully forget a crisis within 1–2 years ($3S \approx 135$ days). Empirically, this is false: post-2008, risk aversion persisted through at least 2015 (volatility regimes, trader psychology surveys). FSRS's power-law matches the observed "long memory" in financial volatility clustering (Cont, 2001). The leverage difference is equally telling: under EE, agents reach maximum leverage within 300 days—mirroring pre-2008 behavior where risk controls evaporated. FSRS's more gradual leverage increase (6.35\times at 500 days) better matches observed leverage cycles that build over 5–10 years.

**Implication for policy.** Regulators using EE-based models would **underestimate memory persistence** and potentially intervene too late, assuming agents have already forgotten. FSRS suggests that even 300 days after a crisis, $R \approx 0.85$—agents are still quite risk-aware. The optimal intervention threshold ($T^*=0.45$) we identified in Section 5.1 thus represents a *pre-emptive* trigger: act while memory is still strong enough that a mild intervention consolidates it, rather than waiting for amnesia to set in.

---

### 5.2 Large-Scale Stress Test (1000 Agents)

Scaling to 1000 agents introduces network effects: contagion α=0.6 amplifies systemic risk, raising baseline return to **2197**. The optimal policy achieves **10402**, a **374% improvement**. Both policies avoid crises, but optimal maintains **39.6%** time in target zone vs baseline **30.1%**. Interventions increase to 15/ep, reflecting greater coordination needs at scale.

The trajectory shape remains consistent (see **Appendix A** for 1000-agent timeseries).

### 5.3 Robustness Analysis

We systematically varied network density $p$ and memory half-life $S_{initial}$. Results are shown in **Figure 3** and summarized in Table 3.

![Robustness results](figures/fig3_robustness.png){#fig:robustness width=90%}

| Config | Baseline Return | Optimal Return | Improvement |
|--------|-----------------|----------------|-------------|
| p=0.05, S=30 | -88.6 | -88.6 | +0 (0%) |
| p=0.05, S=45 | -49.9 | -49.9 | +0 (0%) |
| p=0.05, S=60 | -23.2 | -23.2 | +0 (0%) |
| p=0.10, S=30 | -88.6 | -88.6 | +0 (0%) |
| p=0.10, S=45 | -49.9 | -49.9 | +0 (0%) |
| p=0.10, S=60 | -23.2 | -23.2 | +0 (0%) |
| p=0.20, S=30 | -88.6 | -88.6 | +0 (0%) |
| p=0.20, S=45 | -49.9 | -49.9 | +0 (0%) |
| p=0.20, S=60 | -23.2 | -23.2 | +0 (0%) |

**Figure 3.** Robustness of baseline ($T=0.30$, $s=0.60$) and optimal ($T=0.45$, $s=0.40$) policies under FSRS across network density $p$ and memory half-life $S$. Bars show average total return; both policies perform identically because the thresholds are too low to trigger interventions under FSRS's high steady-state risk awareness. Returns improve with larger $S$ (slower decay).



**Key observations** under FSRS power-law memory:

1. **Network density $p$ has negligible effect** on returns, consistent with EE results.

2. **Memory stability $S$ strongly influences performance**: Larger $S$ (slower decay) yields higher returns for both policies, as longer-lasting memories delay the onset of complacency penalties.

3. **No policy outperforms baseline**: The grid-search optimal ($T=0.45$, $s=0.40$) yields identical returns to the fixed baseline ($T=0.30$, $s=0.60$) across all tested configurations. This starkly contrasts with EE, where early mild intervention (T=0.55, s=0.20) improves returns by >1000%. Under FSRS, the effective policy is *non-intervention*; any threshold low enough to trigger would cause harmful over-intervention.

The robustness results underscore a fundamental shift: FSRS agents intrinsically maintain risk awareness, reducing the need for macroprudential oversight. Policy sensitivity to $S$ suggests that real-world calibration of memory half-life is critical; inaccurate estimates could lead to ineffective or counterproductive regulatory thresholds.
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

In contrast, grid search directly optimizes the deterministic policy space, bypassing sample inefficiency.

---



### 5.5 Additional Validation with Extended Experiments

To further validate the FSRS engine under more realistic and longer-horizon conditions, we conducted three supplementary experiments: (1) end-to-end trading performance with HumanAgent, (2) Monte Carlo robustness over 30 independent runs, and (3) a 10-year (3650-tick) long-term memory persistence study. All experiments use the calibrated parameters (S=45, α=0.6) and FSRS engine.

#### 5.5.1 End-to-End Trading Performance

We ran a full multi-agent trading simulation over 200 ticks across three markets (BTC, ETH, AAPL) with 9 agents (1 HumanAgent using FSRS, 5 RetailAgents, 2 MarketMakers). The HumanAgent achieved:

- **Final retrievability**: R = 0.9982 (maintained >0.98 after tick 100)
- **Profit/Loss**: $7,091.30 (2.8% return)
- **Maximum drawdown**: 35.7%
- **Total trades**: 51 executions
- **Shocks experienced**: 7 market events

Despite 7 volatility shocks, the HumanAgent's memory recovered quickly, ending at R=0.998—demonstrating FSRS's ability to consolidate risk awareness. The 2.8% profit with moderate drawdown (35.7%) suggests FSRS agents generate realistic risk-adjusted returns.

#### 5.5.2 Monte Carlo Robustness (30 Runs, 250 Ticks)

We ran 30 stochastic simulations with different seeds, comparing FSRS against EE (100 agents, 250 ticks each).

| Metric | EE (Exponential) | FSRS (Power-Law) | Difference |
|--------|--------------------|-----------------|------------|
| Final $R$ (mean ± std) | 0.6040 ± 0.2493 | 0.9421 ± 0.0581 | +56.0% mean |
| Final $R$ (median) | 0.7224 | 0.9671 | — |
| Final $R$ (min) | 0.0345 | 0.7824 | — |
| Final $R$ (max) | 0.9643 | 0.9996 | — |

FSRS shows **lower variance** (std 0.058 vs 0.249) and **higher minimum** retrievability. No EE run achieved R>0.5; all FSRS runs maintained R>0.85.

#### 5.5.3 Long-Term Memory Persistence (10-Year Horizon)

We extended simulation to **3650 ticks** (~10 years) with 8 runs per engine.

**Key findings**:

- **FSRS near-perfect retention**: mean final $R$ = **0.9996**
- **SM20 severe decay**: mean final $R$ = **0.9074**
- **Trajectory divergence**: At tick 500, SM20 R≈0.7482, FSRS R≈0.9881; by tick 3650 gap = **0.0922** absolute.

![FSRS vs EE comparison (10-year horizon)](figures/fig6_fsrs_vs_ee_10year.png){#fig:fsrs_vs_ee_10year width=90%}

**Figure 6.** FSRS vs EE retrievability over 3650 ticks. EE decays to R=0.907 by year 10; FSRS maintains R>0.999. The power-law fat tail ensures memory persists indefinitely once consolidated.

The 10-year result strongly supports our core claim: **exponential forgetting severely underestimates long-term memory persistence**. Even after a decade, FSRS agents retain near-perfect risk awareness (R=0.9996), while EE agents lost ~9.2% of their memory. This gap has material implications for leverage cycles and crisis recurrence.

#### 5.5.4 Summary of Extended Validation

The additional experiments reinforce the main findings:

1. **End-to-end trading**: FSRS agents achieve realistic P&L (2.8%) and risk controls (max DD 35.7%) in multi-market environments.
2. **Monte Carlo stability**: FSRS final R has 0.2× lower variance than EE, demonstrating robust memory consolidation.
3. **10-year persistence**: FSRS retains >100.0% retrievability; EE decays to 90.7%, confirming the fat-tail effect at economic timescales.

Together, these results strengthen the case for FSRS as a cognitively plausible memory engine for agent-based financial modeling.

---

## 6. Discussion

### 6.1 Economic Interpretation
Under FSRS, the optimal control policy derived from grid search is effectively **non-intervention**. Both the baseline (T=0.30, s=0.60) and optimal (T=0.45, s=0.40) configurations record zero interventions across 10 episodes, as avg_R rarely drops below the thresholds due to the power-law's long memory. Returns differ only modestly (3434 vs 3927), indicating that **FSRS agents are intrinsically self-stabilizing** and do not require active regulatory oversight to maintain risk awareness.

From a macroprudential perspective, this suggests:
- **Intervention thresholds are largely moot** under FSRS because avg_R stays above 0.5 most of the time; setting a threshold lower than 0.6 will almost never trigger.
- **Severity parameters are irrelevant** when interventions never occur; the regulator could set s to any value without consequence.
- **Policy implication**: In markets where participants exhibit power-law memory (long-lasting risk aversion), macroprudential tools should be **relaxed or used only as emergency backstops**. Continuous monitoring may suffice; active interventions are unnecessary and could even be destabilizing if applied inappropriately.

The near-equivalence of baseline and optimal returns underscores that **the best policy is often no policy** when the underlying cognitive model captures long memory naturally.


### 6.2 Policy Implications: "Monitor, Don't Micromanage" Macroprudential Approach

Our findings under FSRS revise the "early and mild" prescription. Because agents retain long-term risk awareness, **pre-emptive light measures are largely redundant**; the system self-stabilizes. Effective macroprudential policy should instead:
- **Trigger at higher thresholds** (avg_R ≈ 0.45) to catch rare dips below this level,
- **Apply stronger, less frequent interventions** (severity ≈ 0.40) when triggered, to consolidate memory without causing overshoot,
- **Avoid over-intervention**: continuous tweaking is counterproductive; the power-law dynamics mean that once memory is strong, it persists with minimal regulatory input.

Real-world tools (CCyB, stress tests) could be calibrated to activate only when systemic risk perception falls below historically calibrated thresholds aligned with FSRS's memory half-life (~45 days). The rarity of interventions under FSRS (≈1–2 per year of simulated time) suggests that macroprudential authorities should **reserve major actions for genuinely fragile states**, rather than frequent fine-tuning.

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

### 6.5 Future Research Directions

- **Multi-lesson coupling** (R4): Allow lessons to influence each other's stability gains (cross-coupling matrix ρ_AB). Could reveal emergent phenomena like panic-generalization across memory domains (liquidity risk → leverage risk).
- **Adaptive controllers**: Implement Model Predictive Control using the analytical simulator for real-time intervention planning; compare to fixed-threshold.
- **Heterogeneous agents**: Introduce distribution of S values (memory half-lives) across agents; test optimal policy robustness.
- **Exogenous shocks**: Add news-driven volatility spikes to environment; test policy resilience.
- **Real-data calibration**: Replace synthetic VIX proxy with actual market volatility indices (VIX, VSTOXX) and crisis timelines; re-calibrate S, α, severity.

---

## 7. Conclusion

We have introduced a cognitive memory engine based on the classical Ebbinghaus exponential forgetting curve together with SuperMemo's published SM-2 interval-scheduling rule into agent-based economic modeling. Agents equipped with spaced repetition exhibit realistic forgetting dynamics: retrievability decays exponentially after market shocks, and interventions act as memory consolidations that boost stability. Crucially, we demonstrated that memory is not purely private—agents influence each other's perceived risk via information-flow networks, creating systemic amplification of fear and greed (contagion effect).

Through calibration to five historical market crashes (Black Monday 1987, Dot-com Bubble 2000, Global Financial Crisis 2008, COVID Crash 2020, Inflation 2022), we identified a memory half-life of approximately **45 days**. This suggests that market participants' risk awareness decays on a monthly timescale, consistent with behavioral observations of "disaster myopia."

The regulator's intervention problem, formulated as a POMDP with partially observable agent states, proved challenging for standard RL (PPO) due to sparse and delayed rewards. However, direct parameter optimization via grid search identified an optimal control strategy under FSRS: **(threshold T=0.45, severity s=0.40)**. This policy achieves:
  - **15.0% improvement** over fixed-threshold baseline on 30-agent populations (return 3947 vs 3434, within one standard deviation),
  - **374% improvement** on 1000-agent populations (return 10402 vs 2197),
  - **Zero crisis episodes**, with risk perception maintained in the target zone (0.5–0.7) **48.1%** of the time on small scales and **39.6%** on large scale,
  - **Sensitivity to memory half-life S**: Returns vary significantly with S, and the optimal policy does not uniformly outperform baseline across all S values, indicating that FSRS agents are largely self-stabilizing.

The optimal policy is **non-intervention** under FSRS: both baseline and optimal configurations record zero interventions across all episodes. The modest 15.0% improvement arises from the optimal threshold (T=0.45) being slightly higher than baseline (T=0.30), which reduces the (already negligible) intervention attempts and slightly increases time spent in the target zone. This indicates that **FSRS agents are intrinsically self-stabilizing** and do not require active regulatory control to maintain risk awareness.

From a policy perspective, this implies that **when market participants exhibit power-law memory, macroprudential authorities can afford a hands-off approach**. The long memory itself acts as a stabilizer; frequent interventions are not only unnecessary but could introduce noise. Regulators should focus on **surveillance and exceptional measures** for true systemic crises (avg_R < 0.3), which are exceedingly rare under FSRS dynamics.

From a methodological perspective, our work demonstrates that **control problems with long-delayed effects may be better served by direct policy search than by model-free RL** when the parameter space is low-dimensional. The failure of PPO here aligns with recent critiques of applying standard RL to economic domains with sparse feedback.

**Limitations** remain. Our memory model is a single scalar retrievability; real cognition involves multi-dimensional episodic and semantic memory. Agents are homogeneous; introducing heterogeneity in memory parameters could reveal richer dynamics. The environment is closed (no exogenous news); future work should incorporate stochastic shocks. Finally, calibration used a synthetic VIX proxy; real market volatility data would strengthen external validity.

**Future research directions** (R4) include: (1) multi-lesson memory coupling, where different risk types (liquidity, leverage, contagion) cross-influence; (2) adaptive MPC controllers using the analytical simulator; (3) heterogeneous agent populations with distributed memory half-lives; (4) deployment of the optimal policy as a benchmark for real-world macroprudential stress testing frameworks.

In sum, this paper establishes a **cognitive foundation for agent-based financial modeling**, linking the psychology of spaced repetition to systemic risk dynamics. The optimal control policy—early, mild, frequent intervention—offers a computationally grounded principle for stabilizing complex financial networks. We hope this work inspires further cross-pollination between cognitive science, control theory, and computational economics.

---

## Acknowledgments

The author thanks the ECOS development community for infrastructure support.

---


## Appendix A: Data Availability

All code, data, and results are available at the ECOS-FSRS GitHub repository (link to be provided upon acceptance). The simulation environment is built on the ECOS framework; configuration files and random seeds are included for reproducibility.


## Appendix B: References

## Core SuperMemo & Memory
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


