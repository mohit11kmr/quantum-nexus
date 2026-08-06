import React from 'react';
import { fetchStressTest } from '../services/api';

export default function StressTester({ symbol }) {
  const [data, setData] = React.useState([]);

  React.useEffect(() => {
    fetchStressTest(symbol).then(res => {
      const list = Array.isArray(res) ? res : (res?.results || []);
      setData(list);
    });
  }, [symbol]);

  const list = Array.isArray(data) ? data : [];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Portfolio Stress Tester</div>
        <button className="btn btn-primary">Run Custom Scenario</button>
      </div>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Historical Scenario</th>
              <th>Simulated Max Loss</th>
              <th>Est. Recovery (Days)</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {list.map((row, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 'bold' }}>{row.scenario}</td>
                <td className="text-red">{row.maxLoss}%</td>
                <td>{row.recoveryDays}</td>
                <td>
                  <span className={`badge ${row.severity === 'HIGH' ? 'badge-danger' : 'badge-warning'}`}>
                    {row.severity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
