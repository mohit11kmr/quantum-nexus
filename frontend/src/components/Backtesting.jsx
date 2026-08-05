import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { runBacktest } from '../services/api';

export default function Backtesting({ symbol }) {
  const [result, setResult] = React.useState(null);

  React.useEffect(() => {
    runBacktest({ symbol, timeframe: '1D', strategy: 'VWAP Bounce' }).then(setResult);
  }, [symbol]);

  if (!result) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Strategy Backtester</div>
        <button className="btn btn-primary">Run Simulation</button>
      </div>

      <div className="metrics-row" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-title">Win Rate</div>
          <div className="metric-value text-green">{result.winRate}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Profit Factor</div>
          <div className="metric-value text-blue">{result.profitFactor}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Max Drawdown</div>
          <div className="metric-value text-red">{result.maxDrawdown}%</div>
        </div>
      </div>

      <div style={{ height: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={result.equityCurve}>
            <defs>
              <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" stroke="var(--text-secondary)" />
            <YAxis stroke="var(--text-secondary)" domain={['auto', 'auto']} />
            <Tooltip contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }} />
            <Area type="monotone" dataKey="val" stroke="var(--accent-blue)" fillOpacity={1} fill="url(#colorVal)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
