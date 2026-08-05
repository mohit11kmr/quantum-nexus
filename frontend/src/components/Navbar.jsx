import React from 'react';
import { Search, Activity } from 'lucide-react';

export default function Navbar({ symbol, setSymbol }) {
  const [input, setInput] = React.useState(symbol);

  const handleSubmit = (e) => {
    e.preventDefault();
    if(input.trim()) setSymbol(input.toUpperCase());
  };

  return (
    <nav className="navbar">
      <div className="nav-brand">QUANTUM NEXUS</div>
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <div style={{ position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            style={{ 
              background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', 
              borderRadius: '20px', padding: '0.5rem 1rem 0.5rem 2.5rem', 
              color: 'var(--text-primary)', outline: 'none' 
            }}
            placeholder="Search symbol..."
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
          <Activity size={14} className="text-green" />
          <span className="text-green">LIVE</span>
        </div>
      </form>
    </nav>
  );
}
