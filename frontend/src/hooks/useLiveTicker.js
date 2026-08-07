import { useEffect, useRef, useState } from 'react';
import { getWsBaseUrl } from '../services/api';

/**
 * Streams realtime ticks for a symbol over WebSocket with automatic
 * reconnection (exponential backoff) and heartbeat tolerance.
 *
 * Returns { tick, connected, ageSec } where tick is the latest parsed message.
 */
export default function useLiveTicker(symbol, { enabled = true } = {}) {
  const [tick, setTick] = useState(null);
  const [connected, setConnected] = useState(false);
  const [ageSec, setAgeSec] = useState(0);
  const wsRef = useRef(null);
  const tickRef = useRef(null);

  useEffect(() => {
    if (!enabled || !symbol) return undefined;

    let closed = false;
    let retry = 0;
    let timer = null;

    const connect = () => {
      if (closed) return;
      let ws;
      try {
        ws = new WebSocket(`${getWsBaseUrl()}/ws/market?symbol=${encodeURIComponent(symbol)}`);
      } catch {
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        retry = 0;
        setConnected(true);
      };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg && msg.type === 'heartbeat') return;
          if (msg && typeof msg.price === 'number') {
            tickRef.current = msg;
            setTick(msg);
          }
        } catch { /* ignore malformed frames */ }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closed) {
          const delay = Math.min(1000 * (2 ** retry), 15000);
          retry += 1;
          timer = setTimeout(connect, delay);
        }
      };
      ws.onerror = () => {
        // Let the socket fail naturally; onclose triggers the reconnect.
      };
    };

    connect();

    const ageTimer = setInterval(() => {
      const t = tickRef.current;
      if (t && t.timestamp) {
        setAgeSec(Math.max(0, Math.round((Date.now() / 1000) - t.timestamp)));
      }
    }, 2000);

    return () => {
      closed = true;
      if (timer) clearTimeout(timer);
      clearInterval(ageTimer);
      try { wsRef.current && wsRef.current.close(); } catch { /* noop */ }
    };
  }, [symbol, enabled]);

  return { tick, connected, ageSec };
}
