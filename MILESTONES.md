# 🏛️ PHANTOM TERMINAL - DEVELOPMENT ROADMAP & MILESTONES

> **Vision:** Mengubah Phantom Terminal menjadi Institutional-Grade Quant & Market Intelligence Platform bertaraf **Bloomberg Terminal / Refinitiv Eikon**, tanpa elemen *AI-slop* yang berlebihan, dengan fokus pada *clean minimalism, precision latency, multi-asset data*, dan *actionable alpha*.

---

## 🗺️ Milestone Overview

```
[ MILESTONE 1 ] ➔ Bloomberg Clean Minimalist UI (Anti-AI Slop)
[ MILESTONE 2 ] ➔ Crypto Division via Free Binance Public API (Spot & Futures)
[ MILESTONE 3 ] ➔ Telegram Bot Real-Time Alpha Radar (BYOB: BOS, CHoCH, OB, FVG Alerts)
[ MILESTONE 4 ] ➔ Dual-Asset Institutional AI War Room (Forex, Gold & Crypto Alpha)
[ MILESTONE 5 ] ➔ Hybrid Multi-Broker Execution (MT5 Forex + Binance API Webhook)
```

---

## 📌 Milestone 1: Bloomberg Clean Minimalist UI Overhaul (Anti-AI Slop)
**Goal:** Menghilangkan elemen visual *gimmick* (gradien berlebihan, teks AI slop yang berulang, animasi lambat) dan menggantinya dengan estetika **Institutional Dark Terminal**: padat, super-tajam, fungsional, dan memiliki *information density* tinggi layaknya terminal trader Wall Street.

### 🎯 Key Deliverables:
- [ ] **Design System Overhaul (`terminal.css` & `components.css`):**
  - Palet warna institusional: Deep Slate (`#0B0E14`), Obsidian (`#101520`), High-Contrast Accent (Bloomberg Amber `#F59E0B`, Reuters Cyan `#06B6D4`, Bloomberg Green `#10B981`, Wall Street Crimson `#EF4444`).
  - Typography: **JetBrains Mono** untuk seluruh angka kuantitatif, tabel, dan data tick; **Inter** untuk label navigasi.
  - Border mikro 1px tajam tanpa glow kabur yang mengganggu pandangan (*zero visual clutter*).
- [ ] **Header & Workspace Optimization:**
  - Header ramping 36px (*Ultra-Slim Global Toolbar*) berisi Asset Selector, Connection Health, Memory Usage, dan Quick Hotkeys (`F1`-`F5`).
  - Modular Workspace Grid: Chart Area, Level 2 / Orderbook, Tape / Tick Stream, dan Intelligence Panel.
- [ ] **Clean Chart HUD:**
  - Crosshair presisi dengan status bar HUD di pojok atas chart: Open, High, Low, Close, Volume, Spread, Change %, dan ATR.
  - Quick-switch toggle buttons minimalis untuk SMC overlays dan Volume Profile.

---

## 📌 Milestone 2: Divisi Crypto Terintegrasi (Free Binance Public API)
**Goal:** Membuka akses penuh ke pasar Crypto 24/7/365 menggunakan **Binance Public Market API (100% Gratis & Tanpa Perlu API Key)** dengan latensi rendah via WebSockets.

### 🎯 Key Deliverables:
- [ ] **Binance Connector Engine (`bridge/binance_feed.py`):**
  - **REST API:** Fetch historical OHLCV klines (1s, 1m, 5m, 15m, 1h, 4h, 1d) hingga 1.000 candle secara instan.
  - **WebSocket Live Stream (`wss://stream.binance.com:9443`):**
    - `@kline_1s` / `@kline_1m` live candlestick streaming.
    - `@trade` & `@aggTrade` untuk kalkulasi CVD real-time dari transaksi pasar crypto global.
    - `@ticker` / `@miniTicker` untuk daftar 24h gainers/losers radar.
- [ ] **Seamless Dual-Market Switcher (Forex/Gold MT5 ⇄ Binance Crypto):**
  - User dapat beralih aset kapan saja:
    - **Forex & Commodities (via MT5):** `XAUUSD (Gold)`, `EURUSD`, `GBPUSD`, `USDJPY`, `USOIL`.
    - **Crypto (via Binance):** `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `XRPUSDT`, `DOGEUSDT`.
  - Chart secara otomatis menyesuaikan desimal presisi (misal: BTC 2 desimal, XRP 4 desimal, Gold 2 desimal).
- [ ] **Crypto Market Intelligence Bar:**
  - 24h Volume, Funding Rate, Long/Short Ratio, dan Open Interest snapshot.

---

## 📌 Milestone 3: Telegram Bot Real-Time Alpha Radar (BYOB: Custom Alerts)
**Goal:** Memberikan pengguna kebebasan menghubungkan bot Telegram pribadi mereka (*Bring Your Own Bot*) untuk menerima notifikasi sinyal dan struktur pasar institusional secara *instant & sub-second*.

### 🎯 Key Deliverables:
- [ ] **Telegram Dispatcher Engine (`engine/telegram_notifier.py`):**
  - Penyimpanan aman `Bot Token` & `Chat ID` di dalam local vault terminal.
  - Asynchronous non-blocking message dispatcher via Telegram Bot API (`https://api.telegram.org/bot<token>/sendMessage`).
- [ ] **Institutional Event Triggers:**
  - ⚡ **BOS Alert:** Terpicu saat harga menembus level swing/internal dengan label harga & timeframe.
  - 🔄 **CHoCH Alert:** Terpicu saat terjadi pembalikan tren struktural (*Change of Character*).
  - 📦 **Order Block Tap (+OB / -OB):** Terpicu saat harga memasuki zona *Unmitigated Order Block*.
  - 🎯 **FVG Entry & Liquidity Sweep:** Terpicu saat harga menyapu area BSL/SSL atau masuk ke Fair Value Gap.
  - 🤖 **AI War Room Signal Consensus:** Notifikasi instan saat AI Titan Council mencapai konsensus entry dengan probabilitas > 80%.
- [ ] **Telegram Notification Formatting (Bloomberg Style):**
  ```text
  🏛️ [PHANTOM RADAR] MARKET STRUCTURE BREAK
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Pair      : XAUUSD (Gold)
  Timeframe : M1 (Scalper)
  Event     : ⚡ BULLISH BOS DETECTED
  Price     : 2,384.50
  Volume    : CVD Delta +420 (Institutional Buying)
  Action    : Monitor for pullback into +OB at 2,381.20
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```
- [ ] **Telegram Settings UI di Terminal:**
  - Form input Bot Token & Chat ID dengan tombol **"🧪 Send Test Ping"** dan switch toggle untuk memilih alert yang ingin diaktifkan.

---

## 📌 Milestone 4: AI Titan War Room V2 (Deterministic Institutional Prompting)
**Goal:** Membersihkan output AI agar menghasilkan analisis institusional yang *to-the-point*, matematis, dan berlandaskan probabilitas kuantitatif tanpa basa-basi naratif yang panjang.

### 🎯 Key Deliverables:
- [ ] **Kuantitatif Structured Output:**
  - Entry Zone (Exact price), Invalidation / Stop Loss, Take Profit 1 & 2, Expected R:R ratio, Probability Score (0-100%).
- [ ] **Asset-Specific Reasoning:**
  - Analisis Makro DXY & Yields untuk Forex/Gold.
  - Analisis BTC Dominance & Liquidity Sweeps untuk Crypto.

---

## 📌 Milestone 5: Hybrid Execution Engine (Optional Live Automation)
**Goal:** Eksekusi fleksibel ke broker MT5 (Forex) atau akun Binance pengguna jika API key eksekusi dimasukkan.

---

## 📊 Roadmap Timeline & Priority Matrix

| Phase | Milestone | Estimasi Pengerjaan | Status |
|---|---|---|---|
| **Milestone 1** | 🏛️ Bloomberg Clean Minimalist UI Overhaul | Sprint 1 | ⏳ **Siap Dieksekusi** |
| **Milestone 2** | 🪙 Binance Public API Crypto Engine (Free 24/7) | Sprint 2 | ⏳ **Siap Dieksekusi** |
| **Milestone 3** | 📱 Telegram Bot Real-Time Alpha Radar (BOS/CHoCH/OB) | Sprint 3 | ⏳ **Siap Dieksekusi** |
| **Milestone 4** | 🧠 Quantitative Multi-Asset AI War Room | Sprint 4 | 📋 Terencana |
| **Milestone 5** | ⚡ Hybrid Execution & Alert Webhooks | Sprint 5 | 📋 Terencana |
