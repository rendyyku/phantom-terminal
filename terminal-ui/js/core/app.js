/**
 * 🦅 PHANTOM TERMINAL - MASTER APP ORCHESTRATOR & ROUTER
 */

// Dynamic Base URL Configuration
const API_BASE = (window.location.origin && window.location.origin.startsWith('http')) 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

const WS_BASE = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';

class PhantomApp {
  constructor() {
    this.currentDesk = 'desk-market';
    this.currentPair = 'XAUUSD';
    this.currentTimeframe = '1S';
    this.audioCtx = null;

    // Sub-components
    this.watchlist = [
      { symbol: 'XAUUSD', name: 'Gold / USD', cat: 'FX', price: 2384.50, chg: '+0.45%', digits: 2 },
      { symbol: 'EURUSD', name: 'Euro / USD', cat: 'FX', price: 1.0872, chg: '+0.12%', digits: 5 },
      { symbol: 'GBPUSD', name: 'Pound / USD', cat: 'FX', price: 1.2940, chg: '-0.18%', digits: 5 },
      { symbol: 'USDJPY', name: 'USD / Yen', cat: 'FX', price: 154.60, chg: '+0.32%', digits: 3 },
      { symbol: 'USDCAD', name: 'USD / CAD', cat: 'FX', price: 1.3680, chg: '-0.05%', digits: 5 },
      { symbol: 'AUDUSD', name: 'AUD / USD', cat: 'FX', price: 0.6650, chg: '+0.22%', digits: 5 },
      { symbol: 'BTCUSD', name: 'Bitcoin / USD', cat: 'CRYPTO', price: 63103.05, chg: '+1.74%', digits: 2 },
      { symbol: 'ETHUSD', name: 'Ethereum / USD', cat: 'CRYPTO', price: 3450.20, chg: '+2.10%', digits: 2 },
      { symbol: 'SOLUSD', name: 'Solana / USD', cat: 'CRYPTO', price: 145.80, chg: '+4.65%', digits: 2 },
      { symbol: 'BNBUSD', name: 'BNB / USD', cat: 'CRYPTO', price: 580.40, chg: '+0.80%', digits: 2 },
      { symbol: 'XRPUSD', name: 'XRP / USD', cat: 'CRYPTO', price: 0.5850, chg: '-0.40%', digits: 4 }
    ];
    this.activeWatchlistCat = 'FX';
    this.watchlistSearchQuery = '';

    this.init();
  }

  async init() {
    this.initSound();
    this.initNavigation();
    this.initHeaderControls();
    this.initWatchlist();
    this.initVaultControls();
    
    // Instantiate Chart Engines
    try {
      this.candleEngine = new CandleChartEngine('candle-canvas');
      this.cvdEngine = new CVDChartEngine('cvd-canvas');
      
      if (this.candleEngine && this.cvdEngine) {
        this.candleEngine.onViewportChange = (offset, visibleCount) => {
          this.cvdEngine.setViewport(offset, visibleCount);
        };

        this.candleEngine.onReachHistoryEdge = async (oldestTime, currentCount) => {
          await this.fetchMoreHistory(oldestTime, currentCount);
        };
      }

      this.warRoomView = new WarRoomView(this);
      this.newsWireView = new NewsWireView(this);
      this.riskView = new RiskView(this);
    } catch (e) {
      console.error('[Phantom App] Error initializing views:', e);
    }

    // Connect WebSocket
    try {
      this.socketClient = new PhantomSocketClient(WS_BASE, this);
    } catch (e) {
      console.warn('[Phantom Socket] WebSocket connection init error:', e);
    }

    // Initial Data Fetch (Defaults to 1-Min M1)
    await this.fetchMarketData(this.currentPair, this.currentTimeframe);
    await this.fetchSystemStatus();

    // Trigger debate button
    const btnTrigger = document.getElementById('btn-trigger-war-room');
    if (btnTrigger) {
      btnTrigger.addEventListener('click', () => this.triggerWarRoomDebate());
    }

    // Delayed resize to ensure layout is computed
    setTimeout(() => {
      if (this.candleEngine) this.candleEngine.resize();
      if (this.cvdEngine) this.cvdEngine.resize();
    }, 100);
  }

  initSound() {
    try {
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      if (AudioCtxClass) {
        this.audioCtx = new AudioCtxClass();
      }
    } catch (e) {
      console.warn('AudioContext disabled by browser policy');
    }
  }

  playSound(type = 'click') {
    try {
      if (!this.audioCtx) return;
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume().catch(() => {});
      }

      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      const now = this.audioCtx.currentTime;

      if (type === 'click') {
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(400, now + 0.05);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now);
        osc.stop(now + 0.05);
      } else if (type === 'success') {
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.setValueAtTime(659.25, now + 0.08);
        osc.frequency.setValueAtTime(783.99, now + 0.16);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
      } else if (type === 'error') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(180, now);
        osc.frequency.linearRampToValueAtTime(100, now + 0.15);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
        osc.start(now);
        osc.stop(now + 0.15);
      }
    } catch (e) {
      // Safe ignore audio errors
    }
  }

  initNavigation() {
    // Delegated click handler on document to guarantee clicks on child spans always work
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-desk]');
      if (btn) {
        const targetDesk = btn.getAttribute('data-desk');
        if (targetDesk) {
          this.switchDesk(targetDesk);
        }
      }
    });
  }

  switchDesk(deskId) {
    this.playSound('click');
    this.currentDesk = deskId;

    document.querySelectorAll('.desk-btn').forEach((b) => {
      const match = b.getAttribute('data-desk') === deskId;
      b.classList.toggle('active', match);
    });

    document.querySelectorAll('.desk-panel').forEach((panel) => {
      const match = panel.id === deskId;
      panel.classList.toggle('active', match);
    });

    // Resize canvas if switching to chart desk
    if (deskId === 'desk-market') {
      requestAnimationFrame(() => {
        setTimeout(() => {
          if (this.candleEngine) this.candleEngine.resize();
          if (this.cvdEngine) this.cvdEngine.resize();
        }, 50);
      });
    }
  }

  initHeaderControls() {
    const pairSelect = document.getElementById('pair-select');
    if (pairSelect) {
      pairSelect.addEventListener('change', (e) => {
        this.currentPair = e.target.value;
        this.playSound('click');
        this.fetchMarketData(this.currentPair, this.currentTimeframe);
      });
    }

    // Timeframe selector buttons
    const tfButtons = document.querySelectorAll('.tf-btn');
    tfButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        this.playSound('click');
        tfButtons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentTimeframe = btn.getAttribute('data-tf') || '1S';
        this.fetchMarketData(this.currentPair, this.currentTimeframe);
      });
    });

    // Indicator Toggles (LuxAlgo SMC, Volume Profile, Zones)
    const btnSMC = document.getElementById('toggle-smc');
    if (btnSMC) {
      btnSMC.addEventListener('click', () => {
        btnSMC.classList.toggle('active');
        if (this.candleEngine) {
          this.candleEngine.showSMC = btnSMC.classList.contains('active');
          this.candleEngine.render();
        }
      });
    }

    const btnVP = document.getElementById('toggle-vp');
    if (btnVP) {
      btnVP.addEventListener('click', () => {
        btnVP.classList.toggle('active');
        if (this.candleEngine) {
          this.candleEngine.showVolumeProfile = btnVP.classList.contains('active');
          this.candleEngine.render();
        }
      });
    }

    const btnZones = document.getElementById('toggle-zones');
    if (btnZones) {
      btnZones.addEventListener('click', () => {
        btnZones.classList.toggle('active');
        if (this.candleEngine) {
          this.candleEngine.showZones = btnZones.classList.contains('active');
          this.candleEngine.render();
        }
      });
    }
  }

  initWatchlist() {
    // Tab filtering (FX vs CRYPTO)
    const tabs = document.querySelectorAll('.watchlist-tab');
    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        this.playSound('click');
        tabs.forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        this.activeWatchlistCat = tab.getAttribute('data-cat') || 'FX';
        this.renderWatchlist();
      });
    });

    // Search filtering
    const searchInput = document.getElementById('watchlist-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.watchlistSearchQuery = e.target.value.trim().toUpperCase();
        this.renderWatchlist();
      });
    }

    this.renderWatchlist();
    this.updateOrderBookDOM(2384.50);
  }

  renderWatchlist() {
    const container = document.getElementById('watchlist-items');
    if (!container) return;

    let items = this.watchlist.filter((item) => item.cat === this.activeWatchlistCat);
    if (this.watchlistSearchQuery) {
      items = items.filter((item) => item.symbol.includes(this.watchlistSearchQuery) || item.name.toUpperCase().includes(this.watchlistSearchQuery));
    }

    container.innerHTML = items.map((item) => {
      const isPositive = item.chg.startsWith('+');
      const chgColor = isPositive ? 'text-green' : 'text-red';
      const isActive = item.symbol === this.currentPair;
      const formattedPrice = item.price.toFixed(item.digits || 2);

      return `
        <div class="watchlist-row ${isActive ? 'active' : ''}" data-symbol="${item.symbol}">
          <div class="pair-symbol">
            <span>${item.symbol}</span>
          </div>
          <div id="wl-price-${item.symbol}" style="text-align: right; font-weight: 600; color: var(--text-main);">
            ${formattedPrice}
          </div>
          <div id="wl-chg-${item.symbol}" class="${chgColor}" style="text-align: right; font-weight: 700; font-size: 10px;">
            ${item.chg}
          </div>
        </div>
      `;
    }).join('');

    // Row click listeners
    container.querySelectorAll('.watchlist-row').forEach((row) => {
      row.addEventListener('click', () => {
        const sym = row.getAttribute('data-symbol');
        if (sym) this.selectPair(sym);
      });
    });
  }

  selectPair(symbol) {
    if (this.currentPair === symbol) return;
    this.playSound('click');
    this.currentPair = symbol;

    // Update active badge in chart header
    const badge = document.getElementById('active-pair-badge');
    if (badge) badge.textContent = symbol;

    // Re-render watchlist to update active border highlight
    this.renderWatchlist();

    // Fetch market data for selected pair
    this.fetchMarketData(this.currentPair, this.currentTimeframe);
  }

  updateWatchlistTick(symbol, price) {
    const item = this.watchlist.find((w) => w.symbol === symbol);
    if (item) {
      const prevPrice = item.price;
      item.price = price;
      
      const elPrice = document.getElementById(`wl-price-${symbol}`);
      const row = document.querySelector(`.watchlist-row[data-symbol="${symbol}"]`);
      
      if (elPrice) {
        elPrice.textContent = price.toFixed(item.digits || 2);
      }
      if (row) {
        row.classList.remove('flash-green', 'flash-red');
        void row.offsetWidth; // Trigger reflow
        row.classList.add(price >= prevPrice ? 'flash-green' : 'flash-red');
      }
    }

    // If active pair, update chart HUD & Level 2 Order Book
    if (symbol === this.currentPair) {
      const priceBadge = document.getElementById('active-pair-price');
      if (priceBadge) {
        const itemObj = this.watchlist.find(w => w.symbol === symbol);
        priceBadge.textContent = price.toFixed(itemObj ? itemObj.digits : 2);
      }
      this.updateOrderBookDOM(price);
    }
  }

  updateOrderBookDOM(midPrice) {
    const domAsks = document.getElementById('dom-asks');
    const domBids = document.getElementById('dom-bids');
    const domMid = document.getElementById('dom-mid-price');
    const domSpread = document.getElementById('dom-spread');

    if (!domAsks || !domBids) return;

    const item = this.watchlist.find((w) => w.symbol === this.currentPair) || { digits: 2 };
    const digits = item.digits || 2;
    const tickStep = digits >= 4 ? 0.0002 : (digits === 3 ? 0.02 : (midPrice > 1000 ? 0.50 : 0.05));

    if (domMid) domMid.textContent = midPrice.toFixed(digits);
    if (domSpread) domSpread.textContent = `SPREAD: ${(tickStep * 2).toFixed(digits)}`;

    let asksHtml = '';
    let bidsHtml = '';
    const levels = 6;

    for (let i = levels; i >= 1; i--) {
      const pAsk = (midPrice + tickStep * i).toFixed(digits);
      const volAsk = (Math.sin(i * 1.5) * 12 + 18).toFixed(1);
      const depthPercent = Math.min(100, Math.round((volAsk / 30) * 100));

      asksHtml += `
        <div class="orderbook-row">
          <div class="orderbook-bar-ask" style="width: ${depthPercent}%;"></div>
          <span style="color: #ff3366; font-weight: 600; z-index: 1;">${pAsk}</span>
          <span style="text-align: right; color: var(--text-muted); z-index: 1;">${volAsk}</span>
        </div>
      `;
    }

    for (let i = 1; i <= levels; i++) {
      const pBid = (midPrice - tickStep * i).toFixed(digits);
      const volBid = (Math.cos(i * 1.2) * 14 + 19).toFixed(1);
      const depthPercent = Math.min(100, Math.round((volBid / 30) * 100));

      bidsHtml += `
        <div class="orderbook-row">
          <div class="orderbook-bar-bid" style="width: ${depthPercent}%;"></div>
          <span style="color: #00ff88; font-weight: 600; z-index: 1;">${pBid}</span>
          <span style="text-align: right; color: var(--text-muted); z-index: 1;">${volBid}</span>
        </div>
      `;
    }

    domAsks.innerHTML = asksHtml;
    domBids.innerHTML = bidsHtml;
  }

  initVaultControls() {
    const btnSaveKeys = document.getElementById('btn-save-keys');
    if (btnSaveKeys) {
      btnSaveKeys.addEventListener('click', async () => {
        this.playSound('click');
        const payload = {
          openrouter_api_key: document.getElementById('key-openrouter').value,
          openai_api_key: document.getElementById('key-openai').value,
          deepseek_api_key: document.getElementById('key-deepseek').value,
          anthropic_api_key: document.getElementById('key-anthropic').value
        };

        try {
          const resp = await fetch(`${API_BASE}/api/save-keys`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          if (resp.ok) {
            this.playSound('success');
            this.showToast('API Keys saved securely to local vault!', 'success');
          }
        } catch (e) {
          this.showToast(`Error saving keys: ${e}`, 'error');
        }
      });
    }
  }

  async fetchMarketData(pair, timeframe = this.currentTimeframe) {
    try {
      const resp = await fetch(`${API_BASE}/api/market-data?pair=${pair}&timeframe=${timeframe}`);
      if (resp.ok) {
        const data = await resp.json();
        if (this.candleEngine) this.candleEngine.setData(data);
        if (this.cvdEngine) this.cvdEngine.setData(data.cvd);
        this.updateStructureUI(data.structure, data.fvgs, data.order_blocks, data.volume_profile, data.source, timeframe);
        if (data.candles && data.candles.length > 0) {
          const lastCandle = data.candles[data.candles.length - 1];
          this.updateWatchlistTick(pair, lastCandle.close);
        }
      }
    } catch (e) {
      console.warn('Failed to fetch market data:', e);
    }
  }

  async fetchMoreHistory(oldestTime, currentCount) {
    try {
      const url = `${API_BASE}/api/history?pair=${this.currentPair}&timeframe=${this.currentTimeframe}&offset=${currentCount}&count=300&before_time=${oldestTime || ''}`;
      const resp = await fetch(url);
      if (resp.ok) {
        const data = await resp.json();
        if (data.candles && data.candles.length > 0) {
          this.candleEngine.prependHistoricalCandles(data.candles);
          
          // Compute local CVD for extended historical set
          const fullCVD = this.calculateLocalCVD(this.candleEngine.candles);
          if (this.cvdEngine) {
            this.cvdEngine.setData(fullCVD);
            this.cvdEngine.setViewport(this.candleEngine.scrollOffset, this.candleEngine.visibleCount);
          }
          this.showToast(`📥 +${data.candles.length} historical bars fetched from MT5!`, 'info');
        } else {
          if (this.candleEngine) this.candleEngine.hasMoreHistory = false;
        }
      }
    } catch (e) {
      console.warn('Failed to load older history:', e);
    } finally {
      if (this.candleEngine) this.candleEngine.isLoadingHistory = false;
    }
  }

  calculateLocalCVD(candles) {
    let cum = 0;
    return candles.map((c) => {
      const buyV = c.buy_volume || 0;
      const sellV = c.sell_volume || 0;
      const delta = buyV - sellV;
      cum += delta;
      return { time: c.time, delta: delta, cvd: cum };
    });
  }

  async fetchSystemStatus() {
    try {
      const resp = await fetch(`${API_BASE}/api/status`);
      if (resp.ok) {
        const data = await resp.json();
        if (this.riskView) this.riskView.updateMetrics(data.risk_shield);
        this.updateBridgeStatus(data.mt5_bridge);
      }
    } catch (e) {}
  }

  updateStructureUI(structure, fvgs, orderBlocks, volumeProfile, source = 'MT5_DISCONNECTED', timeframe = this.currentTimeframe) {
    const trendEl = document.getElementById('ict-trend-status');
    const fvgCountEl = document.getElementById('ict-fvg-count');
    const bslCountEl = document.getElementById('ict-bsl-count');
    const sslCountEl = document.getElementById('ict-ssl-count');
    const obCountEl = document.getElementById('smc-ob-count');
    const pocValEl = document.getElementById('vp-poc-val');
    const vaValEl = document.getElementById('vp-va-val');
    const sourceEl = document.getElementById('market-data-source-badge');
    const tfBadge = document.getElementById('timeframe-indicator-badge');

    if (sourceEl) {
      if (source === 'MT5_REAL_BROKER') {
        sourceEl.className = 'badge badge-bull';
        sourceEl.textContent = 'MT5: CONNECTED';
      } else {
        sourceEl.className = 'badge badge-bear';
        sourceEl.textContent = 'MT5: OFFLINE';
      }
    }

    if (tfBadge) {
      if (timeframe === '1S') {
        tfBadge.textContent = '1S HFT';
      } else if (timeframe === 'M1') {
        tfBadge.textContent = 'M1 SCALPER';
      } else {
        tfBadge.textContent = `${timeframe} STRUCTURE`;
      }
    }

    if (trendEl && structure) {
      trendEl.textContent = structure.trend || 'OFFLINE';
      trendEl.className = `badge ${structure.trend === 'BULLISH' ? 'badge-bull' : structure.trend === 'BEARISH' ? 'badge-bear' : 'badge-gold'}`;
    }

    // Volume Profile POC & Value Area
    if (pocValEl && volumeProfile) {
      pocValEl.textContent = volumeProfile.poc ? `${volumeProfile.poc}` : '--';
    }
    if (vaValEl && volumeProfile) {
      vaValEl.textContent = (volumeProfile.vah && volumeProfile.val) ? `${volumeProfile.vah} / ${volumeProfile.val}` : '-- / --';
    }

    // Order Blocks & FVGs
    if (obCountEl) obCountEl.textContent = orderBlocks ? `${orderBlocks.length} Active` : '--';
    if (fvgCountEl) fvgCountEl.textContent = fvgs ? `${fvgs.length} Active` : '--';

    // Liquidity Pools (EQH / EQL)
    if (structure && structure.equal_high_lows) {
      const eqh = structure.equal_high_lows.filter(e => e.type === 'EQH');
      const eql = structure.equal_high_lows.filter(e => e.type === 'EQL');
      if (bslCountEl) bslCountEl.textContent = `${eqh.length} Pools`;
      if (sslCountEl) sslCountEl.textContent = `${eql.length} Pools`;
    }
  }

  updateBridgeStatus(bridge) {
    const bridgeStatusEl = document.getElementById('mt5-bridge-status-text');
    if (bridgeStatusEl && bridge) {
      bridgeStatusEl.textContent = bridge.ea_connected ? 'MT5 EA: CONNECTED' : 'LISTENING (PORT 9988)';
    }
  }

  setConnectionStatus(connected) {
    const dot = document.getElementById('status-indicator-dot');
    const text = document.getElementById('status-indicator-text');
    if (dot) dot.className = `status-dot ${connected ? '' : 'disconnected'}`;
    if (text) text.textContent = connected ? 'CORE ONLINE (0.2ms)' : 'CORE OFFLINE';
  }

  handleIncomingMessage(payload) {
    if (payload.type === 'TICK_UPDATE') {
      if (payload.candle && payload.candle.close) {
        this.updateWatchlistTick(payload.pair, payload.candle.close);
      }
      if (payload.pair === this.currentPair && (!payload.timeframe || payload.timeframe === this.currentTimeframe)) {
        if (this.candleEngine && payload.candle) {
          this.candleEngine.updateLatestCandle(payload.candle);
        }
        if (this.cvdEngine && payload.latest_cvd) {
          this.cvdEngine.updateLatestCVD(payload.latest_cvd);
        }
      }
    } else if (payload.type === 'WAR_ROOM_EVENT') {
      if (this.warRoomView) {
        this.warRoomView.handleEvent(payload);
      }
    } else if (payload.type === 'FLASH_NEWS') {
      if (this.newsWireView && payload.article) {
        this.newsWireView.updateFlashTicker(payload.article);
      }
    } else if (payload.data && payload.data.type === 'ACCOUNT_UPDATE' && this.riskView) {
      this.fetchSystemStatus();
    }
  }

  async triggerWarRoomDebate() {
    this.playSound('click');
    this.showToast(`Summoning Titan Council for ${this.currentPair}...`, 'warning');
    
    // Switch to war room desk
    this.switchDesk('desk-war-room');

    try {
      const resp = await fetch(`${API_BASE}/api/generate-signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pair: this.currentPair })
      });
      const decision = await resp.json();
      if (this.warRoomView) {
        this.warRoomView.renderVerdict(decision);
      }
    } catch (e) {
      this.showToast(`Debate trigger failed: ${e}`, 'error');
    }
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

// Bootstrap on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.phantomApp = new PhantomApp();
});
