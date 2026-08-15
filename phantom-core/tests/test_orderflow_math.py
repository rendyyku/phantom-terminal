import pytest
from engine.orderflow_math import LuxAlgoSMC, VolumeProfileMath, OrderFlowMath

def generate_sample_candles(count=100, base_price=2000.0):
    """Generates deterministic synthetic candles for testing."""
    candles = []
    price = base_price
    for i in range(count):
        # Simulate slight trend with pullbacks
        delta = 1.5 if (i % 6 < 4) else -2.0
        open_p = price
        close_p = price + delta
        high_p = max(open_p, close_p) + 1.0
        low_p = min(open_p, close_p) - 1.0
        volume = 150 + (i % 10) * 10
        candles.append({
            "time": 1700000000 + i * 60,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": volume,
            "buy_volume": volume // 2 + 10,
            "sell_volume": volume // 2 - 10
        })
        price = close_p
    return candles

def test_atr_calculation():
    candles = generate_sample_candles(30)
    atrs = LuxAlgoSMC.calculate_atr(candles, period=14)
    assert len(atrs) == 30
    assert atrs[-1] > 0.0

def test_smc_structure_detection():
    candles = generate_sample_candles(120)
    result = LuxAlgoSMC.detect_smc_structure(candles, swing_length=8, internal_length=4)
    
    assert "swing_structures" in result
    assert "order_blocks" in result
    assert "fvgs" in result
    assert "zones" in result
    assert result["trend"] in ["BULLISH", "BEARISH", "SIDEWAYS_RANGING"]

def test_volume_profile_math():
    candles = generate_sample_candles(100)
    vp = VolumeProfileMath.calculate_volume_profile(candles, num_bars=50, row_size=28, va_percent=70.0)
    
    assert "rows" in vp
    assert len(vp["rows"]) == 28
    assert vp["poc"] is not None
    assert vp["vah"] is not None
    assert vp["val"] is not None
    assert vp["vah"] >= vp["val"]

def test_cvd_calculation():
    candles = generate_sample_candles(50)
    cvd = OrderFlowMath.calculate_cvd(candles)
    
    assert len(cvd) == 50
    assert "cvd" in cvd[-1]
    assert "delta" in cvd[-1]
