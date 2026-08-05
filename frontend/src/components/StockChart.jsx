import React from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = Array.from({length: 30}, (_, i) => ({
  time: `10:${i < 10 ? '0'+i : i}`,
  price: 150 + Math.random() * 5 - 2.5,
  vwap: 150,
  volume: Math.floor(Math.random() * 1000)
}));

export default function StockChart({ symbol }) {
  return (
    <div className="card" style={{ height: '500px' }}>
      <div className="card-header">
        <div className="card-title">{symbol} Chart & Volume</div>
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="time" stroke="var(--text-secondary)" />
          <YAxis yAxisId="price" domain={['auto', 'auto']} stroke="var(--text-secondary)" />
          <YAxis yAxisId="volume" orientation="right" stroke="var(--text-secondary)" />
          <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)' }} />
          <Bar yAxisId="volume" dataKey="volume" fill="rgba(56, 189, 248, 0.3)" />
          <Line yAxisId="price" type="monotone" dataKey="price" stroke="var(--accent-green)" dot={false} strokeWidth={2} />
          <Line yAxisId="price" type="monotone" dataKey="vwap" stroke="var(--accent-gold)" dot={false} strokeDasharray="5 5" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
