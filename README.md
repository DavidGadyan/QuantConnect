# QuantConnect

Collection of QuantConnect strategy experiments and research projects.

## Featured Strategy

### `org/High_low_swings`

Short-term `BTCUSDT` swing strategy built on `1-minute` candles. It detects directional bias from market structure using swing highs/lows and `HH`, `HL`, `LH`, `LL` classification, then waits for a pullback before entering instead of chasing the initial move.

**Best model:** `fixK` — Binance Futures + ADX<20 + RSI 45/55 + 12hr cooldown + enhanced plateau + shock filter + daily ROC parabolic filter

#### Logic

1. Detect swing highs/lows using a `50-bar` confirmation window
2. Classify each swing as `HH`/`LH` (highs) or `LL`/`HL` (lows)
3. Count bullish (`HH + HL`) vs bearish (`LL + LH`) in the last `8` swings
4. If not plateauing: `bullish >= 6` (with `hh >= 2`, `hl >= 1`) sets a pending long; mirror for short
5. If plateauing and drift `> 1%` sets pending long; drift `< -1%` sets pending short
6. If an opposite swing signal fires, cancel the existing pending signal
7. Only enter when `ADX(28) < 20` (deep range-bound conditions, skip trends)
8. **Shock filter:** pause entries for `30 minutes` after extreme 1-min moves (`> 4σ` rolling stdev)
9. **ROC parabolic filter:** block counter-trend entries when 20-day price ROC > `20%` (don't short parabolic rallies or long parabolic crashes)
10. Wait for RSI pullback to enter: long when `RSI(14) < 45`, short when `RSI(14) > 55`
11. Confirm trend intact before entry: price must be above last swing low (long) or below last swing high (short)
12. Pending signal expires after `4 hours`; `12-hour` cooldown between swing signals

#### Configuration

| Parameter | Value |
|-----------|-------|
| venue | Binance Futures (`BTCUSDT` perpetual) |
| account currency | `USDT` |
| swing_len | `50` |
| swing lookback | last `8` swings |
| bullish/bearish threshold | `>= 6` out of 8 |
| RSI period | `14` |
| RSI entry | `< 45` long / `> 55` short |
| ADX filter | `ADX(28) < 20` (trade only in deep range) |
| position size | `30%` |
| pending window | `240` bars (4 hr) |
| cooldown | `720` bars (12 hr) |
| SL | `max(8 x ATR(500), 2.5%)` |
| TP | `max(32 x ATR(500), 10%)` |
| trailing stop | activate at `1.5%` profit, trail at `1%` |
| shock filter | pause `30` bars after `abs(1m return) > 4σ` (120-bar rolling stdev) |
| ROC parabolic filter | block counter-trend entries when 20-day price `ROC > 20%` |

#### Backtest Results (fixK — Futures)

Profitable across all time periods tested:

| Period | Net Profit | CAGR | Drawdown | Orders | Fees | Win Rate | P/L Ratio | Sharpe | Sortino | PSR |
|--------|-----------|------|----------|--------|------|----------|-----------|--------|---------|-----|
| 1.25yr (2025-2026) | `+23.36%` | `18.30%` | `4.3%` | `286` | `₮377` | `62%` | `1.10` | `1.747` | `2.564` | `94.1%` |
| 3yr (2023-2026) | `+74.69%` | `18.71%` | `6.4%` | `1,098` | `₮1,759` | `42%` | `2.27` | `1.277` | `2.565` | `93.5%` |
| 6yr (2020-2026) | `+112.53%` | `12.81%` | `19.2%` | `2,670` | `₮4,447` | `56%` | `1.00` | `0.921` | `1.509` | `64.8%` |

#### With Realistic Slippage (1bps `ConstantSlippageModel`)

| Period | Net Profit | CAGR | Drawdown | Win Rate | P/L Ratio | Sharpe | Sortino | PSR |
|--------|-----------|------|----------|----------|-----------|--------|---------|-----|
| 1.25yr (2025-2026) | `+22.27%` | `17.47%` | `4.4%` | `62%` | `1.08` | `1.636` | `2.394` | `92.5%` |
| 3yr (2023-2026) | `+69.15%` | `17.54%` | `6.8%` | `42%` | `2.20` | `1.165` | `2.364` | `89.9%` |
| 6yr (2020-2026) | `+95.82%` | `11.34%` | `20.9%` | `56%` | `0.98` | `0.790` | `1.292` | `52.2%` |

Slippage cost: ~1% (1.25yr), ~5.5% (3yr), ~17% (6yr). Edge survives across all periods. Slippage model is active in the codebase by default.

#### Improvement History

| Version | Change | 1.25yr | 3yr |
|---------|--------|--------|-----|
| v19 (baseline) | Original swing + RSI pullback (spot) | `+2.14%` | `-16.10%` |
| fix10 | Added price-confirms-trend filter | `+4.69%` | `-12.43%` |
| fix18 | Opposite signal cancels pending | `+8.48%` | `-12.50%` |
| fix23 | 8-swing lookback, threshold >= 6 | `+10.76%` | `-11.59%` |
| fix25 | Position size 30% | `+12.93%` | `-14.01%` |
| fixA | Switch to Binance Futures | — | `-5.36%` |
| fixB | + ADX(28) < 25 range filter | — | `-2.07%` |
| fixC | + RSI 45/55 (was 40/60) | `+18.08%` | `+29.89%` |
| fixF | ADX<20 + 12hr cooldown | `+15.84%` | `+34.19%` |
| fixI | + Enhanced plateau detection | — | `+34.54%` |
| fixJ | + Shock/jump filter (4σ, 30-bar pause) | `+21.08%` | `+43.54%` |
| **fixK** | **+ Daily ROC parabolic filter (20-day ROC > 20%)** | **`+23.36%`** | **`+74.69%`** |

Over 50 parameter changes tested. See `org/High_low_swings/experiment_log.md` for full results.

#### Key Insights

- **Daily ROC parabolic filter is the biggest single improvement** — 6yr return +42.64% → +112.53% (+164%), Sharpe 0.310 → 0.921 by blocking counter-trend entries during extreme trends
- **Shock filter is the second biggest improvement** — +9% return, +53% Sharpe by pausing entries during vol spikes
- The strategy was **gross-profitable all along** — fees consumed 150% of edge on spot
- Switching to **Binance Futures** cuts fees by ~60% (0.02%/0.04% vs 0.10%/0.10%)
- **ADX < 20** (tighter than 25) filters borderline entries during ADX oscillations within rallies
- **12hr cooldown** reduces overtrading — Q4 2023 had 121 orders in 3 months, mostly noise
- **RSI 45/55** catches pullbacks earlier — RSI 40/60 waited too long, entries arrived near reversals
- **Edge survives 1bps slippage across all periods** — +22.27% (1.25yr), +69.15% (3yr), +95.82% (6yr) with `ConstantSlippageModel(0.0001)` active by default
- **SMC BOS/CHoCH/liquidity sweeps didn't help** — range strategy needs price near swing levels; invalidation filters cancel valid signals
- **Confidence-based sizing didn't improve all periods** — 85%/25% improved 3yr (+57%, DD 9.6%) but worsened 6yr DD (32.1%) and 1.25yr DD (9.5%)
- Strategy does not work on `ETHUSDT` (`-5.58%` with same params on spot)