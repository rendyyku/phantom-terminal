import time
from datetime import datetime, timezone
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
        self.current_day_utc = datetime.now(timezone.utc).day

    def _check_daily_reset(self):
        """Resets daily starting balance and drawdown metrics at 00:00 UTC."""
        today_utc = datetime.now(timezone.utc).day
        if today_utc != self.current_day_utc:
            self.current_day_utc = today_utc
            self.starting_daily_balance = self.current_balance
            self.daily_pnl = 0.0
            self.is_hard_stopped = False
            self.lockout_reason = ""

    def update_account_state(self, balance: float, equity: float, active_trades: int = 0):
        """Updates live account state from MT5."""
        self._check_daily_reset()
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
        Supports standard Forex (0.0001 pip), JPY crosses (0.01 pip), Gold ($1.00 = $100), and Crypto.
        """
        risk_percent = self.settings.get("risk_percent_per_trade", 1.0)
        risk_capital = self.current_balance * (risk_percent / 100.0)
        
        sl_distance = abs(entry_price - stop_loss)
        pair_upper = pair.upper()

        if "XAU" in pair_upper or "GOLD" in pair_upper:
            # Gold: 1 lot = 100 oz. $1.00 move = $100/lot
            sl_distance = max(0.20, sl_distance)
            dollar_per_point_per_lot = 100.0
            lot_size = risk_capital / (sl_distance * dollar_per_point_per_lot)
        elif "JPY" in pair_upper:
            # JPY Crosses: 1 pip = 0.01. $10/pip on standard lot (approx)
            sl_distance = max(0.02, sl_distance)
            pips = sl_distance / 0.01
            dollar_per_pip_per_lot = 10.0
            lot_size = risk_capital / (pips * dollar_per_pip_per_lot)
        elif "BTC" in pair_upper or "ETH" in pair_upper or "USDT" in pair_upper:
            # Crypto: 1 unit contract
            sl_distance = max(1.0, sl_distance)
            lot_size = risk_capital / sl_distance
        else:
            # Standard Forex (EURUSD, GBPUSD): 1 pip = 0.0001. $10/pip on standard lot
            sl_distance = max(0.0002, sl_distance)
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
        self._check_daily_reset()
        if self.is_hard_stopped:
            return False, self.lockout_reason, 0.0

        if self.active_trades_count >= self.settings.get("max_open_trades", 3):
            return False, f"Max open trades limit reached ({self.active_trades_count}/{self.settings['max_open_trades']})", 0.0

        lot, details = self.calculate_lot_size(pair, entry_price, stop_loss)
        return True, "Risk validation PASSED", lot

    def get_risk_status(self) -> Dict[str, Any]:
        """Returns risk shield metrics for the UI."""
        self._check_daily_reset()
        max_daily_loss = self.starting_daily_balance * (self.settings["daily_max_drawdown_percent"] / 100.0)
        current_drawdown_percent = 0.0
        if self.daily_pnl < 0:
            current_drawdown_percent = abs(self.daily_pnl) / self.starting_daily_balance * 100.0

        return {
            "account_balance": round(self.current_balance, 2),
            "current_equity": round(self.current_equity, 2),
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
