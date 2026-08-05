import React from 'react';
import { fetchOptionsStrategy } from '../services/api';

export default function OptionsStrategy({ symbol }) {
  const [strategy, setStrategy] = React.useState(null);

  React.useEffect(() => {
    fetchOptionsStrategy(symbol).then(setStrategy);
  }, [symbol]);

  if (!strategy) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Options Strategy Engine</div>
        <span className="badge badge-success">Setup Quality: {strategy.quality}</span>
      </div>
      
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-title">Recommended Strategy</div>
          <div className="metric-value" style={{ fontSize: '1.2rem' }}>{strategy.setup}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Entry Range</div>
          <div className="metric-value text-blue">${strategy.entry}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Target</div>
          <div className="metric-value text-green">${strategy.target}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Stop Loss</div>
          <div className="metric-value text-red">${strategy.stop}</div>
        </div>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <h4 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>7-Condition Entry System</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {['SuperTrend', 'VWAP', 'RSI', 'EMA Ribbon', 'Volume Spike', 'ADX', 'AI Confidence'].map((cond, i) => (
            <span key={i} className="badge badge-success" style={{ padding: '0.5rem 1rem' }}>
              ✓ {cond}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
