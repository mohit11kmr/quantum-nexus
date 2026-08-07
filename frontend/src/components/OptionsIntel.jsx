import React, { useEffect, useState } from 'react';
import { fetchOptionsIntel } from '../services/api';
import { useLanguage } from '../i18n.jsx';
import { Radar, TrendingUp, TrendingDown, Minus, ShieldAlert, Activity, Gauge } from 'lucide-react';

const fmt = (n) => (typeof n === 'number' ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—');

export default function OptionsIntel({ symbol = 'NIFTY' }) {
  const { t } = useLanguage();
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchOptionsIntel(symbol).then(setData).catch(() => setData(null));
  }, [symbol]);

  if (!data) {
    return <div className="card text-center py-12 text-secondary font-semibold">{t('intel.loading')}</div>;
  }

  const score = data.directionScore ?? 50;
  const label = data.directionLabel || 'NEUTRAL';
  const isBull = label === 'BULLISH';
  const isBear = label === 'BEARISH';
  const LabelIcon = isBull ? TrendingUp : isBear ? TrendingDown : Minus;
  const labelTone = isBull ? 'text-emerald-400' : isBear ? 'text-rose-400' : 'text-amber-400';
  const sourceLive = data.dataSource === 'LIVE' || data.dataSource === 'nse-direct' || data.dataSource === 'yahoo';

  const metrics = [
    { label: t('intel.pcrOi'), value: fmt(data.pcr_oi), sub: t('intel.pcrSub'), tone: 'text-cyan-400' },
    { label: t('intel.pcrVol'), value: fmt(data.pcr_volume), sub: t('intel.pcrSub'), tone: 'text-cyan-400' },
    { label: t('intel.maxPain'), value: data.max_pain_strike ? fmt(data.max_pain_strike) : '—', sub: t('intel.maxPainSub'), tone: 'text-violet-400' },
    { label: t('intel.ivRank'), value: `${fmt(data.iv_rank_pct)}%`, sub: t('intel.ivRankSub'), tone: 'text-gold' },
    { label: t('intel.atmIv'), value: fmt(data.atm_iv), sub: t('intel.ivSkew') + ': ' + (data.iv_skew ?? 0), tone: 'text-amber-400' },
    { label: t('intel.callWall'), value: data.call_wall ? fmt(data.call_wall) : '—', sub: t('intel.callWallSub'), tone: 'text-emerald-400' },
    { label: t('intel.putWall'), value: data.put_wall ? fmt(data.put_wall) : '—', sub: t('intel.putWallSub'), tone: 'text-rose-400' },
  ];

  const maxOi = Math.max(1, ...(data.oiMap || []).map((r) => Math.max(r.ceOi || 0, r.peOi || 0)));
  const features = data.features || {};

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title"><Radar size={18} className="text-cyan-400" /> {t('intel.title')}</div>
        <span className={`badge ${sourceLive ? 'badge-success' : 'badge-warning'}`}>
          {sourceLive ? t('intel.sourceLive') : t('intel.sourceSynthetic')}
        </span>
      </div>

      {/* Direction score */}
      <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800 mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-secondary font-semibold">
            <Gauge size={12} className="text-cyan-400" /> {t('intel.direction')}
          </div>
          <span className={`flex items-center gap-1.5 text-sm font-bold ${labelTone}`}>
            <LabelIcon size={15} /> {t(`intel.${label.toLowerCase()}`) || label}
          </span>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.08)', height: '10px', borderRadius: '6px', position: 'relative' }}>
          <div style={{ width: `${score}%`, height: '100%', borderRadius: '6px', transition: 'width 0.6s ease', background: isBull ? 'var(--accent-green)' : isBear ? '#fb7185' : 'var(--accent-gold)' }} />
          <div style={{ position: 'absolute', left: '50%', top: '-4px', bottom: '-4px', width: '1px', background: 'rgba(255,255,255,0.3)' }} />
        </div>
        <div className="flex justify-between text-[10px] text-secondary mt-1">
          <span>0 (Bearish)</span><span>{score}</span><span>100 (Bullish)</span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        {metrics.map((m) => (
          <div key={m.label} className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
            <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{m.label}</div>
            <div className={`text-base font-bold font-mono ${m.tone}`}>{m.value}</div>
            <div className="text-[11px] text-secondary mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* OI Strike Map */}
      <h3 style={{ marginBottom: '0.75rem' }} className="text-sm font-semibold text-white">{t('intel.strikeMap')}</h3>
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>{t('intel.strike')}</th>
              <th>CE {t('intel.ceOi')}</th>
              <th>CE {t('intel.ceLtp')}</th>
              <th>CE {t('intel.ceIv')}</th>
              <th>PE {t('intel.peOi')}</th>
              <th>PE {t('intel.peLtp')}</th>
              <th>PE {t('intel.peIv')}</th>
            </tr>
          </thead>
          <tbody>
            {(data.oiMap || []).map((r) => (
              <tr key={r.strike}>
                <td className="font-mono">
                  {fmt(r.strike)}
                  {r.moneyness === 'ATM' && <span className="badge badge-warning" style={{ marginLeft: '0.5rem', fontSize: '0.55rem' }}>{t('intel.atm')}</span>}
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <div style={{ flex: 1, maxWidth: '70px', background: 'rgba(255,255,255,0.06)', height: '6px', borderRadius: '3px' }}>
                      <div style={{ width: `${((r.ceOi || 0) / maxOi) * 100}%`, height: '100%', background: 'var(--accent-green)', borderRadius: '3px' }} />
                    </div>
                    <span className="font-mono text-xs">{(r.ceOi / 100000).toFixed(1)}L</span>
                  </div>
                </td>
                <td className="font-mono">₹{fmt(r.ceLtp)}</td>
                <td className="font-mono">{fmt(r.ceIv)}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <div style={{ flex: 1, maxWidth: '70px', background: 'rgba(255,255,255,0.06)', height: '6px', borderRadius: '3px' }}>
                      <div style={{ width: `${((r.peOi || 0) / maxOi) * 100}%`, height: '100%', background: '#fb7185', borderRadius: '3px' }} />
                    </div>
                    <span className="font-mono text-xs">{(r.peOi / 100000).toFixed(1)}L</span>
                  </div>
                </td>
                <td className="font-mono">₹{fmt(r.peLtp)}</td>
                <td className="font-mono">{fmt(r.peIv)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Flow read */}
      {Array.isArray(data.reasons) && data.reasons.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white">{t('intel.reasons')}</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {data.reasons.map((r, i) => (
              <span key={i} className="badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                <ShieldAlert size={11} className="text-cyan-400" /> {r}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ML features */}
      <div style={{ marginTop: '1rem' }}>
        <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white">{t('intel.features')}</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {Object.entries(features).map(([k, v]) => (
            <span key={k} className="badge" style={{ fontFamily: 'monospace' }}>
              <Activity size={11} className="text-violet-400" /> {k}: {typeof v === 'number' ? v.toFixed(3) : v}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
