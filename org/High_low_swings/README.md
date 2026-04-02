# High Low Swings

Short-term `BTCUSDT` swing strategy for QuantConnect. It uses market structure to detect direction, then waits for a pullback before entering. The current best tested version is the deeper pullback setup (`v18`), which produced a modest positive result in backtesting.

## Best Result

- Period: `2025-01-01` to `2026-04-01`
- Net profit: `+1.17%`
- End equity: `$10,116.73`
- Max drawdown: `10.0%`
- Total orders: `149`
- Win rate: `14%`
- Average win / loss: `+2.06% / -0.34%`
- Profit-loss ratio: `6.01`
- Fees: `$387.02`

## Core Logic

- Market: `BTCUSDT` on `1-minute` candles
- Swing detection: finds local swing highs and lows using a `50` bar window
- Structure filter: classifies swings as `HH`, `HL`, `LH`, `LL`
- Trend signal:
  - Long bias when recent swings show strong bullish structure
  - Short bias when recent swings show strong bearish structure
  - Plateauing structure can still trigger if drift remains directional
- Entry style: do not enter immediately on signal; wait for a pullback

## Entry Rules

- Long entry:
  - Bullish swing signal is active
  - `RSI(14) < 40`
  - Price stays above `EMA(200)`
- Short entry:
  - Bearish swing signal is active
  - `RSI(14) > 60`
  - Price stays below `EMA(200)`
- Entry window: signal stays valid for up to `4 hours`
- Cooldown: at least `8 hours` between swing signals

## Exit Rules

- Uses dynamic `ATR(500)` stop-loss and take-profit
- Stop-loss distance:
  - `8 x ATR`, with a minimum floor of `2.5%`
- Take-profit distance:
  - `32 x ATR`, with a minimum floor of `10%`
- Position closes automatically when stop or target is reached

## Risk Management

- Position size: `25%` of portfolio per trade
- Built for low trade frequency to reduce fees
- Pullback entries are used to improve reward-to-risk instead of chasing breakouts
- Main strength so far: large winners relative to losers

## Notes

- This is still an experimental strategy.
- Performance is only slightly positive, so more validation and out-of-sample testing are recommended before live use.
