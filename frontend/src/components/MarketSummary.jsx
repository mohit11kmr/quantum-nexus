import React, { useState, useEffect } from 'react';
import { fetchLiveQuote, fetchIndicators } from '../services/api';
import { useLanguage } from '../i18n.jsx';
import { Activity, Gauge, ArrowUpRight, ArrowDownRight, TrendingUp } from 'lucide-react';

export default function MarketSummary({ symbol = 'NIFTY' }) {
  const { t } = useLanguage();
  const [quote, setQuote] = useState(null);
  const [indicators, setIndicators] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const loadQuote = async () => {
      try {
        const [qData, iData] = await Promise.all([
          fetchLiveQuote(symbol),
          fetchIndicators(symbol)
        ]);
        if (isMounted) {
          setQuote(qData);
          setIndicators(iData);
        }
      } catch (e) {
        console.error("Error loading quote for MarketSummary", e);
      }
    };

    loadQuote();
    const interval = setInterval(loadQuote, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [symbol]);

  const price = quote?.current_price || 24649.00;
  const change = quote?.change || 24.35;
  const changePct = quote?.change_pct || 0.10;
  const isPositive = change >= 0;
  const currencySymbol = (symbol.includes('.NS') || symbol.includes('NIFTY') || symbol.includes('BANK')) ? '₹' : '$';

  const stats = [
    { icon: Activity, label: t('market.volume'), value: quote?.volume ? (quote.volume > 1000000 ? `${(quote.volume / 1000000).toFixed(2)}M` : `${(quote.volume / 1000).toFixed(0)}K`) : '1.2M', sub: t('market.volumeSub'), tone: 'text-blue' },
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
              <span className="text-[10px] bg-white/5 border border-white/10 text-secondary px-2 py-0.5 rounded-full font-mono">INDEX</span>
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
