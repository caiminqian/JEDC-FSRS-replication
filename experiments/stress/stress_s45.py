#!/usr/bin/env python3
"""S=45 rerun of the 1000-agent stress test (v49 audit).

Design mirrors experiments/stress/stress_control_optimal.py except:
- After every env.reset(seed), every FSRS lesson of every agent is set
  to S = 45.0 and observations are recomputed via env._compute_obs(),
  exactly the override used by experiments/robustness/ps_sweep.py.
- Episodes use seeds 1, 2, 3 for BOTH policies (paired). The original
  used seeds 0, 1, 2, where seed 0 is falsy in ECOSControlEnv.reset and
  draws a random seed, so its episode 0 was unpaired. Seeds 1-3 avoid
  that flaw; the design change is disclosed in the paper.
- Per-episode returns, interventions and zone fractions are recorded
  (the original only stored means).

Policies: baseline threshold 0.30 / severity 0.60, comparison
threshold 0.55 / severity 0.20 (the pair actually run in the original).
"""
import sys
import os
import time
import json
import numpy as np

from ecos.control.ecos_env import ECOSControlEnv


def set_s45(env):
    for agent in env.agents:
        bank = getattr(agent, "memory_fsrs", None)
        if bank is None:
            continue
        for mem in bank.memories.values():
            mem.S = 45.0
    env._compute_obs()


def run_policy(env, threshold, severity, seeds, max_ticks=1000):
    returns = []
    interventions = []
    crisis_steps = []
    in_zone = []
    for seed in seeds:
        obs, _ = env.reset(seed=seed)
        set_s45(env)
        obs = env._compute_obs()
        total_r = steps = n_int = crisis = zone_steps = 0
        for t in range(max_ticks):
            action = np.array([severity if obs[0] < threshold else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += r
            steps += 1
            if action[0] > 0.01:
                n_int += 1
            if obs[0] < 0.25:
                crisis += 1
            if 0.5 <= obs[0] <= 0.7:
                zone_steps += 1
            if term or trunc:
                break
        returns.append(float(total_r))
        interventions.append(int(n_int))
        crisis_steps.append(int(crisis))
        in_zone.append(float(zone_steps / steps))
    return {
        "avg_return": float(np.mean(returns)),
        "std_return": float(np.std(returns)),
        "avg_interventions": float(np.mean(interventions)),
        "avg_crisis": float(np.mean(crisis_steps)),
        "avg_zone_pct": float(np.mean(in_zone) * 100),
        "min_return": float(np.min(returns)),
        "max_return": float(np.max(returns)),
        "per_episode_returns": returns,
        "per_episode_interventions": interventions,
        "per_episode_zone_pct": [float(z * 100) for z in in_zone],
        "seeds": list(seeds),
    }


def main():
    n_agents = 1000
    max_ticks = 1000
    seeds = [1, 2, 3]
    print("Config: %d agents, %d ticks, seeds %s, S=45 override" % (n_agents, max_ticks, seeds))
    env = ECOSControlEnv(n_agents=n_agents, max_ticks=max_ticks)
    out = {"config": {"n_agents": n_agents, "max_ticks": max_ticks, "seeds": seeds, "S_override": 45.0,
                      "policies": {"baseline": [0.30, 0.60], "comparison": [0.55, 0.20]}}}
    for name, (thr, sev) in [("baseline", (0.30, 0.60)), ("comparison", (0.55, 0.20))]:
        start = time.time()
        res = run_policy(env, thr, sev, seeds, max_ticks=max_ticks)
        res["runtime_s"] = float(time.time() - start)
        out[name] = res
        print("[%s] return %.2f +- %.2f, interventions %.1f, zone %.1f%%, %.0fs"
              % (name, res["avg_return"], res["std_return"], res["avg_interventions"],
                 res["avg_zone_pct"], res["runtime_s"]))
    out["improvement"] = out["comparison"]["avg_return"] - out["baseline"]["avg_return"]
    with open("stress_1000a_s45.json", "w") as f:
        json.dump(out, f, indent=2)
    print("[Saved] stress_1000a_s45.json")


if __name__ == "__main__":
    main()
