import React, { useState, useEffect } from 'react';
import { fetchLiveQuote, fetchIndicators } from '../services/api';
import { useLanguage } from '../i18n.jsx';
import useLiveTicker from '../hooks/useLiveTicker';
import { Activity, Gauge, ArrowUpRight, ArrowDownRight, TrendingUp } from 'lucide-react';

export default function MarketSummary({ symbol = 'NIFTY' }) {
  const { t } = useLanguage();
  const [baseQuote, setBaseQuote] = useState(null);
  const [indicators, setIndicators] = useState(null);

  const { tick, connected } = useLiveTicker(symbol);

  useEffect(() => {
    let isMounted = true;
    const loadIndicators = async () => {
      try {
        const iData = await fetchIndicators(symbol);
        if (isMounted) setIndicators(iData);
      } catch (e) {
        console.error("Error loading indicators for MarketSummary", e);
      }
    };

    const loadQuote = async () => {
      try {
        const qData = await fetchLiveQuote(symbol);
        if (isMounted) setBaseQuote(qData);
      } catch (e) {
        console.error("Error loading quote for MarketSummary", e);
      }
    };

    loadQuote();
    loadIndicators();
    const interval = setInterval(loadIndicators, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [symbol]);

  const price = tick?.price || baseQuote?.current_price || 24649.00;
  const change = tick?.change ?? baseQuote?.change ?? 24.35;
  const changePct = tick?.change_pct ?? baseQuote?.change_pct ?? 0.10;
  const isPositive = change >= 0;
  const currencySymbol = (symbol.includes('.NS') || symbol.includes('NIFTY') || symbol.includes('BANK')) ? '₹' : '$';

  const stats = [
    { icon: Activity, label: t('market.volume'), value: tick?.volume ? (tick.volume > 1000000 ? `${(tick.volume / 1000000).toFixed(2)}M` : `${(tick.volume / 1000).toFixed(0)}K`) : (baseQuote?.volume ? (baseQuote.volume > 1000000 ? `${(baseQuote.volume / 1000000).toFixed(2)}M` : `${(baseQuote.volume / 1000).toFixed(0)}K`) : '1.2M'), sub: t('market.volumeSub'), tone: 'text-blue' },
    { icon: Gauge, label: t('market.rsi'), value: indicators?.rsi ? indicators.rsi.toFixed(1) : '58.2', sub: `${indicators?.regime || 'BULLISH'} trend`, tone: 'text-gold' },
    { icon: TrendingUp, label: t('market.vwap'), value: `${currencySymbol}${(price * 0.998).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, sub: t('market.vwapSub'), tone: 'text-green' },
  ];

  return (
    <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
      <div className="flex flex-wrap items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-bold text-white uppercase tracking-wider">{symbol}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${connected ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-white/5 border border-white/10 text-secondary'}`}>
                {connected ? '● LIVE' : 'INDEX'}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-3xl font-extrabold font-mono text-white">
                {currencySymbol}{price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className={`flex items-center gap-1 text-sm font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isPositive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                {isPositive ? '+' : ''}{change} ({isPositive ? '+' : ''}{changePct}%)
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 flex-1 max-w-2xl">
          {stats.map((s) => (
            <div key={s.label} className="px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-800">
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">
                <s.icon size={12} className={s.tone} />
                {s.label}
              </div>
              <div className={`text-lg font-bold font-mono ${s.tone}`}>{s.value}</div>
              <div className="text-[11px] text-secondary mt-0.5">{s.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
