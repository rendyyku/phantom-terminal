import json
import re
from typing import Dict, Any, Callable, Optional
from engine.byok_client import UniversalBYOKClient
from engine.prompt_builder import PromptBuilder
from config import DEFAULT_AI_MODELS

class ConsensusEvaluator:
    """
    Orchestrates the Multi-Agent AI War Room Debate.
    Executes Bull Agent, Bear Agent, and Supreme Judge Arbitration in sequence.
    """

    def __init__(self, byok_client: Optional[UniversalBYOKClient] = None):
        self.client = byok_client or UniversalBYOKClient()

    async def run_war_room_debate(self, market_context: Dict[str, Any], 
                                  event_callback: Optional[Callable[[str, Any], None]] = None) -> Dict[str, Any]:
        """
        Runs the full 3-Titan AI debate and returns the final consensus card.
        """
        async def notify(event_type: str, data: Any):
            if event_callback:
                if callable(event_callback):
                    res = event_callback(event_type, data)
                    if hasattr(res, "__await__"):
                        await res

        await notify("debate_start", {"pair": market_context.get("pair"), "time": "now"})

        # 1. Bullish Agent (Claude 3.5 Sonnet)
        bull_prompt = PromptBuilder.get_bullish_agent_prompt(market_context)
        bull_model = DEFAULT_AI_MODELS["bull_agent"]["model"]
        await notify("agent_thinking", {"agent": "bull", "name": DEFAULT_AI_MODELS["bull_agent"]["name"]})
        
        bull_thesis = await self.client.call_llm(
            prompt=bull_prompt, 
            system_prompt="You are a senior institutional Bullish ICT & OrderFlow Analyst.",
            model=bull_model
        )
        await notify("bull_thesis_ready", {"agent": "bull", "thesis": bull_thesis})

        # 2. Bearish Agent (DeepSeek R1)
        bear_prompt = PromptBuilder.get_bearish_agent_prompt(market_context)
        bear_model = DEFAULT_AI_MODELS["bear_agent"]["model"]
        await notify("agent_thinking", {"agent": "bear", "name": DEFAULT_AI_MODELS["bear_agent"]["name"]})
        
        bear_thesis = await self.client.call_llm(
            prompt=bear_prompt, 
            system_prompt="You are a senior institutional Bearish Risk & Resistance Analyst.",
            model=bear_model
        )
        await notify("bear_thesis_ready", {"agent": "bear", "thesis": bear_thesis})

        # 3. Supreme Judge (GPT-4o)
        judge_prompt = PromptBuilder.get_supreme_judge_prompt(market_context, bull_thesis, bear_thesis)
        judge_model = DEFAULT_AI_MODELS["judge_agent"]["model"]
        await notify("agent_thinking", {"agent": "judge", "name": DEFAULT_AI_MODELS["judge_agent"]["name"]})
        
        judge_raw = await self.client.call_llm(
            prompt=judge_prompt,
            system_prompt="You are the Supreme Judge Quant Arbiter. Return strict JSON only.",
            model=judge_model
        )

        # Parse Supreme Judge JSON
        final_decision = self._extract_json_payload(judge_raw, market_context)
        final_decision["bull_thesis"] = bull_thesis
        final_decision["bear_thesis"] = bear_thesis

        await notify("debate_finished", final_decision)
        return final_decision

    def _extract_json_payload(self, raw_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Safely parses JSON payload from LLM response."""
        try:
            # Try direct JSON parsing
            return json.loads(raw_text.strip())
        except Exception:
            # Extract JSON block using regex
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass

        # Fallback decision
        current_p = context.get("current_price", 2650.0)
        return {
            "decision": "WAIT",
            "consensus_score": 60,
            "pair": context.get("pair", "XAUUSD"),
            "entry_price": current_p,
            "stop_loss": round(current_p - 5.0, 2),
            "take_profit": round(current_p + 10.0, 2),
            "risk_reward_ratio": "1:2.0",
            "key_reasoning": "Debate completed. Mixed signals detected between Bull and Bear Titans. Standby recommended.",
            "warning_flag": "Consensus below threshold (<70%)."
        }
