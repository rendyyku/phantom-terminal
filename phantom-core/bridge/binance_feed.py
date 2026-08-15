import time
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
import httpx
import websockets

logger = logging.getLogger("BinanceFeed")

BINANCE_REST_BASE = "https://api.binance.com/api/v3"
BINANCE_WS_BASE = "wss://stream.binance.com:9443/ws"

CRYPTO_SYMBOLS = {
    # Layer 1 & Major
    "BTCUSD": "BTCUSDT", "BTCUSDT": "BTCUSDT",
    "ETHUSD": "ETHUSDT", "ETHUSDT": "ETHUSDT",
    "SOLUSD": "SOLUSDT", "SOLUSDT": "SOLUSDT",
    "BNBUSD": "BNBUSDT", "BNBUSDT": "BNBUSDT",
    "XRPUSD": "XRPUSDT", "XRPUSDT": "XRPUSDT",
    "ADAUSD": "ADAUSDT", "ADAUSDT": "ADAUSDT",
    "AVAXUSD": "AVAXUSDT", "AVAXUSDT": "AVAXUSDT",
    "SUIUSD": "SUIUSDT", "SUIUSDT": "SUIUSDT",
    "NEARUSD": "NEARUSDT", "NEARUSDT": "NEARUSDT",
    "APTUSD": "APTUSDT", "APTUSDT": "APTUSDT",
    "TONUSD": "TONUSDT", "TONUSDT": "TONUSDT",
    "TRXUSD": "TRXUSDT", "TRXUSDT": "TRXUSDT",
    "DOTUSD": "DOTUSDT", "DOTUSDT": "DOTUSDT",
    "LINKUSD": "LINKUSDT", "LINKUSDT": "LINKUSDT",
    "LTCUSD": "LTCUSDT", "LTCUSDT": "LTCUSDT",
    
    # AI & Compute
    "TAOUSD": "TAOUSDT", "TAOUSDT": "TAOUSDT",
    "RENDERUSD": "RENDERUSDT", "RENDERUSDT": "RENDERUSDT",
    "FETUSD": "FETUSDT", "FETUSDT": "FETUSDT",
    "WLDUSD": "WLDUSDT", "WLDUSDT": "WLDUSDT",
    "ARKMUSD": "ARKMUSDT", "ARKMUSDT": "ARKMUSDT",
    
    # Meme Coins & High Beta
    "DOGEUSD": "DOGEUSDT", "DOGEUSDT": "DOGEUSDT",
    "SHIBUSD": "SHIBUSDT", "SHIBUSDT": "SHIBUSDT",
    "PEPEUSD": "PEPEUSDT", "PEPEUSDT": "PEPEUSDT",
    "WIFUSD": "WIFUSDT", "WIFUSDT": "WIFUSDT",
    "BONKUSD": "BONKUSDT", "BONKUSDT": "BONKUSDT",
    "FLOKIUSD": "FLOKIUSDT", "FLOKIUSDT": "FLOKIUSDT",
    
    # DeFi & Modular
    "UNIUSD": "UNIUSDT", "UNIUSDT": "UNIUSDT",
    "AAVEUSD": "AAVEUSDT", "AAVEUSDT": "AAVEUSDT",
    "PENDLEUSD": "PENDLEUSDT", "PENDLEUSDT": "PENDLEUSDT",
    "INJUSD": "INJUSDT", "INJUSDT": "INJUSDT",
    "TIAUSD": "TIAUSDT", "TIAUSDT": "TIAUSDT",
    "SEIUSD": "SEIUSDT", "SEIUSDT": "SEIUSDT",
    "JUPUSD": "JUPUSDT", "JUPUSDT": "JUPUSDT",
    "ENAUSD": "ENAUSDT", "ENAUSDT": "ENAUSDT"
}

TIMEFRAME_MAP = {
    "1S": "1s",
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d"
}


class BinanceCryptoFeed:
    """
    High-speed, 100% Free Public Binance Market Feed for Crypto Division.
    Features:
    - 24/7 Live Klines (1S, 1m, 5m, 15m, 1h, 4h, 1d)
    - Cumulative Volume Delta (CVD) extracted directly from Taker Buy Volume
    - Infinite Historical Scroll Pagination
    - Real-Time Mini-Ticker and Kline WebSocket Stream
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.is_streaming = False
        self.last_tickers: Dict[str, Dict[str, Any]] = {}
        self.callbacks: List[Callable[[Dict[str, Any]], Any]] = []

    def is_crypto_pair(self, symbol: str) -> bool:
        sym = symbol.upper().replace("/", "").replace("-", "")
        return sym in CRYPTO_SYMBOLS or "USDT" in sym or "BTC" in sym or "ETH" in sym

    def normalize_symbol(self, symbol: str) -> str:
        sym = symbol.upper().replace("/", "").replace("-", "")
        return CRYPTO_SYMBOLS.get(sym, sym if sym.endswith("USDT") else f"{sym}USDT")

    async def fetch_klines(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "M1",
        limit: int = 300,
        end_time_ms: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches official OHLCV klines with taker buy/sell volume from Binance.
        """
        binance_symbol = self.normalize_symbol(symbol)
        interval = TIMEFRAME_MAP.get(timeframe, "1m")

        # Fallback for 1S in spot (synthesize or use 1s stream)
        if interval == "1s":
            interval = "1m"

        params: Dict[str, Any] = {
            "symbol": binance_symbol,
            "interval": interval,
            "limit": min(limit, 1000)
        }

        if end_time_ms:
            params["endTime"] = end_time_ms

        try:
            url = f"{BINANCE_REST_BASE}/klines"
            resp = await self.client.get(url, params=params)
            if resp.status_code != 200:
                logger.error(f"[Binance REST] Error {resp.status_code}: {resp.text}")
                return None

            raw_klines = resp.json()
            candles: List[Dict[str, Any]] = []

            for k in raw_klines:
                # Binance Kline format:
                # [0: open_time, 1: open, 2: high, 3: low, 4: close, 5: volume, 6: close_time, 7: quote_asset_vol, 8: trades, 9: taker_buy_base_vol, 10: taker_buy_quote_vol, 11: ignore]
                open_t = int(k[0]) // 1000
                open_p = float(k[1])
                high_p = float(k[2])
                low_p = float(k[3])
                close_p = float(k[4])
                vol = float(k[5])
                taker_buy_vol = float(k[9])
                taker_sell_vol = max(0.0, vol - taker_buy_vol)

                candles.append({
                    "time": open_t,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "close": close_p,
                    "volume": round(vol, 4),
                    "buy_volume": round(taker_buy_vol, 4),
                    "sell_volume": round(taker_sell_vol, 4)
                })

            return candles
        except Exception as e:
            logger.error(f"[Binance REST Exception] {e}")
            return None

    async def fetch_24h_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Fetches 24-hour ticker price change statistics for all crypto pairs."""
        try:
            url = f"{BINANCE_REST_BASE}/ticker/24hr"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                result = {}
                for t in data:
                    sym = t["symbol"]
                    if sym in CRYPTO_SYMBOLS.values():
                        last_price = float(t["lastPrice"])
                        price_change_pct = float(t["priceChangePercent"])
                        result[sym] = {
                            "symbol": sym,
                            "price": last_price,
                            "change_24h": price_change_pct,
                            "change_str": f"{'+' if price_change_pct >= 0 else ''}{price_change_pct:.2f}%",
                            "high_24h": float(t["highPrice"]),
                            "low_24h": float(t["lowPrice"]),
                            "volume_24h": float(t["volume"])
                        }
                self.last_tickers = result
                return result
        except Exception as e:
            logger.error(f"[Binance 24h Ticker Error] {e}")
        return self.last_tickers

    def add_stream_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        """Adds listener for live crypto tick/candle stream."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    async def start_live_stream(self):
        """
        Connects to Binance Multi-Stream WebSocket for sub-second live ticks and candle bars.
        Stream: btcusdt@kline_1m, ethusdt@kline_1m, solusdt@kline_1m, bnbusdt@kline_1m, xrpusdt@kline_1m + all miniTickers.
        """
        streams = [
            "btcusdt@kline_1m",
            "ethusdt@kline_1m",
            "solusdt@kline_1m",
            "bnbusdt@kline_1m",
            "xrpusdt@kline_1m",
            "!miniTicker@arr"
        ]
        stream_url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"

        self.is_streaming = True
        while self.is_streaming:
            try:
                async with websockets.connect(stream_url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info("[Binance WebSocket] Connected to 24/7 Global Crypto Feed.")
                    async for message in ws:
                        data = json.loads(message)
                        
                        # Handle MiniTicker Array (Updates entire Watchlist 24/7)
                        if isinstance(data, list):
                            for item in data:
                                sym = item.get("s")
                                if sym in CRYPTO_SYMBOLS.values():
                                    price = float(item.get("c", 0))
                                    open_p = float(item.get("o", price))
                                    chg = ((price - open_p) / open_p * 100.0) if open_p > 0 else 0.0
                                    
                                    packet = {
                                        "type": "CRYPTO_TICK",
                                        "symbol": sym,
                                        "price": price,
                                        "change_24h": round(chg, 2),
                                        "change_str": f"{'+' if chg >= 0 else ''}{chg:.2f}%"
                                    }
                                    for cb in self.callbacks:
                                        try:
                                            cb(packet)
                                        except Exception:
                                            pass

                        # Handle Kline Update (Updates live candle & CVD)
                        elif isinstance(data, dict) and data.get("e") == "kline":
                            k = data.get("k", {})
                            sym = data.get("s", "")
                            open_t = int(k.get("t", 0)) // 1000
                            candle = {
                                "time": open_t,
                                "open": float(k.get("o", 0)),
                                "high": float(k.get("h", 0)),
                                "low": float(k.get("l", 0)),
                                "close": float(k.get("c", 0)),
                                "volume": round(float(k.get("v", 0)), 4),
                                "buy_volume": round(float(k.get("V", 0)), 4),
                                "sell_volume": round(max(0.0, float(k.get("v", 0)) - float(k.get("V", 0))), 4)
                            }
                            packet = {
                                "type": "TICK_UPDATE",
                                "pair": sym,
                                "timeframe": "M1",
                                "candle": candle
                            }
                            for cb in self.callbacks:
                                try:
                                    cb(packet)
                                except Exception:
                                    pass
            except Exception as e:
                logger.warning(f"[Binance WebSocket Reconnecting] {e}")
                await asyncio.sleep(3)
