import math, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# v55 (J1 joint fit) params; v47 script used 1.8729/0.5425/0.0912
w17, w18, w19 = 0.6096, 0.0496, 0.1841

def mult(S, G):
    return math.exp(w17 * (G - 3 + w18) * (S ** (-w19)))

S_grid = np.logspace(0, 3, 200)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
ax = axes[0]
for G, ls, lab in [(1, "-", "G=1"), (2, "-", "G=2"), (3, "-", "G=3"), (4, "-", "G=4")]:
    ax.plot(S_grid, [mult(float(s), G) for s in S_grid], label=lab)
ax.axhline(1.0, color="k", lw=0.8, ls="--")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Initial stability S (days, log scale)")
ax.set_ylabel("Multiplier S'/S (log scale)")
ax.set_title("(a) Multiplier vs initial S")
ax.grid(True, alpha=0.3)
ax.legend()
for S in (5, 45, 1000):
    ax.axvline(S, color="grey", lw=0.6, ls=":")
ax = axes[1]
grades = [1, 2, 3, 4]
for S0 in (5, 45, 1000):
    ax.plot(grades, [mult(S0, G) for G in grades], "o-", label=f"S={S0}")
ax.axhline(1.0, color="k", lw=0.8, ls="--")
ax.set_xticks(grades)
ax.set_xlabel("Shock grade G")
ax.set_ylabel("Multiplier S'/S")
ax.set_title("(b) Multiplier vs grade, at S=5, 45, 1000")
ax.grid(True, alpha=0.3)
ax.legend()
fig.suptitle("Correct FSRS stability update: S' = S * exp(w17*(G-3+w18)*S^(-w19)), w17=0.6096, w18=0.0496, w19=0.1841")
fig.tight_layout()
out = "/home/hatch/workspace/jedc_push/figures/fig5_grade_impact_v55.png"
fig.savefig(out, dpi=150)
print(f"Saved {out}")
for S in (5, 45, 1000):
    print(f"S={S} multipliers G1-4: {[round(mult(S, G), 3) for G in grades]}")
