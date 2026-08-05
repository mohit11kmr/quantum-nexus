import React from 'react';

export default function VolumeProfile({ symbol }) {
  return (
    <div className="card">
      <div className="card-title">Volume Profile</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {[
          { price: 152, vol: 20 },
          { price: 151, vol: 45 },
          { price: 150, vol: 100, isPOC: true },
          { price: 149, vol: 60 },
          { price: 148, vol: 30 },
        ].map(level => (
          <div key={level.price} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: '40px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>${level.price}</div>
            <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', height: '12px', borderRadius: '6px', overflow: 'hidden' }}>
              <div style={{ 
                width: `${level.vol}%`, 
                height: '100%', 
                background: level.isPOC ? 'var(--accent-gold)' : 'var(--accent-blue)',
                opacity: level.isPOC ? 1 : 0.6
              }} />
            </div>
            {level.isPOC && <span className="badge badge-warning" style={{ fontSize: '0.6rem' }}>POC</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
