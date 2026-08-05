import React from 'react';

export default function TradeJournal() {
  const [trades] = React.useState([
    { date: '2023-10-25', symbol: 'AAPL', side: 'LONG', entry: 145.2, exit: 150.1, pnl: 490, notes: 'VWAP Bounce' }
  ]);

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Trade Journal & Analytics</div>
        <button className="btn">Export CSV</button>
      </div>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Entry</th>
              <th>Exit</th>
              <th>P&L</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t, i) => (
              <tr key={i}>
                <td>{t.date}</td>
                <td style={{ fontWeight: 'bold' }}>{t.symbol}</td>
                <td><span className="badge badge-success">{t.side}</span></td>
                <td>${t.entry}</td>
                <td>${t.exit}</td>
                <td className={t.pnl >= 0 ? 'text-green' : 'text-red'}>${t.pnl}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{t.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
