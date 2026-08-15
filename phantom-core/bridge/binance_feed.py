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
        self._client: Optional[httpx.AsyncClient] = None
        self.is_streaming = False
        self.last_tickers: Dict[str, Dict[str, Any]] = {}
        self.callbacks: List[Callable[[Dict[str, Any]], Any]] = []

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    def is_crypto_pair(self, symbol: str) -> bool:
        sym = symbol.upper().replace("/", "").replace("-", "")
        return sym in CRYPTO_SYMBOLS or "USDT" in sym or "BTC" in sym or "ETH" in sym

    def normalize_symbol(self, symbol: str) -> str:
        sym = symbol.upper().replace("/", "").replace("-", "")
        return CRYPTO_SYMBOLS.get(sym, sym if sym.endswith("USDT") else f"{sym}USDT")

    async def fetch_1s_candles(
        self,
        symbol: str = "BTCUSDT",
        count: int = 150
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Builds genuine 1-Second (1S / HFT) candles directly from Binance Public recent trades stream.
        """
        binance_symbol = self.normalize_symbol(symbol)
        try:
            url = f"{BINANCE_REST_BASE}/trades"
            params = {"symbol": binance_symbol, "limit": 1000}
            client = await self.get_client()
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            trades = resp.json()
            if not trades:
                return None

            buckets: Dict[int, List[Dict[str, Any]]] = {}
            for t in trades:
                sec = int(t["time"]) // 1000
                if sec not in buckets:
                    buckets[sec] = []
                buckets[sec].append(t)

            sorted_secs = sorted(buckets.keys())
            if not sorted_secs:
                return None

            candles: List[Dict[str, Any]] = []
            prev_close = float(trades[0]["price"])

            min_sec = max(sorted_secs[0], sorted_secs[-1] - count)
            max_sec = sorted_secs[-1]

            for s in range(min_sec, max_sec + 1):
                if s in buckets:
                    sec_trades = buckets[s]
                    open_p = float(sec_trades[0]["price"])
                    close_p = float(sec_trades[-1]["price"])
                    prices = [float(t["price"]) for t in sec_trades]
                    high_p = max(prices)
                    low_p = min(prices)
                    vol = sum(float(t["qty"]) for t in sec_trades)
                    buy_vol = sum(float(t["qty"]) for t in sec_trades if not t.get("isBuyerMaker", False))
                    sell_vol = max(0.0, vol - buy_vol)
                    prev_close = close_p
                else:
                    open_p = prev_close
                    high_p = prev_close
                    low_p = prev_close
                    close_p = prev_close
                    vol = 0.001
                    buy_vol = 0.0
                    sell_vol = 0.0

                candles.append({
                    "time": s,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "close": close_p,
                    "volume": round(vol, 4),
                    "buy_volume": round(buy_vol, 4),
                    "sell_volume": round(sell_vol, 4)
                })

            return candles[-count:]
        except Exception as e:
            logger.error(f"[Binance 1S Build Error] {e}")
            return None

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
        tf_upper = timeframe.upper()

        if tf_upper in ["1S", "S1", "SEC", "1SEC"]:
            return await self.fetch_1s_candles(binance_symbol, count=limit)

        interval = TIMEFRAME_MAP.get(timeframe, "1m")

        params: Dict[str, Any] = {
            "symbol": binance_symbol,
            "interval": interval,
            "limit": min(limit, 1000)
        }

        if end_time_ms:
            params["endTime"] = end_time_ms

        try:
            url = f"{BINANCE_REST_BASE}/klines"
            client = await self.get_client()
            resp = await client.get(url, params=params)
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

    async def fetch_order_book(self, symbol: str = "BTCUSDT", limit: int = 6) -> Optional[Dict[str, Any]]:
        """
        Fetches 100% REAL Level 2 Order Book Depth directly from Binance Order Matching Engine.
        Returns live real bids and asks limit orders placed by market participants.
        """
        binance_symbol = self.normalize_symbol(symbol)
        try:
            url = f"{BINANCE_REST_BASE}/depth"
            params = {"symbol": binance_symbol, "limit": limit}
            client = await self.get_client()
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                bids = [{"price": float(b[0]), "quantity": float(b[1])} for b in data.get("bids", [])]
                asks = [{"price": float(a[0]), "quantity": float(a[1])} for a in data.get("asks", [])]
                best_bid = bids[0]["price"] if bids else 0.0
                best_ask = asks[0]["price"] if asks else 0.0
                return {
                    "symbol": binance_symbol,
                    "last_update_id": data.get("lastUpdateId"),
                    "bids": bids,
                    "asks": asks,
                    "mid_price": best_bid,
                    "spread": round(best_ask - best_bid, 6) if (best_ask and best_bid) else 0.0,
                    "is_real": True
                }
        except Exception as e:
            logger.error(f"[Binance Depth Error] {e}")
        return None

    async def fetch_24h_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Fetches 24-hour ticker price change statistics for all crypto pairs."""
        try:
            url = f"{BINANCE_REST_BASE}/ticker/24hr"
            client = await self.get_client()
            resp = await client.get(url)
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
