import os
import json
import base64
import hashlib
import platform
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
KEY_VAULT_FILE = BASE_DIR / "keys_vault.json"

# Server Configuration
SERVER_HOST = os.getenv("PHANTOM_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("PHANTOM_PORT", 8000))
MT5_SOCKET_PORT = int(os.getenv("MT5_PORT", 9988))

# Allowed CORS Origins (Restricted to localhost/local IPs for security)
ALLOWED_ORIGINS = [
    f"http://127.0.0.1:{SERVER_PORT}",
    f"http://localhost:{SERVER_PORT}",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

# Supported Market Pairs
DEFAULT_PAIRS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]
TIMEFRAMES = ["1S", "M1", "M5", "M15", "H1", "H4", "D1"]

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


def _derive_machine_key() -> bytes:
    """Derives a deterministic, host-unique encryption key from machine hardware identity."""
    salt = f"{platform.node()}_{platform.processor()}_{os.environ.get('USERNAME', os.environ.get('USER', 'phantom'))}"
    return hashlib.sha256(salt.encode("utf-8")).digest()


def _encrypt_payload(data_str: str) -> str:
    """Encrypts string with machine-derived key."""
    key = _derive_machine_key()
    raw = data_str.encode("utf-8")
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
    return "ENC:" + base64.b64encode(encrypted).decode("utf-8")


def _decrypt_payload(enc_str: str) -> str:
    """Decrypts string with machine-derived key."""
    if not enc_str.startswith("ENC:"):
        return enc_str  # Plaintext fallback for legacy
    raw_b64 = enc_str[4:]
    encrypted = base64.b64decode(raw_b64.encode("utf-8"))
    key = _derive_machine_key()
    decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])
    return decrypted.decode("utf-8")


def load_keys_vault() -> dict:
    """Load local encrypted API keys from user machine."""
    if KEY_VAULT_FILE.exists():
        try:
            with open(KEY_VAULT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                if content.startswith("ENC:"):
                    decrypted_json = _decrypt_payload(content)
                    return json.loads(decrypted_json)
                else:
                    # Legacy plaintext: load and auto-upgrade to encrypted
                    data = json.loads(content)
                    save_keys_vault(data)
                    return data
        except Exception as e:
            print(f"[Vault Warning] Failed to load encrypted keys: {e}")
            return {}
    return {}


def save_keys_vault(keys_data: dict) -> bool:
    """Encrypts and saves API keys locally with restricted file permissions."""
    try:
        json_str = json.dumps(keys_data)
        enc_content = _encrypt_payload(json_str)
        with open(KEY_VAULT_FILE, "w", encoding="utf-8") as f:
            f.write(enc_content)
        
        # Set restrictive permissions (user read/write only)
        try:
            os.chmod(KEY_VAULT_FILE, 0o600)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"[Vault Error] Failed to save keys: {e}")
        return False
