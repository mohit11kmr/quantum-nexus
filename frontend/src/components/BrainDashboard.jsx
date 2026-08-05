import React from 'react';
import { fetchBrainStatus, fetchBrainScenarios } from '../services/api';

export default function BrainDashboard() {
  const [status, setStatus] = React.useState(null);
  const [scenarios, setScenarios] = React.useState([]);

  React.useEffect(() => {
    fetchBrainStatus().then(setStatus);
    fetchBrainScenarios().then(setScenarios);
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">AI Brain & Zero-Loss Optimizer</div>
        <button className="btn btn-primary">Force Retrain</button>
      </div>

      {status && (
        <div className="metrics-row" style={{ marginBottom: '2rem' }}>
          <div className="metric-card">
            <div className="metric-title">Model Accuracy</div>
            <div className="metric-value text-green">{status.accuracy}%</div>
          </div>
          <div className="metric-card">
            <div className="metric-title">Epochs</div>
            <div className="metric-value">{status.epochs}</div>
          </div>
          <div className="metric-card">
            <div className="metric-title">Memory Footprint</div>
            <div className="metric-value">{status.memory}</div>
          </div>
        </div>
      )}

      <div>
        <h3 style={{ marginBottom: '1rem' }}>Zero-Loss Scenario Ranker</h3>
        <table className="data-table">
          <thead>
            <tr><th>Scenario Name</th><th>Probability</th><th>AI Recommended Action</th></tr>
          </thead>
          <tbody>
            {scenarios.map((s, i) => (
              <tr key={i}>
                <td>{s.name}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ flex: 1, background: 'rgba(255,255,255,0.1)', height: '8px', borderRadius: '4px' }}>
                      <div style={{ width: `${s.probability * 100}%`, height: '100%', background: 'var(--accent-blue)', borderRadius: '4px' }} />
                    </div>
                    <span>{(s.probability * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td><span className="badge badge-warning">HEDGE</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
