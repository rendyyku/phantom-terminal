/**
 * 🦅 PHANTOM TERMINAL - AI WAR ROOM CONTROLLER
 * Orchestrates multi-agent debate UI, live streaming log, and 1-Click execution.
 */

class WarRoomView {
  constructor(app) {
    this.app = app;
    this.isDebating = false;
    this.latestDecision = null;
    this.initElements();
  }

  initElements() {
    this.bullContent = document.getElementById('bull-thesis-content');
    this.bearContent = document.getElementById('bear-thesis-content');
    this.judgeBanner = document.getElementById('judge-decision-banner');
    this.consensusScore = document.getElementById('consensus-score-val');
    this.judgeReasoning = document.getElementById('judge-reasoning-text');
    this.levelEntry = document.getElementById('level-entry');
    this.levelSL = document.getElementById('level-sl');
    this.levelTP = document.getElementById('level-tp');
    this.levelRR = document.getElementById('level-rr');
    this.levelLot = document.getElementById('level-lot');
    this.btnExecute = document.getElementById('btn-execute-1click');
    this.streamLog = document.getElementById('live-stream-log');

    if (this.btnExecute) {
      this.btnExecute.addEventListener('click', () => this.handleExecuteClick());
    }
  }

  appendLog(msg, type = '') {
    if (!this.streamLog) return;
    const div = document.createElement('div');
    div.className = `log-entry ${type}`;
    const timeStr = new Date().toTimeString().split(' ')[0];
    div.textContent = `[${timeStr}] ${msg}`;
    this.streamLog.appendChild(div);
    this.streamLog.scrollTop = this.streamLog.scrollHeight;
  }

  handleEvent(eventData) {
    const { event, data } = eventData;

    switch (event) {
      case 'debate_start':
        this.appendLog(`⚔️ AI War Room activated for ${data.pair}...`, 'judge');
        break;

      case 'agent_thinking':
        this.appendLog(`🧠 ${data.name} is formulating institutional thesis...`, data.agent);
        break;

      case 'bull_thesis_ready':
        if (this.bullContent) this.bullContent.textContent = data.thesis;
        this.appendLog(`🟢 Titan 1 (Claude 3.5) published Bullish Thesis.`, 'bull');
        break;

      case 'bear_thesis_ready':
        if (this.bearContent) this.bearContent.textContent = data.thesis;
        this.appendLog(`🔴 Titan 2 (DeepSeek R1) published Bearish Thesis.`, 'bear');
        break;

      case 'debate_finished':
        this.latestDecision = data;
        this.renderVerdict(data);
        this.appendLog(`⚖️ Supreme Judge issued verdict: ${data.decision} (${data.consensus_score}%)`, 'judge');
        break;
    }
  }

  renderVerdict(decision) {
    if (!decision) return;

    // Consensus Score
    if (this.consensusScore) {
      this.consensusScore.textContent = `${decision.consensus_score || 0}%`;
    }

    // Decision Banner
    if (this.judgeBanner) {
      this.judgeBanner.className = 'decision-banner';
      if (decision.decision === 'BUY') {
        this.judgeBanner.classList.add('decision-buy');
        this.judgeBanner.innerHTML = `🟢 BUY ORDER DETECTED`;
      } else if (decision.decision === 'SELL') {
        this.judgeBanner.classList.add('decision-sell');
        this.judgeBanner.innerHTML = `🔴 SELL ORDER DETECTED`;
      } else {
        this.judgeBanner.classList.add('decision-wait');
        this.judgeBanner.innerHTML = `🟡 STANDBY / NO TRADE`;
      }
    }

    // Levels
    if (this.levelEntry) this.levelEntry.textContent = decision.entry_price || '--';
    if (this.levelSL) this.levelSL.textContent = decision.stop_loss || '--';
    if (this.levelTP) this.levelTP.textContent = decision.take_profit || '--';
    if (this.levelRR) this.levelRR.textContent = decision.risk_reward_ratio || '--';
    if (this.levelLot) this.levelLot.textContent = `${decision.lot_size || 0.50} Lots`;

    if (this.judgeReasoning) {
      this.judgeReasoning.textContent = decision.key_reasoning || '';
    }

    // Enable / Disable 1-Click button
    if (this.btnExecute) {
      if (decision.decision === 'BUY' || decision.decision === 'SELL') {
        this.btnExecute.style.display = 'inline-flex';
        this.btnExecute.className = decision.decision === 'BUY' ? 'btn-glow btn-buy' : 'btn-glow btn-sell';
        this.btnExecute.innerHTML = `⚡ 1-CLICK MT5 EXECUTION (${decision.decision} ${decision.pair})`;
      } else {
        this.btnExecute.style.display = 'none';
      }
    }
  }

  async handleExecuteClick() {
    if (!this.latestDecision || this.latestDecision.decision === 'WAIT') return;

    this.app.playSound('click');
    const orderPayload = {
      pair: this.latestDecision.pair || this.app.currentPair,
      action: this.latestDecision.decision,
      entry_price: this.latestDecision.entry_price,
      stop_loss: this.latestDecision.stop_loss,
      take_profit: this.latestDecision.take_profit,
      comment: `Phantom WarRoom (${this.latestDecision.consensus_score}%)`
    };

    try {
      this.appendLog(`📡 Dispatching ${orderPayload.action} order to MT5 Bridge...`, 'judge');
      const baseUrl = (window.location.origin && window.location.origin.startsWith('http')) ? window.location.origin : 'http://127.0.0.1:8000';
      const resp = await fetch(`${baseUrl}/api/execute-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderPayload)
      });

      const res = await resp.json();
      if (resp.ok) {
        this.app.playSound('success');
        this.app.showToast(`Order ${orderPayload.action} ${orderPayload.pair} executed on MT5!`, 'success');
        this.appendLog(`✅ MT5 Execution Confirmed. Lot: ${res.order.volume}. SL: ${res.order.sl}`, 'judge');
      } else {
        this.app.playSound('error');
        this.app.showToast(`Execution Blocked: ${res.detail}`, 'error');
        this.appendLog(`❌ Execution Blocked: ${res.detail}`, 'bear');
      }
    } catch (e) {
      this.app.showToast(`Connection to Core failed: ${e}`, 'error');
    }
  }
}
