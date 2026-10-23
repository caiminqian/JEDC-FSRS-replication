# Parameter Calibration Report (R2)
**Date**: 2026-04-16 20:21
**Method**: grid_search_5event
**Events**: 1987, 2000, 2008, 2020, 2022
**Best Loss**: 0.5604

## Optimal Parameters (5-event calibration)

- **S_initial**: 45.0000
- **severity_crisis**: 0.5000
- **alpha**: 0.6000
- **S_recovery**: 10.0000
- **severity_correction**: 0.5000
- **difficulty_factor**: 1.0000

## Per-Event Fit

### 1987 - Black Monday
- R-curve MSE: 0.1779
- Recovery (sim): N/A days
- Recovery (hist): 520 days
- Trough: day 799, R=0.000

### 2000 - Dot-com Bubble
- R-curve MSE: 0.1607
- Recovery (sim): N/A days
- Recovery (hist): 2555 days
- Trough: day 799, R=0.000

### 2008 - Global Financial Crisis
- R-curve MSE: 0.1588
- Recovery (sim): N/A days
- Recovery (hist): 1460 days
- Trough: day 799, R=0.000

### 2020 - COVID Crash
- R-curve MSE: 0.1741
- Recovery (sim): N/A days
- Recovery (hist): 153 days
- Trough: day 799, R=0.000

### 2022 - Inflation/Hiking
- R-curve MSE: 0.1578
- Recovery (sim): N/A days
- Recovery (hist): N/A days
- Trough: day 799, R=0.000


## Economic Interpretation

S_initial = 45 days → half-life ~31 days. Market forgets risk monthly.
severity_crisis = 0.5 → crashes halve risk awareness (realistic VIX jump).
alpha = 0.6 → strong panic contagion (60% from neighbors).
S_recovery = 10 days → interventions reset memory in ~2 weeks.

## Next Steps

1. Integrate params into ECOS config (config/markets.json)
2. Run 1000-agent pressure test to validate avg_R vs VIX
3. If fit inadequate, add real VIX data via yfinance