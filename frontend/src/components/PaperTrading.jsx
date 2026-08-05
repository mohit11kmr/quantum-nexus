import React from 'react';
import { fetchPaperPortfolio } from '../services/api';

export default function PaperTrading() {
  const [portfolio, setPortfolio] = React.useState(null);

  React.useEffect(() => {
    fetchPaperPortfolio().then(setPortfolio);
  }, []);

  if (!portfolio) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Paper Trading Portfolio</div>
        <button className="btn" style={{ borderColor: 'var(--accent-red)', color: 'var(--accent-red)' }}>Reset Account</button>
      </div>

      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-title">Account Equity</div>
          <div className="metric-value text-blue">${portfolio.equity.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Available Cash</div>
          <div className="metric-value">${portfolio.balance.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">Open P&L</div>
          <div className="metric-value text-green">+$5,000.00</div>
        </div>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Active Positions</h3>
        <p className="text-secondary" style={{ fontStyle: 'italic' }}>No open positions. Use the Trade Terminal to enter a trade.</p>
      </div>
    </div>
  );
}
