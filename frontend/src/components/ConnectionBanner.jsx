import React, { useEffect, useState } from 'react';
import { checkApiHealth } from '../services/api';
import { WifiOff, Wifi } from 'lucide-react';

export default function ConnectionBanner() {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let timer;

    const ping = async () => {
      const result = await checkApiHealth();
      if (!cancelled) setOnline(result.ok);
    };

    ping();
    timer = setInterval(ping, 20000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (online) return null;

  return (
    <div style={{
      background: 'rgba(255,51,102,0.12)',
      border: '1px solid rgba(255,51,102,0.4)',
      color: '#FF3366',
      padding: '0.5rem 1rem',
      fontSize: '0.8rem',
      fontWeight: 600,
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
    }}>
      <WifiOff size={14} />
      API CONNECTION LOST — backend offline, showing cached/synthetic data. Retrying every 20s…
    </div>
  );
}
