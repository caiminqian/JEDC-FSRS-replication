# v55 regeneration of Figure 6 (FSRS vs EE+SM-2, 10-year Monte Carlo, 8 runs).
# Panel structure follows the shipped v54 PNG (trajectory IQR / final-R box /
# delta histogram / retention-vs-shock scatter), NOT the std-over-time panel 4
# in run_fsrs_vs_ee_10year_3650d.py:plot_comparison. Data: v55 A10y reference
# runs, FSRS = A10y_C1_ref_run*, EE = A10y_C3_ref_run*, paired by archive_seed.
import json, glob, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = "/home/hatch/workspace/jedc_pack/v55/results"

def load(pat):
    rows = [json.load(open(p)) for p in sorted(glob.glob(RES + "/" + pat))]
    rows.sort(key=lambda d: d["archive_seed"])
    return rows

fsrs = load("A10y_C1_ref_run*.json")
ee = load("A10y_C3_ref_run*.json")
assert len(fsrs) == 8 and len(ee) == 8, (len(fsrs), len(ee))
assert [d["archive_seed"] for d in fsrs] == [d["archive_seed"] for d in ee]

def traj(rows):
    arr = np.array([[pt["avg_R"] for pt in d["series"]] for d in rows])
    ticks = [pt["tick"] for pt in rows[0]["series"]]
    return ticks, arr.mean(axis=0), np.percentile(arr, 25, axis=0), np.percentile(arr, 75, axis=0)

ticks, fm, fq25, fq75 = traj(fsrs)
_, em, eq25, eq75 = traj(ee)
fr = [d["summary"]["final_R"] for d in fsrs]
er = [d["summary"]["final_R"] for d in ee]
delta = [a - b for a, b in zip(fr, er)]
fshock = [d["n_shocks"] for d in fsrs]
eshock = [d["n_shocks"] for d in ee]
print(f"FSRS final_R mean={np.mean(fr):.4f} (expect 0.9522)")
print(f"EE final_R mean={np.mean(er):.4f} (expect 0.9074)")
print(f"delta mean={np.mean(delta):.4f}")

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle("FSRS vs EE+SM-2: 10-Year (3650 days) Monte Carlo - 8 Runs", fontsize=14)
ax1 = axes[0, 0]
ax1.plot(ticks, em, 'b-', label='EE+SM-2', linewidth=2.5)
ax1.fill_between(ticks, eq25, eq75, color='blue', alpha=0.2)
ax1.plot(ticks, fm, 'r-', label='FSRS', linewidth=2.5)
ax1.fill_between(ticks, fq25, fq75, color='red', alpha=0.2)
ax1.set_xlabel("Tick")
ax1.set_ylabel("Risk Awareness R")
ax1.set_title("Trajectory Comparison (mean ± IQR)")
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, 1.0)
ax2 = axes[0, 1]
ax2.boxplot([er, fr], labels=['EE+SM-2', 'FSRS'])
ax2.set_ylabel("Final R(3650)")
ax2.set_title("Distribution of Final Retention (10 years)")
ax2.grid(True, alpha=0.3, axis='y')
ax3 = axes[1, 0]
ax3.hist(delta, bins=10, edgecolor='black', alpha=0.7, color='purple')
ax3.axvline(0, color='k', linestyle='--', linewidth=1)
ax3.set_xlabel("FSRS R - EE R")
ax3.set_ylabel("Count")
ax3.set_title("Performance Difference (positive = FSRS better)")
ax3.grid(True, alpha=0.3, axis='y')
ax4 = axes[1, 1]
ax4.plot(eshock, er, 'bo', label='EE')
ax4.plot(fshock, fr, 'ro', label='FSRS')
ax4.set_xlabel("Number of Black Swan Events")
ax4.set_ylabel("Final R(3650)")
ax4.set_title("Retention vs Shock Frequency (10 years)")
ax4.legend()
ax4.grid(True, alpha=0.3)
fig.tight_layout()
out = "/home/hatch/workspace/jedc_push/figures/fig6_fsrs_vs_ee_10year_v55.png"
fig.savefig(out, dpi=150)
print(f"Saved {out}")
