import json
import asyncio
import socket
from typing import Dict, Any, Optional, Callable
from config import MT5_SOCKET_PORT

class MT5SocketBridge:
    """
    Non-blocking Async TCP Socket Bridge between Phantom Terminal and MetaTrader 5 EA.
    Listens on 127.0.0.1:9988 for incoming connection from Phantom_Executor.mq5.
    """

    def __init__(self, port: int = MT5_SOCKET_PORT):
        self.port = port
        self.connected_client_reader = None
        self.connected_client_writer = None
        self.is_connected = False
        self.on_data_received_callback = None
        self.server = None

    async def start_server(self, on_data_received: Optional[Callable[[Dict[str, Any]], None]] = None):
        """Starts local TCP socket server."""
        self.on_data_received_callback = on_data_received
        try:
            self.server = await asyncio.start_server(self._handle_client, "127.0.0.1", self.port)
            print(f"[MT5 Bridge] Socket Server listening on 127.0.0.1:{self.port}")
        except Exception as e:
            print(f"[MT5 Bridge Error] Failed to start socket server: {e}")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.connected_client_reader = reader
        self.connected_client_writer = writer
        self.is_connected = True
        addr = writer.get_extra_info("peername")
        print(f"[MT5 Bridge] MetaTrader 5 EA Connected from {addr}")

        buffer = ""
        try:
            while self.is_connected:
                data = await reader.read(4096)
                if not data:
                    break
                
                buffer += data.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            payload = json.loads(line)
                            if self.on_data_received_callback:
                                res = self.on_data_received_callback(payload)
                                if hasattr(res, "__await__"):
                                    await res
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"[MT5 Bridge] Client connection exception: {e}")
        finally:
            self.is_connected = False
            self.connected_client_reader = None
            self.connected_client_writer = None
            print("[MT5 Bridge] MetaTrader 5 EA Disconnected.")

    async def send_order(self, order_data: Dict[str, Any]) -> bool:
        """
        Sends an execution order packet to MT5 EA.
        Packet format: {"action": "EXECUTE_ORDER", "symbol": "XAUUSD", "type": "BUY", "volume": 0.5, "sl": 2648.0, "tp": 2670.0, "magic": 777999}
        """
        if not self.is_connected or not self.connected_client_writer:
            print("[MT5 Bridge Warning] MT5 EA is not connected. Simulating execution locally.")
            return False

        try:
            message = json.dumps(order_data) + "\n"
            self.connected_client_writer.write(message.encode("utf-8"))
            await self.connected_client_writer.drain()
            print(f"[MT5 Bridge] Sent order packet to MT5: {order_data}")
            return True
        except Exception as e:
            print(f"[MT5 Bridge Error] Failed to send order to MT5: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "mt5_bridge_active": True,
            "ea_connected": self.is_connected,
            "listening_port": self.port
        }
