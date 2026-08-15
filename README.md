# 🦅 PHANTOM TERMINAL
### *The Modern Open-Core Financial Intelligence Terminal for Forex & Gold*

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Platform: WebGL & Python](https://img.shields.io/badge/Platform-Python%20FastAPI%20%7C%20Canvas%2060FPS-blue.svg)]()
[![MetaTrader 5](https://img.shields.io/badge/Bridge-MetaTrader%205%20(MQL5)-green.svg)]()
[![AI Swarm](https://img.shields.io/badge/AI%20Swarm-Claude%203.5%20%7C%20DeepSeek--R1%20%7C%20GPT--4o-purple.svg)]()

---

## ⚡ Overview
**Phantom Terminal** adalah platform trading institusional open-core yang menggabungkan kemampuan penalaran spasial **AI Frontier Swarm** (Claude 3.5 Sonnet, DeepSeek R1, GPT-4o) dengan analisis mikro **Order Flow** (*Cumulative Volume Delta, Fair Value Gap, Liquidity Sweeps*) dan eksekusi instan 1-klik ke **MetaTrader 5**.

```
[1. Market Stream] ──> [2. Local Math Filter (FVG/CVD)] ──> [3. AI War Room Debate (BYOK)]
                                                                       │
[5. MT5 Terminal Order] <── [4. Prop Risk Shield & Auto-Lot] <─────────┘
```

---

## ✨ Fitur Utama (6 Core Desks)

1. **📊 Desk 1: Market & OrderFlow Desk:**
   * HTML5 Canvas Candlestick Engine 60 FPS dengan tema Cyberpunk Glassmorphism.
   * Cumulative Volume Delta (CVD) & deteksi penyerapan agresif pembeli vs penjual.
   * Radar likuiditas retail (*Equal Highs/Lows - BSL/SSL*) dan deteksi Fair Value Gap (FVG).

2. **⚔️ Desk 2: AI War Room & Swarm Intelligence:**
   * **Titan 1 (Bull Specialist):** Claude 3.5 Sonnet membedah peluang buy berbasis ICT displacement.
   * **Titan 2 (Bear Specialist):** DeepSeek R1 menguji risiko perangkap likuiditas (*Stop Loss hunting*).
   * **Supreme Judge:** GPT-4o menerbitkan keputusan final (*BUY/SELL/WAIT*) beserta skor konsensus & rasio R:R.

3. **🧪 Desk 3: ICT & Quant Strategy Lab:**
   * Filter matematis lokal zero-token untuk menghemat biaya API hingga 90%.

4. **⚡ Desk 4: MT5 Execution Bridge:**
   * Socket non-blocking TCP (< 5 milidetik) menghubungkan kartu sinyal AI langsung ke MetaTrader 5 EA.

5. **🛡️ Desk 5: Risk Manager & Prop Shield:**
   * Pemutus darurat harian (*Hard Stop Drawdown Guard*) untuk perlindungan akun Prop Firm (**FTMO / The5ers / FundedNext**).
   * Kalkulasi ukuran lot otomatis sesuai persentase risiko modal per transaksi.

6. **🔑 Desk 6: BYOK Hub (Bring Your Own Key):**
   * Mendukung OpenRouter, Anthropic, DeepSeek, dan OpenAI dengan penyimpanan kunci terenkripsi 100% lokal di perangkat Anda.

---

## 🚀 Quickstart

### 1. Jalankan Backend Core
```bash
cd phantom-terminal/phantom-core
pip install -r requirements.txt
python server.py
```

### 2. Buka Terminal UI
Buka file `phantom-terminal/terminal-ui/index.html` di browser Anda, atau klik dua kali `start_terminal.bat`.

### 3. Pasang MT5 EA (Opsional)
Salin `phantom-terminal/mt5-executor/Phantom_Executor.mq5` ke folder `MQL5/Experts/` pada MetaTrader 5 Anda dan aktifkan Algo Trading.

---

## 🏛️ Arsitektur Direktori
```
phantom-terminal/
├── terminal-ui/         # WebGL & Canvas Dashboard Cyberpunk (Frontend)
├── phantom-core/        # FastAPI, Quant Math, & BYOK Swarm Engine (Backend)
├── mt5-executor/        # Non-blocking Socket EA untuk MetaTrader 5
├── docs/                # Quickstart, Blueprint Arsitektur, & Panduan BYOK
├── start_terminal.bat   # 1-Click Launcher Windows
└── README.md            # Dokumentasi Resmi
```

---
*Created for institutional-grade quantitative reasoning and precision execution.*
