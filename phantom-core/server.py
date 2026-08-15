import os
import sys
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

# Force UTF-8 on Windows stdout/stderr to prevent cp1252 charmap encoding errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import (
    SERVER_HOST, SERVER_PORT, DEFAULT_PAIRS, DEFAULT_RISK_SETTINGS, 
    load_keys_vault, save_keys_vault, DEFAULT_AI_MODELS, BASE_DIR, ALLOWED_ORIGINS
)
from engine.orderflow_math import OrderFlowMath
from engine.prompt_builder import PromptBuilder
from engine.byok_client import UniversalBYOKClient
from engine.consensus_evaluator import ConsensusEvaluator
from engine.news_service import MacroNewsService
from bridge.risk_guard import RiskGuard
from bridge.mt5_connector import MT5SocketBridge
from bridge.mt5_feed import MT5NativeFeed
from bridge.binance_feed import BinanceCryptoFeed

# Directory to Terminal UI frontend
UI_DIST_DIR = BASE_DIR.parent / "terminal-ui"

# Core Instances
risk_guard = RiskGuard()
mt5_bridge = MT5SocketBridge()
mt5_native_feed = MT5NativeFeed()
binance_feed = BinanceCryptoFeed()
byok_client = UniversalBYOKClient()
prompt_builder = PromptBuilder()
consensus_evaluator = ConsensusEvaluator(byok_client)
news_service = MacroNewsService()

# WebSocket Active Connections
active_websockets: set[WebSocket] = set()

# Live Market Cache & Global Context
current_pair = "XAUUSD"
current_timeframe = "M1"
market_cache: Dict[str, List[Dict[str, Any]]] = {}

async def broadcast_ws(message: Dict[str, Any]):
    """Broadcasts JSON messages to all connected frontend clients concurrently without blocking."""
    if not active_websockets:
        return
    text = json.dumps(message)
    clients = list(active_websockets)
    tasks = [ws.send_text(text) for ws in clients]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for ws, res in zip(clients, results):
        if isinstance(res, Exception) and ws in active_websockets:
            active_websockets.remove(ws)

def on_mt5_data_received(data: Dict[str, Any]):
    """Callback when MT5 EA sends live tick or account status."""
    event_type = data.get("type", "")
    if event_type == "ACCOUNT_UPDATE":
        risk_guard.update_account_state(
            balance=data.get("balance", 10000.0),
            equity=data.get("equity", 10000.0),
            active_trades=data.get("active_trades", 0)
        )
    asyncio.create_task(broadcast_ws({"type": "MT5_DATA", "data": data}))

async def market_tick_streamer():
    """Streams ultra-fast EVERY-TICK real-time data from MT5 (<100ms) with 1-Second HFT support."""
    while True:
        await asyncio.sleep(0.1)  # 100ms ultra-low latency
        
        # Check if MT5 is connected and live
        if mt5_native_feed.ensure_connected():
            real_tick = mt5_native_feed.fetch_live_tick(current_pair)
            if real_tick:
                cache_key = f"{current_pair}_{current_timeframe}"
                candles = market_cache.get(cache_key, [])
                
                if candles and len(candles) > 0:
                    last = candles[-1]
                    tick_time = real_tick["time"]
                    p = real_tick["last"]
                    
                    if current_timeframe == "1S":
                        # Check if a new second has elapsed
                        if tick_time > last["time"]:
                            # Create new 1-second candle
                            new_candle = {
                                "time": tick_time,
                                "open": p, "high": p, "low": p, "close": p,
                                "volume": 1,
                                "buy_volume": 1 if p >= last["close"] else 0,
                                "sell_volume": 1 if p < last["close"] else 0
                            }
                            candles.append(new_candle)
                            if len(candles) > 100:
                                candles.pop(0)
                            last = new_candle
                        else:
                            # Update current 1-second candle
                            last["close"] = p
                            last["high"] = max(last["high"], p)
                            last["low"] = min(last["low"], p)
                            last["volume"] += 1
                            last["buy_volume"] += 1 if p >= last["open"] else 0
                            last["sell_volume"] += 1 if p < last["open"] else 0
                    else:
                        # Timeframe interval in seconds
                        tf_seconds = 60 if current_timeframe == "M1" else (300 if current_timeframe == "M5" else (900 if current_timeframe == "M15" else 3600))
                        
                        # Check if a new candle period has started
                        if (tick_time // tf_seconds) > (last["time"] // tf_seconds):
                            refreshed = mt5_native_feed.fetch_ohlcv(current_pair, current_timeframe, 80)
                            if refreshed:
                                market_cache[cache_key] = refreshed
                                candles = refreshed
                                last = candles[-1]

                        last["close"] = p
                        last["high"] = max(last["high"], p)
                        last["low"] = min(last["low"], p)
                        last["volume"] += 1
                        last["buy_volume"] += 1 if p >= last["open"] else 0
                        last["sell_volume"] += 1 if p < last["open"] else 0

                    # Sync live MT5 account info
                    acc_info = mt5_native_feed.get_account_info()
                    if acc_info:
                        risk_guard.update_account_state(
                            balance=acc_info["balance"],
                            equity=acc_info["equity"]
                        )

                    if active_websockets:
                        cvd = OrderFlowMath.calculate_cvd(candles[-30:])
                        await broadcast_ws({
                            "type": "TICK_UPDATE",
                            "pair": current_pair,
                            "timeframe": current_timeframe,
                            "candle": last,
                            "latest_cvd": cvd[-1] if cvd else None
                        })

async def news_updater_task():
    """Periodically fetches live news feeds and broadcasts flash alerts."""
    while True:
        try:
            articles = await news_service.fetch_live_rss()
            if articles and active_websockets:
                top_art = articles[0]
                await broadcast_ws({
                    "type": "FLASH_NEWS",
                    "article": top_art
                })
        except Exception:
            pass
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await mt5_bridge.start_server(on_data_received=on_mt5_data_received)
    
    # Register Binance Crypto WebSocket callback
    def on_binance_data(packet: Dict[str, Any]):
        asyncio.create_task(broadcast_ws(packet))
    
    binance_feed.add_stream_callback(on_binance_data)

    task1 = asyncio.create_task(market_tick_streamer())
    task2 = asyncio.create_task(news_updater_task())
    task3 = asyncio.create_task(binance_feed.start_live_stream())
    yield
    # Shutdown
    task1.cancel()
    task2.cancel()
    task3.cancel()

app = FastAPI(title="Phantom Terminal AI Quant Core", version="2.0.0", lifespan=lifespan)

# Enable CORS restricted to trusted local terminal clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class SaveKeysPayload(BaseModel):
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    anthropic_api_key: str = ""

class SignalRequestPayload(BaseModel):
    pair: str = "XAUUSD"

class ExecuteOrderPayload(BaseModel):
    pair: str
    action: str  # BUY or SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    comment: str = "Phantom AI Signal"

class RiskSettingsPayload(BaseModel):
    account_balance: float
    risk_percent_per_trade: float
    daily_max_drawdown_percent: float
    max_open_trades: int
    enable_hard_stop: bool
    prop_firm_mode: bool

@app.get("/api/crypto/tickers")
async def get_crypto_tickers():
    """Returns real-time 24h ticker prices from Binance."""
    tickers = await binance_feed.fetch_24h_tickers()
    return tickers

@app.get("/api/news")
async def get_news(category: str = "ALL"):
    articles = news_service.get_articles(category)
    return {
        "category": category,
        "count": len(articles),
        "articles": articles
    }

@app.get("/api/economic-calendar")
async def get_economic_calendar():
    return {
        "calendar": news_service.economic_calendar
    }

@app.post("/api/refresh-news")
async def refresh_news():
    articles = await news_service.fetch_live_rss()
    return {"status": "SUCCESS", "articles_count": len(articles), "articles": articles}

@app.get("/api/status")
async def get_status():
    keys = load_keys_vault()
    return {
        "status": "ONLINE",
        "version": "2.0.0-inhouse",
        "current_pair": current_pair,
        "pairs": DEFAULT_PAIRS,
        "models": DEFAULT_AI_MODELS,
        "keys_configured": {
            "openrouter": bool(keys.get("openrouter_api_key")),
            "openai": bool(keys.get("openai_api_key")),
            "deepseek": bool(keys.get("deepseek_api_key")),
            "anthropic": bool(keys.get("anthropic_api_key"))
        },
        "risk_shield": risk_guard.get_risk_status(),
        "mt5_bridge": {
            **mt5_bridge.get_status(),
            "native_interface_active": mt5_native_feed.is_initialized
        },
        "binance_feed": {
            "status": "ONLINE",
            "provider": "Binance Public Global Stream"
        }
    }

@app.get("/api/market-data")
async def get_market_data(pair: str = "XAUUSD", timeframe: str = "1S"):
    global current_pair, current_timeframe
    current_pair = pair
    current_timeframe = timeframe.upper()
    cache_key = f"{pair}_{current_timeframe}"

    # 1. CHECK IF PAIR IS CRYPTO (BINANCE PUBLIC API)
    if binance_feed.is_crypto_pair(pair):
        real_candles = await binance_feed.fetch_klines(pair, current_timeframe, 300)
        if real_candles and len(real_candles) > 0:
            market_cache[cache_key] = real_candles
            analysis = OrderFlowMath.compute_all_indicators(real_candles, current_timeframe)
            return {
                "pair": pair,
                "timeframe": current_timeframe,
                "candles": real_candles,
                "cvd": analysis["cvd"],
                "smc": analysis["smc"],
                "volume_profile": analysis["volume_profile"],
                "fvgs": analysis["smc"]["fvgs"],
                "order_blocks": analysis["smc"]["order_blocks"],
                "structure": {
                    "trend": analysis["trend"],
                    "swing_structures": analysis["smc"]["swing_structures"],
                    "equal_high_lows": analysis["smc"]["equal_high_lows"],
                    "zones": analysis["smc"]["zones"],
                    "strong_weak": analysis["smc"]["strong_weak"]
                },
                "source": "BINANCE_PUBLIC_API",
                "is_connected": True
            }

    # 2. FOREX / GOLD (MT5 DIRECT INTERFACE)
    if current_timeframe in ["1S", "S1", "SEC", "1SEC"]:
        real_candles = mt5_native_feed.fetch_1s_candles(pair, 300)
    else:
        real_candles = mt5_native_feed.fetch_ohlcv(pair, current_timeframe, 300)

    if real_candles and len(real_candles) > 0:
        market_cache[cache_key] = real_candles
        analysis = OrderFlowMath.compute_all_indicators(real_candles, current_timeframe)

        return {
            "pair": pair,
            "timeframe": current_timeframe,
            "candles": real_candles,
            "cvd": analysis["cvd"],
            "smc": analysis["smc"],
            "volume_profile": analysis["volume_profile"],
            "fvgs": analysis["smc"]["fvgs"],
            "order_blocks": analysis["smc"]["order_blocks"],
            "structure": {
                "trend": analysis["trend"],
                "swing_structures": analysis["smc"]["swing_structures"],
                "equal_high_lows": analysis["smc"]["equal_high_lows"],
                "zones": analysis["smc"]["zones"],
                "strong_weak": analysis["smc"]["strong_weak"]
            },
            "source": "MT5_REAL_BROKER",
            "is_connected": True
        }
    else:
        # MT5 is offline / not opened
        market_cache[cache_key] = []
        return {
            "pair": pair,
            "timeframe": current_timeframe,
            "candles": [],
            "cvd": [],
            "smc": None,
            "volume_profile": None,
            "fvgs": [],
            "order_blocks": [],
            "structure": {
                "trend": "OFFLINE",
                "event": "MT5_DISCONNECTED",
                "description": "MetaTrader 5 is not open. Launch MT5 and enable Algo Trading to stream live candles."
            },
            "source": "MT5_DISCONNECTED",
            "is_connected": False
        }

@app.get("/api/history")
async def get_history(pair: str = "XAUUSD", timeframe: str = "1S", offset: int = 0, count: int = 300, before_time: Optional[int] = None):
    """
    Fetches older historical candles for seamless Infinite Scroll.
    Supports both Binance Crypto and MT5 Forex/Gold.
    """
    tf = timeframe.upper()

    if binance_feed.is_crypto_pair(pair):
        end_time_ms = (before_time * 1000) if before_time else None
        older_candles = await binance_feed.fetch_klines(pair, tf, count=count, end_time_ms=end_time_ms)
    else:
        if tf in ["1S", "S1", "SEC", "1SEC"]:
            older_candles = mt5_native_feed.fetch_1s_candles(pair, count=count, before_timestamp=before_time)
        else:
            older_candles = mt5_native_feed.fetch_ohlcv(pair, tf, count=count, start_pos=offset)

    if older_candles and len(older_candles) > 0:
        return {
            "pair": pair,
            "timeframe": tf,
            "offset": offset,
            "count": len(older_candles),
            "candles": older_candles,
            "has_more": True
        }
    return {
        "pair": pair,
        "timeframe": tf,
        "offset": offset,
        "count": 0,
        "candles": [],
        "has_more": False
    }

@app.post("/api/generate-signal")
async def generate_signal(payload: SignalRequestPayload):
    pair = payload.pair
    candles = market_cache.get(pair, OrderFlowMath.generate_synthetic_candles(pair, count=80))
    cvd = OrderFlowMath.calculate_cvd(candles)
    fvgs = OrderFlowMath.detect_fvg(candles)
    liq_pools = OrderFlowMath.detect_liquidity_pools(candles)
    structure = OrderFlowMath.detect_structure_shift(candles)
    macro_context = news_service.get_macro_context_for_ai()

    context = PromptBuilder.build_market_context(pair, candles, fvgs, liq_pools, cvd, structure, macro_context=macro_context)

    # Event streaming callback for WebSocket
    async def war_room_event_handler(event_type: str, data: Any):
        await broadcast_ws({
            "type": "WAR_ROOM_EVENT",
            "event": event_type,
            "data": data
        })

    decision = await consensus_evaluator.run_war_room_debate(context, event_callback=war_room_event_handler)

    # Calculate lot size if valid trade
    if decision.get("decision") in ["BUY", "SELL"]:
        is_safe, msg, lot = risk_guard.validate_trade_execution(
            pair=pair,
            entry_price=decision.get("entry_price", candles[-1]["close"]),
            stop_loss=decision.get("stop_loss", candles[-1]["close"] - 5.0)
        )
        decision["lot_size"] = lot
        decision["risk_validation"] = {"passed": is_safe, "message": msg}

    return decision

@app.post("/api/execute-order")
async def execute_order(payload: ExecuteOrderPayload):
    # Sync live positions if MT5 is connected
    acc = mt5_native_feed.get_account_info()
    if acc:
        risk_guard.update_account_state(
            balance=acc.get("balance", risk_guard.current_balance),
            equity=acc.get("equity", risk_guard.current_equity),
            active_trades=acc.get("positions_total", risk_guard.active_trades_count)
        )

    # 1. Validate through Risk Shield
    is_safe, reason, lot = risk_guard.validate_trade_execution(
        pair=payload.pair,
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss
    )

    if not is_safe:
        raise HTTPException(status_code=400, detail=f"Risk Guard Block: {reason}")

    # 2. Dispatch to MT5 EA Bridge
    order_packet = {
        "action": "EXECUTE_ORDER",
        "symbol": payload.pair,
        "type": payload.action,
        "volume": lot,
        "price": payload.entry_price,
        "sl": payload.stop_loss,
        "tp": payload.take_profit,
        "magic": 777999,
        "comment": payload.comment
    }

    sent_to_mt5 = await mt5_bridge.send_order(order_packet)

    return {
        "status": "EXECUTED",
        "sent_to_mt5_ea": sent_to_mt5,
        "order": order_packet,
        "risk_guard": risk_guard.get_risk_status()
    }

@app.post("/api/save-keys")
async def save_keys(payload: SaveKeysPayload):
    vault = load_keys_vault()
    if payload.openrouter_api_key:
        vault["openrouter_api_key"] = payload.openrouter_api_key.strip()
    if payload.openai_api_key:
        vault["openai_api_key"] = payload.openai_api_key.strip()
    if payload.deepseek_api_key:
        vault["deepseek_api_key"] = payload.deepseek_api_key.strip()
    if payload.anthropic_api_key:
        vault["anthropic_api_key"] = payload.anthropic_api_key.strip()

    success = save_keys_vault(vault)
    byok_client.reload_keys()
    return {"status": "SUCCESS" if success else "ERROR", "message": "Keys saved securely in local vault."}

@app.post("/api/update-risk")
async def update_risk_settings(payload: RiskSettingsPayload):
    risk_guard.settings.update(payload.dict())
    risk_guard.starting_daily_balance = payload.account_balance
    risk_guard.current_balance = payload.account_balance
    risk_guard.current_equity = payload.account_balance
    risk_guard.is_hard_stopped = False
    return {"status": "SUCCESS", "risk_settings": risk_guard.get_risk_status()}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        # Send initial status & data immediately upon connection
        await websocket.send_text(json.dumps({
            "type": "INITIAL_HANDSHAKE",
            "message": "Connected to Phantom Terminal Core 2.0",
            "current_pair": current_pair
        }))
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
    except Exception:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

# Mount Terminal UI static files directly on root "/"
if UI_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(UI_DIST_DIR), html=True), name="static_ui")

if __name__ == "__main__":
    import uvicorn
    print(f"🦅 Starting Phantom Terminal Core on http://{SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run("server:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
