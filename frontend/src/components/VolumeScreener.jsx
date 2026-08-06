import React from 'react';
import { fetchVolumeScreener } from '../services/api';

export default function VolumeScreener() {
  const [data, setData] = React.useState([]);

  React.useEffect(() => {
    fetchVolumeScreener().then(res => {
      const list = Array.isArray(res) ? res : (res?.results || []);
      setData(list);
    });
  }, []);

  const list = Array.isArray(data) ? data : [];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Volume Surge Screener</div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn">Filter &gt; 200%</button>
          <button className="btn btn-primary">Scan Now</button>
        </div>
      </div>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Price</th>
              <th>Volume Surge</th>
              <th>RSI</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {list.map((row, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 'bold' }}>{row.symbol}</td>
                <td>₹{row.price || row.score || 24649}</td>
                <td className="text-green">{row.surge || '+180%'}</td>
                <td>{row.rsi || 58}</td>
                <td><button className="btn" style={{ padding: '0.25rem 0.5rem' }}>Analyze</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
