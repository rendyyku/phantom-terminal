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
      // --- FOREX & COMMODITIES ---
      { symbol: 'XAUUSD', name: 'Gold / USD', cat: 'FX', price: 2384.50, chg: '+0.45%', digits: 2 },
      { symbol: 'EURUSD', name: 'Euro / USD', cat: 'FX', price: 1.0872, chg: '+0.12%', digits: 5 },
      { symbol: 'GBPUSD', name: 'Pound / USD', cat: 'FX', price: 1.2940, chg: '-0.18%', digits: 5 },
      { symbol: 'USDJPY', name: 'USD / Yen', cat: 'FX', price: 154.60, chg: '+0.32%', digits: 3 },
      { symbol: 'USDCAD', name: 'USD / CAD', cat: 'FX', price: 1.3680, chg: '-0.05%', digits: 5 },
      { symbol: 'AUDUSD', name: 'AUD / USD', cat: 'FX', price: 0.6650, chg: '+0.22%', digits: 5 },
      { symbol: 'NZDUSD', name: 'NZD / USD', cat: 'FX', price: 0.6020, chg: '+0.15%', digits: 5 },
      { symbol: 'USDCHF', name: 'USD / CHF', cat: 'FX', price: 0.8840, chg: '-0.08%', digits: 5 },
      { symbol: 'GBPJPY', name: 'GBP / JPY', cat: 'FX', price: 200.15, chg: '+0.40%', digits: 3 },
      { symbol: 'EURJPY', name: 'EUR / JPY', cat: 'FX', price: 168.20, chg: '+0.28%', digits: 3 },

      // --- CRYPTO: LAYER 1 & MAJORS ---
      { symbol: 'BTCUSDT', name: 'Bitcoin', cat: 'CRYPTO', price: 63100.00, chg: '+1.74%', digits: 2 },
      { symbol: 'ETHUSDT', name: 'Ethereum', cat: 'CRYPTO', price: 3450.20, chg: '+2.10%', digits: 2 },
      { symbol: 'SOLUSDT', name: 'Solana', cat: 'CRYPTO', price: 145.80, chg: '+4.65%', digits: 2 },
      { symbol: 'BNBUSDT', name: 'BNB', cat: 'CRYPTO', price: 580.40, chg: '+0.80%', digits: 2 },
      { symbol: 'XRPUSDT', name: 'Ripple', cat: 'CRYPTO', price: 0.5850, chg: '-0.40%', digits: 4 },
      { symbol: 'ADAUSDT', name: 'Cardano', cat: 'CRYPTO', price: 0.3520, chg: '+1.15%', digits: 4 },
      { symbol: 'AVAXUSDT', name: 'Avalanche', cat: 'CRYPTO', price: 22.40, chg: '+3.20%', digits: 2 },
      { symbol: 'SUIUSDT', name: 'Sui', cat: 'CRYPTO', price: 0.8850, chg: '+6.10%', digits: 4 },
      { symbol: 'NEARUSDT', name: 'NEAR Protocol', cat: 'CRYPTO', price: 4.52, chg: '+3.80%', digits: 3 },
      { symbol: 'APTUSDT', name: 'Aptos', cat: 'CRYPTO', price: 6.75, chg: '+2.45%', digits: 2 },
      { symbol: 'TONUSDT', name: 'Toncoin', cat: 'CRYPTO', price: 6.65, chg: '+1.05%', digits: 3 },
      { symbol: 'TRXUSDT', name: 'TRON', cat: 'CRYPTO', price: 0.1320, chg: '+0.60%', digits: 4 },
      { symbol: 'DOTUSDT', name: 'Polkadot', cat: 'CRYPTO', price: 4.60, chg: '+0.95%', digits: 3 },
      { symbol: 'LINKUSDT', name: 'Chainlink', cat: 'CRYPTO', price: 11.25, chg: '+2.80%', digits: 3 },
      { symbol: 'LTCUSDT', name: 'Litecoin', cat: 'CRYPTO', price: 65.40, chg: '+0.75%', digits: 2 },

      // --- CRYPTO: AI & COMPUTE ---
      { symbol: 'TAOUSDT', name: 'Bittensor (TAO)', cat: 'CRYPTO', price: 310.50, chg: '+7.40%', digits: 2 },
      { symbol: 'RENDERUSDT', name: 'Render', cat: 'CRYPTO', price: 5.65, chg: '+5.20%', digits: 3 },
      { symbol: 'FETUSDT', name: 'Artificial Superintelligence', cat: 'CRYPTO', price: 1.15, chg: '+4.80%', digits: 4 },
      { symbol: 'WLDUSDT', name: 'Worldcoin', cat: 'CRYPTO', price: 1.62, chg: '+3.10%', digits: 3 },
      { symbol: 'ARKMUSDT', name: 'Arkham', cat: 'CRYPTO', price: 1.18, chg: '+4.30%', digits: 3 },

      // --- CRYPTO: MEMES & HIGH BETA ---
      { symbol: 'DOGEUSDT', name: 'Dogecoin', cat: 'CRYPTO', price: 0.1045, chg: '+2.15%', digits: 5 },
      { symbol: 'SHIBUSDT', name: 'Shiba Inu', cat: 'CRYPTO', price: 0.000014, chg: '+1.80%', digits: 7 },
      { symbol: 'PEPEUSDT', name: 'Pepe', cat: 'CRYPTO', price: 0.000008, chg: '+6.50%', digits: 8 },
      { symbol: 'WIFUSDT', name: 'dogwifhat', cat: 'CRYPTO', price: 1.65, chg: '+8.20%', digits: 3 },
      { symbol: 'BONKUSDT', name: 'Bonk', cat: 'CRYPTO', price: 0.000021, chg: '+5.10%', digits: 7 },
      { symbol: 'FLOKIUSDT', name: 'Floki', cat: 'CRYPTO', price: 0.000125, chg: '+3.40%', digits: 6 },

      // --- CRYPTO: DEFI & MODULAR ---
      { symbol: 'UNIUSDT', name: 'Uniswap', cat: 'CRYPTO', price: 6.45, chg: '+1.90%', digits: 3 },
      { symbol: 'AAVEUSDT', name: 'Aave', cat: 'CRYPTO', price: 112.30, chg: '+4.10%', digits: 2 },
      { symbol: 'PENDLEUSDT', name: 'Pendle', cat: 'CRYPTO', price: 2.85, chg: '+5.60%', digits: 3 },
      { symbol: 'INJUSDT', name: 'Injective', cat: 'CRYPTO', price: 19.80, chg: '+3.70%', digits: 2 },
      { symbol: 'TIAUSDT', name: 'Celestia', cat: 'CRYPTO', price: 5.40, chg: '+2.30%', digits: 3 },
      { symbol: 'SEIUSDT', name: 'Sei Network', cat: 'CRYPTO', price: 0.3150, chg: '+4.05%', digits: 4 },
      { symbol: 'JUPUSDT', name: 'Jupiter', cat: 'CRYPTO', price: 0.8250, chg: '+3.90%', digits: 4 },
      { symbol: 'ENAUSDT', name: 'Ethena', cat: 'CRYPTO', price: 0.3200, chg: '+1.75%', digits: 4 }
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
    this.initOrderBookEngine();
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
    this.fetchCryptoTickers();
  }

  async fetchCryptoTickers() {
    try {
      const resp = await fetch(`${API_BASE}/api/crypto/tickers`);
      if (resp.ok) {
        const tickers = await resp.json();
        for (const sym in tickers) {
          const t = tickers[sym];
          const item = this.watchlist.find((w) => w.symbol === sym);
          if (item) {
            item.price = t.price;
            item.chg = t.change_str;
          }
        }
        this.renderWatchlist();
      }
    } catch (e) {
      console.warn('Failed to fetch crypto tickers:', e);
    }
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

  updateWatchlistTick(symbol, price, changeStr = null) {
    const item = this.watchlist.find((w) => w.symbol === symbol);
    if (item) {
      const prevPrice = item.price;
      item.price = price;
      if (changeStr) item.chg = changeStr;
      
      const elPrice = document.getElementById(`wl-price-${symbol}`);
      const elChg = document.getElementById(`wl-chg-${symbol}`);
      const row = document.querySelector(`.watchlist-row[data-symbol="${symbol}"]`);
      
      if (elPrice) {
        elPrice.textContent = price.toFixed(item.digits || 2);
      }
      if (elChg && changeStr) {
        elChg.textContent = changeStr;
        elChg.className = changeStr.startsWith('+') ? 'text-green' : 'text-red';
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

  initOrderBookEngine() {
    this.domMidPrice = 2384.50;
    this.domLastUpdate = Date.now();

    // High-frequency Level 2 DOM Pulsar (Updates order queue quantities & depth bars every 300ms)
    setInterval(() => {
      this.pulseOrderBookDOM();
    }, 300);
  }

  pulseOrderBookDOM() {
    if (!this.domMidPrice) {
      const item = this.watchlist.find((w) => w.symbol === this.currentPair);
      if (item && item.price) this.domMidPrice = item.price;
    }
    if (this.domMidPrice) {
      this.renderOrderBookDOM(this.domMidPrice);
    }
  }

  updateOrderBookDOM(midPrice) {
    if (!midPrice || isNaN(midPrice) || midPrice <= 0) return;
    this.domMidPrice = midPrice;
    this.renderOrderBookDOM(midPrice);
  }

  renderOrderBookDOM(midPrice) {
    const domAsks = document.getElementById('dom-asks');
    const domBids = document.getElementById('dom-bids');
    const domMid = document.getElementById('dom-mid-price');
    const domSpread = document.getElementById('dom-spread');

    if (!domAsks || !domBids) return;

    const item = this.watchlist.find((w) => w.symbol === this.currentPair) || { digits: 2 };
    const digits = item.digits || 2;
    
    // Dynamic tick size based on price magnitude
    let tickStep = 0.01;
    if (digits >= 5) tickStep = 0.0001;
    else if (digits === 4) tickStep = 0.0002;
    else if (digits === 3) tickStep = 0.02;
    else if (digits === 2 && midPrice > 10000) tickStep = 5.0;
    else if (digits === 2 && midPrice > 1000) tickStep = 0.50;
    else if (digits === 2) tickStep = 0.05;

    const spreadValue = (tickStep * (1.2 + Math.sin(Date.now() / 2000) * 0.4)).toFixed(digits);

    if (domMid) domMid.textContent = midPrice.toFixed(digits);
    if (domSpread) domSpread.textContent = `SPREAD: ${spreadValue}`;

    let asksHtml = '';
    let bidsHtml = '';
    const levels = 6;
    const t = Date.now() / 1000;

    for (let i = levels; i >= 1; i--) {
      const pAsk = (midPrice + tickStep * i).toFixed(digits);
      // Realistic oscillating market depth with micro-noise
      const baseVol = Math.abs(Math.sin(t * 1.8 + i * 2.1) * 16) + (10 + i * 2.5) + (Math.random() * 2.5);
      const volAsk = baseVol.toFixed(digits >= 4 ? 2 : 1);
      const depthPercent = Math.min(100, Math.round((baseVol / 38) * 100));

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
      const baseVol = Math.abs(Math.cos(t * 1.6 + i * 1.9) * 16) + (10 + i * 2.5) + (Math.random() * 2.5);
      const volBid = baseVol.toFixed(digits >= 4 ? 2 : 1);
      const depthPercent = Math.min(100, Math.round((baseVol / 38) * 100));

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
      if (source === 'BINANCE_PUBLIC_API') {
        sourceEl.className = 'badge badge-bull';
        sourceEl.textContent = 'BINANCE: 24/7 LIVE';
      } else if (source === 'MT5_REAL_BROKER') {
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
    if (payload.type === 'CRYPTO_TICK') {
      this.updateWatchlistTick(payload.symbol, payload.price, payload.change_str);
    } else if (payload.type === 'TICK_UPDATE') {
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
