# 🏛️ PHANTOM TERMINAL: SYSTEM ARCHITECTURE SPECIFICATION

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PHANTOM TERMINAL UI                           │
│  [Market & CVD Canvas]  [AI War Room Swarm]  [Prop Firm Risk Shield]  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ WebSocket (0.2ms) / REST API
┌───────────────────────────────────▼────────────────────────────────────┐
│                        PHANTOM CORE (FastAPI)                          │
│                                                                        │
│  ┌───────────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │   OrderFlow Math      │  │  AI War Room     │  │  Risk Guard     │  │
│  │   - CVD Accumulator   │  │  - Claude 3.5    │  │  - Drawdown     │  │
│  │   - FVG Detector      │  │  - DeepSeek R1   │  │  - Auto-Lot     │  │
│  │   - Liquidity Pools   │  │  - Supreme Judge │  │  - BE Trailing  │  │
│  └───────────────────────┘  └────────┬─────────┘  └─────────────────┘  │
└──────────────────────────────────────┼─────────────────────────────────┘
                                       │ Async Non-blocking TCP Socket (Port 9988)
┌──────────────────────────────────────▼─────────────────────────────────┐
│                 METATRADER 5 (Phantom_Executor EA)                     │
│  [Instant 1-Click Order] [Stop Loss & Take Profit] [Live Tick Stream]  │
└────────────────────────────────────────────────────────────────────────┘
```

## 1. Zero-Lag Local Math Processing
Kalkulasi teknikal seperti Fair Value Gap (FVG), Cumulative Volume Delta (CVD), dan Equal Highs/Lows dihitung di engine lokal Python menggunakan NumPy sebelum AI dipanggil. Hal ini menghemat biaya token API hingga 90%.

## 2. Multi-Titan AI War Room Swarm
- **Titan 1 (Bull Specialist - Claude 3.5 Sonnet):** Membedah argumen buy berbasis displacement dan discount pricing.
- **Titan 2 (Bear Specialist - DeepSeek R1):** Menganalisis risiko perangkap likuiditas dan area pasokan (supply).
- **Supreme Judge (GPT-4o / Gemini 2.0):** Menilai logika kedua titan dan menerbitkan skor konsensus serta level harga R:R minimum 1:2.0.

## 3. Prop Firm Compliance Shield
Melindungi modal trader dan tantangan Prop Firm (FTMO/The5ers) dengan fitur **Hard Drawdown Lockout** otomatis saat batas kerugian harian mendekati toleransi maksimum.
