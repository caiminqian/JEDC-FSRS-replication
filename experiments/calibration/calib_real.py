import csv
import importlib.util
import json
import math
import statistics

SPEC = importlib.util.spec_from_file_location(
    "fsrs_memory", "/home/hatch/workspace/jedc_push/src/ecos/agents/fsrs_memory.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

POST_PEAK = 779  # ticks after peak; window = peak + 779 = 780 ticks


def load_series(path, col):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            v = r[col].strip()
            if v in ("", "."):
                continue
            rows.append((r["observation_date"], float(v)))
    return rows


def peak_in_range(series, lo, hi):
    seg = [(d, v) for d, v in series if lo <= d <= hi]
    return max(seg, key=lambda x: x[1])


def grade_from_peak(peak):
    if peak >= 80:
        return 1
    if peak >= 40:
        return 2
    if peak >= 25:
        return 3
    return 4


def simulate_event(series, peak_date, s0):
    idx = next(i for i, (d, _) in enumerate(series) if d == peak_date)
    _, peak = series[idx]
    floor = statistics.median(v for _, v in series[max(0, idx - 60):idx])
    window = series[idx:idx + POST_PEAK + 1]
    ref = [min(1.0, max(0.0, (v - floor) / (peak - floor))) for _, v in window]
    mem = MOD.FSRS_Economic_Memory(lesson_id="x", lesson_name="x", S=s0)
    mem.process_market_shock(0, grade_from_peak(peak))
    sim = [mem.get_retrievability(t) for t in range(len(window))]
    mse = sum((a - b) ** 2 for a, b in zip(sim, ref)) / len(window)
    d_sim = next((t for t, r in enumerate(sim) if r < 0.5), len(window))
    d_ref = next((t for t, r in enumerate(ref) if r < 0.5), len(window))
    rec = abs(d_sim - d_ref) / len(window)
    return {
        "peak_date": peak_date, "peak": peak, "grade": grade_from_peak(peak),
        "floor": floor, "n_ticks": len(window), "mse": mse,
        "days_sim": d_sim, "days_ref": d_ref, "recovery": rec,
        "loss": mse + rec,
    }


VIX = load_series("/home/hatch/workspace/jedc_pack/vixcls.csv", "VIXCLS")
VXO = load_series("/tmp/vxocls.csv", "VXOCLS")

EVENTS = [
    ("1987", VXO, "1987-10-19"),
    ("2000", VIX, peak_in_range(VIX, "2000-01-01", "2002-12-31")[0]),
    ("2008", VIX, "2008-11-20"),
    ("2020", VIX, "2020-03-16"),
    ("2022", VIX, "2022-03-07"),
]

GRID_S = [5, 10, 15, 20, 25, 30, 35, 37, 40, 42, 45, 50, 60, 75]
results = {}
for s0 in GRID_S:
    per_event = {}
    for name, series, peak_date in EVENTS:
        per_event[name] = simulate_event(series, peak_date, s0)
    total = sum(e["loss"] for e in per_event.values()) / len(per_event)
    results[str(s0)] = {"total_loss": total, "events": per_event}
    print("S=%s total_loss=%.4f %s" % (
        s0, total,
        " ".join("%s:%.3f" % (n, e["loss"]) for n, e in per_event.items())),
        flush=True)

best = min(results, key=lambda k: results[k]["total_loss"])
print("BEST S=%s loss=%.4f" % (best, results[best]["total_loss"]))
with open("/home/hatch/workspace/jedc_pack/calib_real_results.json", "w") as f:
    json.dump({"grid_S": GRID_S, "best_S": best, "results": results},
              f, indent=2)
