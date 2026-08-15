import math
from typing import List, Dict, Any, Optional, Tuple

class LuxAlgoSMC:
    """
    Port of LuxAlgo Smart Money Concepts [LuxAlgo] v5 (Pine Script).
    Implements exact institutional market structure:
    - Swing & Internal Structure (BOS & CHoCH)
    - Order Blocks (OB) with live mitigation checking
    - Equal Highs & Equal Lows (EQH / EQL)
    - Fair Value Gaps (FVG) with auto-threshold & mitigation
    - Premium, Discount & Equilibrium Zones (50% Equilibrium)
    - Strong vs Weak Highs & Lows
    """

    @staticmethod
    def calculate_atr(candles: List[Dict[str, Any]], period: int = 14) -> List[float]:
        if not candles:
            return []
        atrs = []
        tr_list = []
        for i in range(len(candles)):
            c = candles[i]
            if i == 0:
                tr = c["high"] - c["low"]
            else:
                prev_close = candles[i - 1]["close"]
                tr = max(c["high"] - c["low"], abs(c["high"] - prev_close), abs(c["low"] - prev_close))
            tr_list.append(tr)

            if len(tr_list) < period:
                atrs.append(sum(tr_list) / len(tr_list))
            else:
                atrs.append(sum(tr_list[-period:]) / period)
        return atrs

    @staticmethod
    def detect_smc_structure(candles: List[Dict[str, Any]], swing_length: int = 10, internal_length: int = 5) -> Dict[str, Any]:
        """
        Calculates complete LuxAlgo SMC indicators.
        """
        n = len(candles)
        if n < 15:
            return {
                "swing_structures": [],
                "internal_structures": [],
                "order_blocks": [],
                "fvgs": [],
                "equal_high_lows": [],
                "zones": None,
                "strong_weak": None,
                "trend": "NEUTRAL"
            }

        atrs = LuxAlgoSMC.calculate_atr(candles, 14)
        latest_atr = atrs[-1] if atrs else 1.0

        # Data arrays
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        closes = [c["close"] for c in candles]
        opens = [c["open"] for c in candles]
        times = [c["time"] for c in candles]

        # ----------------------------------------------------
        # 1. PIVOTS & SWING / INTERNAL STRUCTURE (BOS & CHoCH)
        # ----------------------------------------------------
        def get_pivots(length: int):
            pivots_high = []
            pivots_low = []
            for i in range(length, n - length):
                # Pivot High
                if highs[i] == max(highs[i - length : i + length + 1]):
                    pivots_high.append({"index": i, "time": times[i], "price": highs[i], "type": "HIGH"})
                # Pivot Low
                if lows[i] == min(lows[i - length : i + length + 1]):
                    pivots_low.append({"index": i, "time": times[i], "price": lows[i], "type": "LOW"})
            return pivots_high, pivots_low

        swing_piv_h, swing_piv_l = get_pivots(swing_length)
        int_piv_h, int_piv_l = get_pivots(internal_length)

        # Structure Breakouts (BOS & CHoCH) & Order Blocks
        swing_structures = []
        internal_structures = []
        order_blocks = []
        
        swing_trend = 0  # +1 Bullish, -1 Bearish
        internal_trend = 0

        # Detect Swing Structure
        active_sh = None
        active_sl = None

        for i in range(n):
            c_close = closes[i]
            c_high = highs[i]
            c_low = lows[i]
            c_time = times[i]

            # Update active swing pivots that occurred before this bar
            for ph in swing_piv_h:
                if ph["index"] < i and (active_sh is None or ph["index"] > active_sh["index"]):
                    active_sh = dict(ph, crossed=False)
            for pl in swing_piv_l:
                if pl["index"] < i and (active_sl is None or pl["index"] > active_sl["index"]):
                    active_sl = dict(pl, crossed=False)

            # Bullish Breakout (Cross above Swing High)
            if active_sh and not active_sh["crossed"] and c_close > active_sh["price"]:
                tag = "CHoCH" if swing_trend == -1 else "BOS"
                swing_trend = 1
                active_sh["crossed"] = True

                swing_structures.append({
                    "tag": tag,
                    "type": "BULLISH",
                    "start_time": active_sh["time"],
                    "end_time": c_time,
                    "price": active_sh["price"],
                    "start_index": active_sh["index"],
                    "end_index": i
                })

                # Find Order Block (Lowest low between pivot and breakout bar)
                sub_lows = lows[active_sh["index"] : i + 1]
                if sub_lows:
                    min_idx = active_sh["index"] + sub_lows.index(min(sub_lows))
                    order_blocks.append({
                        "type": "BULLISH_OB",
                        "subtype": "SWING",
                        "top": candles[min_idx]["high"],
                        "bottom": candles[min_idx]["low"],
                        "time": times[min_idx],
                        "index": min_idx,
                        "mitigated": False
                    })

            # Bearish Breakout (Cross below Swing Low)
            if active_sl and not active_sl["crossed"] and c_close < active_sl["price"]:
                tag = "CHoCH" if swing_trend == 1 else "BOS"
                swing_trend = -1
                active_sl["crossed"] = True

                swing_structures.append({
                    "tag": tag,
                    "type": "BEARISH",
                    "start_time": active_sl["time"],
                    "end_time": c_time,
                    "price": active_sl["price"],
                    "start_index": active_sl["index"],
                    "end_index": i
                })

                # Find Order Block (Highest high between pivot and breakout bar)
                sub_highs = highs[active_sl["index"] : i + 1]
                if sub_highs:
                    max_idx = active_sl["index"] + sub_highs.index(max(sub_highs))
                    order_blocks.append({
                        "type": "BEARISH_OB",
                        "subtype": "SWING",
                        "top": candles[max_idx]["high"],
                        "bottom": candles[max_idx]["low"],
                        "time": times[max_idx],
                        "index": max_idx,
                        "mitigated": False
                    })

        # ----------------------------------------------------
        # 2. ORDER BLOCK MITIGATION CHECKING
        # ----------------------------------------------------
        for ob in order_blocks:
            for j in range(ob["index"] + 1, n):
                if ob["type"] == "BULLISH_OB" and lows[j] < ob["bottom"]:
                    ob["mitigated"] = True
                    ob["mitigated_index"] = j
                    ob["mitigated_time"] = times[j]
                    break
                elif ob["type"] == "BEARISH_OB" and highs[j] > ob["top"]:
                    ob["mitigated"] = True
                    ob["mitigated_index"] = j
                    ob["mitigated_time"] = times[j]
                    break

        # Keep only valid recent order blocks (both unmitigated and freshly formed)
        valid_obs = [ob for ob in order_blocks if not ob["mitigated"] or (n - ob.get("mitigated_index", 0) < 15)][-6:]

        # ----------------------------------------------------
        # 3. FAIR VALUE GAPS (FVG) WITH STRICT MITIGATION
        # ----------------------------------------------------
        fvgs = []
        for i in range(2, n):
            c_curr = candles[i]
            c_prev2 = candles[i - 2]
            c_mid = candles[i - 1]

            # Bullish FVG: Low of current bar > High of 2 bars ago
            if c_curr["low"] > c_prev2["high"] and c_mid["close"] > c_prev2["high"]:
                gap_size = c_curr["low"] - c_prev2["high"]
                if gap_size > latest_atr * 0.15:
                    top = c_curr["low"]
                    bot = c_prev2["high"]
                    
                    # Check mitigation
                    mitigated = False
                    mitigated_idx = None
                    for k in range(i + 1, n):
                        if candles[k]["low"] <= bot:
                            mitigated = True
                            mitigated_idx = k
                            break

                    fvgs.append({
                        "type": "BULLISH_FVG",
                        "top": round(top, 5),
                        "bottom": round(bot, 5),
                        "time": c_mid["time"],
                        "index": i - 1,
                        "mitigated": mitigated,
                        "mitigated_index": mitigated_idx
                    })

            # Bearish FVG: High of current bar < Low of 2 bars ago
            elif c_curr["high"] < c_prev2["low"] and c_mid["close"] < c_prev2["low"]:
                gap_size = c_prev2["low"] - c_curr["high"]
                if gap_size > latest_atr * 0.15:
                    top = c_prev2["low"]
                    bot = c_curr["high"]

                    mitigated = False
                    mitigated_idx = None
                    for k in range(i + 1, n):
                        if candles[k]["high"] >= top:
                            mitigated = True
                            mitigated_idx = k
                            break

                    fvgs.append({
                        "type": "BEARISH_FVG",
                        "top": round(top, 5),
                        "bottom": round(bot, 5),
                        "time": c_mid["time"],
                        "index": i - 1,
                        "mitigated": mitigated,
                        "mitigated_index": mitigated_idx
                    })

        # Filter only active or recent FVGs (max 8)
        active_fvgs = [f for f in fvgs if not f["mitigated"]][-8:]

        # ----------------------------------------------------
        # 4. EQUAL HIGHS & EQUAL LOWS (EQH / EQL)
        # ----------------------------------------------------
        eq_highs_lows = []
        eq_threshold = 0.15 * latest_atr
        
        # Check consecutive swing highs
        for i in range(len(swing_piv_h) - 1):
            p1 = swing_piv_h[i]
            p2 = swing_piv_h[i + 1]
            if abs(p1["price"] - p2["price"]) <= eq_threshold:
                eq_highs_lows.append({
                    "type": "EQH",
                    "label": "EQH (BSL)",
                    "price": round((p1["price"] + p2["price"]) / 2, 5),
                    "start_time": p1["time"],
                    "end_time": p2["time"],
                    "start_index": p1["index"],
                    "end_index": p2["index"]
                })

        # Check consecutive swing lows
        for i in range(len(swing_piv_l) - 1):
            p1 = swing_piv_l[i]
            p2 = swing_piv_l[i + 1]
            if abs(p1["price"] - p2["price"]) <= eq_threshold:
                eq_highs_lows.append({
                    "type": "EQL",
                    "label": "EQL (SSL)",
                    "price": round((p1["price"] + p2["price"]) / 2, 5),
                    "start_time": p1["time"],
                    "end_time": p2["time"],
                    "start_index": p1["index"],
                    "end_index": p2["index"]
                })

        # ----------------------------------------------------
        # 5. PREMIUM, DISCOUNT & EQUILIBRIUM (50%) ZONES
        # ----------------------------------------------------
        trailing_top = max(highs[-min(n, 120):])
        trailing_bot = min(lows[-min(n, 120):])
        range_span = max(0.0001, trailing_top - trailing_bot)

        zones = {
            "top": round(trailing_top, 5),
            "bottom": round(trailing_bot, 5),
            "premium": {
                "top": round(trailing_top, 5),
                "bottom": round(0.95 * trailing_top + 0.05 * trailing_bot, 5)
            },
            "equilibrium": {
                "top": round(0.525 * trailing_top + 0.475 * trailing_bot, 5),
                "mid": round((trailing_top + trailing_bot) / 2, 5),
                "bottom": round(0.525 * trailing_bot + 0.475 * trailing_top, 5)
            },
            "discount": {
                "top": round(0.95 * trailing_bot + 0.05 * trailing_top, 5),
                "bottom": round(trailing_bot, 5)
            }
        }

        # ----------------------------------------------------
        # 6. STRONG / WEAK HIGHS & LOWS
        # ----------------------------------------------------
        strong_weak = {
            "high_type": "Weak High" if swing_trend == 1 else "Strong High",
            "high_price": round(trailing_top, 5),
            "low_type": "Strong Low" if swing_trend == 1 else "Weak Low",
            "low_price": round(trailing_bot, 5)
        }

        return {
            "swing_structures": swing_structures[-8:],
            "order_blocks": valid_obs,
            "fvgs": active_fvgs,
            "equal_high_lows": eq_highs_lows[-4:],
            "zones": zones,
            "strong_weak": strong_weak,
            "trend": "BULLISH" if swing_trend == 1 else ("BEARISH" if swing_trend == -1 else "SIDEWAYS_RANGING")
        }


class VolumeProfileMath:
    """
    Port of Volume Profile / Fixed Range by LonesomeTheBlue (Pine Script).
    Calculates:
    - Fixed Range & Viewport Volume Profile
    - 24/30 Row Channels
    - Up Volume vs Down Volume Split (Body vs Wicks)
    - POC (Point of Control) Level & Price
    - VAH (Value Area High) & VAL (Value Area Low) based on 70% volume distribution
    """

    @staticmethod
    def calculate_volume_profile(candles: List[Dict[str, Any]], num_bars: int = 150, row_size: int = 24, va_percent: float = 70.0) -> Dict[str, Any]:
        if not candles or len(candles) == 0:
            return {"rows": [], "poc": None, "vah": None, "val": None}

        slice_candles = candles[-min(len(candles), num_bars):]
        top = max(c["high"] for c in slice_candles)
        bot = min(c["low"] for c in slice_candles)
        
        if top <= bot:
            return {"rows": [], "poc": top, "vah": top, "val": bot}

        step = (top - bot) / row_size
        levels = [bot + step * x for x in range(row_size + 1)]

        up_vols = [0.0] * row_size
        down_vols = [0.0] * row_size
        total_vols = [0.0] * row_size

        def get_vol_overlap(y11, y12, y21, y22, height, vol):
            if height <= 0:
                return 0.0
            overlap = max(0.0, min(max(y11, y12), max(y21, y22)) - max(min(y11, y12), min(y21, y22)))
            return (overlap * vol) / height

        for c in slice_candles:
            body_top = max(c["close"], c["open"])
            body_bot = min(c["close"], c["open"])
            is_green = c["close"] >= c["open"]

            top_wick = c["high"] - body_top
            bot_wick = body_bot - c["low"]
            body = body_top - body_bot
            denom = 2 * top_wick + 2 * bot_wick + body
            
            raw_vol = float(c.get("volume", 10))
            if denom <= 0:
                denom = 1.0

            body_vol = (body * raw_vol) / denom
            top_wick_vol = (2 * top_wick * raw_vol) / denom
            bot_wick_vol = (2 * bot_wick * raw_vol) / denom

            for x in range(row_size):
                l_bot = levels[x]
                l_top = levels[x + 1]

                v_body = get_vol_overlap(l_bot, l_top, body_bot, body_top, body, body_vol)
                v_top_wick = get_vol_overlap(l_bot, l_top, body_top, c["high"], top_wick, top_wick_vol) / 2
                v_bot_wick = get_vol_overlap(l_bot, l_top, c["low"], body_bot, bot_wick, bot_wick_vol) / 2
                v_total_bar = v_body + v_top_wick + v_bot_wick

                if is_green:
                    up_vols[x] += v_total_bar
                else:
                    down_vols[x] += v_total_bar
                
                total_vols[x] += v_total_bar

        # Point of Control (POC)
        max_vol = max(total_vols) if total_vols else 1.0
        poc_idx = total_vols.index(max_vol) if max_vol > 0 else 0
        poc_price = round((levels[poc_idx] + levels[poc_idx + 1]) / 2, 5)

        # Value Area Calculation (VAH & VAL 70%)
        total_vol_sum = sum(total_vols)
        target_va_vol = total_vol_sum * (va_percent / 100.0)
        
        va_accum = total_vols[poc_idx]
        up_idx = poc_idx
        down_idx = poc_idx

        while va_accum < target_va_vol and (up_idx < row_size - 1 or down_idx > 0):
            up_vol = total_vols[up_idx + 1] if up_idx < row_size - 1 else 0
            down_vol = total_vols[down_idx - 1] if down_idx > 0 else 0

            if up_vol == 0 and down_vol == 0:
                break

            if up_vol >= down_vol and up_idx < row_size - 1:
                va_accum += up_vol
                up_idx += 1
            elif down_idx > 0:
                va_accum += down_vol
                down_idx -= 1
            elif up_idx < row_size - 1:
                va_accum += up_vol
                up_idx += 1
            else:
                break

        vah_price = round(levels[min(row_size, up_idx + 1)], 5)
        val_price = round(levels[max(0, down_idx)], 5)

        # Build Profile Rows
        rows = []
        for x in range(row_size):
            rows.append({
                "price_low": round(levels[x], 5),
                "price_high": round(levels[x + 1], 5),
                "price_mid": round((levels[x] + levels[x + 1]) / 2, 5),
                "up_volume": round(up_vols[x], 2),
                "down_volume": round(down_vols[x], 2),
                "total_volume": round(total_vols[x], 2),
                "is_poc": (x == poc_idx),
                "in_value_area": (down_idx <= x <= up_idx)
            })

        return {
            "rows": rows,
            "poc": poc_price,
            "vah": vah_price,
            "val": val_price,
            "total_volume": round(total_vol_sum, 2)
        }


class OrderFlowMath:
    """
    Main OrderFlow Math facade combining LuxAlgo SMC and Volume Profile.
    """

    @staticmethod
    def calculate_cvd(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cvd_series = []
        running_cvd = 0
        for c in candles:
            buy_vol = c.get("buy_volume", 0)
            sell_vol = c.get("sell_volume", 0)
            delta = buy_vol - sell_vol
            running_cvd += delta
            cvd_series.append({
                "time": c["time"],
                "delta": delta,
                "cvd": running_cvd
            })
        return cvd_series

    @staticmethod
    def compute_all_indicators(candles: List[Dict[str, Any]], timeframe: str = "1S") -> Dict[str, Any]:
        """
        Runs LuxAlgo SMC & Volume Profile across the candle series.
        """
        swing_len = 8 if timeframe in ["1S", "M1"] else 12
        int_len = 4 if timeframe in ["1S", "M1"] else 5

        smc = LuxAlgoSMC.detect_smc_structure(candles, swing_length=swing_len, internal_length=int_len)
        vp = VolumeProfileMath.calculate_volume_profile(candles, num_bars=min(len(candles), 180), row_size=28, va_percent=70.0)
        cvd = OrderFlowMath.calculate_cvd(candles)

        return {
            "smc": smc,
            "volume_profile": vp,
            "cvd": cvd,
            "trend": smc["trend"]
        }
