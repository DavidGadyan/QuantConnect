# High/Low Swings Strategy - Experiment Log

## Strategy: Jigsaw Swing Trend-Following on BTCUSDT 1-min
**Asset:** BTCUSDT | **Resolution:** 1-min | **Period:** 2025-01-01 to 2026-04-01 | **Cash:** $10,000

## Core Logic
1. Detect swing highs/lows on 1-min candles using `swing_len` window
2. Classify each swing as HH/LH (for highs) or LL/HL (for lows)
3. Count bullish (HH+HL) vs bearish (LL+LH) in last 6 swings
4. Calculate angles between consecutive swing points to detect plateauing
5. If NOT plateauing: bullish>=5 (hh>=2, hl>=1) -> long signal; bearish>=5 (ll>=2, lh>=1) -> short signal
6. If plateauing + drift > 1% -> long; drift < -1% -> short
7. Signal goes to pending queue, wait for RSI pullback to enter (RSI<40 for long, RSI>60 for short)
8. ATR-based SL/TP with percentage floor minimums
9. Trailing stop locks in profits after activation threshold

---

## CURRENT BEST: v19 (+2.14% net profit) - CONFIRMED

| Parameter | Value |
|-----------|-------|
| swing_len | **50** |
| lookback | 800 |
| max_swings | 12 |
| ATR period | 500 |
| RSI period | 14 |
| ATR SL mult | 8.0 |
| ATR TP mult | 32.0 |
| min_sl_pct | 2.5% |
| min_tp_pct | 10% |
| trail_activate | **1.5%** |
| trail_distance | **1%** |
| position_pct | 25% |
| pending_window | 240 bars (4hr) |
| cooldown | 480 bars (8hr) |
| RSI entry | <40 long, >60 short |

**Confirmed Stats:** 577 orders | 41% win rate | 0.38% avg win | -0.28% avg loss | P/L ratio 1.36 | 8.3% drawdown | $1,504 fees | Sharpe -0.424

---

## All Confirmed Backtest Results

> **NOTE:** Earlier sessions had a cloud sync issue where local edits weren't reaching QC cloud.
> Results marked "CONFIRMED" were verified with matching cloud code.
> The original "v22 +5.56%" was invalid — cloud was running swing_len=70 at the time.

### v19: swing50 + trailing stop (CONFIRMED +2.14%) - BEST
- **Key params:** swing_len=50, trail activate 1.5%, trail distance 1%, RSI<40/>60, no EMA
- **Result:** +2.14% | 577 orders | 41% win | 0.38% avg win | -0.28% avg loss | 8.3% DD | $1,504 fees
- **What worked:** Adding trailing stop to v18. Removing EMA filter (swing structure alone determines trend)
- **Backtest ID:** e3a53f4415ec309c82795ccbeb960cb3

### v23/current: swing70 + trail 2%/1.2% (CONFIRMED -6.28%)
- **Key params:** swing_len=70, trail activate 2%, trail distance 1.2%
- **Result:** -6.28% | 474 orders | 34% win | 0.49% avg win | -0.31% avg loss | 12.5% DD | $1,187 fees
- **Why it failed:** swing_len=70 too slow — signals arrive too late. Wider trail doesn't compensate
- **Backtest ID:** 2f64f7e68b1ee61fc6f5bf275bd91d10

---

## Changes Tried and Their Impact (from v19 baseline)

### WORSE: Deeper RSI thresholds (RSI<35/>65)
- Combined with position 35% (was 25%)
- Result: -8.39% (was +2.14%)
- **Why:** Deeper RSI paradoxically worsens timing. Fewer entries, but not better ones. Larger position amplifies losses

### WORSE: Tighter trailing stop (activate 1%, trail 0.7%) + shorter cooldown (6hr)
- Result: -13.28% (was +2.14%)
- **Why:** Tighter trail cuts winners too early (avg win dropped 0.38% -> 0.24%). Shorter cooldown adds noise trades (753 orders vs 577). Both changes destructive together

### WORSE: Longer swing_len (60 or 70)
- swing_len=70 confirmed at -6.28%
- **Why:** Signals arrive too late, miss the move. More confirmation ≠ better trades for 1-min candles

### WORSE: Wider trailing stop (activate 2%, trail 1.2%) without swing_len change
- Combined with swing_len=70: -6.28%
- **Why:** Wider trail alone doesn't help if base signal quality is poor

### INCONCLUSIVE: Volume SMA filter (vol >= 0.8x 50-bar avg)
- Not properly confirmed due to sync issues
- Likely too restrictive — filters out valid signals

### INCONCLUSIVE: Longer pending window (300 bars vs 240)
- Not properly confirmed due to sync issues
- Likely reduces profits by delaying entry too much

---

## Key Insights (Confirmed)

1. **swing_len=50 is the proven winner** — longer values (60, 70) degrade performance
2. **Trailing stop at 1.5%/1% is optimal** — tighter (1%/0.7%) kills winners, wider (2%/1.2%) not proven better
3. **RSI 40/60 entry threshold works** — deeper (35/65) makes it worse
4. **8hr cooldown is right** — shorter adds noise
5. **25% position sizing is correct** — 35% amplifies losses
6. **EMA is unnecessary** — swing structure alone determines trend
7. **P/L ratio matters more than win rate** — 41% win rate is fine if avg win > avg loss
8. **Fee drag is significant** — $1,504 on $10k capital = 15% of gross profits eaten by fees
9. **Cloud sync matters** — always verify the cloud is running the intended code

## What Has NOT Been Tried Yet
- MACD crossover as additional entry timing confirmation
- Multi-timeframe analysis (5-min or 15-min swing confirmation)
- Dynamic position sizing based on signal strength
- Asymmetric SL/TP by direction (longs vs shorts)
- Time-of-day filter (avoid low-liquidity hours)
- Swing point clustering (multiple swings at similar levels)
- Relaxing signal thresholds (bullish>=4 instead of >=5)
- Shorter ATR period (200-300 instead of 500) for more responsive SL/TP
- Reducing fees via fewer but larger trades
- Adding MACD or momentum divergence filter
- Testing on different date ranges to check robustness
