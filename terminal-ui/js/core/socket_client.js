/**
 * 🦅 PHANTOM TERMINAL - WEBSOCKET CLIENT
 * Connects directly to local FastAPI server for sub-millisecond IPC data stream.
 */

class PhantomSocketClient {
  constructor(url = 'ws://127.0.0.1:8000/ws', app) {
    this.url = url;
    this.app = app;
    this.ws = null;
    this.isConnected = false;
    this.reconnectTimer = null;
    this.connect();
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.app.setConnectionStatus(true);
        console.log('[Phantom Socket] Connected to Core Engine.');
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.app.handleIncomingMessage(payload);
        } catch (e) {
          console.error('[Phantom Socket] Error parsing message:', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.app.setConnectionStatus(false);
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        this.isConnected = false;
        this.app.setConnectionStatus(false);
        this.ws.close();
      };
    } catch (e) {
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 2000);
    }
  }

  send(data) {
    if (this.ws && this.isConnected) {
      this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }
}
