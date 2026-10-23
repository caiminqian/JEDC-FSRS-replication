import sys, numpy as np
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\src")
from ecos.control.ecos_env import ECOSControlEnv
for p in (0.05, 0.10, 0.20):
    for seed in (1, 2, 3):
        env = ECOSControlEnv(n_agents=30, max_ticks=300, agent_config={'use_fsrs': True})
        obs, _ = env.reset(seed=seed)
        g = env.world.graph
        for u, v, k in list(g.edges(keys=True)):
            g.remove_edge(u, v, k)
        rng = np.random.RandomState(seed)
        ids = [a.agent_id for a in env.agents]
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if rng.rand() < p:
                    env.world.add_edge(ids[i], ids[j], 'info_flow', weight=1.0)
                    env.world.add_edge(ids[j], ids[i], 'info_flow', weight=1.0)
        iso = sum(1 for a in env.agents if len(list(g.predecessors(a.agent_id))) == 0)
        print(f"ISO p={p} seed={seed} isolated={iso} edges={g.number_of_edges()}")
