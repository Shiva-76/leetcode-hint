/**
 * wsClient.js — WebSocket client stub (Phase 1 skeleton)
 *
 * In Phase 2 this module will establish a persistent WebSocket connection
 * to the FastAPI backend and handle bidirectional streaming.
 *
 * For Phase 1 it provides the interface so the UI can wire up event handlers
 * without needing a live backend.
 */

const WS_URL = 'ws://localhost:8000/ws/coach';

let _socket = null;
let _onMessage = null;
let _onStatusChange = null;

/** @type {'disconnected' | 'connecting' | 'connected' | 'error'} */
export let connectionStatus = 'disconnected';

/**
 * Connect to the backend WebSocket.
 * Silently retries on failure (Phase 2 will add exponential backoff).
 */
export function connect() {
  if (_socket && _socket.readyState === WebSocket.OPEN) return;

  connectionStatus = 'connecting';
  _onStatusChange?.(connectionStatus);

  try {
    _socket = new WebSocket(WS_URL);

    _socket.onopen = () => {
      connectionStatus = 'connected';
      _onStatusChange?.(connectionStatus);
      console.log('[wsClient] Connected to backend.');
    };

    _socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        _onMessage?.(data);
      } catch {
        // Raw text token (streaming chunk) — pass through as-is
        _onMessage?.({ type: 'TOKEN', token: event.data });
      }
    };

    _socket.onerror = () => {
      connectionStatus = 'error';
      _onStatusChange?.(connectionStatus);
    };

    _socket.onclose = () => {
      connectionStatus = 'disconnected';
      _onStatusChange?.(connectionStatus);
      console.log('[wsClient] Disconnected.');
    };
  } catch (err) {
    connectionStatus = 'error';
    _onStatusChange?.(connectionStatus);
    console.warn('[wsClient] Connection failed (backend not running):', err.message);
  }
}

/**
 * Send a payload to the backend.
 * @param {object} payload
 */
export function sendPayload(payload) {
  if (!_socket || _socket.readyState !== WebSocket.OPEN) {
    console.warn('[wsClient] Socket not open. Payload dropped:', payload);
    return;
  }
  _socket.send(JSON.stringify(payload));
}

/**
 * Register a callback for incoming messages.
 * @param {function(object): void} cb
 */
export function onMessage(cb) {
  _onMessage = cb;
}

/**
 * Register a callback for connection status changes.
 * @param {function(string): void} cb
 */
export function onStatusChange(cb) {
  _onStatusChange = cb;
}

export function disconnect() {
  _socket?.close();
}
