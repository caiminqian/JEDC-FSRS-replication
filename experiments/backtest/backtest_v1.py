#!/usr/bin/env python3
"""Real-data backtest v1 (frozen J1 params).

Implements ~/workspace/jedc_pack/BACKTEST_PROPOSAL.md.
Reference functions are copied VERBATIM from joint_fit.py
(load_series, grade_from_peak, build_event, sim_curve,
event_loss_from_curve) -- provenance noted, construction unchanged.
Importing joint_fit.py directly would run the full fit (Steps A/B/C),
so the copy is the brief-sanctioned route. No fitting is performed
anywhere in this script: J1 parameters are asserted frozen and only
evaluated. No paper, repo, or push is touched by this script.
"""
import csv
import datetime
import importlib.util
import json
import math
import statistics

# ---- frozen J1 parameters (asserted, never fitted) ----
W17, W18, W19, W20, S0 = 0.6096, 0.0496, 0.1841, 0.4, 0.5
S_POST = {1: 0.1295, 2: 0.2589, 3: 0.5175}
assert (W17, W18, W19, W20, S0) == (0.6096, 0.0496, 0.1841, 0.4, 0.5)
assert S_POST == {1: 0.1295, 2: 0.2589, 3: 0.5175}

DATA = "/home/hatch/workspace/jedc_push/data/vixcls.csv"
POST_PEAK = 779
FWD_START = "2022-03-08"  # day after J1's last event 2022-03-07


# ---- verbatim from joint_fit.py (provenance: joint_fit.py) ----
def load_series(path, col):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            v = r[col].strip()
            if v in ("", "."):
                continue
            rows.append((r["observation_date"], float(v)))
    return rows


def grade_from_peak(p):
    return 1 if p >= 80 else 2 if p >= 40 else 3 if p >= 25 else 4


def build_event(name, series, peak_date):
    idx = next(i for i, (d, _) in enumerate(series) if d == peak_date)
    _, peak = series[idx]
    floor = statistics.median(v for _, v in series[max(0, idx - 60):idx])
    window = series[idx:idx + POST_PEAK + 1]
    ref = [min(1.0, max(0.0, (v - floor) / (peak - floor))) for _, v in window]
    d_ref = next((t for t, r in enumerate(ref) if r < 0.5), len(window))
    return {"name": name, "peak_date": peak_date, "peak": peak,
            "grade": grade_from_peak(peak), "floor": floor, "ref": ref,
            "days_ref": d_ref, "n": len(window)}


def sim_curve(w20, s_post, n):
    factor = 0.9 ** (-1.0 / w20) - 1.0
    return [(1.0 + factor * (t / s_post)) ** (-w20) for t in range(n)]


def event_loss_from_curve(sim, ev):
    mse = sum((a - b) ** 2 for a, b in zip(sim, ev["ref"])) / len(sim)
    d_sim = next((t for t, r in enumerate(sim) if r < 0.5), len(sim))
    rec = abs(d_sim - ev["days_ref"]) / len(sim)
    return mse + rec, mse, rec, d_sim
# ---- end verbatim copy ----


# Engine: same module joint_fit.py imports (v55 kernel file).
SPEC = importlib.util.spec_from_file_location(
    "fsrs_memory", "/home/hatch/workspace/jedc_push/src/ecos/agents/fsrs_memory.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
# Second check: module defaults must equal frozen J1 values.
assert MOD.FSRS_DEFAULT_PARAMS == {"w17": W17, "w18": W18, "w19": W19, "w20": W20}


def scan_forward_peaks(series):
    """Peaks in the forward period: a day whose value is the max of its
    +-15 calendar-day window (first occurrence wins ties), value >= 25."""
    dates = [datetime.date.fromisoformat(d) for d, _ in series]
    vals = [v for _, v in series]
    peaks = []
    for i, (d, v) in enumerate(series):
        if d < FWD_START or v < 25:
            continue
        di = dates[i]
        lo = di - datetime.timedelta(days=15)
        hi = di + datetime.timedelta(days=15)
        win = [(dj, vj) for dj, vj in zip(dates, vals) if lo <= dj <= hi]
        maxv = max(vj for _, vj in win)
        if v < maxv:
            continue
        first = min(dj for dj, vj in win if vj == maxv)
        if di != first:
            continue
        peaks.append((d, v))
    return peaks


def arm2_event(series, ev):
    """Multi-shock engine run over the same window as build_event.
    Rule: no shock on window-start day (no previous grade, so no change);
    a shock fires on every later day whose grade differs from the previous
    trading day's grade. R sampled at every window day; only post-peak
    days are scored."""
    idx = next(i for i, (d, _) in enumerate(series) if d == ev["peak_date"])
    start = max(0, idx - 60)
    win = series[start:idx + POST_PEAK + 1]
    grades = [grade_from_peak(v) for _, v in win]
    peak_pos = idx - start
    mem = MOD.FSRS_Economic_Memory(
        lesson_id="x", lesson_name="x", S=S0,
        w17=W17, w18=W18, w19=W19, w20=W20)
    R = []
    shocks = []
    for pos in range(len(win)):
        if pos > 0 and grades[pos] != grades[pos - 1]:
            mem.process_market_shock(pos, grades[pos])
            shocks.append({"day_from_peak": pos - peak_pos,
                           "grade": grades[pos]})
        R.append(mem.get_retrievability(pos))
    post = R[peak_pos:peak_pos + ev["n"]]
    assert len(post) == ev["n"]
    mse_eng = sum((a - b) ** 2 for a, b in zip(post, ev["ref"])) / len(post)
    sim = sim_curve(W20, S_POST[ev["grade"]], ev["n"])
    mse_cf = sum((a - b) ** 2 for a, b in zip(sim, ev["ref"])) / len(sim)
    return {"mse_engine": mse_eng, "mse_closed": mse_cf,
            "engine_wins": mse_eng < mse_cf, "n_shocks": len(shocks),
            "shocks": shocks, "final_S": mem.S}


def main():
    series = load_series(DATA, "VIXCLS")
    print("series: %d rows, %s .. %s" % (len(series), series[0][0], series[-1][0]))

    # --- cross-check: reproduce J1 Step B on the 12 J1 events ---
    j1 = [("1987", "/home/hatch/workspace/jedc_pack/vxocls.csv", "VXOCLS", "1987-10-19"),
          ("2000", None, None, "2002-08-05"),
          ("2008", None, None, "2008-11-20"),
          ("2020", None, None, "2020-03-16"),
          ("2022", None, None, "2022-03-07"),
          ("1997", None, None, "1997-10-30"),
          ("1998", None, None, "1998-09-10"),
          ("2001", None, None, "2001-09-20"),
          ("2010", None, None, "2010-05-20"),
          ("2011", None, None, "2011-08-08"),
          ("2015", None, None, "2015-08-24"),
          ("2018", None, None, "2018-02-05")]
    vxo = load_series("/home/hatch/workspace/jedc_pack/vxocls.csv", "VXOCLS")
    tot = 0.0
    for name, path, col, pd in j1:
        s = vxo if path else series
        ev = build_event(name, s, pd)
        sim = sim_curve(W20, S_POST[ev["grade"]], ev["n"])
        loss, _, _, _ = event_loss_from_curve(sim, ev)
        tot += loss
    print("J1 reproduction: mean loss on 12 J1 events = %.4f (expect 0.0360)" % (tot / 12))

    # --- Arm 1 + Arm 2 on forward peaks ---
    peaks = scan_forward_peaks(series)
    print("forward peaks found: %d" % len(peaks))
    for d, v in peaks:
        print("  peak %s VIX=%.2f grade=%d" % (d, v, grade_from_peak(v)))
    results = []
    for d, v in peaks:
        ev = build_event(d, series, d)
        sim = sim_curve(W20, S_POST[ev["grade"]], ev["n"])
        loss, mse, rec, d_sim = event_loss_from_curve(sim, ev)
        a2 = arm2_event(series, ev)
        results.append({
            "peak_date": d, "peak": v, "grade": ev["grade"],
            "floor": ev["floor"], "n": ev["n"], "days_ref": ev["days_ref"],
            "arm1": {"loss": loss, "mse": mse, "recovery": rec,
                     "days_sim": d_sim,
                     "gate_loss": loss < 0.5, "gate_rec": rec < 0.2},
            "arm2": a2,
        })
        print("EVENT %s G=%d n=%d dr=%d ds=%d loss=%.4f mse=%.4f rec=%.4f | "
              "eng_mse=%.4f cf_mse=%.4f eng_wins=%s shocks=%d" % (
            d, ev["grade"], ev["n"], ev["days_ref"], d_sim, loss, mse, rec,
            a2["mse_engine"], a2["mse_closed"], a2["engine_wins"], a2["n_shocks"]))
    mean_loss = (sum(r["arm1"]["loss"] for r in results) / len(results)) if results else None
    arm1_pass = bool(results) and all(
        r["arm1"]["gate_loss"] and r["arm1"]["gate_rec"] for r in results) and mean_loss < 0.5
    arm1_verdict = ("PASS" if arm1_pass else
                    ("INSUFFICIENT_EVENTS" if len(results) < 2 else "FAIL"))
    arm2_pass = bool(results) and all(r["arm2"]["engine_wins"] for r in results)
    out = {"frozen_params": {"w17": W17, "w18": W18, "w19": W19, "w20": W20,
                             "S0": S0, "S_POST": S_POST},
           "series": {"rows": len(series), "first": series[0][0], "last": series[-1][0]},
           "j1_reproduction_mean_loss": tot / 12,
           "forward_peaks": [{"date": d, "vix": v} for d, v in peaks],
           "events": results,
           "arm1_mean_loss": mean_loss,
           "arm1_verdict": arm1_verdict,
           "arm2_verdict": "PASS" if arm2_pass else ("NO_EVENTS" if not results else "FAIL")}
    with open("/home/hatch/workspace/jedc_pack/backtest_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("ARM1 verdict=%s mean_loss=%s" % (arm1_verdict, mean_loss))
    print("ARM2 verdict=%s" % out["arm2_verdict"])
    print("WROTE backtest_results.json")


if __name__ == "__main__":
    main()
