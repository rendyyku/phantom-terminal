# 🔑 BYOK (BRING YOUR OWN KEY) GUIDE

Phantom Terminal dirancang dengan filosofi **Open-Core & Zero-Subscription**. Anda tidak perlu membayar biaya langganan bulanan software. Cukup gunakan kunci API dari penyedia kecerdasan buatan pilihan Anda.

---

### 1. Rekomendasi Utama: OpenRouter API (All-in-One)
Dengan satu API Key dari [OpenRouter](https://openrouter.ai), Anda dapat mengakses seluruh model frontier secara bersamaan:
* **Claude 3.5 Sonnet** (Anthropic)
* **DeepSeek-R1 / DeepSeek-V3** (DeepSeek)
* **GPT-4o** (OpenAI)

#### Cara Mendapatkan:
1. Daftar di [openrouter.ai](https://openrouter.ai).
2. Isi saldo kecil (misal: $5 - cukup untuk ratusan analisis trade).
3. Buka menu **Keys**, buat key baru (`sk-or-v1-...`).
4. Masukkan ke **Desk 6: BYOK Vault** di Phantom Terminal.

---

### 2. Kunci Langsung (Direct Provider Keys)
Anda juga dapat memasukkan kunci langsung:
* OpenAI API Key (`sk-proj-...`)
* DeepSeek API Key (`sk-...`)
* Anthropic API Key (`sk-ant-...`)

### 🛡️ Keamanan & Privasi Kunci
Semua API Key disimpan secara eksklusif di mesin lokal Anda dalam file `phantom-core/keys_vault.json`. Tidak ada kunci yang pernah dikirimkan ke server pengembang Phantom Terminal.
