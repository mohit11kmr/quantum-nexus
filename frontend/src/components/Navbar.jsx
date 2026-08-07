import React from 'react';
import { Search, Activity, TrendingUp, Languages } from 'lucide-react';
import { useLanguage, LANGUAGES } from '../i18n.jsx';

export default function Navbar({ symbol, setSymbol }) {
  const { lang, setLang, t } = useLanguage();
  const [input, setInput] = React.useState(symbol);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) setSymbol(input.toUpperCase());
  };

  const handleToggle = () => {
    const next = lang === 'en' ? 'hi' : 'en';
    setLang(next);
    document.documentElement.setAttribute('lang', next);
  };

  const other = LANGUAGES.find((l) => l.code !== lang);

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span className="nav-brand-mark">
          <TrendingUp size={18} />
        </span>
        {t('brand.name')}
      </div>

      <div className="nav-controls">
        <button
          type="button"
          className="lang-toggle"
          onClick={handleToggle}
          aria-label={`Switch language to ${other.label}`}
          title={`Language / भाषा: ${other.label}`}
        >
          <Languages size={15} />
          {other.label}
        </button>
        <form onSubmit={handleSubmit} style={{ margin: 0 }}>
          <div className="nav-search">
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t('nav.search')}
              aria-label={t('nav.search')}
            />
          </div>
        </form>
        <div className="live-pill">
          <span className="live-dot" />
          <Activity size={13} />
          <span>{t('nav.live')}</span>
        </div>
      </div>
    </nav>
  );
}
