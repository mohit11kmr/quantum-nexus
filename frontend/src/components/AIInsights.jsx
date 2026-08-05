import React from 'react';

export default function AIInsights({ symbol }) {
  return (
    <div className="card" style={{ border: '1px solid var(--accent-gold)' }}>
      <div className="card-header">
        <div className="card-title" style={{ color: 'var(--accent-gold)' }}>AI Commentary</div>
      </div>
      <p style={{ lineHeight: '1.6', fontSize: '0.9rem' }}>
        QUANTUM NEXUS detects significant accumulation on <span className="text-blue">{symbol}</span>. 
        Institutional footprint found at VWAP levels. The options flow indicates heavy call buying for next Friday expiration. 
        Regime shifted to <span className="text-green">BULLISH TREND</span>.
      </p>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', padding: '1rem', background: 'rgba(255,215,0,0.1)', borderRadius: '8px' }}>
        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Regime Confidence</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent-gold)' }}>92%</div>
        </div>
        <button className="btn" style={{ borderColor: 'var(--accent-gold)', color: 'var(--accent-gold)' }}>
          View Full AI Report
        </button>
      </div>
    </div>
  );
}
