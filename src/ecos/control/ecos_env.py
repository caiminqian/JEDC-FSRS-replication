#!/usr/bin/env python3
"""Simplified ECOS Control Env - Gymnasium compatible"""

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.governance.governance_manager import GovernanceManager
from datetime import datetime, timezone, timedelta
import numpy as np
import gymnasium as gym
from gymnasium import spaces

class ECOSControlEnv(gym.Env):
    """ECOS 宏观审慎控制环境 (Gymnasium)"""

    metadata = {'render_modes': []}

    def __init__(self, n_agents=50, max_ticks=500, agent_config=None):
        super().__init__()
        self.n_agents = n_agents
        self.max_ticks = max_ticks
        self.agent_config = agent_config or {}
        self.agents = []
        self.world = None
        self.gov = None
        self.current_tick = 0
        self.start_time = None
        self.last_intervention_tick = -1000
        self.last_severity = 0.0

        # Spaces
        self.observation_space = spaces.Box(0, 1, shape=(6,), dtype=np.float32)
        self.action_space = spaces.Box(0, 1, shape=(1,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Init agents
        self.agents = [HumanAgent(f"A_{i:03d}", self.agent_config.copy()) for i in range(self.n_agents)]
        self.world = WorldStateGraph()
        for a in self.agents:
            self.world.add_node(a.agent_id, 'agent', {'balance': a.balance})

        self.gov = GovernanceManager(self.world, self.agents)
        self.gov.contagion_alpha = 0.6
        self.gov.memory_monitoring_enabled = False  # Disable auto-intervention

        # Build info_flow network (p=0.1)
        np.random.seed(seed if seed else np.random.randint(0, 10000))
        edges = 0
        for i in range(self.n_agents):
            for j in range(i+1, self.n_agents):
                if np.random.rand() < 0.1:
                    self.world.add_edge(self.agents[i].agent_id, self.agents[j].agent_id, 'info_flow', weight=1.0)
                    self.world.add_edge(self.agents[j].agent_id, self.agents[i].agent_id, 'info_flow', weight=1.0)
                    edges += 1
        print(f"[Reset] {self.n_agents} agents, {edges} undirected edges")

        self.current_tick = 0
        self.start_time = datetime.now(timezone.utc)
        self.last_intervention_tick = -1000
        self.last_severity = 0.0

        obs = self._compute_obs()
        return obs, {}

    def _compute_obs(self):
        """Compute state from current world"""
        current_time = self.start_time + timedelta(days=self.current_tick)

        # True R from agent cognitive state (supports both EE and FSRS)
        true_R = {}
        for a in self.agents:
            state = a.get_cognitive_state()
            # Extract avg_R depending on engine
            if 'risk_awareness' in state:
                # FSRS engine
                avg_R = state['risk_awareness'].get('overall_R', 0.5)
            elif 'risk_awareness_R' in state:
                # EE engine
                avg_R = state['risk_awareness_R'].get('overall_R', 0.5)
            else:
                avg_R = 0.5
            true_R[a.agent_id] = avg_R

        # Contagion
        perceived_R = {}
        R_vals = []
        for a in self.agents:
            # Handle case where agent node may not be present in graph (e.g., test overrides)
            if self.world.graph.has_node(a.agent_id):
                nbrs = list(self.world.graph.predecessors(a.agent_id))
            else:
                nbrs = []
            nbr_R = [true_R.get(n, 0.5) for n in nbrs if n in true_R]
            if nbr_R:
                # Has predecessors: apply contagion blending
                pR = (1 - self.gov.contagion_alpha) * true_R[a.agent_id]
                pR += self.gov.contagion_alpha * np.mean(nbr_R)
            else:
                # No predecessors: perceived risk equals true risk exactly
                pR = true_R[a.agent_id]
            perceived_R[a.agent_id] = pR
            R_vals.append(pR)

        avg_R = np.mean(R_vals)
        R_std = np.std(R_vals)
        crisis_prob = max(0.0, 1.0 - avg_R * 4)
        time_since_inter = (self.current_tick - self.last_intervention_tick) / 100.0
        time_norm = min(time_since_inter, 1.0)

        state = np.array([
            avg_R,
            R_std,
            crisis_prob,
            self.current_tick / self.max_ticks,
            self.last_severity,
            time_norm
        ], dtype=np.float32)

        return state

    def step(self, action):
        severity = float(np.clip(action[0], 0.0, 1.0))
        current_time = self.start_time + timedelta(days=self.current_tick)

        # Pre-intervention state (for bonus)
        pre_obs = self._compute_obs()
        pre_avg_R = pre_obs[0]

        # Intervention
        intervened = 0
        if severity > 0.01:
            for a in self.agents:
                if hasattr(a, 'process_market_shock'):
                    q = max(0, min(5, int(round(severity * 5))))
                    a.process_market_shock(self.current_tick, severity=severity, quality=q)
            self.last_intervention_tick = self.current_tick
            self.last_severity = severity
            intervened = 1

        # Advance time
        self.current_tick += 1
        # Sync agent's sim_tick for memory decay
        for a in self.agents:
            a.sim_tick = self.current_tick


        # New state
        obs = self._compute_obs()
        avg_R = obs[0]
        R_std = obs[1]

        # Reward v4: strong intervention incentive + dense shaping
        reward_dense = avg_R * 10.0
        survival_bonus = 1.0 if avg_R > 0.2 else 0.0

        # Stability zones (more extreme)
        if 0.5 <= avg_R <= 0.7:
            stability = 20.0          # higher reward for target
        elif avg_R < 0.5:
            stability = -20.0         # stronger penalty for danger
        else:  # avg_R > 0.7
            stability = -10.0         # complacency penalty

        # Lower intervention cost
        cost = 2.0 * severity + 5.0 * R_std

        # Intervention bonus: encourage acting when risk is high (pre_avg_R < 0.5)
        intervention_bonus = 0.0
        if severity > 0.01 and pre_avg_R < 0.5:
            intervention_bonus = severity * 5.0   # e.g., sev=0.5 -> +2.5

        reward = reward_dense + survival_bonus + stability - cost + intervention_bonus

        terminated = avg_R < 0.1
        truncated = self.current_tick >= self.max_ticks

        info = {
            'avg_R': float(avg_R),
            'R_std': float(R_std),
            'severity': severity,
            'intervened': intervened,
            'tick': self.current_tick
        }

        return obs, reward, terminated, truncated, info

    def render(self):
        pass

    def close(self):
        pass


# ========== Test ==========

if __name__ == "__main__":
    print("=== ECOSControlEnv Test ===")
    env = ECOSControlEnv(n_agents=30, max_ticks=200)
    obs, _ = env.reset(42)
    print(f"Init obs: {obs.round(3)}")

    total_r = 0.0
    n_interv = 0
    for t in range(200):
        # Simple policy: intervene if avg_R < 0.3
        action = np.array([0.6 if obs[0] < 0.3 else 0.0], dtype=np.float32)
        obs, r, term, trunc, info = env.step(action)
        total_r += r
        if info['intervened']:
            n_interv += 1
        if term or trunc:
            break

    print(f"\nEpisode: {t+1} steps, reward={total_r:.1f}, interventions={n_interv}")
    print(f"Final state: avg_R={obs[0]:.3f}, std={obs[1]:.3f}")
    print("\n[OK] ECOSControlEnv working - ready for RL")
