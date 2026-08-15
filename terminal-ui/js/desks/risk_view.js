/**
 * 🦅 PHANTOM TERMINAL - RISK SHIELD & PROP FIRM MANAGER
 * Manages daily drawdown guards (FTMO/The5ers) and real-time lot calculator.
 */

class RiskView {
  constructor(app) {
    this.app = app;
    this.initElements();
  }

  initElements() {
    this.balanceInput = document.getElementById('risk-balance-input');
    this.riskPerTradeInput = document.getElementById('risk-per-trade-input');
    this.dailyDrawdownInput = document.getElementById('risk-daily-dd-input');
    this.maxTradesInput = document.getElementById('risk-max-trades-input');
    this.btnSaveRisk = document.getElementById('btn-save-risk');

    this.statBalance = document.getElementById('stat-account-balance');
    this.statEquity = document.getElementById('stat-account-equity');
    this.statDailyPnL = document.getElementById('stat-daily-pnl');
    this.statDrawdownPercent = document.getElementById('stat-drawdown-percent');
    this.hardStopBadge = document.getElementById('hard-stop-badge');

    if (this.btnSaveRisk) {
      this.btnSaveRisk.addEventListener('click', () => this.saveRiskSettings());
    }
  }

  updateMetrics(riskData) {
    if (!riskData) return;

    if (this.statBalance) this.statBalance.textContent = `$${(riskData.account_balance || 10000).toLocaleString()}`;
    if (this.statEquity) this.statEquity.textContent = `$${(riskData.current_equity || 10000).toLocaleString()}`;
    
    if (this.statDailyPnL) {
      const pnl = riskData.daily_pnl || 0.0;
      this.statDailyPnL.textContent = `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`;
      this.statDailyPnL.className = `stat-val ${pnl >= 0 ? 'text-green' : 'text-red'}`;
    }

    if (this.statDrawdownPercent) {
      const dd = riskData.daily_drawdown_percent || 0.0;
      this.statDrawdownPercent.textContent = `${dd.toFixed(2)}% / ${riskData.max_daily_drawdown_percent}%`;
    }

    if (this.hardStopBadge) {
      if (riskData.is_hard_stopped) {
        this.hardStopBadge.className = 'badge badge-bear';
        this.hardStopBadge.textContent = '🚨 LOCKED (HARD STOP REACHED)';
      } else {
        this.hardStopBadge.className = 'badge badge-bull';
        this.hardStopBadge.textContent = '🛡️ ACTIVE & PROTECTED';
      }
    }
  }

  async saveRiskSettings() {
    this.app.playSound('click');
    const payload = {
      account_balance: parseFloat(this.balanceInput.value) || 10000.0,
      risk_percent_per_trade: parseFloat(this.riskPerTradeInput.value) || 1.0,
      daily_max_drawdown_percent: parseFloat(this.dailyDrawdownInput.value) || 3.0,
      max_open_trades: parseInt(this.maxTradesInput.value) || 3,
      enable_hard_stop: true,
      prop_firm_mode: true
    };

    try {
      const baseUrl = (window.location.origin && window.location.origin.startsWith('http')) ? window.location.origin : 'http://127.0.0.1:8000';
      const resp = await fetch(`${baseUrl}/api/update-risk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (resp.ok) {
        this.updateMetrics(data.risk_settings);
        this.app.playSound('success');
        this.app.showToast('Prop Firm Risk parameters updated successfully!', 'success');
      }
    } catch (e) {
      this.app.showToast(`Failed to update risk settings: ${e}`, 'error');
    }
  }
}
