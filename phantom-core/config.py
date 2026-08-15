import os
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
KEY_VAULT_FILE = BASE_DIR / "keys_vault.json"

# Server Configuration
SERVER_HOST = os.getenv("PHANTOM_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("PHANTOM_PORT", 8000))
MT5_SOCKET_PORT = int(os.getenv("MT5_PORT", 9988))

# Supported Market Pairs
DEFAULT_PAIRS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]
TIMEFRAMES = ["M1", "M5", "M15", "H1", "H4", "D1"]

# Risk Default Parameters
DEFAULT_RISK_SETTINGS = {
    "account_balance": 10000.0,
    "risk_percent_per_trade": 1.0,
    "daily_max_drawdown_percent": 3.0,
    "max_open_trades": 3,
    "enable_hard_stop": True,
    "auto_be_trigger_rr": 1.5,
    "prop_firm_mode": True  # FTMO/The5ers compliance mode
}

# LLM Providers Configuration
DEFAULT_AI_MODELS = {
    "bull_agent": {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "name": "General Claude 3.5 (Bull Specialist)"
    },
    "bear_agent": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-r1",
        "name": "General DeepSeek R1 (Bear Specialist)"
    },
    "judge_agent": {
        "provider": "openrouter",
        "model": "openai/gpt-4o",
        "name": "Supreme Judge GPT-4o"
    }
}

def load_keys_vault() -> dict:
    """Load local encrypted or plaintext API keys from local vault."""
    if KEY_VAULT_FILE.exists():
        try:
            with open(KEY_VAULT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_keys_vault(keys_data: dict) -> bool:
    """Save API keys locally to user machine."""
    try:
        with open(KEY_VAULT_FILE, "w", encoding="utf-8") as f:
            json.dump(keys_data, f, indent=2)
        return True
    except Exception:
        return False
