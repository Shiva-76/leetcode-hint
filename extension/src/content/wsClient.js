/**
 * wsClient.js — WebSocket client (Phase 2: full bidirectional streaming)
 *
 * Features:
 * - Auto-reconnect with exponential backoff (1s → 2s → 4s → max 30s)
 * - Handles TOKEN / DONE / CACHE_HIT / ERROR / RATE_LIMIT messages
 * - Exposes a clean API: connect, sendPayload, onMessage, onStatusChange
 */

const WS_URL = 'ws://localhost:8000/ws/coach';

const RECONNECT_BASE_MS  = 1000;
const RECONNECT_MAX_MS   = 30000;
const RECONNECT_FACTOR   = 2;

let _socket         = null;
let _onMessage      = null;
let _onStatusChange = null;
let _reconnectDelay = RECONNECT_BASE_MS;
let _reconnecting   = false;
let _intentionalClose = false;
let _authToken      = '';

/** @type {'disconnected' | 'connecting' | 'connected' | 'error'} */
export let connectionStatus = 'disconnected';

// ── Connection lifecycle ──────────────────────────────────────────────────────

/**
 * Connect to the backend WebSocket.
 * Safe to call multiple times — ignores if already connected.
 */
export function connect() {
  if (_socket && (_socket.readyState === WebSocket.OPEN ||
                  _socket.readyState === WebSocket.CONNECTING)) return;

  _intentionalClose = false;
  _setStatus('connecting');

  chrome.storage.local.get(['backendUrl', 'authToken'], (res) => {
    const url = res.backendUrl || 'ws://localhost:8000/ws/coach';
    _authToken = res.authToken || '';

    try {
      _socket = new WebSocket(url);

      _socket.onopen = () => {
        _reconnectDelay = RECONNECT_BASE_MS; // reset backoff on success
        _reconnecting   = false;
        _setStatus('connected');
        console.log(`[wsClient] Connected to backend at ${url}`);
      };

      _socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          _onMessage?.(data);
        } catch {
          // Shouldn't happen — all messages are JSON
          _onMessage?.({ type: 'TOKEN', token: event.data });
        }
      };

      _socket.onerror = () => {
        _setStatus('error');
      };

      _socket.onclose = () => {
        _setStatus('disconnected');
        if (!_intentionalClose) {
          _scheduleReconnect();
        }
      };

    } catch (err) {
      _setStatus('error');
      console.warn('[wsClient] Connection failed:', err.message);
      _scheduleReconnect();
    }
  });
}

function _scheduleReconnect() {
  if (_reconnecting || _intentionalClose) return;
  _reconnecting = true;
  console.log(`[wsClient] Reconnecting in ${_reconnectDelay / 1000}s...`);
  setTimeout(() => {
    _reconnecting = false;
    connect();
  }, _reconnectDelay);
  // Exponential backoff
  _reconnectDelay = Math.min(_reconnectDelay * RECONNECT_FACTOR, RECONNECT_MAX_MS);
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Send a CoachRequest payload to the backend.
 * @param {object} payload — must conform to CoachRequest schema
 */
export function sendPayload(payload) {
  if (!_socket || _socket.readyState !== WebSocket.OPEN) {
    console.warn('[wsClient] Socket not open. Queuing not implemented — payload dropped:', payload);
    // Notify UI of the dropped payload
    _onMessage?.({
      type: 'ERROR',
      message: 'Backend offline. Please start the server or configure the correct URL in Options.',
    });
    return;
  }
  
  // Attach auth token if available
  const finalPayload = { ...payload, auth_token: _authToken };
  _socket.send(JSON.stringify(finalPayload));
}

/**
 * Register handler for incoming messages.
 * Called with: { type: 'TOKEN'|'DONE'|'CACHE_HIT'|'ERROR'|'RATE_LIMIT', ... }
 * @param {function(object): void} cb
 */
export function onMessage(cb) {
  _onMessage = cb;
}

/**
 * Register handler for connection status changes.
 * @param {function('disconnected'|'connecting'|'connected'|'error'): void} cb
 */
export function onStatusChange(cb) {
  _onStatusChange = cb;
}

/** Intentionally close the connection (disables auto-reconnect). */
export function disconnect() {
  _intentionalClose = true;
  _socket?.close();
}

// ── Internal helpers ──────────────────────────────────────────────────────────

function _setStatus(status) {
  connectionStatus = status;
  _onStatusChange?.(status);
}
