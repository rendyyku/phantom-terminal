# 🚀 PANDUAN CEPAT: MEMULAI PHANTOM TERMINAL (2 MENIT)

Selamat datang di **Phantom Terminal**, platform kecerdasan finansial berbasis AI Quant & Order Flow mutakhir untuk Forex & Gold.

---

## ⚡ Langkah 1: Jalankan Backend Python Core

Buka terminal PowerShell di folder `phantom-terminal/phantom-core`:

```bash
cd phantom-terminal/phantom-core
pip install -r requirements.txt
python server.py
```

*Server FastAPI & WebSocket akan aktif di `http://127.0.0.1:8000` dan mendengarkan socket MT5 di port `9988`.*

---

## 🌐 Langkah 2: Buka Terminal UI di Browser

Buka file `phantom-terminal/terminal-ui/index.html` langsung di browser pilihan Anda (Google Chrome / Brave / Edge).

Atau Anda bisa menggunakan launcher otomatis:
* Klik ganda `start_terminal.bat` di root folder `phantom-terminal/`.

---

## 🔑 Langkah 3: Pasang API Key (BYOK)

1. Klik tab **Desk 6: BYOK Vault** pada terminal.
2. Masukkan API Key Anda (Rekomendasi: **OpenRouter** untuk mengakses Claude 3.5, DeepSeek-R1, dan GPT-4o sekaligus).
3. Klik **Save Keys**. Kunci tersimpan 100% aman dan lokal di komputer Anda.

---

## 🔌 Langkah 4: Hubungkan ke MetaTrader 5 (Opsional)

1. Salin file `mt5-executor/Phantom_Executor.mq5` dan folder `Include/` ke direktori MT5 Anda (`MQL5/Experts/`).
2. Buka MetaTrader 5, buka MetaEditor, dan tekan `F7` untuk compile.
3. Pasang EA ke chart manapun dan pastikan tombol **Algo Trading** aktif.
4. EA akan langsung terhubung ke Phantom Terminal melalui socket lokal `127.0.0.1:9988`.
