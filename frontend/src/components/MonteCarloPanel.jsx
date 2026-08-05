import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchMonteCarloSimulation } from '../services/api';

export default function MonteCarloPanel({ symbol }) {
  const [data, setData] = React.useState(null);

  React.useEffect(() => {
    fetchMonteCarloSimulation(symbol).then(setData);
  }, [symbol]);

  if (!data) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Monte Carlo Value at Risk (VaR) - 10,000 Iterations</div>
      </div>
      
      <div className="metrics-row" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-title">VaR (95%)</div>
          <div className="metric-value text-red">{data.var95}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">VaR (99%)</div>
          <div className="metric-value text-red">{data.var99}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">CVaR (Expected Shortfall)</div>
          <div className="metric-value text-gold">{data.cvar}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Median Outcome</div>
          <div className="metric-value text-green">+{data.median}%</div>
        </div>
      </div>

      <div style={{ height: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data.histogram}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="bin" stroke="var(--text-secondary)" label={{ value: 'Return (%)', position: 'insideBottom', fill: 'var(--text-secondary)', dy: 10 }} />
            <YAxis stroke="var(--text-secondary)" label={{ value: 'Frequency', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }} />
            <Bar dataKey="count" fill="var(--accent-blue)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
