import numpy as np
from ecos.control.ecos_env import ECOSControlEnv

class DummyAgent:
    def __init__(self, agent_id, true_R):
        self.agent_id = agent_id
        self._true_R = true_R
    def get_cognitive_state(self):
        # Return EE style dict
        return {'risk_awareness_R': {'overall_R': self._true_R}}

def test_predecessor_less_and_with():
    env = ECOSControlEnv(n_agents=2, max_ticks=10)
    env.reset(seed=42)
    # Replace agents with deterministic ones
    a0 = DummyAgent('A_000', true_R=0.8)
    a1 = DummyAgent('A_001', true_R=0.2)
    env.agents = [a0, a1]
    # Clear graph edges and add edge from a0 -> a1 (a1 has predecessor)
    env.world.graph.remove_edges_from(list(env.world.graph.edges()))
    env.world.add_edge('A_000', 'A_001', 'info_flow', weight=1.0)
    # Compute observation
    obs = env._compute_obs()
    avg_R = obs[0]
    # Expected perceived R: a0 = 0.8 (no preds), a1 = 0.4*0.2 + 0.6*0.8 = 0.56
    expected_avg = (0.8 + 0.56) / 2.0
    assert np.isclose(avg_R, expected_avg, atol=1e-6), f"avg_R {avg_R} != expected {expected_avg}"

def test_no_predecessors():
    env = ECOSControlEnv(n_agents=2, max_ticks=10)
    env.reset(seed=1)
    a0 = DummyAgent('A_000', true_R=0.5)
    a1 = DummyAgent('A_001', true_R=0.5)
    env.agents = [a0, a1]
    env.world.graph.remove_edges_from(list(env.world.graph.edges()))
    # No edges at all
    obs = env._compute_obs()
    avg_R = obs[0]
    # Both perceived equal true risk 0.5 -> avg 0.5
    assert np.isclose(avg_R, 0.5, atol=1e-6), f"avg_R {avg_R} != 0.5"

if __name__ == '__main__':
    test_predecessor_less_and_with()
    test_no_predecessors()
    print('All tests passed')
