import React from 'react';

export default function HostingGuideModal() {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="card" style={{ maxWidth: '600px', width: '100%' }}>
        <div className="card-header">
          <div className="card-title">Deployment Guide</div>
          <button className="btn" style={{ padding: '0.25rem 0.5rem' }}>✕</button>
        </div>
        <div style={{ lineHeight: '1.6' }}>
          <h4>Frontend (Vercel)</h4>
          <ol style={{ paddingLeft: '1.5rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
            <li>Connect GitHub repo to Vercel</li>
            <li>Framework Preset: Vite</li>
            <li>Build Command: <code className="mono">npm run build</code></li>
            <li>Environment Variables: <code className="mono">VITE_API_URL=https://your-backend.onrender.com</code></li>
          </ol>
          <h4>Backend (Render)</h4>
          <ol style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
            <li>Connect GitHub repo to Render as Web Service</li>
            <li>Environment: Python 3</li>
            <li>Build Command: <code className="mono">pip install -r requirements.txt</code></li>
            <li>Start Command: <code className="mono">uvicorn main:app --host 0.0.0.0 --port 10000</code></li>
          </ol>
        </div>
      </div>
    </div>
  );
}
