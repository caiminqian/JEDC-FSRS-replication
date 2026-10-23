import sys, json
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\src")
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\experiments\grid_search")
from grid_search_control import evaluate_policy
best = evaluate_policy(0.45, 0.40, n_episodes=10, seed_offset=9)
print("VERIFY_BEST", best)
base = evaluate_policy(0.30, 0.60, n_episodes=10, seed_offset=22)
print("VERIFY_BASE", base)
ref = json.load(open(r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\results\grid\results_grid.json"))
print("REF_BEST", ref["all_results"]["thr=0.45,sev=0.40"])
print("REF_BASE", ref["all_results"]["thr=0.30,sev=0.60"])
print("VERIFY_DONE")
