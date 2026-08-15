# 🤝 Contributing to Phantom Terminal

Thank you for your interest in contributing to **Phantom Terminal**! We welcome contributions from quants, software engineers, and algorithmic traders worldwide.

---

## 🛠️ Development Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/rendyyku/phantom-terminal.git
   cd phantom-terminal
   ```

2. **Setup Python Virtual Environment:**
   ```bash
   cd phantom-core
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Run the Development Server:**
   ```bash
   python server.py
   ```
   Open `http://127.0.0.1:8000` in your browser.

---

## 🧪 Running Tests

We use `pytest` for unit testing quantitative indicators and risk guards:

```bash
cd phantom-core
pytest tests/ -v
```

---

## 📐 Coding Standards & Guidelines

1. **Clean Architecture:** Keep `bridge/` (I/O & MT5 bindings), `engine/` (pure math & consensus logic), and `server.py` (API routing) strictly decoupled.
2. **Zero Lookahead Bias:** All quantitative indicator functions in `engine/orderflow_math.py` must operate strictly on past confirmed candle data.
3. **Type Annotations:** Use Python type hints (`List`, `Dict`, `Optional`, `Tuple`) on all function signatures.
4. **Security First:** Never commit API keys or vault data. All keys must remain encrypted at rest.

---

## 🚀 Submitting a Pull Request (PR)

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Commit your changes with clear semantic commit messages:
   ```bash
   git commit -m "feat(quant): add VWAP institutional anchor calculation"
   ```
3. Push to your fork and submit a PR against `main`.

Thank you for helping build the future of open-source quant trading! 🦅💎
