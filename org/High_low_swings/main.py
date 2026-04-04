# region imports
from AlgorithmImports import *
import math
# endregion


class SmartMoneyBTC(QCAlgorithm):
    """Jigsaw swing strategy on BTCUSDT 1-min candles.
    Swing structure detects trend. Waits for RSI pullback to enter.
    Trailing stop locks in profits. ATR-based dynamic SL/TP.
    """

    def initialize(self):
        self.set_start_date(2023, 1, 1)
        self.set_end_date(2026, 4, 1)
        self.set_account_currency("USDT")
        self.set_cash(10000)
        self.set_brokerage_model(BrokerageName.BINANCE_FUTURES, AccountType.MARGIN)

        self._symbol = self.add_crypto_future("BTCUSDT", Resolution.MINUTE, Market.BINANCE).symbol
        # 1bps constant slippage for realistic execution modeling
        self.securities[self._symbol].set_slippage_model(ConstantSlippageModel(0.0001))

        # swing params
        self._swing_len = 50
        self._lookback = 800
        self._max_swings = 12

        # indicators
        self._atr = self.atr(self._symbol, 500, resolution=Resolution.MINUTE)
        self._rsi_ind = self.rsi(self._symbol, 14, resolution=Resolution.MINUTE)

        # ADX — trade only in range (ADX < 20), longer period for smoothing
        self._adx_ind = self.adx(self._symbol, 28, resolution=Resolution.MINUTE)

        # daily macro trend: 20-day ROC filter for parabolic moves
        self._daily_consolidator = TradeBarConsolidator(timedelta(days=1))
        self._daily_consolidator.data_consolidated += self._on_daily_bar
        self.subscription_manager.add_consolidator(self._symbol, self._daily_consolidator)
        self._daily_closes = []

        # ATR multipliers + floors
        self._atr_sl_mult = 8.0
        self._atr_tp_mult = 32.0
        self._min_sl_pct = 0.025
        self._min_tp_pct = 0.10

        # trailing stop: activate at 1.5% profit, trail at 1%
        self._trail_activate_pct = 0.015
        self._trail_distance_pct = 0.01


        self._position_pct = 0.30

        # candle storage
        self._highs = []
        self._lows = []
        self._bar_count = 0

        # swing points
        self._swing_points = []
        self._prev_high_level = None
        self._prev_low_level = None

        # pending signal
        self._pending_signal = 0
        self._pending_bar = 0
        self._pending_window = 240

        # trade state
        self._entry_price = None
        self._stop_price = None
        self._target_price = None
        self._trail_price = None
        self._last_trade_bar = 0
        self._in_position = 0

        # monthly tracking
        self._month_trades = 0
        self._month_wins = 0
        self._month_losses = 0
        self._month_sl = 0
        self._month_tp = 0
        self._month_trail = 0
        self._month_pnl_sum = 0.0
        self._month_long_pnl = 0.0
        self._month_short_pnl = 0.0
        self._month_longs = 0
        self._month_shorts = 0
        self._prev_month = None
        self._trade_num = 0
        self._all_months = {}
        self._month_start_eq = 10000.0

        # diagnostic tracking
        self._entry_adx = 0.0
        self._entry_bar_num = 0
        self._consec_losses = 0
        self._all_trades = []

        # shock/jump filter: pause entries after extreme 1m moves
        self._shock_pause_until = 0
        self._shock_k = 4.0
        self._shock_pause_bars = 30
        self._prev_close = None
        self._return_window = []
        self._return_lookback = 120

        self.is_live = self.live_mode
        self.log(f"Live mode: {self.is_live}")

    def on_end_of_algorithm(self):
        """Output monthly breakdown and diagnostic analysis."""
        eq = self.portfolio.total_portfolio_value
        month_ret = (eq - self._month_start_eq) / self._month_start_eq * 100
        self._all_months[self._prev_month] = {
            "ret": month_ret, "trades": self._month_trades,
            "w": self._month_wins, "l": self._month_losses,
            "sl": self._month_sl, "tp": self._month_tp, "trail": self._month_trail,
            "long_pnl": self._month_long_pnl, "short_pnl": self._month_short_pnl,
            "longs": self._month_longs, "shorts": self._month_shorts,
        }

        # monthly stats
        for m, d in sorted(self._all_months.items()):
            self.set_runtime_statistic(
                m,
                f"{d['ret']:.1f}% T{d['trades']} W{d['w']}L{d['l']} SL{d['sl']}TP{d['tp']}TR{d['trail']} L{d['longs']}={d['long_pnl']:.1f}%S{d['shorts']}={d['short_pnl']:.1f}%"
            )

        # worst and best months
        sorted_months = sorted(self._all_months.items(), key=lambda x: x[1]["ret"])
        worst5 = sorted_months[:5]
        best5 = sorted_months[-5:][::-1]
        self.set_runtime_statistic("WORST5",
            " | ".join([f"{m}:{d['ret']:.1f}%" for m, d in worst5]))
        self.set_runtime_statistic("BEST5",
            " | ".join([f"{m}:{d['ret']:.1f}%" for m, d in best5]))

        # trade-level analysis
        if self._all_trades:
            wins = [t for t in self._all_trades if t["pnl"] > 0]
            losses = [t for t in self._all_trades if t["pnl"] <= 0]
            # ADX analysis
            w_adx = sum(t["adx"] for t in wins) / len(wins) if wins else 0
            l_adx = sum(t["adx"] for t in losses) / len(losses) if losses else 0
            self.set_runtime_statistic("ADX_WIN_vs_LOSS",
                f"W={w_adx:.1f} L={l_adx:.1f}")
            # bars in trade
            w_bars = sum(t["bars_in"] for t in wins) / len(wins) if wins else 0
            l_bars = sum(t["bars_in"] for t in losses) / len(losses) if losses else 0
            self.set_runtime_statistic("BARS_WIN_vs_LOSS",
                f"W={w_bars:.0f} L={l_bars:.0f}")
            # signal age
            w_age = sum(t["sig_age"] for t in wins) / len(wins) if wins else 0
            l_age = sum(t["sig_age"] for t in losses) / len(losses) if losses else 0
            self.set_runtime_statistic("AGE_WIN_vs_LOSS",
                f"W={w_age:.0f} L={l_age:.0f}")
            # direction breakdown
            longs = [t for t in self._all_trades if t["side"] == "LONG"]
            shorts = [t for t in self._all_trades if t["side"] == "SHORT"]
            l_pnl = sum(t["pnl"] for t in longs)
            s_pnl = sum(t["pnl"] for t in shorts)
            l_wr = len([t for t in longs if t["pnl"] > 0]) / len(longs) * 100 if longs else 0
            s_wr = len([t for t in shorts if t["pnl"] > 0]) / len(shorts) * 100 if shorts else 0
            self.set_runtime_statistic("LONG_TOTAL",
                f"N={len(longs)} pnl={l_pnl:.1f}% wr={l_wr:.0f}%")
            self.set_runtime_statistic("SHORT_TOTAL",
                f"N={len(shorts)} pnl={s_pnl:.1f}% wr={s_wr:.0f}%")
            # exit reason breakdown
            sl_trades = [t for t in self._all_trades if t["reason"] == "SL"]
            tp_trades = [t for t in self._all_trades if t["reason"] == "TP"]
            tr_trades = [t for t in self._all_trades if t["reason"] == "TRAIL"]
            self.set_runtime_statistic("EXIT_REASONS",
                f"SL={len(sl_trades)} TP={len(tp_trades)} TRAIL={len(tr_trades)}")
            # max consecutive losses
            max_cl = max((t["consec_l"] for t in self._all_trades), default=0)
            self.set_runtime_statistic("MAX_CONSEC_LOSS", str(max_cl))
            # ADX bucket analysis: trades with ADX 0-15 vs 15-20 vs 20-25
            for lo, hi, label in [(0, 15, "ADX0-15"), (15, 20, "ADX15-20"), (20, 25, "ADX20-25")]:
                bucket = [t for t in self._all_trades if lo <= t["adx"] < hi]
                if bucket:
                    b_pnl = sum(t["pnl"] for t in bucket)
                    b_wr = len([t for t in bucket if t["pnl"] > 0]) / len(bucket) * 100
                    self.set_runtime_statistic(label,
                        f"N={len(bucket)} pnl={b_pnl:.1f}% wr={b_wr:.0f}%")
            # weekly breakdown — worst weeks
            week_pnl = {}
            for t in self._all_trades:
                w = t["week"]
                week_pnl[w] = week_pnl.get(w, 0) + t["pnl"]
            sorted_weeks = sorted(week_pnl.items(), key=lambda x: x[1])
            worst_wk = sorted_weeks[:5]
            self.set_runtime_statistic("WORST_WEEKS",
                " | ".join([f"{w}:{p:.1f}%" for w, p in worst_wk]))

    def _classify_hl_type(self, swing_type, level):
        """Classify swing as HH/LH/HL/LL."""
        if swing_type == 1:
            if self._prev_high_level is None:
                hl_type = None
            elif level > self._prev_high_level:
                hl_type = "HH"
            else:
                hl_type = "LH"
            self._prev_high_level = level
        else:
            if self._prev_low_level is None:
                hl_type = None
            elif level < self._prev_low_level:
                hl_type = "LL"
            else:
                hl_type = "HL"
            self._prev_low_level = level
        return hl_type

    def _get_swing_signal(self):
        """Swing structure signal: 1=bullish, -1=bearish, 0=none."""
        pts = self._swing_points
        if len(pts) < 8:
            return 0

        last6 = pts[-8:]
        types = [p["hl_type"] for p in last6 if p["hl_type"] is not None]
        if len(types) < 6:
            return 0

        hh = sum(1 for t in types if t == "HH")
        hl = sum(1 for t in types if t == "HL")
        ll = sum(1 for t in types if t == "LL")
        lh = sum(1 for t in types if t == "LH")

        bullish = hh + hl
        bearish = ll + lh

        angles = []
        for i in range(len(pts) - 4, len(pts) - 1):
            if i < 0:
                continue
            dx = pts[i + 1]["bar_idx"] - pts[i]["bar_idx"]
            prev_lvl = pts[i]["level"]
            if not prev_lvl or prev_lvl == 0 or dx == 0:
                continue
            dp = (pts[i + 1]["level"] - prev_lvl) / prev_lvl
            angles.append(math.degrees(math.atan2(dp * 10000, dx)))

        if len(angles) < 2:
            return 0

        abs_angles = [abs(a) for a in angles]
        first_abs = abs_angles[0]
        last_abs = abs_angles[-1]

        # compression detection: bar distances between swings getting shorter
        bar_distances = []
        for i in range(len(pts) - 4, len(pts) - 1):
            if i >= 0:
                bar_distances.append(pts[i + 1]["bar_idx"] - pts[i]["bar_idx"])
        is_compressing = (len(bar_distances) >= 2
                          and bar_distances[-1] < bar_distances[0] * 0.7)

        is_plateauing = (first_abs > 0 and last_abs < first_abs * 0.4) or \
                        (first_abs > 0 and last_abs < first_abs * 0.6 and is_compressing)

        drift = 0
        if len(pts) >= 3 and pts[-3]["level"] != 0:
            drift = (pts[-1]["level"] - pts[-3]["level"]) / pts[-3]["level"]

        if not is_plateauing:
            if bullish >= 6 and hh >= 2 and hl >= 1:
                return 1
            if bearish >= 6 and ll >= 2 and lh >= 1:
                return -1

        if is_plateauing:
            if drift < -0.01:
                return -1
            if drift > 0.01:
                return 1

        return 0

    def _price_confirms_trend(self, direction, price):
        """Check price hasn't broken trend structure.
        For longs: price must be above the last swing low (uptrend intact).
        For shorts: price must be below the last swing high (downtrend intact).
        """
        pts = self._swing_points
        if len(pts) < 2:
            return True

        if direction == 1:
            # find last swing low
            for p in reversed(pts):
                if p["swing_type"] == -1:
                    return price > p["level"]
        else:
            # find last swing high
            for p in reversed(pts):
                if p["swing_type"] == 1:
                    return price < p["level"]
        return True

    def _pullback_entry_ok(self, direction):
        """Check if RSI shows a pullback for entry."""
        if not self._rsi_ind.is_ready:
            return False

        rsi_val = self._rsi_ind.current.value

        if direction == 1:
            return rsi_val < 45
        else:
            return rsi_val > 55

    def _calc_sl_tp(self, price, direction):
        """Calculate SL/TP using ATR with minimum % floors."""
        if self._atr.is_ready and self._atr.current.value > 0:
            atr_val = self._atr.current.value
            sl_dist = max(self._atr_sl_mult * atr_val, price * self._min_sl_pct)
            tp_dist = max(self._atr_tp_mult * atr_val, price * self._min_tp_pct)
        else:
            sl_dist = price * self._min_sl_pct
            tp_dist = price * self._min_tp_pct

        if direction == 1:
            return price - sl_dist, price + tp_dist
        else:
            return price + sl_dist, price - tp_dist

    def _on_daily_bar(self, sender, bar):
        """Track daily closes for ROC-based macro trend filter."""
        self._daily_closes.append(float(bar.close))
        if len(self._daily_closes) > 25:
            self._daily_closes = self._daily_closes[-25:]

    def _macro_trend_allows(self, direction):
        """Block counter-trend trades during parabolic moves.
        Uses 20-day price ROC > 25% as threshold for extreme trends.
        """
        if len(self._daily_closes) < 20:
            return True
        roc = (self._daily_closes[-1] - self._daily_closes[0]) / self._daily_closes[0]
        if roc > 0.20 and direction == -1:
            return False  # don't short during parabolic rally
        if roc < -0.20 and direction == 1:
            return False  # don't long during parabolic crash
        return True

    def _update_trailing_stop(self, price):
        """Update trailing stop once trade is in sufficient profit."""
        if self._in_position == 0 or not self._entry_price:
            return

        if self._in_position == 1:
            pnl_pct = (price - self._entry_price) / self._entry_price
            if pnl_pct >= self._trail_activate_pct:
                new_trail = price * (1 - self._trail_distance_pct)
                if self._trail_price is None or new_trail > self._trail_price:
                    self._trail_price = new_trail
        else:
            pnl_pct = (self._entry_price - price) / self._entry_price
            if pnl_pct >= self._trail_activate_pct:
                new_trail = price * (1 + self._trail_distance_pct)
                if self._trail_price is None or new_trail < self._trail_price:
                    self._trail_price = new_trail

    def on_data(self, data: Slice):
        """Process each 1-min candle."""
        if not data.bars.contains_key(self._symbol):
            return

        bar = data.bars[self._symbol]
        self._bar_count += 1
        price = float(bar.close)

        # shock/jump detection
        if self._prev_close is not None and self._prev_close > 0:
            ret = abs(price / self._prev_close - 1)
            self._return_window.append(ret)
            if len(self._return_window) > self._return_lookback:
                self._return_window = self._return_window[-self._return_lookback:]
            if len(self._return_window) >= 60:
                mean_ret = sum(self._return_window) / len(self._return_window)
                roll_std = (sum((r - mean_ret) ** 2 for r in self._return_window) / len(self._return_window)) ** 0.5
                if roll_std > 0 and ret > self._shock_k * roll_std:
                    self._shock_pause_until = self._bar_count + self._shock_pause_bars
        self._prev_close = price

        # monthly summary log
        cur_month = self.time.strftime("%Y-%m")
        if self._prev_month and cur_month != self._prev_month:
            eq = self.portfolio.total_portfolio_value
            month_ret = (eq - self._month_start_eq) / self._month_start_eq * 100
            self._all_months[self._prev_month] = {
                "ret": month_ret, "trades": self._month_trades,
                "w": self._month_wins, "l": self._month_losses,
                "sl": self._month_sl, "tp": self._month_tp, "trail": self._month_trail,
                "long_pnl": self._month_long_pnl, "short_pnl": self._month_short_pnl,
                "longs": self._month_longs, "shorts": self._month_shorts,
            }
            self.log(f"MONTH {self._prev_month} | ret={month_ret:.2f}% trades={self._month_trades} W={self._month_wins} L={self._month_losses} | SL={self._month_sl} TP={self._month_tp} TRAIL={self._month_trail} | LONG({self._month_longs})={self._month_long_pnl:.2f}% SHORT({self._month_shorts})={self._month_short_pnl:.2f}% | equity={eq:.0f}")
            d = self._all_months[self._prev_month]
            self.set_runtime_statistic(self._prev_month, f"{d['ret']:.1f}% T{d['trades']} W{d['w']}L{d['l']} SL{d['sl']}TP{d['tp']}TR{d['trail']}")
            self._month_start_eq = eq
            self._month_trades = 0
            self._month_wins = 0
            self._month_losses = 0
            self._month_sl = 0
            self._month_tp = 0
            self._month_trail = 0
            self._month_pnl_sum = 0.0
            self._month_long_pnl = 0.0
            self._month_short_pnl = 0.0
            self._month_longs = 0
            self._month_shorts = 0
        self._prev_month = cur_month

        self._highs.append(float(bar.high))
        self._lows.append(float(bar.low))

        if len(self._highs) > self._lookback:
            self._highs = self._highs[-self._lookback:]
            self._lows = self._lows[-self._lookback:]

        # exit checks: SL, TP, trailing stop
        if self._in_position != 0 and self._stop_price and self._target_price:
            self._update_trailing_stop(price)

            hit_exit = False
            if self._in_position == 1:
                hit_exit = (price <= self._stop_price
                            or price >= self._target_price
                            or (self._trail_price and price <= self._trail_price))
            else:
                hit_exit = (price >= self._stop_price
                            or price <= self._target_price
                            or (self._trail_price and price >= self._trail_price))

            if hit_exit:
                side = "LONG" if self._in_position == 1 else "SHORT"
                pnl = 0
                reason = "?"
                if self._entry_price:
                    if self._in_position == 1:
                        pnl = (price - self._entry_price) / self._entry_price * 100
                        reason = "SL" if price <= self._stop_price else ("TP" if price >= self._target_price else "TRAIL")
                    else:
                        pnl = (self._entry_price - price) / self._entry_price * 100
                        reason = "SL" if price >= self._stop_price else ("TP" if price <= self._target_price else "TRAIL")
                self._trade_num += 1
                bars_in = self._bar_count - self._entry_bar_num
                sig_age = self._entry_bar_num - self._pending_bar if self._pending_bar else 0
                # get swing context
                last_types = ""
                if len(self._swing_points) >= 4:
                    last_types = ",".join([str(p.get("hl_type", "?")) for p in self._swing_points[-4:]])
                self.log(f"#{self._trade_num} EXIT {side} {reason} entry={self._entry_price:.0f} exit={price:.0f} pnl={pnl:.2f}% adx={self._entry_adx:.1f} bars={bars_in} age={sig_age} swings=[{last_types}] eq={self.portfolio.total_portfolio_value:.0f}")
                # track consecutive losses
                if pnl <= 0:
                    self._consec_losses += 1
                else:
                    self._consec_losses = 0
                # store trade for analysis
                self._all_trades.append({
                    "num": self._trade_num, "month": self.time.strftime("%Y-%m"),
                    "week": self.time.strftime("%Y-W%W"),
                    "side": side, "reason": reason, "pnl": pnl,
                    "adx": self._entry_adx, "bars_in": bars_in,
                    "sig_age": sig_age, "consec_l": self._consec_losses,
                })
                self._month_trades += 1
                self._month_pnl_sum += pnl
                if self._in_position == 1:
                    self._month_long_pnl += pnl
                    self._month_longs += 1
                else:
                    self._month_short_pnl += pnl
                    self._month_shorts += 1
                if pnl > 0:
                    self._month_wins += 1
                else:
                    self._month_losses += 1
                if reason == "SL":
                    self._month_sl += 1
                elif reason == "TP":
                    self._month_tp += 1
                elif reason == "TRAIL":
                    self._month_trail += 1
                self.plot("Trade PnL", "pnl%", pnl)
                self.liquidate(self._symbol)
                self._entry_price = None
                self._stop_price = None
                self._target_price = None
                self._trail_price = None

                self._in_position = 0
                self._last_trade_bar = self._bar_count
                return

        # check pending signal for pullback entry
        if (self._pending_signal != 0
                and self._in_position == 0
                and self._bar_count - self._last_trade_bar >= 60
                and self._bar_count >= self._shock_pause_until):

            if self._bar_count - self._pending_bar > self._pending_window:
                self._pending_signal = 0
            elif (self._pullback_entry_ok(self._pending_signal)
                    and self._price_confirms_trend(self._pending_signal, price)
                    and (not self._adx_ind.is_ready
                         or self._adx_ind.current.value < 20)
                    and self._macro_trend_allows(self._pending_signal)):
                direction = self._pending_signal
                self._pending_signal = 0

                pos_pct = self._position_pct

                if direction == 1:
                    self.set_holdings(self._symbol, pos_pct)
                else:
                    self.set_holdings(self._symbol, -pos_pct)

                self._entry_price = price
                self._stop_price, self._target_price = self._calc_sl_tp(price, direction)
                self._trail_price = None

                self._in_position = direction
                self._entry_adx = self._adx_ind.current.value if self._adx_ind.is_ready else 0
                self._entry_bar_num = self._bar_count
                self._last_trade_bar = self._bar_count
                side = "LONG" if direction == 1 else "SHORT"
                rsi_val = self._rsi_ind.current.value
                adx_val = self._entry_adx
                self.log(f"ENTER {side} price={price:.0f} sl={self._stop_price:.0f} tp={self._target_price:.0f} rsi={rsi_val:.1f} adx={adx_val:.1f} eq={self.portfolio.total_portfolio_value:.0f}")
                return

        if len(self._highs) < self._swing_len * 2 + 1:
            return

        # detect swing
        idx = len(self._highs) - self._swing_len - 1
        new_swing = False

        is_swing_high = all(
            self._highs[idx] >= self._highs[idx - j] and
            self._highs[idx] >= self._highs[idx + j]
            for j in range(1, self._swing_len + 1)
        )
        is_swing_low = all(
            self._lows[idx] <= self._lows[idx - j] and
            self._lows[idx] <= self._lows[idx + j]
            for j in range(1, self._swing_len + 1)
        )

        if is_swing_high:
            level = self._highs[idx]
            hl_type = self._classify_hl_type(1, level)
            self._swing_points.append({
                "bar_idx": self._bar_count - self._swing_len,
                "level": level,
                "swing_type": 1,
                "hl_type": hl_type,
            })
            if len(self._swing_points) > self._max_swings:
                self._swing_points = self._swing_points[-self._max_swings:]
            new_swing = True

        if is_swing_low:
            level = self._lows[idx]
            hl_type = self._classify_hl_type(-1, level)
            self._swing_points.append({
                "bar_idx": self._bar_count - self._swing_len,
                "level": level,
                "swing_type": -1,
                "hl_type": hl_type,
            })
            if len(self._swing_points) > self._max_swings:
                self._swing_points = self._swing_points[-self._max_swings:]
            new_swing = True

        if not new_swing:
            return

        signal = self._get_swing_signal()

        # opposite signal cancels pending (even during cooldown)
        if (self._pending_signal != 0
                and signal != 0
                and signal != self._pending_signal):
            self._pending_signal = 0

        # cooldown: 12 hours between swing signals
        if self._bar_count - self._last_trade_bar < 720:
            return
        if signal == 0:
            return

        self._pending_signal = signal
        self._pending_bar = self._bar_count
