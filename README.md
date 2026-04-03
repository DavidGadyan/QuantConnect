# QuantConnect

Collection of QuantConnect strategy experiments and research projects.

## Featured Strategy

### `org/High_low_swings`

Short-term `BTCUSDT` swing strategy built on `1-minute` candles. It detects directional bias from market structure using swing highs/lows and `HH`, `HL`, `LH`, `LL` classification, then waits for a pullback before entering instead of chasing the initial move.

**Best model:** `fixC` — Binance Futures + ADX range filter + RSI 45/55

#### Logic

1. Detect swing highs/lows using a `50-bar` confirmation window
2. Classify each swing as `HH`/`LH` (highs) or `LL`/`HL` (lows)
3. Count bullish (`HH + HL`) vs bearish (`LL + LH`) in the last `8` swings
4. If not plateauing: `bullish >= 6` (with `hh >= 2`, `hl >= 1`) sets a pending long; mirror for short
5. If plateauing and drift `> 1%` sets pending long; drift `< -1%` sets pending short
6. If an opposite swing signal fires, cancel the existing pending signal
7. Only enter when `ADX(28) < 25` (range-bound conditions, skip strong trends)
8. Wait for RSI pullback to enter: long when `RSI(14) < 45`, short when `RSI(14) > 55`
9. Confirm trend intact before entry: price must be above last swing low (long) or below last swing high (short)
10. Pending signal expires after `4 hours`; `8-hour` cooldown between swing signals

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
| ADX filter | `ADX(28) < 25` (trade only in range) |
| position size | `30%` |
| pending window | `240` bars (4 hr) |
| cooldown | `480` bars (8 hr) |
| SL | `max(8 x ATR(500), 2.5%)` |
| TP | `max(32 x ATR(500), 10%)` |
| trailing stop | activate at `1.5%` profit, trail at `1%` |

#### Backtest Results (fixC — Futures)

Profitable across all time periods tested:

| Period | Net Profit | Drawdown | Orders | Fees | Win Rate | Sharpe |
|--------|-----------|----------|--------|------|----------|--------|
| 1.25yr (2025-2026) | `+18.08%` | `3.6%` | `339` | `₮429` | `59%` | `1.167` |
| 3yr (2023-2026) | `+29.89%` | `10.5%` | `1,305` | `₮1,648` | `37%` | `0.314` |
| 6yr (2020-2026) | `+34.41%` | `19.3%` | `3,381` | `₮4,211` | `53%` | `0.199` |

#### Spot Margin Results (fixC — same logic, Binance Spot)

Same logic on spot with higher fees (0.1%/0.1% vs 0.02%/0.04%):

| Period | Net Profit | Drawdown | Fees |
|--------|-----------|----------|------|
| 1.25yr (2025-2026) | `+10.46%` | `10.1%` | `$1,833` |
| 3yr (2023-2026) | `-15.75%` | `31.0%` | `$4,029` |
| 6yr (2020-2026) | `-51.74%` | `56.8%` | `$7,014` |

Spot is profitable only on the 1.25yr period. Futures is required for multi-year profitability.

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
| **fixC** | **+ RSI 45/55 (was 40/60)** | **`+18.08%`** | **`+29.89%`** |

Over 35 parameter changes tested. See `org/High_low_swings/experiment_log.md` for full results.

#### Key Insights

- The strategy was **gross-profitable all along** — fees consumed 150% of edge on spot
- Switching to **Binance Futures** cuts fees by ~60% (0.02%/0.04% vs 0.10%/0.10%)
- **ADX < 25 filter** prevents trading during fast rallies/crashes where swing detection lags
- **RSI 45/55** catches pullbacks earlier — RSI 40/60 waited too long, entries arrived near reversals
- Strategy does not work on `ETHUSDT` (`-5.58%` with same params on spot)