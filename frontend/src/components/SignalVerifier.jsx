import React from 'react';
import { fetchSignalVerification } from '../services/api';

export default function SignalVerifier({ symbol }) {
  const [data, setData] = React.useState(null);

  React.useEffect(() => {
    fetchSignalVerification(symbol).then(setData);
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
    <div className="card">
      <div className="card-header">
        <div className="card-title">Multi-Layer Signal Verifier</div>
        <span className={`badge ${data.rating === 'EXCELLENT' ? 'badge-success' : 'badge-warning'}`}>{data.rating}</span>
      </div>

      <div className="grid-2col" style={{ alignItems: 'center' }}>
        <div>
          <ProgressBar label="Technical Score" value={data.techScore} color="var(--accent-blue)" />
          <ProgressBar label="Options Greeks Score" value={data.greekScore} color="var(--accent-green)" />
          <ProgressBar label="Market Regime Score" value={data.marketScore} color="var(--accent-gold)" />
        </div>
        
        <div style={{ textAlign: 'center', padding: '2rem', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Overall AI Confidence</div>
          <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--accent-green)', margin: '0.5rem 0', fontFamily: 'JetBrains Mono' }}>
            {data.confidence}%
          </div>
          <button className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>Execute Trade</button>
        </div>
      </div>
    </div>
  );
}
