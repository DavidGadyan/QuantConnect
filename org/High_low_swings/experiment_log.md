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
7. Pending signal -> wait for RSI pullback (RSI<40 long, >60 short)
8. **Price-confirms-trend:** for longs, price > last swing low; for shorts, price < last swing high
9. ATR-based SL/TP with 2.5%/10% floors. Trailing stop 1.5%/1%

---

## CURRENT BEST: fix25 (+12.93% net profit)

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

## Key Insights
1. **Opposite signal cancels pending is the biggest single improvement** — nearly doubled profit (+4.69% → +8.48%)
2. **8-swing lookback with >=6 threshold** — more swing history = better trend confirmation without being too strict
3. **Position sizing matters** — 30% is optimal balance of return vs drawdown
4. **Additional entry filters consistently hurt** — ADX, EMA, MACD all block good trades
5. **Chandelier Exit doesn't work with this ATR setup** — ATR(500) on 1-min gives tiny values, exits too tight
6. **RSI(14) is optimal** — faster/slower both degrade performance
7. **Fee drag ~16%** — $1,865 fees on ~$3,161 gross profit
8. **ETH doesn't work** — -5.58% with same params

## What Has NOT Been Tried Yet
- Multi-timeframe: confirm trend on 5-min or 15-min candles
- Time-of-day filter (weekend/low-liquidity hours)
- Longer ATR period for Chandelier (e.g. ATR on 5-min or 15-min resolution)
- Different swing_len values with 8-swing lookback
- Fee reduction via maker orders (limit orders instead of market)
