import React from 'react';
import { fetchSignalVerification, fetchLiveVerificationStats, fetchBrokerStatus } from '../services/api';

export default function SignalVerifier({ symbol }) {
  const [data, setData] = React.useState(null);
  const [liveStats, setLiveStats] = React.useState(null);
  const [brokerStatus, setBrokerStatus] = React.useState(null);

  React.useEffect(() => {
    fetchSignalVerification(symbol).then(setData);
    fetchLiveVerificationStats().then(setLiveStats);
    fetchBrokerStatus().then(setBrokerStatus);
  }, [symbol]);

  if (!data) return null;

  const ProgressBar = ({ label, value, color }) => (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.8rem' }}>
        <span>{label}</span>
        <span>{value}/100</span>
      </div>
      <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px' }}>
        <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: '4px' }} />
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Live Market Audit Header Banner */}
      <div className="card" style={{ background: 'linear-gradient(135deg, rgba(18, 24, 38, 0.9), rgba(0, 245, 160, 0.05))', border: '1px solid rgba(0, 245, 160, 0.3)' }}>
        <div className="card-header">
          <div>
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>🛡️ Real Market Forward-Tester & Truth Verifier</span>
              <span className="badge badge-success" style={{ animation: 'pulse 2s infinite' }}>LIVE FEED AUDIT</span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Cross-verifying generated signals against real-time NSE/BSE tick feeds & Black-Scholes market drift
            </div>
          </div>
          {brokerStatus && (
            <div style={{ textAlign: 'right' }}>
              <span className={`badge ${brokerStatus.is_connected ? 'badge-success' : 'badge-warning'}`}>
                {brokerStatus.is_connected ? '🟢 ANGELONE LIVE CONNECTED' : '🟡 PAPER TRADING MODE'}
              </span>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Protocol: {brokerStatus.protocol || 'WebSocket V2'}
              </div>
            </div>
          )}
        </div>

        {/* Live Empirical Metrics Grid */}
        {liveStats && (
          <div className="metrics-row" style={{ marginTop: '1rem' }}>
            <div className="metric-card">
              <div className="metric-title">Empirical Win Rate</div>
              <div className="metric-value text-green">{liveStats.empirical_win_rate}%</div>
              <div className="metric-sub">{liveStats.wins} Wins / {liveStats.losses} Losses Audited</div>
            </div>
            <div className="metric-card">
              <div className="metric-title">BS vs Market LTP Drift</div>
              <div className="metric-value text-gold">{liveStats.avg_bs_vs_market_drift_pct}%</div>
              <div className="metric-sub">Theoretical vs Real Premium Diff</div>
            </div>
            <div className="metric-card">
              <div className="metric-title">Est. Slippage & Brokerage</div>
              <div className="metric-value text-blue">{liveStats.estimated_slippage_pct}%</div>
              <div className="metric-sub">Modeled Exec Costs</div>
            </div>
            <div className="metric-card">
              <div className="metric-title">Total Signals Audited</div>
              <div className="metric-value">{liveStats.total_signals_audited}</div>
              <div className="metric-sub">SQLite Memory Logged</div>
            </div>
          </div>
        )}
      </div>

      {/* Multi-Layer Signal Verifier */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">3-Layer Signal Verifier Engine</div>
          <span className={`badge ${data.rating === 'EXCELLENT' ? 'badge-success' : 'badge-warning'}`}>{data.rating}</span>
        </div>

        <div className="grid-2col" style={{ alignItems: 'center' }}>
          <div>
            <ProgressBar label="Technical Layer Score (EMA/VWAP/RSI)" value={data.techScore} color="var(--accent-blue)" />
            <ProgressBar label="Options Greeks Score (Delta/Theta/Vega)" value={data.greekScore} color="var(--accent-green)" />
            <ProgressBar label="Market Regime Score (ATR/Trend)" value={data.marketScore} color="var(--accent-gold)" />
          </div>
          
          <div style={{ textAlign: 'center', padding: '2rem', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Overall Verification Confidence</div>
            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--accent-green)', margin: '0.5rem 0', fontFamily: 'JetBrains Mono' }}>
              {data.confidence}%
            </div>
            <button className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>Execute Verified Trade</button>
          </div>
        </div>
      </div>

      {/* Live Signals Forward-Testing Audit Table */}
      {liveStats && liveStats.recent_audits && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">📋 Live Signal Verification Audit Log</div>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Contract / Symbol</th>
                  <th>Type</th>
                  <th>Entry Price</th>
                  <th>Target Price</th>
                  <th>Stop Loss</th>
                  <th>LTP Drift</th>
                  <th>Outcome Status</th>
                </tr>
              </thead>
              <tbody>
                {liveStats.recent_audits.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.85rem' }}>{item.timestamp}</td>
                    <td style={{ fontWeight: 'bold' }}>{item.symbol}</td>
                    <td><span className={`badge ${item.signal_type === 'BUY' ? 'badge-success' : 'badge-danger'}`}>{item.signal_type}</span></td>
                    <td>₹{item.entry_price}</td>
                    <td className="text-green">₹{item.target_price}</td>
                    <td className="text-red">₹{item.stop_loss_price}</td>
                    <td>{item.ltp_drift_pct}%</td>
                    <td>
                      <span className={`badge ${item.status === 'WIN' ? 'badge-success' : item.status === 'LOSS' ? 'badge-danger' : 'badge-warning'}`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

