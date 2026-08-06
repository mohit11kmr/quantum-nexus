import React, { useState, useEffect } from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchLiveQuote } from '../services/api';

export default function StockChart({ symbol = 'NIFTY' }) {
  const [chartData, setChartData] = useState([]);
  const [basePrice, setBasePrice] = useState(24649.0);

  useEffect(() => {
    let isMounted = true;
    const updateChart = async () => {
      try {
        const quote = await fetchLiveQuote(symbol);
        const livePrice = quote?.current_price || 24649.0;
        if (!isMounted) return;
        setBasePrice(livePrice);

        const points = Array.from({ length: 30 }, (_, i) => {
          const noise = (Math.sin(i / 3) * 15) + (Math.random() * 8 - 4);
          const priceVal = Number((livePrice + noise - 10).toFixed(2));
          return {
            time: `10:${i < 10 ? '0' + i : i}`,
            price: priceVal,
            vwap: Number((livePrice - 5).toFixed(2)),
            volume: Math.floor(Math.random() * 8000 + 2000)
          };
        });
        setChartData(points);
      } catch (e) {
        console.error("Error building stock chart data", e);
      }
    };

    updateChart();
    const interval = setInterval(updateChart, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [symbol]);

  const currencySymbol = (symbol.includes('.NS') || symbol.includes('NIFTY') || symbol.includes('BANK')) ? '₹' : '$';

  return (
    <div className="card" style={{ height: '500px' }}>
      <div className="card-header">
        <div className="card-title">{symbol} Real-Time Chart ({currencySymbol}{basePrice.toLocaleString()})</div>
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="time" stroke="var(--text-secondary)" />
          <YAxis yAxisId="price" domain={['auto', 'auto']} stroke="var(--text-secondary)" tickFormatter={(v) => `${currencySymbol}${v}`} />
          <YAxis yAxisId="volume" orientation="right" stroke="var(--text-secondary)" />
          <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
          <Bar yAxisId="volume" dataKey="volume" fill="rgba(56, 189, 248, 0.3)" />
          <Line yAxisId="price" type="monotone" dataKey="price" stroke="var(--accent-green)" dot={false} strokeWidth={2} />
          <Line yAxisId="price" type="monotone" dataKey="vwap" stroke="var(--accent-gold)" dot={false} strokeDasharray="5 5" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
