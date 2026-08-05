import React from 'react';
import { fetchOptionsValuation } from '../services/api';

export default function OptionsValuation({ symbol }) {
  const [data, setData] = React.useState({ calls: [], puts: [] });

  React.useEffect(() => {
    fetchOptionsValuation(symbol).then(setData);
  }, [symbol]);

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Options Valuation & Greeks</div>
      </div>
      <div className="grid-2col">
        <div>
          <h3 style={{ color: 'var(--accent-green)', marginBottom: '1rem' }}>CALLS</h3>
          <table className="data-table">
            <thead>
              <tr><th>Strike</th><th>Premium</th><th>Fair Value</th><th>Status</th></tr>
            </thead>
            <tbody>
              {data.calls.map((c, i) => (
                <tr key={i}>
                  <td>{c.strike}</td>
                  <td>${c.premium}</td>
                  <td>${c.fairValue}</td>
                  <td>
                    <span className={`badge ${c.status === 'CHEAP' ? 'badge-success' : 'badge-danger'}`}>
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h3 style={{ color: 'var(--accent-red)', marginBottom: '1rem' }}>PUTS</h3>
          <table className="data-table">
            <thead>
              <tr><th>Strike</th><th>Premium</th><th>Fair Value</th><th>Status</th></tr>
            </thead>
            <tbody>
              {data.puts.map((p, i) => (
                <tr key={i}>
                  <td>{p.strike}</td>
                  <td>${p.premium}</td>
                  <td>${p.fairValue}</td>
                  <td>
                    <span className={`badge ${p.status === 'CHEAP' ? 'badge-success' : 'badge-danger'}`}>
                      {p.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
