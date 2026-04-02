# QuantConnect

Collection of QuantConnect strategy experiments and research projects.

## Featured Strategy

### `org/High_low_swings`

Short-term `BTCUSDT` swing strategy built on `1-minute` candles. It detects directional bias from market structure using swing highs/lows and `HH`, `HL`, `LH`, `LL` classification, then waits for a pullback before entering instead of chasing the initial move.

Current simple logic:

- Detect bullish or bearish swing structure
- Set a pending signal instead of entering immediately
- Enter long when `RSI(14) < 40` and price is above `EMA(200)`
- Enter short when `RSI(14) > 60` and price is below `EMA(200)`
- Keep the signal valid for up to `4 hours`
- Enforce an `8-hour` cooldown between swing signals

Exit and risk management:

- Position size: `25%` of portfolio
- Stop-loss: `max(8 x ATR(500), 2.5%)`
- Take-profit: `max(32 x ATR(500), 10%)`
- Trade closes automatically on stop-loss or take-profit
- Lower trade frequency is used to reduce fee drag

Best observed backtest result for the current simple version:

- Period: `2025-01-01` to `2026-04-01`
- Net profit: `+1.17%`
- End equity: `$10,116.73`
- Max drawdown: `10.0%`
- Orders: `149`
- Win rate: `14%`
- Average win / loss: `+2.06% / -0.34%`
- Profit-loss ratio: `6.01`
- Fees: `$387.02`

Notes:

- The strategy is currently only slightly profitable and still experimental.
- Main strength so far is strong reward-to-risk with relatively controlled drawdown.