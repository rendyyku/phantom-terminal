import pytest
from bridge.risk_guard import RiskGuard

def test_risk_guard_lot_sizing():
    guard = RiskGuard({"account_balance": 10000.0, "risk_percent_per_trade": 1.0})
    
    # Gold: $100 risk capital, 2.0 SL distance = 100 / (2.0 * 100) = 0.50 lots
    lot, details = guard.calculate_lot_size("XAUUSD", entry_price=2400.0, stop_loss=2398.0)
    assert lot == 0.50
    assert details["risk_capital_usd"] == 100.0

    # JPY: $100 risk capital, 50 pips (0.50 price distance) = 100 / (50 * 10) = 0.20 lots
    lot_jpy, details_jpy = guard.calculate_lot_size("USDJPY", entry_price=150.00, stop_loss=149.50)
    assert lot_jpy == 0.20

def test_risk_guard_hard_stop():
    guard = RiskGuard({"account_balance": 10000.0, "daily_max_drawdown_percent": 3.0, "enable_hard_stop": True})
    
    # Normal state
    guard.update_account_state(balance=10000.0, equity=9900.0)
    assert not guard.is_hard_stopped
    
    # Hit max daily drawdown ($300 loss on $10k)
    guard.update_account_state(balance=10000.0, equity=9650.0)
    assert guard.is_hard_stopped
    
    # Validate trade must be blocked
    is_safe, reason, lot = guard.validate_trade_execution("XAUUSD", 2400.0, 2395.0)
    assert not is_safe
    assert "PROP SHIELD TRIGGERED" in reason
