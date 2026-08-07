import React, { useEffect, useState } from 'react';
import { fetchDailyReport, generateDailyReport } from '../services/api';
import { useLanguage } from '../i18n.jsx';
import {
  FileText, CalendarClock, RefreshCw, TrendingUp, TrendingDown, Minus,
  Wallet, Target, ShieldAlert, Gauge, Newspaper, ShieldCheck, ListChecks, Activity
} from 'lucide-react';

const fmt = (n) => (typeof n === 'number' ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—');
const fmtSigned = (n) => (typeof n === 'number' ? `${n > 0 ? '+' : ''}${n.toFixed(2)}%` : '—');
const fmtPnl = (n) => (typeof n === 'number' ? `₹${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '—');

function Movement({ value }) {
  const v = Number(value || 0);
  const cls = v > 0 ? 'text-emerald-400' : v < 0 ? 'text-rose-400' : 'text-secondary';
  return <span className={cls} style={{ fontFamily: 'monospace' }}>{v > 0 ? '+' : ''}{v.toFixed(2)}%</span>;
}

function Label({ children }) {
  return <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{children}</div>;
}

function LogicList({ items, t }) {
  if (!items || !items.length) return null;
  return (
    <div style={{ marginTop: '0.5rem' }}>
      <Label>{t('report.logic')}</Label>
      <div style={{ marginTop: '0.25rem' }}>
        {items.map((l, i) => (
          <div key={i} className="flex items-start gap-1.5 text-xs text-secondary mb-0.5">
            <span className="text-cyan-500" style={{ lineHeight: '1.4' }}>▸</span>
            <span style={{ lineHeight: '1.4' }}>{l}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ToneBadge({ label }) {
  const cls = label === 'BULLISH' ? 'badge-success'
    : label === 'BEARISH' ? 'badge-danger'
    : label === 'NEUTRAL' ? 'badge-warning' : 'badge';
  return <span className={cls}>{label}</span>;
}

export default function DailyReport({ symbol = 'NIFTY' }) {
  const { t } = useLanguage();
  const [data, setData] = useState({ report: null, next_run_ist: null });
  const [busy, setBusy] = useState(false);

  const load = async () => setData(await fetchDailyReport());

  useEffect(() => { load(); }, []);

  const handleGenerate = async () => {
    setBusy(true);
    const res = await generateDailyReport();
    if (res && res.report) setData({ report: res.report, next_run_ist: data.next_run_ist });
    setBusy(false);
  };

  const rep = data.report;

  if (!rep) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title"><FileText size={18} className="text-cyan-400" /> {t('report.heading')}</div>
        </div>
        <div className="text-center py-10 text-secondary font-semibold">{t('report.notGenerated')}</div>
        {data.next_run_ist && (
          <div className="text-center pb-6 text-xs text-secondary">
            {t('report.nextRun')}: <span className="font-mono" style={{ color: 'var(--accent-gold)' }}>{new Date(data.next_run_ist).toLocaleString()}</span>
          </div>
        )}
        <div className="text-center pb-6">
          <button className="tab-btn" onClick={handleGenerate} disabled={busy} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <RefreshCw size={14} className={busy ? 'spin' : ''} /> {t('report.generate')}
          </button>
        </div>
      </div>
    );
  }

  const cond = rep.market_condition;
  const condTone = cond === 'BULLISH' ? 'text-emerald-400' : cond === 'BEARISH' ? 'text-rose-400' : 'text-amber-400';
  const CondIcon = cond === 'BULLISH' ? TrendingUp : cond === 'BEARISH' ? TrendingDown : Minus;
  const opts = rep.options || {};
  const od = opts.detail && opts.detail.available ? opts.detail : null;
  const sig = rep.signal || {};
  const port = rep.portfolio || {};
  const tech = rep.technical || {};
  const news = rep.news || {};
  const risk = rep.risk || {};
  const plan = rep.plan || {};
  const movers = rep.movers || {};
  const sourceLive = opts.data_source === 'LIVE' || opts.data_source === 'nse-direct';

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title"><FileText size={18} className="text-cyan-400" /> {t('report.heading')}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className={`badge ${rep.posted === 'AUTO' ? 'badge-success' : 'badge-warning'}`}>
            {rep.posted === 'AUTO' ? t('report.autoBadge') : t('report.manualBadge')}
          </span>
          <button className="tab-btn" onClick={handleGenerate} disabled={busy} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <RefreshCw size={14} className={busy ? 'spin' : ''} /> {t('report.generate')}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
        <span className="flex items-center gap-1"><CalendarClock size={13} /> {rep.date} · {new Date(rep.generated_at).toLocaleTimeString()}</span>
        {data.next_run_ist && <span>{t('report.nextRun')}: <span className="font-mono">{new Date(data.next_run_ist).toLocaleString()}</span></span>}
      </div>

      {/* Headline + condition */}
      <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800 mb-4">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
          <span className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{t('report.condition')}</span>
          <span className={`flex items-center gap-1.5 text-sm font-bold ${condTone}`}>
            <CondIcon size={15} /> {cond}
            {typeof rep.cond_score === 'number' && <span className="font-mono text-xs text-secondary">({fmtSigned(rep.cond_score)})</span>}
          </span>
        </div>
        <div className="text-sm font-semibold text-white">{rep.headline}</div>
        {typeof rep.avg_index_change_pct === 'number' && (
          <div className="text-xs text-secondary mt-1">
            {t('report.avgIndex')}: <Movement value={rep.avg_index_change_pct} />
          </div>
        )}
      </div>

      {/* Index snapshot */}
      <h3 style={{ marginBottom: '0.75rem' }} className="text-sm font-semibold text-white">{t('report.indices')}</h3>
      <div className="grid grid-cols-3 gap-3 mb-4">
        {(rep.indices || []).map((i) => (
          <div key={i.symbol} className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
            <div className="flex items-center justify-between">
              <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{i.symbol}</div>
              {i.trend && <ToneBadge label={i.trend} />}
            </div>
            <div className="text-lg font-bold font-mono">₹{fmt(i.price)}</div>
            <div className="text-xs"><Movement value={i.change_pct} /> <span className="text-secondary">({i.data_source})</span></div>
          </div>
        ))}
      </div>

      {/* Movers */}
      <div className="grid-2col mb-4">
        <div>
          <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-emerald-400">{t('report.gainers')}</h3>
          <table className="data-table">
            <thead><tr><th>Symbol</th><th>Price</th><th>Chg %</th></tr></thead>
            <tbody>
              {(movers.gainers || []).map((g) => (
                <tr key={g.symbol}><td className="font-mono">{g.symbol}</td><td className="font-mono">₹{fmt(g.price)}</td><td><Movement value={g.change_pct} /></td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-rose-400">{t('report.losers')}</h3>
          <table className="data-table">
            <thead><tr><th>Symbol</th><th>Price</th><th>Chg %</th></tr></thead>
            <tbody>
              {(movers.losers || []).map((g) => (
                <tr key={g.symbol}><td className="font-mono">{g.symbol}</td><td className="font-mono">₹{fmt(g.price)}</td><td><Movement value={g.change_pct} /></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid-2col">
        {/* Trading signal */}
        {sig.action && (
          <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
            <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><Target size={14} className="text-cyan-400" /> {t('report.signal')}</h3>
            <div className="flex items-center gap-2 mb-2">
              <span className={`badge ${sig.action.includes('BUY') ? 'badge-success' : 'badge-warning'}`}>{sig.action}</span>
              <span className="text-xs text-secondary">{t('report.contract')}: <span className="font-mono text-white">{sig.contract}</span></span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-secondary">{t('report.entry')}</span> <span className="font-mono font-semibold">₹{fmt(sig.entry)}</span></div>
              <div><span className="text-secondary">{t('report.target')}</span> <span className="font-mono font-semibold text-emerald-400">₹{fmt(sig.target)}</span></div>
              <div><span className="text-secondary">{t('report.stopLoss')}</span> <span className="font-mono font-semibold text-rose-400">₹{fmt(sig.stop_loss)}</span></div>
              <div><span className="text-secondary">{t('report.rr')}</span> <span className="font-mono font-semibold">{sig.rr}</span></div>
            </div>
            <div style={{ marginTop: '0.5rem' }} className="text-xs">
              <span className="text-secondary">{t('report.winProb')}:</span>{' '}
              <span className="font-mono font-bold" style={{ color: 'var(--accent-gold)' }}>{sig.win_probability}%</span>
            </div>
            {(sig.rules || []).length > 0 && (
              <div style={{ marginTop: '0.5rem' }}>
                <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{t('report.rules')}</div>
                {(sig.rules).map((r, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-xs mb-0.5">
                    <span className={r.status === 'PASSED' ? 'text-emerald-400' : r.status === 'CAUTION' ? 'text-amber-400' : 'text-secondary'}>{r.status === 'PASSED' ? '✓' : r.status === 'CAUTION' ? '⚠' : '○'}</span>
                    <span className="text-secondary">{r.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Options intelligence */}
        <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
          <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><ShieldAlert size={14} className="text-cyan-400" /> {t('report.options')}</h3>
          <div className="flex items-center gap-2 mb-2">
            <span className={`badge ${sourceLive ? 'badge-success' : 'badge-warning'}`}>{sourceLive ? t('report.sourceLive') : t('report.sourceSynthetic')}</span>
            <span className="text-xs font-bold" style={{ color: condTone }}>{opts.direction_label} ({opts.direction_score})</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div><span className="text-secondary">{t('report.pcr')}</span> <span className="font-mono font-semibold">{fmt(opts.pcr_oi)}</span></div>
            <div><span className="text-secondary">{t('report.maxPain')}</span> <span className="font-mono font-semibold">{fmt(opts.max_pain_strike)}</span></div>
            <div><span className="text-secondary">{t('report.ivRank')}</span> <span className="font-mono font-semibold">{fmt(opts.iv_rank_pct)}%</span></div>
            <div><span className="text-secondary">ATM IV</span> <span className="font-mono font-semibold">{fmt(opts.atm_iv)}</span></div>
            <div><span className="text-secondary">Call Wall</span> <span className="font-mono font-semibold text-emerald-400">{fmt(opts.call_wall)}</span></div>
            <div><span className="text-secondary">Put Wall</span> <span className="font-mono font-semibold text-rose-400">{fmt(opts.put_wall)}</span></div>
          </div>
          {(opts.reasons || []).length > 0 && (
            <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
              {opts.reasons.map((r, i) => <span key={i} className="badge">{r}</span>)}
            </div>
          )}
        </div>
      </div>

      {/* Technical analysis */}
      {tech.available && (
        <div style={{ marginTop: '1rem' }} className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
          <h3 style={{ marginBottom: '0.75rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><Gauge size={14} className="text-cyan-400" /> {t('report.technical')} <span className="font-mono text-xs text-secondary">· {rep.symbol}</span></h3>

          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className={`badge ${tech.regime === 'BULLISH' ? 'badge-success' : tech.regime === 'BEARISH' ? 'badge-danger' : 'badge-warning'}`}>
              {t('report.regime')}: {tech.regime} {typeof tech.regime_confidence === 'number' && `(${tech.regime_confidence}%)`}
            </span>
            <span className={`badge ${tech.signal_strength && tech.signal_strength.includes('BUY') ? 'badge-success' : tech.signal_strength && tech.signal_strength.includes('SELL') ? 'badge-danger' : 'badge-warning'}`}>
              {tech.signal_strength || '—'} {tech.signal_grade && <span className="font-bold" style={{ color: 'var(--accent-gold)' }}>· {tech.signal_grade}</span>}
            </span>
            {typeof tech.signal_score === 'number' && <span className="text-xs text-secondary">{t('report.signalScore')}: <span className="font-mono text-white">{tech.signal_score}</span></span>}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            <div><Label>{t('report.rsi')}</Label><div className="font-mono font-bold text-sm">{fmt(tech.rsi)}</div></div>
            <div><Label>{t('report.stochRsi')}</Label><div className="font-mono font-bold text-sm">{fmt(tech.stoch_rsi)}</div></div>
            <div><Label>{t('report.adx')}</Label><div className="font-mono font-bold text-sm">{fmt(tech.adx)}</div></div>
            <div><Label>{t('report.vwap')}</Label><div className="font-mono font-bold text-sm">{fmt(tech.vwap)}</div></div>
            <div><Label>{t('report.atr')}</Label><div className="font-mono font-bold text-sm">{fmt(tech.atr_pct)}%</div></div>
            <div><Label>{t('report.volSurge')}</Label><div className="font-mono font-bold text-sm">{fmt(tech.vol_surge_ratio)}x</div></div>
            <div><Label>SuperTrend</Label><div className="text-sm font-bold">{tech.supertrend_bullish ? <span className="text-emerald-400">GREEN</span> : <span className="text-rose-400">RED</span>}</div></div>
            <div><Label>EMA 9/21</Label><div className="text-sm font-bold">{tech.ema_bullish ? <span className="text-emerald-400">{t('report.bullish')}</span> : <span className="text-rose-400">{t('report.bearish')}</span>}</div></div>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
              <Label>{t('report.supports')}</Label>
              <div style={{ marginTop: '0.25rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {(tech.supports || []).map((s, i) => <span key={i} className="badge" style={{ color: '#6ee7b7' }}>{fmt(s)}</span>)}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
              <Label>{t('report.resistances')}</Label>
              <div style={{ marginTop: '0.25rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {(tech.resistances || []).map((s, i) => <span key={i} className="badge" style={{ color: '#fda4af' }}>{fmt(s)}</span>)}
              </div>
            </div>
          </div>

          {(tech.signal_reasons || []).length > 0 && (
            <div style={{ marginTop: '0.25rem' }}>
              <Label>{t('report.reasons')}</Label>
              <div style={{ marginTop: '0.35rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {tech.signal_reasons.map((r, i) => (
                  <span key={i} className="badge" style={{ color: r.type === 'bull' ? '#6ee7b7' : r.type === 'bear' ? '#fda4af' : '#fcd34d' }}>{r.text}</span>
                ))}
              </div>
            </div>
          )}

          {tech.interpretation && (
            <div style={{ marginTop: '0.5rem' }} className="text-xs text-white/90">
              <span className="text-secondary font-semibold">{t('report.interpretation')}: </span>{tech.interpretation}
            </div>
          )}
          <LogicList items={tech.logic} t={t} />
        </div>
      )}

      <div className="grid-2col" style={{ marginTop: '1rem' }}>
        {/* Options strategy detail */}
        {od && (
          <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
            <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><Activity size={14} className="text-cyan-400" /> {t('report.optionsStrategy')}</h3>
            <div className="flex items-center gap-2 mb-2">
              <span className="badge" style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80', borderColor: 'rgba(34,197,94,0.4)' }}>{od.signal}</span>
              <span className="text-xs"><span className="text-secondary">{t('report.strategyScore')}:</span> <span className="font-mono font-bold text-white">{fmt(od.strategy_score)}/100</span></span>
              <span className="text-xs"><span className="text-secondary">{t('report.quality')}:</span> <span className="font-bold" style={{ color: 'var(--accent-gold)' }}>{od.quality}</span></span>
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              <div className="flex flex-wrap gap-1.5">
                {(od.passed || []).map((p, i) => <span key={i} className="badge badge-success">{p}</span>)}
                {(od.failed || []).map((p, i) => <span key={i} className="badge badge-danger">{p}</span>)}
              </div>
            </div>
            {od.recommendation && <div className="text-xs text-white/90 mb-1"><span className="text-secondary font-semibold">{t('report.recommendation')}: </span>{od.recommendation}</div>}
            {od.iv_interpretation && <div className="text-xs text-white/90 mb-1"><span className="text-secondary font-semibold">{t('report.ivRead')}: </span>{od.iv_interpretation}</div>}
            <LogicList items={od.logic} t={t} />
          </div>
        )}

        {/* News sentiment */}
        {news.available && (
          <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
            <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><Newspaper size={14} className="text-cyan-400" /> {t('report.newsSentiment')}</h3>
            <div className="flex items-center gap-2 mb-2">
              <ToneBadge label={news.classification} />
              <span className="text-xs text-secondary">{t('report.newsScore')}: <span className="font-mono text-white">{fmt(news.score)}</span></span>
              <span className="text-xs text-secondary">{t('report.sources')}: <span className="font-mono text-white">{news.sources}</span></span>
            </div>
            {(news.headlines || []).length > 0 && (
              <div style={{ marginBottom: '0.25rem' }}>
                <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{t('report.headlines')}</div>
                {(news.headlines).slice(0, 5).map((h, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-xs text-secondary mb-0.5">
                    <span className="text-cyan-500" style={{ lineHeight: '1.4' }}>•</span>
                    <span style={{ lineHeight: '1.4' }}>{h}</span>
                  </div>
                ))}
              </div>
            )}
            <LogicList items={news.logic} t={t} />
          </div>
        )}
      </div>

      <div className="grid-2col" style={{ marginTop: '1rem' }}>
        {/* Risk summary */}
        {risk && typeof risk.atr_pct === 'number' && (
          <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
            <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><ShieldCheck size={14} className="text-cyan-400" /> {t('report.risk')}</h3>
            <div className="grid grid-cols-2 gap-2 text-xs mb-1">
              <div><span className="text-secondary">{t('report.atr')}</span> <span className="font-mono font-semibold">{fmt(risk.atr_pct)}%</span></div>
              <div><span className="text-secondary">{t('report.volClass')}</span> <span className="font-semibold">{risk.vol_class}</span></div>
              <div><span className="text-secondary">{t('report.ivRank')}</span> <span className="font-mono font-semibold">{fmt(risk.iv_rank_pct)}%</span></div>
              <div><span className="text-secondary">{t('report.directionScore')}</span> <span className="font-mono font-semibold">{fmt(risk.direction_score)}</span></div>
            </div>
            <LogicList items={risk.logic} t={t} />
          </div>
        )}

        {/* Action plan */}
        {plan && plan.verdict && (
          <div className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
            <h3 style={{ marginBottom: '0.5rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><ListChecks size={14} className="text-cyan-400" /> {t('report.plan')}</h3>
            <div className="text-xs font-semibold text-white mb-1">{t('report.verdict')}:</div>
            <div className="text-sm font-semibold mb-2" style={{ color: 'var(--accent-gold)' }}>{plan.verdict}</div>
            {(plan.actions || []).length > 0 && (
              <div style={{ marginBottom: '0.25rem' }}>
                <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{t('report.actions')}</div>
                {plan.actions.map((a, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-xs text-secondary mb-0.5">
                    <span className="text-emerald-400" style={{ lineHeight: '1.4' }}>✓</span>
                    <span style={{ lineHeight: '1.4' }}>{a}</span>
                  </div>
                ))}
              </div>
            )}
            <LogicList items={plan.logic} t={t} />
          </div>
        )}
      </div>

      {/* Portfolio */}
      <div style={{ marginTop: '1rem' }} className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
        <h3 style={{ marginBottom: '0.75rem' }} className="text-sm font-semibold text-white flex items-center gap-1.5"><Wallet size={14} className="text-gold" /> {t('report.portfolio')}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div><div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{t('report.totalValue')}</div><div className="text-base font-bold font-mono">{fmtPnl(port.total_value)}</div></div>
          <div><div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{t('report.cash')}</div><div className="text-base font-bold font-mono">{fmtPnl(port.cash)}</div></div>
          <div><div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{t('report.totalPnl')}</div><div className="text-base font-bold font-mono"><Movement value={port.total_pnl_pct} /> <span className="text-secondary">({fmtPnl(port.total_pnl)})</span></div></div>
          <div><div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{t('report.winRate')}</div><div className="text-base font-bold font-mono">{port.win_rate_pct}%</div></div>
        </div>
        <div className="text-xs text-secondary" style={{ marginTop: '0.5rem' }}>
          {t('report.openPositions')}: <span className="font-mono text-white">{port.open_positions}</span> · Closed: <span className="font-mono text-white">{port.closed_trades}</span>
        </div>
        {(port.positions || []).length > 0 && (
          <div style={{ marginTop: '0.75rem' }}>
            <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1">{t('report.positions')}</div>
            <table className="data-table">
              <thead><tr><th>{t('report.colSymbol')}</th><th>{t('report.colEntry')}</th><th>{t('report.colCurrent')}</th><th>P&L %</th><th>P&L ₹</th></tr></thead>
              <tbody>
                {(port.positions).map((p, i) => (
                  <tr key={i}>
                    <td className="font-mono">{p.symbol}</td>
                    <td className="font-mono">₹{fmt(p.entry)}</td>
                    <td className="font-mono">₹{fmt(p.current)}</td>
                    <td><Movement value={p.pnl_pct} /></td>
                    <td className={`font-mono ${p.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{fmtPnl(p.unrealized_pnl)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
