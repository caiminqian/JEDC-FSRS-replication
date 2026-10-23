#!/usr/bin/env python3
"""ECOS Control Env - backwards-compatible re-export.

The single source of truth for ``ECOSControlEnv`` is
``ecos/control/ecos_env.py`` (the Gymnasium-compatible, canonical version).

This module is kept only so that legacy callers doing
``from ecos.control.ecos_env_fixed import ECOSControlEnv`` keep working.
It no longer contains a forked copy of the class.
"""

from ecos.control.ecos_env import ECOSControlEnv

__all__ = ["ECOSControlEnv"]


if __name__ == "__main__":
    import numpy as np

    print("=== ECOSControlEnv (via ecos_env_fixed) Quick Test ===")
    env = ECOSControlEnv(n_agents=30, max_ticks=200)
    obs, _ = env.reset(42)
    print(f"Init obs: {obs}")

    total_r = 0
    interventions = 0
    for t in range(200):
        action = np.array([0.6 if obs[0] < 0.3 else 0.0], dtype=np.float32)
        obs, r, term, trunc, info = env.step(action)
        total_r += r
        if info['intervened']:
            interventions += 1
        if term or trunc:
            break

    print(f"\nEpisode: {t+1} steps, reward={total_r:.1f}, interventions={interventions}")
    print(f"Final state: avg_R={obs[0]:.3f}, std={obs[1]:.3f}")
    print("\n[OK] Environment ready for RL training")
