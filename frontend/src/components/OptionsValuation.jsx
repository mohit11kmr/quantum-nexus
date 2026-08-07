import React from 'react';
import { fetchOptionsValuation } from '../services/api';
import { useLanguage } from '../i18n.jsx';
import { Coins, Percent, Activity, Timer, Waves, ShieldCheck, AlertTriangle } from 'lucide-react';

export default function OptionsValuation({ symbol }) {
  const { t } = useLanguage();
  const [data, setData] = React.useState(null);
  const [error, setError] = React.useState(false);

  React.useEffect(() => {
    setError(false);
    fetchOptionsValuation(symbol)
      .then((d) => { if (d && d.greeks) setData(d); else setError(true); })
      .catch(() => setError(true));
  }, [symbol]);

  if (error) {
    return (
      <div className="card text-center py-12">
        <p className="text-sm text-rose-300">{t('opt.error')}</p>
      </div>
    );
  }

  if (!data) {
    return <div className="card text-center py-12 text-secondary font-semibold">{t('opt.loading')}</div>;
  }

  const greeks = data.greeks || {};
  const valuation = data.valuation || 'N/A';
  const isCheap = valuation.toUpperCase().includes('CHEAP');
  const premium = data.market_premium_ce ?? greeks.fair_value;

  const greekCards = [
    { icon: Percent, label: t('opt.delta'), value: greeks.delta?.toFixed(4), sub: t('opt.deltaSub'), tone: 'text-cyan-400' },
    { icon: Activity, label: t('opt.gamma'), value: greeks.gamma?.toFixed(6), sub: t('opt.gammaSub'), tone: 'text-violet-400' },
    { icon: Timer, label: t('opt.theta'), value: greeks.theta?.toFixed(2), sub: t('opt.thetaSub'), tone: 'text-amber-400' },
    { icon: Waves, label: t('opt.vega'), value: greeks.vega?.toFixed(2), sub: t('opt.vegaSub'), tone: 'text-emerald-400' },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title"><Coins size={18} className="text-emerald-400" /> {t('opt.title')}</div>
      </div>

      {/* ATM Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
          <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{t('opt.spot')}</div>
          <div className="text-2xl font-bold font-mono text-white">₹{data.spot_price?.toLocaleString()}</div>
          <div className="text-[11px] text-secondary mt-0.5">{t('opt.underlying', { symbol })}</div>
        </div>
        <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
          <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{t('opt.atm')}</div>
          <div className="text-2xl font-bold font-mono text-amber-400">₹{data.strike_price?.toLocaleString()}</div>
          <div className="text-[11px] text-secondary mt-0.5">{t('opt.callRef')}</div>
        </div>
        <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
          <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{t('opt.fairValue')}</div>
          <div className="text-2xl font-bold font-mono text-white">
            ₹{greeks.fair_value?.toFixed?.(2)} <span className="text-sm text-secondary">/ ₹{premium?.toFixed?.(2)}</span>
          </div>
          <div className={`mt-1 inline-flex items-center gap-1.5 text-[11px] font-bold px-2 py-0.5 rounded-full border ${isCheap ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' : 'text-amber-400 bg-amber-500/10 border-amber-500/30'}`}>
            {isCheap ? <ShieldCheck size={11} /> : <AlertTriangle size={11} />}
            {isCheap ? t('opt.cheap') : valuation}
          </div>
        </div>
      </div>

      {/* Greeks */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {greekCards.map((g) => (
          <div key={g.label} className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1.5">
              <g.icon size={12} className={g.tone} />
              {g.label}
            </div>
            <div className={`text-lg font-bold font-mono ${g.tone}`}>{g.value}</div>
            <div className="text-[11px] text-secondary mt-0.5">{g.sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
