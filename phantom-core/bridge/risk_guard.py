import time
from typing import Dict, Any, Tuple
from config import DEFAULT_RISK_SETTINGS

class RiskGuard:
    """
    Military-grade Prop Firm Risk Shield & Auto Lot Sizer.
    Protects against FTMO / The5ers / FundedNext daily drawdown violations.
    """

    def __init__(self, initial_settings: Dict[str, Any] = None):
        self.settings = initial_settings or DEFAULT_RISK_SETTINGS.copy()
        self.starting_daily_balance = self.settings.get("account_balance", 10000.0)
        self.current_balance = self.starting_daily_balance
        self.current_equity = self.starting_daily_balance
        self.daily_pnl = 0.0
        self.is_hard_stopped = False
        self.lockout_reason = ""
        self.active_trades_count = 0

    def update_account_state(self, balance: float, equity: float, active_trades: int = 0):
        """Updates live account state from MT5."""
        self.current_balance = balance
        self.current_equity = equity
        self.daily_pnl = self.current_equity - self.starting_daily_balance
        self.active_trades_count = active_trades

        # Evaluate Hard Stop Drawdown
        max_loss = self.starting_daily_balance * (self.settings["daily_max_drawdown_percent"] / 100.0)
        if self.daily_pnl <= -max_loss and self.settings.get("enable_hard_stop", True):
            self.is_hard_stopped = True
            self.lockout_reason = f"🚨 PROP SHIELD TRIGGERED: Daily loss (-${abs(self.daily_pnl):.2f}) exceeded max allowed -{self.settings['daily_max_drawdown_percent']}% (-${max_loss:.2f})"

    def calculate_lot_size(self, pair: str, entry_price: float, stop_loss: float) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates exact position lot size based on account balance, risk percent, and SL distance.
        """
        risk_percent = self.settings.get("risk_percent_per_trade", 1.0)
        risk_capital = self.current_balance * (risk_percent / 100.0)
        
        sl_distance = abs(entry_price - stop_loss)
        if sl_distance <= 0:
            sl_distance = 1.0 if "XAU" in pair else 0.0020

        # Pip value & Contract size
        # Gold: 1 lot = 100 oz. 1.0 price move = $100 per lot.
        # Forex: 1 lot = 100,000 units. 0.0001 price move (1 pip) = $10 per lot.
        if "XAU" in pair or "GOLD" in pair:
            dollar_per_point_per_lot = 100.0  # $1.00 move on 1.0 lot = $100
            lot_size = risk_capital / (sl_distance * dollar_per_point_per_lot)
        else:
            pips = sl_distance / 0.0001
            dollar_per_pip_per_lot = 10.0
            lot_size = risk_capital / (pips * dollar_per_pip_per_lot)

        # Standard lot clamping
        lot_size = max(0.01, min(round(lot_size, 2), 50.0))

        details = {
            "risk_capital_usd": round(risk_capital, 2),
            "risk_percent": risk_percent,
            "sl_distance": round(sl_distance, 5),
            "calculated_lot": lot_size,
            "account_balance": self.current_balance
        }

        return lot_size, details

    def validate_trade_execution(self, pair: str, entry_price: float, stop_loss: float) -> Tuple[bool, str, float]:
        """
        Validates if a trade is safe to execute according to Prop Firm rules.
        """
        if self.is_hard_stopped:
            return False, self.lockout_reason, 0.0

        if self.active_trades_count >= self.settings.get("max_open_trades", 3):
            return False, f"Max open trades limit reached ({self.active_trades_count}/{self.settings['max_open_trades']})", 0.0

        lot, details = self.calculate_lot_size(pair, entry_price, stop_loss)
        return True, "Risk validation PASSED", lot

    def get_risk_status(self) -> Dict[str, Any]:
        """Returns risk shield metrics for the UI."""
        max_daily_loss = self.starting_daily_balance * (self.settings["daily_max_drawdown_percent"] / 100.0)
        current_drawdown_percent = 0.0
        if self.daily_pnl < 0:
            current_drawdown_percent = abs(self.daily_pnl) / self.starting_daily_balance * 100.0

        return {
            "account_balance": self.current_balance,
            "current_equity": self.current_equity,
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_drawdown_percent": round(current_drawdown_percent, 2),
            "max_daily_drawdown_percent": self.settings["daily_max_drawdown_percent"],
            "max_daily_loss_usd": round(max_daily_loss, 2),
            "is_hard_stopped": self.is_hard_stopped,
            "lockout_reason": self.lockout_reason,
            "active_trades": self.active_trades_count,
            "max_open_trades": self.settings["max_open_trades"],
            "risk_per_trade_percent": self.settings["risk_percent_per_trade"],
            "prop_firm_mode": self.settings.get("prop_firm_mode", True)
        }
