import json
from typing import Dict, Any, List

class PromptBuilder:
    """
    Constructs high-density ICT & Order Flow context prompts for AI War Room models.
    """

    @staticmethod
    def build_ascii_chart(candles: List[Dict[str, Any]], height: int = 10, width: int = 30) -> str:
        """
        Creates an ASCII representation of the recent price action for AI visual reasoning.
        """
        if not candles:
            return "[No Chart Data]"

        recent = candles[-width:]
        closes = [c["close"] for c in recent]
        min_p = min(closes)
        max_p = max(closes)
        rng = max(0.0001, max_p - min_p)

        grid = [[" " for _ in range(len(recent))] for _ in range(height)]

        for col, c in enumerate(recent):
            row = int(((c["close"] - min_p) / rng) * (height - 1))
            row = min(height - 1, max(0, row))
            char = "▲" if c["close"] >= c["open"] else "▼"
            grid[height - 1 - row][col] = char

        lines = []
        for r in range(height):
            val = max_p - (r / (height - 1)) * rng
            line_str = f"{val:9.2f} | " + "".join(grid[r])
            lines.append(line_str)

        lines.append("          +" + "-" * len(recent))
        return "\n".join(lines)

    @classmethod
    def build_market_context(cls, pair: str, candles: List[Dict[str, Any]], fvgs: List[Dict[str, Any]], 
                             liq_pools: Dict[str, Any], cvd_data: List[Dict[str, Any]], 
                             structure: Dict[str, Any], macro_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Combines mathematical indicators and macro news into a concise institutional context summary.
        """
        latest_c = candles[-1]
        recent_cvd = cvd_data[-1]["cvd"] if cvd_data else 0.0
        delta_last_5 = sum([c["delta"] for c in cvd_data[-5:]]) if len(cvd_data) >= 5 else 0.0

        active_bullish_fvgs = [f for f in fvgs if f["type"] == "BULLISH_FVG" and not f["mitigated"]][-3:]
        active_bearish_fvgs = [f for f in fvgs if f["type"] == "BEARISH_FVG" and not f["mitigated"]][-3:]

        ascii_art = cls.build_ascii_chart(candles)

        return {
            "pair": pair,
            "current_price": latest_c["close"],
            "latest_candle": {
                "open": latest_c["open"],
                "high": latest_c["high"],
                "low": latest_c["low"],
                "close": latest_c["close"],
                "volume": latest_c["volume"]
            },
            "orderflow": {
                "cumulative_volume_delta": recent_cvd,
                "delta_momentum_5_periods": delta_last_5,
                "institutional_bias": "AGGRESSIVE_BUYING" if delta_last_5 > 500 else ("AGGRESSIVE_SELLING" if delta_last_5 < -500 else "BALANCED")
            },
            "ict_structure": {
                "trend_status": structure.get("trend", "NEUTRAL"),
                "structure_event": structure.get("event", "NONE"),
                "structure_note": structure.get("description", "")
            },
            "macro_intelligence": macro_context or {
                "breaking_macro_headlines": ["Inflation data moderates", "Gold draws safe haven flows"],
                "macro_risk_warning": "NORMAL RISK ENVIRONMENT"
            },
            "liquidity_pools": {
                "equal_highs_bsl": [p["price"] for p in liq_pools.get("eqh", [])],
                "equal_lows_ssl": [p["price"] for p in liq_pools.get("eql", [])],
                "recent_sweeps": liq_pools.get("sweeps", [])
            },
            "unmitigated_fvgs": {
                "bullish_fvg_zones": [{"top": f["top"], "bottom": f["bottom"]} for f in active_bullish_fvgs],
                "bearish_fvg_zones": [{"top": f["top"], "bottom": f["bottom"]} for f in active_bearish_fvgs]
            },
            "ascii_chart": ascii_art
        }

    @staticmethod
    def get_bullish_agent_prompt(context: Dict[str, Any]) -> str:
        return f"""You are the BULLISH ICT QUANT AGENT (Titan 1) in the Phantom Terminal War Room.
Your role is to rigorously search for institutional BUY arguments based on:
1. Discount pricing & Bullish Fair Value Gaps (FVG)
2. Sell-Side Liquidity (SSL) Sweeps followed by Market Structure Shift (MSS)
3. Cumulative Volume Delta (CVD) absorption divergences (price lower low, CVD higher low)

Current Market Context:
{json.dumps(context, indent=2)}

ASCII CHART VISUALIZATION:
{context.get('ascii_chart', '')}

Provide your structured bullish thesis in 3-4 concise tactical bullet points, your suggested BUY Entry, SL, and TP levels, and your Bullish Conviction Score (0-100%)."""

    @staticmethod
    def get_bearish_agent_prompt(context: Dict[str, Any]) -> str:
        return f"""You are the BEARISH RISK & RESISTANCE AGENT (Titan 2) in the Phantom Terminal War Room.
Your role is to critically analyze trap setups and search for institutional SELL arguments based on:
1. Premium pricing & Bearish Fair Value Gaps (FVG)
2. Buy-Side Liquidity (BSL) Sweeps followed by Displacement downward
3. High timeframe resistance overhead and CVD buyer exhaustion

Current Market Context:
{json.dumps(context, indent=2)}

ASCII CHART VISUALIZATION:
{context.get('ascii_chart', '')}

Provide your structured bearish thesis in 3-4 concise tactical bullet points, your suggested SELL Entry, SL, and TP levels, and your Bearish Conviction Score (0-100%)."""

    @staticmethod
    def get_supreme_judge_prompt(context: Dict[str, Any], bull_thesis: str, bear_thesis: str) -> str:
        return f"""You are the SUPREME JUDGE & CHIEF QUANT ARBITER in the Phantom Terminal War Room.
You are evaluating the live debate between the Bullish Agent and Bearish Agent.

Market Data:
{json.dumps(context, indent=2)}

BULLISH THESIS:
{bull_thesis}

BEARISH THESIS:
{bear_thesis}

REQUIREMENTS:
1. Deliver the final decision: "BUY", "SELL", or "WAIT / NO TRADE".
2. Set precise Entry, Stop Loss (SL), Take Profit (TP), and calculated Risk:Reward ratio (min 1:2.0).
3. Compute Consensus Score (0-100%). Only recommend execution if Consensus >= 70%.
4. Output STRICT JSON format as follows:
{{
  "decision": "BUY" | "SELL" | "WAIT",
  "consensus_score": 85,
  "pair": "{context.get('pair', 'XAUUSD')}",
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "risk_reward_ratio": "1:2.5",
  "key_reasoning": "Detailed 2-sentence summary of why this decision won the debate",
  "warning_flag": "Optional note on upcoming high-impact news or liquidity risk"
}}"""
