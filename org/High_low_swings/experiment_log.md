# High/Low Swings Strategy - Experiment Log

## Strategy: Jigsaw Swing Trend-Following on BTCUSDT 1-min
**Asset:** BTCUSDT | **Resolution:** 1-min | **Period:** 2025-01-01 to 2026-04-01 | **Cash:** $10,000

## Core Logic
1. Detect swing highs/lows on 1-min candles using `swing_len` window
2. Classify each swing as HH/LH (for highs) or LL/HL (for lows)
3. Count bullish (HH+HL) vs bearish (LL+LH) in last 6 swings
4. Calculate angles between consecutive swing points to detect plateauing
5. If NOT plateauing: bullish>=5 (hh>=2, hl>=1) -> long; bearish>=5 (ll>=2, lh>=1) -> short
6. If plateauing + drift > 1% -> long; drift < -1% -> short
7. Signal goes to pending queue, wait for RSI pullback to enter (RSI<40 for long, RSI>60 for short)
8. **NEW: Price-confirms-trend filter** — for longs, price must be above last swing low; for shorts, below last swing high
9. ATR-based SL/TP with percentage floor minimums
10. Trailing stop locks in profits after activation threshold

---

## CURRENT BEST: fix10 (+5.12% net profit) - CONFIRMED

| Parameter | Value |
|-----------|-------|
| swing_len | 50 |
| lookback | 800 |
| max_swings | 12 |
| ATR period | 500 |
| RSI period | 14 |
| ATR SL mult | 8.0 |
| ATR TP mult | 32.0 |
| min_sl_pct | 2.5% |
| min_tp_pct | 10% |
| trail_activate | 1.5% |
| trail_distance | 1% |
| position_pct | 25% |
| pending_window | 240 bars (4hr) |
| cooldown | 480 bars (8hr) |
| RSI entry | <40 long, >60 short |
| **price_confirms** | **long: price > last swing low; short: price < last swing high** |

**Stats:** 575 orders | 41% win | 0.39% avg win | -0.28% avg loss | P/L 1.40 | 7.2% DD | $1,520 fees
**Backtest ID:** aa0318e0d0d5109fefbe50a462e3ec6e

---

## Monthly Equity Analysis

### v19 (before price-confirms-trend)
| Period End | Equity | Net Return | Period Return |
|-----------|--------|-----------|---------------|
| Sep 2025 | $10,860 | +8.60% | +8.60% (Jan-Sep) |
| Oct 2025 | $10,587 | +5.87% | -2.73% (Oct) |
| Nov 2025 | $10,900 | +9.00% | +3.13% (Nov) |
| Dec 2025 | $10,285 | +2.85% | **-6.15% (Dec)** |
| Feb 2026 | $10,569 | +5.69% | +2.84% (Jan-Feb) |
| Apr 2026 | $10,214 | +2.14% | -3.55% (Mar) |

### fix10 (with price-confirms-trend)
| Period End | Equity | Net Return | Dec Loss |
|-----------|--------|-----------|----------|
| Dec 2025 | $10,475 | +4.75% | **~-4.25%** (improved from -6.15%) |
| Apr 2026 | $10,512 | +5.12% | — |

**Key improvement:** December drawdown reduced from -6.15% to ~-4.25% (saved ~2%).

---

## Previous Best: v19 (+2.14%)
- Same params as fix10 but WITHOUT price-confirms-trend filter
- **Stats:** 577 orders | 41% win | 0.38% avg win | -0.28% avg loss | P/L 1.36 | 8.3% DD | $1,504 fees

---

## All Parameter Changes Tested (from v19 baseline +2.14%)

### IMPROVED: Price-Confirms-Trend Filter (fix10) -> +5.12%
- For longs: current price must be above last swing low (uptrend intact)
- For shorts: current price must be below last swing high (downtrend intact)
- **Why it works:** Prevents entering long when price has already broken below support (trend broken). Specifically helps during December 2025 crash where swing structure still showed bullish but price had already collapsed

### Signal Strength / Trend Filters
| Fix | Change | Result | Delta |
|-----|--------|--------|-------|
| fix1 | bullish>=6 (was >=5) | -7.97% | -10.1% — too strict |
| fix5 | hh>=3 (was >=2) | -4.19% | -6.3% — too strict on consecutive HH |
| fix6 | Disable plateau trades | -4.54% | -6.7% — plateau trades are net positive |
| fix7 | bullish>=4 (was >=5) | +1.60% | -0.5% — more trades, more fees |

### SL/TP Parameters
| Fix | Change | Result | Delta |
|-----|--------|--------|-------|
| fix2 | min_sl_pct=3% (was 2.5%) | +1.56% | -0.6% |
| fix8 | min_tp_pct=12% (was 10%) | +1.47% | -0.7% |
| fix4 | ATR period=300 (was 500) | +2.14% | 0% — floors dominate |

### Trailing Stop
| Fix | Change | Result | Delta |
|-----|--------|--------|-------|
| earlier | trail 1%/0.7% | -13.28% | -15.4% — cuts winners |
| earlier | trail 2%/1.2% | -6.28%* | *with swing70 |

### Cooldown
| Fix | Change | Result | Delta |
|-----|--------|--------|-------|
| fix9 | 12hr (was 8hr) | -8.38% | -10.5% — misses signals |
| earlier | 6hr (was 8hr) | -13.28% | -15.4% — noise trades |

### Risk Management
| Fix | Change | Result | Delta |
|-----|--------|--------|-------|
| v28 | Drawdown protection + loss streak breaker | -6.38% | -8.5% — prevents recovery |
| fix3 | drift threshold 2% (was 1%) | -1.60% | -3.7% |

### Other
| Fix | Change | Result | Delta |
|-----|--------|--------|-------|
| earlier | RSI<35/>65 + pos 35% | -8.39% | -10.5% |
| earlier | swing_len=70 | -6.28% | -8.4% |
| earlier | EMA filter | +1.17% | -1.0% |

---

## Key Insights
1. **Price-confirms-trend is the biggest single improvement** (+3% net, reduced Dec DD by ~2%)
2. **v19 params are otherwise a local optimum** — all other single-param changes degraded
3. **December 2025 is the problem month** — BTC crash after Nov rally breaks swing patterns
4. **Plateau trades are valuable** — removing costs -4.54%
5. **ATR floors dominate** — ATR period irrelevant
6. **Fee drag is ~15% of gross** — $1,520 fees on ~$2,060 gross profit

## What Has NOT Been Tried Yet
- MACD crossover as additional entry timing confirmation
- Multi-timeframe analysis (5-min or 15-min swing confirmation)
- Asymmetric SL/TP by direction (longs vs shorts)
- Time-of-day filter (avoid low-liquidity hours)
- ATR volatility regime filter (skip when ATR > 1.5x average)
- Different RSI period (7 or 21 instead of 14)
- Analyzing last 8 swings instead of 6
- Using swing amplitude to weight signals
