# High/Low Swings Strategy - Experiment Log

## Strategy: Jigsaw Swing Trend-Following on BTCUSDT 1-min
**Asset:** BTCUSDT | **Resolution:** 1-min | **Period:** 2025-01-01 to 2026-04-01 | **Cash:** $10,000

## Core Logic
1. Detect swing highs/lows on 1-min candles using `swing_len` window
2. Classify each swing as HH/LH (for highs) or LL/HL (for lows)
3. Count bullish (HH+HL) vs bearish (LL+LH) in last N swings
4. If NOT plateauing: bullish>=threshold (hh>=2, hl>=1) -> long; bearish>=threshold -> short
5. If plateauing + drift > 1% -> long; drift < -1% -> short
6. **Opposite signal cancels pending** — if bearish signal fires while bullish pending, cancel it
7. **ADX(28) < 20 gate** — only enter in range-bound conditions, skip strong trends
8. Pending signal -> wait for RSI pullback (RSI<45 long, >55 short)
8. **Price-confirms-trend:** for longs, price > last swing low; for shorts, price < last swing high
9. ATR-based SL/TP with 2.5%/10% floors. Trailing stop 1.5%/1%

---

## CURRENT BEST: fixK — fixJ + Daily ROC Parabolic Filter

**Blocks counter-trend entries during parabolic moves (20-day price ROC > 20%). Prevents shorting during bull runs and longing during crashes. Uses daily consolidator to track closes.**

| Period | Net Profit | CAGR | Drawdown | Orders | Fees | Win Rate | P/L Ratio | Sharpe | Sortino | PSR |
|--------|-----------|------|----------|--------|------|----------|-----------|--------|---------|-----|
| 1.25yr (2025-2026) | **+23.36%** | 18.30% | 4.3% | 286 | ₮377 | 62% | 1.10 | 1.747 | 2.564 | 94.1% |
| 3yr (2023-2026) | **+74.69%** | 18.71% | 6.4% | 1,098 | ₮1,759 | 42% | 2.27 | 1.277 | 2.565 | 93.5% |
| 6yr (2020-2026) | **+112.53%** | 12.81% | 19.2% | 2,670 | ₮4,447 | 56% | 1.00 | 0.921 | 1.509 | 64.8% |

**With 1bps slippage (ConstantSlippageModel(0.0001)):**

| Period | No Slip | With Slip | Slip Cost | DD (slip) | Sharpe (slip) |
|--------|---------|-----------|-----------|-----------|---------------|
| 1.25yr | +23.36% | +22.27% | -1.09% | 4.4% | 1.636 |
| 3yr | +74.69% | +69.15% | -5.54% | 6.8% | 1.165 |
| 6yr | +112.53% | +95.82% | -16.71% | 20.9% | 0.790 |

Edge survives realistic execution across all periods. Slippage is now active in the codebase by default.

### What changed from fixJ to fixK:
- **Daily ROC parabolic filter**: consolidates 1-min bars into daily bars, tracks last 20 daily closes
- When 20-day price ROC > +20%: blocks short entries (don't short into parabolic rally)
- When 20-day price ROC < -20%: blocks long entries (don't long into parabolic crash)
- Only ~200 trades blocked across 6yr, but those were the worst losers (counter-trend entries during 2021 bull run, 2022 bear crash)
- **Most impactful single change in strategy history**: 6yr return +42.64% → **+112.53%** (+164%), DD 25.5% → 19.2%, Sharpe 0.310 → **0.921** (+197%)
- 3yr: +43.54% → **+74.69%**, DD 10.0% → **6.4%**, Sharpe 0.766 → **1.277** (+67%)
- 1.25yr: +21.08% → **+23.36%**, Sharpe 1.501 → **1.747** (+16%)

### 2020-2022 Diagnostic (before fix)
| Year | Return | DD | Sharpe | WR | P/L | Problem |
|------|--------|-----|--------|-----|------|---------|
| 2020 | +11.81% | 8.3% | 1.085 | 67% | 0.57 | Profitable — COVID crash recovered |
| 2021 | +1.96% | 15.0% | 0.203 | 65% | 0.56 | Near-flat, 15% DD from counter-trend shorts |
| 2022 | **-13.65%** | **17.0%** | -1.279 | 57% | 0.63 | **Main culprit** — longs against bear market |

### ROC threshold comparison
| ROC Threshold | 6yr Return | 6yr DD | 6yr Sharpe | 3yr Return | 3yr DD | 1.25yr Return |
|---------------|-----------|--------|-----------|-----------|--------|--------------|
| 25% | +80.87% | 21.7% | 0.655 | +70.39% | 7.1% | +21.80% |
| **20%** | **+112.53%** | **19.2%** | **0.921** | **+74.69%** | **6.4%** | **+23.36%** |
| 15% | +102.82% | 15.5% | 0.851 | +73.43% | 5.9% | +22.12% |

### Previous best: fixJ — fixI + Shock/Jump Filter

| Period | Net Profit | CAGR | Drawdown | Orders | Fees | Win Rate | P/L Ratio | Sharpe | Sortino | PSR |
|--------|-----------|------|----------|--------|------|----------|-----------|--------|---------|-----|
| 1.25yr (2025-2026) | +21.08% | 16.55% | 4.3% | 293 | ₮387 | 61% | 1.07 | 1.501 | 2.342 | 90.1% |
| 3yr (2023-2026) | +43.54% | 11.76% | 10.0% | 1,129 | ₮1,557 | 41% | 2.02 | 0.766 | 1.209 | 71.7% |
| 6yr (2020-2026) | +42.64% | 5.84% | 25.5% | 2,867 | ₮3,795 | 55% | 0.93 | 0.310 | 0.455 | 15.7% |

**With 1bps slippage:** +38.86% (3yr), Sharpe 0.637 — edge survives realistic execution.

| Parameter | Value |
|-----------|-------|
| **venue** | **Binance Futures** (was spot) |
| **account currency** | **USDT** |
| swing_len | 50 |
| swing_lookback | last 8 swings |
| bullish/bearish threshold | >=6 out of 8 |
| ATR SL mult | 8.0 |
| ATR TP mult | 32.0 |
| min_sl/tp_pct | 2.5% / 10% |
| trail | activate 1.5%, distance 1% |
| position | 30% |
| pending_window | 240 bars (4hr) |
| **cooldown** | **720 bars (12hr)** (was 480/8hr) |
| **RSI entry** | **< 45 long / > 55 short** (was 40/60) |
| **ADX filter** | **ADX(28) < 20 — trade only in range** (was < 25) |
| opposite_cancels | opposite swing signal cancels pending |
| price_confirms | price > last swing low (long) / price < last swing high (short) |
| **shock filter** | **pause entries 30 bars after abs(1m return) > 4σ rolling stdev (120-bar window)** |

### What changed from fixI to fixJ:
- **Shock/jump filter**: pauses all entries for 30 minutes after an extreme 1-minute price move
- "Extreme" = absolute return > 4x rolling standard deviation (computed on 120-bar window of absolute returns)
- Prevents entering during liquidation cascades, flash crashes, or news-driven spikes
- Pending signal stays alive during pause — it just can't trigger entry until pause expires
- 3yr improvement: +34.54% → **+43.54%**, Sharpe 0.499 → **0.766** (+53% Sharpe improvement)
- 1.25yr improvement: +15.84% → **+21.08%**, Sharpe 0.993 → **1.501**
- 6yr DD improved: 29.0% → **25.5%**

### What changed from fixF to fixI:
- **Enhanced plateau detection**: angles declining OR (angles declining moderately + swing compression)
- Original plateau: `last_angle < first_angle * 0.4`
- Enhanced: also triggers when `last_angle < first_angle * 0.6 AND bar_distances shrinking (last < first * 0.7)`
- Detects consolidation earlier, catches drift trades sooner
- 6yr improvement: +36.28% → **+42.43%**, Sharpe 0.234 → **0.303**

### Incremental Improvements: fixA → fixI (Futures)

| Version | Change | 1.25yr | 3yr | 6yr |
|---------|--------|--------|-----|-----|
| fix25 (spot baseline) | 30% pos, 8 swings, >=6 | +12.93% | -14.01% | -38.89% |
| fixA | Switch to Binance Futures | — | -5.36% | — |
| fixB | + ADX(28) < 25 range filter | — | -2.07% | — |
| fixC | + RSI 45/55 (was 40/60) | +18.08% | +29.89% | +34.41% |
| fixF | ADX<20 + 12hr cooldown | +15.84% | +34.19% | +36.28% |
| fixI | + Enhanced plateau detection | — | +34.54% | +42.43% |
| fixJ | + Shock/jump filter (4σ, 30-bar pause) | +21.08% | +43.54% | +42.64% |
| **fixK** | **+ Daily ROC parabolic filter (20-day ROC > 20%)** | **+23.36%** | **+74.69%** | **+112.53%** |

### Spot Margin Comparison (fixC logic on Binance Spot)

Same fixC logic running on spot with higher fees (0.1%/0.1% vs 0.02%/0.04%):

| Period | Net Profit | Drawdown | Fees |
|--------|-----------|----------|------|
| 1.25yr (2025-2026) | +10.46% | 10.1% | $1,833 |
| 3yr (2023-2026) | -15.75% | 31.0% | $4,029 |
| 6yr (2020-2026) | -51.74% | 56.8% | $7,014 |

**Conclusion:** Spot is profitable only on 1.25yr. Futures fee structure (0.02%/0.04%) is required for multi-year profitability. Fee drag on spot consumes the entire edge.

---

## Losing Period Analysis (fixC baseline)

### Per-Year Breakdown (fixC, 3yr period)

| Period | Net Profit | Orders | Win Rate | P/L Ratio | Avg Win | Avg Loss | DD |
|--------|-----------|--------|----------|-----------|---------|----------|-----|
| 2023 H1 | +1.04% | 205 | 56% | 0.82 | 0.66% | 0.81% | 9.7% |
| 2023 Q3 | +2.15% | 65 | 66% | 0.67 | 0.57% | 0.86% | 3.6% |
| **2023 Q4** | **-8.25%** | **121** | **37%** | **1.00** | 0.51% | 0.51% | 9.8% |
| 2024 | +13.31% | 580 | 14% | 9.13 | 1.01% | 0.11% | 9.8% |
| 2025 | +18.08% | 339 | 59% | 1.05 | 0.52% | 0.50% | 3.6% |

### Root Cause: Q4 2023

Q4 2023 is the worst period (**-8.25%**). BTC rallied ~27k→42k (Oct-Dec 2023).

**Why ADX<25 didn't fully protect:** During sustained rallies, ADX oscillates. It dips below 25 during pullback phases within the rally, allowing entries. Those entries then face the strong trend resumption, resulting in SL exits.

**Key diagnostic:** P/L ratio is exactly 1.00 — avg win equals avg loss (0.51% each). With 63% loss rate and no edge, the period is a guaranteed loss.

**2024 anomaly:** 14% win rate but P/L ratio 9.13 — very few wins but they're enormous (catching large BTC moves from 42k→94k). Most "losses" are tiny (avg 0.11%) — trailing stops exiting near breakeven.

### Fixes Tested (from fixC baseline, 3yr period)

| Fix | Change | 3yr Result | Sharpe | DD | Why |
|-----|--------|-----------|--------|-----|-----|
| fixD | ADX < 20 (was < 25) | +30.66% | 0.335 | 10.6% | Marginal, blocks 12 borderline trades |
| fixE | 12hr cooldown (was 8hr) | +30.67% | 0.397 | 9.5% | Fewer noise trades, lower DD |
| **fixF** | **ADX<20 + 12hr cooldown** | **+34.19%** | **0.493** | **10.2%** | **Synergistic: both filter Q4 2023 losses** |
| fixG-old | fixF + 3-loss circuit breaker | +26.36% | 0.279 | 9.5% | Breaker skips valid recovery entries |
| fixH-old | fixF + pending window 180 (3hr) | +25.72% | 0.262 | 9.5% | Shorter window misses valid pullbacks |
| fixG | Amplitude + chainsaw filter | +31.29% | 0.420 | 11.5% | Filters block good trades (too strict at 0.3%) |
| fixH | ADX hysteresis (18/23, 60-bar dwell) | +19.02% | 0.055 | 10.3% | Too restrictive, 1hr dwell blocks most entries |
| fixH2 | ADX hysteresis soft (20/24, 15-bar) | +25.93% | 0.269 | 16.2% | Dwell still delays entries, worse DD |
| **fixI** | **Enhanced plateau (+ compression)** | **+34.54%** | **0.499** | **10.2%** | **Better structure reading, +6% on 6yr** |
| **fixJ** | **Shock filter (4σ, 30-bar pause)** | **+43.54%** | **0.766** | **10.0%** | **Prevents entries during vol spikes, +9% return, +53% Sharpe** |
| fixK | 15m ADX consolidated (threshold 25) | +13.59% | -0.136 | 16.3% | 15m ADX too loose at 25, lets bad trades through |
| fixK2 | 15m ADX consolidated (threshold 20) | +9.17% | -0.369 | 7.0% | 15m ADX at 20 too restrictive, blocks most trades |
| fixL | Shock + BOS invalidation (SMC) | +40.31% | 0.683 | 7.4% | BOS too aggressive — range strategy needs price near swing levels |
| fixM | Shock + liquidity sweep invalidation (SMC) | +42.61% | 0.757 | 11.3% | Marginal — sweep filter doesn't add value |
| fixN | Shock + 1bps slippage model | +38.86% | 0.637 | 10.2% | Edge survives slippage — 4.7% cost from realistic execution |

### Optimization Tests (from fixJ baseline, targeting DD<10%, Sharpe>1, WR>50%)

#### Position Sizing Variants
| Fix | Change | 3yr Return | Sharpe | DD | WR | Notes |
|-----|--------|-----------|--------|-----|-----|-------|
| fix2 | 25% flat position (was 30%) | +35.37% | 0.631 | **8.4%** | 41% | DD under target but Sharpe drops |
| fix7 | 25% + vol scale 0.5-1.5 | +56.70% | **0.911** | 12.4% | 41% | Actually flat 37.5% — BTC ATRP always at cap |
| fix7b | 25% + vol scale 0.4-1.0 | +35.38% | 0.631 | 8.4% | 41% | Identical to fix2 — downscaling has no effect |
| fix8a | 30% + vol scale 0.4-1.0 | +43.55% | 0.766 | 10.0% | 41% | Identical to fixJ — vol scaling is a no-op |
| fix8b | 25% + vol scale 0.5-1.2 | +43.58% | 0.767 | 10.0% | 41% | 1.2 cap too small for any effect |

**Key finding:** Vol-scaling on 1-min ATR is actually flat sizing in disguise. BTC's ATRP (~0.1-0.2%) is always well below the 0.5% target, so scale factor always hits the cap. DD/Sharpe/return trade-off is strictly linear with position size.

#### Exit Strategy Changes (all failed)
| Fix | Change | 3yr Return | Sharpe | DD | WR | Notes |
|-----|--------|-----------|--------|-----|-----|-------|
| fix1 | Tighter trail 1.0%/0.7% (was 1.5%/1.0%) | +11.21% | -0.257 | 9.3% | 45% | Destroys P/L ratio by cutting winners early |
| fix3 | SL 6×ATR/2.0% (was 8×ATR/2.5%) | +10.81% | -0.281 | 8.0% | 35% | Tighter SL = more stop-outs, smaller losses but too many |
| fix4 | Breakeven stop + TP 5% (at +0.5%) | -5.35% | -1.116 | 15.0% | 20% | BE stop converts winners to flat, TP 5% caps upside |
| fix5 | Time-based exit (stale trades) | +0.46% | -0.764 | 9.9% | 23% | Exits before big moves materialize |
| fix10 | Partial TP at 2% (close half) | +32.59% | 0.496 | 9.7% | 48% | WR improved to 48% but P/L dropped from 2.02 to 1.44 |

**Key finding:** Strategy's edge is in asymmetric P/L (2.02 ratio). Any exit change that improves WR destroys the fat-tail profits that carry the strategy.

#### Entry Filter Changes
| Fix | Change | 3yr Return | Sharpe | DD | WR | Notes |
|-----|--------|-----------|--------|-----|-----|-------|
| fix6 | ADX slope filter (ADX rising = skip) | +23.68% | 0.229 | 12.2% | 40% | ADX slope too noisy on 1-min, blocks good entries |
| fix9 | ATRP < 0.8% entry gate | +43.54% | 0.766 | 10.0% | 41% | No effect — 1-min ATRP always below 0.8% |
| fix9b | ATRP < 0.5% entry gate | +43.53% | 0.765 | 10.0% | 41% | No effect — 1-min ATRP always below 0.5% |

**Key finding:** 1-min ATRP is always 0.1-0.3% for BTC, so percentage-based vol filters don't work at this resolution.

#### Confidence-Based Position Sizing (tested, rejected — didn't improve all periods)
| Fix | Strong/Weak | 3yr Return | Sharpe | DD | WR | Notes |
|-----|-------------|-----------|--------|-----|-----|-------|
| fix11 | 35% / 20% | +32.80% | 0.567 | **7.0%** | 41% | Most trades are 6/8, so avg pos ~20% |
| fix11b | 33% / 25% | +38.15% | 0.681 | 8.5% | 41% | Better balance |
| fix11c | 37% / 25% | +39.83% | 0.708 | 8.6% | 41% | Approaching fixJ return |
| fix11d | 40% / 25% | +40.99% | 0.723 | 8.6% | 41% | DD stable at 8.6% |
| fix11e | 45% / 25% | +42.69% | 0.740 | 8.8% | 41% | Near fixJ return with lower DD |
| fix11f | 50% / 25% | +44.95% | 0.766 | 8.8% | 41% | Matches fixJ Sharpe, better DD |
| fix11g | 55% / 25% | +47.00% | 0.783 | 8.9% | 41% | New best return at DD<10% |
| fix11h | 60% / 25% | +48.50% | 0.785 | 9.0% | 41% | |
| fix11i | 65% / 25% | +50.92% | 0.804 | 9.2% | 41% | 50%+ return with DD<10% |
| fix11j | 70% / 25% | +52.77% | 0.810 | 9.3% | 41% | |
| fix11k | 75% / 25% | +54.58% | 0.814 | 9.3% | 41% | |
| fix11L | 80% / 25% | +56.81% | 0.824 | 9.4% | 41% | |
| **fix11n** | **85% / 25%** | **+58.69%** | **0.827** | **9.6%** | 41% | **Best before plateau bug fix** |
| fix11m | 90% / 25% | +60.84% | 0.833 | 10.2% | 41% | DD exceeds 10% target |
| fix11o | 85% / 15% | +44.87% | 0.623 | 11.5% | 41% | Too little on weak — loses diversification |
| fix11p | 85% / 20% | +51.77% | 0.734 | 10.4% | 41% | Still too concentrated |
| fix11n-p | 85% / 25% + plateau fix | +57.46% | 0.806 | 9.6% | 41% | Plateau signals correctly use 25% |

**Key finding:** High-confidence signals (7-8/8 swings) have dramatically lower DD contribution than low-confidence signals (6/8). However, confidence sizing improved 3yr (+57%) but **worsened 6yr DD (32.1% vs 25.5%) and 1.25yr DD (9.5% vs 4.3%)**. Rejected because it didn't improve ALL periods simultaneously. The ROC parabolic filter (fixK) achieved better balanced improvements.

#### Target Assessment (confidence sizing approach)
- **DD < 10% (3yr): ACHIEVED** — 9.6% (was 10.0% with fixJ)
- **Sharpe > 1.0 (3yr): NOT ACHIEVABLE** — 0.806 is best at DD<10%. Strategy's 41% WR / 2.1 P/L profile means annual std dev scales proportionally with return.
- **WR > 50% (3yr): NOT ACHIEVABLE** — partial TP gets to 48% but destroys P/L ratio (1.44 vs 2.10), making Sharpe worse.
- **All-period improvement: NOT ACHIEVED** — confidence sizing sacrificed 6yr DD and 1.25yr DD. Approach abandoned in favor of ROC filter (fixK).

### fixF vs fixC Comparison

| Metric | fixC 1.25yr | fixF 1.25yr | fixC 3yr | fixF 3yr | fixC 6yr | fixF 6yr |
|--------|-----------|-----------|---------|---------|---------|---------|
| Net Profit | +18.08% | +15.84% | +29.89% | **+34.19%** | +34.41% | **+36.28%** |
| Sharpe | 1.167 | 0.993 | 0.314 | **0.493** | 0.199 | **0.234** |
| DD | **3.6%** | 4.3% | 10.5% | **10.2%** | **19.3%** | 28.4% |
| Orders | 339 | 303 | 1305 | **1145** | 3381 | **2897** |
| Win Rate | 59% | 59% | 37% | **40%** | 53% | 54% |
| Fees | ₮429 | **₮385** | ₮1,648 | **₮1,519** | ₮4,211 | **₮3,854** |

**fixF is better on 3yr** (primary target period): +14% more return, +57% better Sharpe, fewer trades, lower fees.
**fixC is better on 1.25yr** (higher return, lower DD) and **6yr DD** (19.3% vs 28.4%).
**6yr DD concern:** fixF's 28.4% DD comes from the 2020-2021 extreme BTC moves (7k→60k→30k). Both versions are profitable on 6yr.

---

## Previous Best (Spot): fix25 (+12.93% net profit, 1.25yr only)

| Parameter | Value |
|-----------|-------|
| swing_len | 50 |
| swing_lookback | last 8 swings (was 6) |
| bullish/bearish threshold | >=6 out of 8 (was >=5 out of 6) |
| ATR SL/TP mult | 8.0 / 32.0 |
| min_sl/tp_pct | 2.5% / 10% |
| trail | activate 1.5%, distance 1% |
| position | **30%** (was 25%) |
| pending_window | 240 bars (4hr) |
| cooldown | 480 bars (8hr) |
| **opposite_cancels** | opposite swing signal cancels pending |
| **price_confirms** | price > last swing low (long) / price < last swing high (short) |

**Stats:** 582 orders | 41% win | 0.49% avg win | -0.32% avg loss | P/L 1.52 | 8.0% DD | $1,865 fees | Sharpe 0.417

### What changed from fix10 to fix25 (two improvements stacked):
1. **Opposite signal cancels pending (fix18):** +4.69% → +8.48%. Prevents entering on stale bullish signals after market reverses. High-leverage December fix.
2. **8 swings with bullish>=6 (fix23):** +8.48% → +10.76%. Stronger trend confirmation using more swing history. P/L ratio improved from 1.45 to 1.52.
3. **Position 30% (fix25):** +10.76% → +12.93%. Slightly larger position captures more from improved signal quality. DD went from 6.7% to 8.0%.

---

## Previous Best: fix10 (+4.69% net profit)

| Parameter | Value |
|-----------|-------|
| swing_len | 50 |
| swing_lookback | last 6 swings |
| bullish/bearish threshold | >=5 out of 6 |
| position | 25% |
| **price_confirms** | price > last swing low (long) / price < last swing high (short) |

**Stats:** 576 orders | 41% win | 0.39% avg win | -0.28% avg loss | P/L 1.39 | 7.2% DD | $1,522 fees

---

## All Fixes Tested (Session 2 — from fix10 baseline)

### IMPROVED (kept, stacked into fix25)
| Fix | Change | Result | Why it works |
|-----|--------|--------|-------------|
| fix18 | Opposite swing signal cancels pending | **+8.48%** (was +4.69%) | Prevents entering long after bearish signal fires — blocks stale entries during reversals |
| fix23 | 8 swings, bullish>=6 threshold (was 6 swings, >=5) | **+10.76%** (on top of fix18) | More swing history = stronger trend confirmation, fewer false signals |
| fix25 | Position 30% (was 25%) | **+12.93%** (on top of fix23) | Larger position capitalizes on improved signal quality |

### Donchian Kill Switch (no effect)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix14 | Donchian(20) cancel pending + exit on breakdown | +4.69% (no change) | 20-bar DCH on 1-min too narrow — never triggers |
| fix15 | Donchian(120) cancel pending + exit on breakdown | +4.69% (no change) | DCH includes current bar — price can't break below its own recent low |

### ADX Regime Filter (all worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix16 | ADX(14) > 20 entry gate | +2.37% | Blocks good trades in moderate-trend environments |
| fix16b | ADX(14) > 25 entry gate | -5.02% | Too strict, blocks most entries |

### Chandelier Exit (all worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix17 | Chandelier 3x ATR, no TP | -29.18% | ATR(500) on 1-min ≈ $50-100, so 3x = $150-300 (0.2%) — way too tight |
| fix17b | Chandelier 15x ATR, no TP | -21.51% | Still too tight without TP — many trades reverse before meaningful profit |

### EMA Regime Gate (worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix19 | EMA200 regime gate (longs above, shorts below) + fix18 | -8.20% | Blocks too many good pullback entries |

### MACD Crossover (worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix21 | MACD(12,26,9) confirmation for entries + fix18 | -8.83% | Conflicts with RSI pullback — RSI says buy dip, MACD says don't (momentum down) |

### RSI Period Variants (all worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix22 | RSI(7) instead of RSI(14) + fix18+fix23 | +7.08% | Faster RSI is noisier, more false pullback signals |
| fix22b | RSI(21) instead of RSI(14) + fix18+fix23 | -7.06% | Slower RSI misses pullback entries, too late |

### Swing Threshold Variants (worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix23b | 8 swings, bullish>=7 (stricter) + fix18 | -1.79% | Too strict, blocks valid trend signals |

### Pending Window (worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix24 | pending_window 180 bars (3hr, was 4hr) + fix18+fix23 | +7.23% | Shorter window misses valid RSI pullback entries |

### Position Size Variants
| Fix | Change | Result | Notes |
|-----|--------|--------|-------|
| fix25 | 30% position + fix18+fix23 | **+12.93%**, 8.0% DD | **Best risk/reward balance — kept** |
| fix25b | 35% position + fix18+fix23 | +15.09%, 9.2% DD | Higher return but proportionally higher DD and fees ($2,200) |

### Cooldown (worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix26 | 6hr cooldown (was 8hr) + fix18+fix23+30% | +3.51% | More trades = more fee drag, worse quality signals |

---

## All Fixes Tested (Session 1 — from v19 baseline)

### IMPROVED (kept)
| Fix | Change | Result | Why it works |
|-----|--------|--------|-------------|
| fix10 | Price-confirms-trend filter | **+4.69%** (was +2.14%) | Prevents entering long when price broke below last swing low |

### Entry Filters Tested (all worse)
| Fix | Change | Result | Why it failed |
|-----|--------|--------|--------------|
| fix11 | ATR volatility filter (short ATR < 1.5x long ATR) | +0.47% | Too aggressive, blocks good volatile moves too |
| fix12 | Last swing confirms (block if last swing is LH for long) | -7.38% | Too restrictive, blocks valid pullback entries |
| fix13 | Price range filter (price in upper half for long) | -8.33% | Contradicts RSI pullback logic — we WANT low entries |

### Signal Thresholds (all worse)
| Fix | Change | Result |
|-----|--------|--------|
| fix1 | bullish>=6 (6 swings) | -7.97% |
| fix5 | hh>=3 | -4.19% |
| fix6 | No plateau trades | -4.54% |
| fix7 | bullish>=4 | +1.60% |

### SL/TP/Trail (all worse or same)
| Fix | Change | Result |
|-----|--------|--------|
| fix2 | SL 3% | +1.56% |
| fix8 | TP 12% | +1.47% |
| fix4 | ATR period 300 | +2.14% (same) |
| earlier | trail 1%/0.7% | -13.28% |
| earlier | trail 2%/1.2% + swing70 | -6.28% |
| fix20 | trail activate 2%, distance 1.5% + fix18 | -5.18% |

### Cooldown/Risk (all worse)
| Fix | Change | Result |
|-----|--------|--------|
| fix9 | 12hr cooldown | -8.38% |
| earlier | 6hr cooldown (session 1) | -13.28% |
| v28 | Drawdown protection | -6.38% |
| fix3 | drift 2% | -1.60% |
| earlier | RSI<35/>65 + pos 35% | -8.39% |

---

## Robustness Tests — All Versions Across Time Periods

### 3-Year Test (2023-01-01 to 2026-04-01)

| Version | 1.25yr (2025-2026) | 3yr (2023-2026) | 3yr DD | 3yr Orders | 3yr Fees |
|---------|-------------------|-----------------|--------|-----------|----------|
| v19 (baseline) | +2.14% | **-16.10%** | 23.4% | 1,512 | $3,458 |
| fix10 (price-confirms) | +4.69% | **-12.43%** | 22.7% | 1,498 | $3,479 |
| fix18 (+ opposite cancel) | +8.48% | **-12.50%** | 25.5% | 1,488 | $3,378 |
| **fix23 (+ 8 swings, 25%)** | +10.76% | **-11.59%** | 24.9% | 1,550 | $3,462 |
| fix25 (+ 30% pos) | +12.93% | **-14.01%** | 29.1% | 1,550 | $4,061 |

### 6-Year Test (2020-01-01 to 2026-04-01)

| Version | 1.25yr (2025-2026) | 6yr (2020-2026) | 6yr DD | 6yr Orders | 6yr Fees |
|---------|-------------------|-----------------|--------|-----------|----------|
| v19 (baseline) | +2.14% | **-46.42%** | 48.2% | 3,498 | $6,214 |
| fix10 (price-confirms) | +4.69% | **-45.33%** | 48.5% | 3,462 | $6,133 |
| fix18 (+ opposite cancel) | +8.48% | **-45.93%** | 50.9% | 3,446 | $5,978 |
| **fix23 (+ 8 swings, 25%)** | +10.76% | **-33.28%** | 39.7% | 3,576 | $6,711 |
| fix25 (+ 30% pos) | +12.93% | **-38.89%** | 45.9% | 3,576 | $7,595 |

### Key Findings (Updated after fixC)

1. **fixC is profitable across ALL time periods** — +18.08% (1.25yr), +29.89% (3yr), +34.41% (6yr)
2. **Spot versions lose on longer periods** — fee drag ($3,400-$4,000 on $10k) consumed the gross edge
3. **Three changes flipped -38.89% to +34.41% (6yr):** futures fees, ADX<25 filter, RSI 45/55
4. **Strategy was gross-profitable all along** — the edge was hidden behind spot fees eating 150% of it
5. **ADX<25 prevents trading the worst regime** — fast rallies/crashes in 2023 H2 and 2024 H2
6. **RSI 45/55 catches pullbacks earlier** — RSI 40/60 waited too long, entries arrived near reversals
7. **Spot is only viable short-term** — fixC on spot: +10.46% (1.25yr), -15.75% (3yr), -51.74% (6yr)

---

## Key Insights
1. **Fee regime is the #1 lever** — spot fees (0.1%/0.1%) consumed 150% of gross edge; futures (0.02%/0.04%) preserved it
2. **Opposite signal cancels pending** — nearly doubled profit (+4.69% → +8.48%), prevents stale entries
3. **ADX inversion (trade low ADX, skip high)** — matches the strategy's true edge regime (range-bound, not trending)
4. **RSI range shift (45/55 vs 40/60)** — consistent with RSI "range shift" behavior: uptrend RSI oscillates 40-90, so <40 is already too deep
5. **8-swing lookback with >=6 threshold** — more history = stronger trend confirmation without being too strict
6. **Confidence-based sizing improves 3yr but not all periods** — 85%/25% beats flat 30% on 3yr (+57%, DD 9.6%) but worsens 6yr DD (32.1% vs 25.5%) and 1.25yr DD (9.5% vs 4.3%). Rejected for unbalanced improvement.
7. **Daily ROC parabolic filter is the most impactful change in strategy history** — 20-day price ROC > 20% blocks counter-trend entries during extreme trends. 6yr: +42.64% → +112.53% (+164%), DD 25.5% → 19.2%, Sharpe 0.310 → 0.921. Only ~200 trades blocked but they were the worst losers.
8. **2020-2022 losses were counter-trend entries in parabolic markets** — 2022 was -13.65% (longs against bear), 2021 near-flat with 15% DD (shorts against bull). ROC filter precisely targets these without affecting moderate trends.
9. **Trend-confirmation filters (EMA, MACD) conflict with pullback logic** — momentum says "don't buy dip" while RSI says "buy dip"
10. **Chandelier Exit failed due to ATR scale mismatch** — ATR(500) on 1-min gives tiny values, exits too tight
11. **RSI(14) is optimal** — RSI(7) too noisy, RSI(21) too slow
12. **ETH doesn't work** — -5.58% with same params on spot
13. **Shock filter is the biggest single improvement** — pausing entries after extreme 1m moves (+9% return, +53% Sharpe). The strategy's weakness was entering during volatility spikes where swing structure is unreliable.
14. **SMC BOS/CHoCH invalidation hurts a range strategy** — BOS cancels signals when price breaks swing levels, but in a range, price oscillating around swing levels is normal behavior
15. **15m ADX consolidation doesn't help** — either too loose (ADX<25, +13.59%) or too restrictive (ADX<20, +9.17%). The 1m ADX<20 gate is better calibrated for this strategy.
16. **Liquidity sweep invalidation is neutral** — didn't add or remove significant value (-0.9% return vs shock alone)
17. **Edge survives 1bps slippage across all periods (fixK)** — +22.27% (1.25yr), +69.15% (3yr), +95.82% (6yr) with ConstantSlippageModel(0.0001). Slippage cost scales with trade count: ~1% (1.25yr, 286 orders), ~5.5% (3yr, 1098 orders), ~17% (6yr, 2670 orders). Slippage now active in codebase by default.
18. **Vol-scaling on 1-min ATR is a no-op** — BTC's ATRP (~0.1-0.2%) is always below any reasonable target, so scale factor always hits the cap. It's just flat sizing in disguise.
19. **Exit changes destroy the asymmetric edge** — the strategy's P/L ratio of 2.02 relies on rare big winners. Tighter trails, tighter TP, breakeven stops, time exits, and partial TP all cut these winners.
20. **WR > 50% is structurally incompatible** — partial TP gets WR to 48% but P/L drops to 1.44, net effect is worse Sharpe. The strategy's edge IS low WR + high P/L.

## Why fixC Works Together (Research Analysis)
- **Fee reduction** preserves gross edge that was always there (+23% gross over 3yr on spot)
- **ADX<25** routes trades to range regime where swing detection is accurate; skips strong trends where it lags
- **RSI 45/55** aligns with RSI range-shift theory: in uptrends RSI uses ~40 as support, so <40 is unnecessarily deep
- These three changes are **mechanically complementary**: lower fees reduce churn penalty, ADX removes the worst regime, RSI improves entry timing in the remaining regime

## Research-Backed Roadmap (What to Try Next)

### High Priority
1. **Add conservative slippage model** — QC defaults to NullSlippageModel; add constant slippage before scaling to validate edge survives realistic execution
2. **Maker-style entries (PostOnly orders)** — Binance supports PostOnly to ensure limit fills; further reduces fees from 0.04% taker to 0.02% maker on entries
3. **Directional-change (DC) swing detection** — replace fixed swing_len=50 with event-based swings that adapt to volatility; academically motivated, reduces time-based lag during fast moves

### Medium Priority
4. **Two-mode system (range + trend)** — current fixC goes flat when ADX≥25; optionally add a simple trend-follow module (e.g., time-series momentum) for strong-trend regimes to monetize skipped periods
5. **Multi-coin expansion (time-series per coin)** — run fixC independently per symbol with per-coin state; start with most liquid futures (BTC, ETH); scale position by inverse volatility; cap concurrent positions at 3-5
6. **Walk-forward validation** — train/test rolling windows to estimate overfitting risk (Bailey et al. backtest overfitting framework)

### Lower Priority
7. **Time-of-day/weekend filter** — crypto liquidity varies; low-liquidity hours may produce worse fills
8. **Cross-sectional momentum** — academic evidence in crypto is weaker than time-series; defer until time-series per-coin is validated
9. **Different swing_len values** — test swing_len 30-70 with 8-swing lookback under DC framework

### What NOT to Try (Research-Confirmed Dead Ends)
- ADX > threshold gates — structurally mismatched with pullback entry logic
- EMA/MACD entry confirmation — conflicts with "buy the dip" approach
- Chandelier on 1-min ATR — scale mismatch makes stops too tight
- Cross-sectional ranking for crypto — evidence is weak under realistic costs
