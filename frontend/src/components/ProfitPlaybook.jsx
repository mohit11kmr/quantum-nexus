import React, { useState, useEffect } from 'react';
import { fetchProfitPlaybook } from '../services/api';
import { useLanguage } from '../i18n.jsx';
import { TrendingUp, ShieldCheck, DollarSign, HelpCircle, CheckCircle2, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function ProfitPlaybook({ symbol }) {
  const { t } = useLanguage();
  const [data, setData] = useState(null);
  const [capital, setCapital] = useState(100000);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPlaybookData();
  }, [symbol, capital]);

  const loadPlaybookData = async () => {
    setLoading(true);
    try {
      const res = await fetchProfitPlaybook(symbol, capital);
      setData(res);
    } catch (e) {
      console.error("Error loading playbook data", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return <div className="card text-center py-12 text-secondary font-semibold animate-fade-up">{t('pp.loading')}</div>;
  }

  const sizing = data?.position_sizing || {};
  const rules = data?.golden_rules_audit || [];
  const isBuy = data?.trade_status === 'ACTIVE_STRONG_BUY';
  const winProb = data?.win_probability ?? 0;
  const winTone = winProb >= 70 ? 'emerald' : winProb >= 50 ? 'amber' : 'rose';

  return (
    <div className="profit-playbook-wrapper flex flex-col gap-6">

      {/* 3-Second Explainer */}
      <div className="card p-4 border border-cyan-500/30 bg-gradient-to-r from-gray-900 via-gray-950 to-gray-900">
        <div className="flex items-center justify-between gap-2 border-b border-gray-800 pb-3 mb-3">
          <div className="flex items-center gap-2">
            <HelpCircle className="text-cyan-400 w-5 h-5" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              {t('pp.explainerTitle')}
            </h3>
          </div>
          <span className="text-xs bg-cyan-950 text-cyan-400 font-mono px-2.5 py-1 rounded border border-cyan-500/30">
            {t('pp.steps')}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="flex items-start gap-2.5 p-2.5 rounded bg-gray-900/60 border border-gray-800">
            <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center shrink-0">1</span>
            <div>
              <div className="font-bold text-white mb-0.5">{t('pp.step1Title')}</div>
              <div className="text-secondary">{t('pp.step1Body')}</div>
            </div>
          </div>
          <div className="flex items-start gap-2.5 p-2.5 rounded bg-gray-900/60 border border-gray-800">
            <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center shrink-0">2</span>
            <div>
              <div className="font-bold text-white mb-0.5">{t('pp.step2Title')}</div>
              <div className="text-secondary">{t('pp.step2Body')}</div>
            </div>
          </div>
          <div className="flex items-start gap-2.5 p-2.5 rounded bg-gray-900/60 border border-gray-800">
            <span className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 font-bold flex items-center justify-center shrink-0">3</span>
            <div>
              <div className="font-bold text-white mb-0.5">{t('pp.step3Title')}</div>
              <div className="text-secondary">{t('pp.step3Body')}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Decision Card */}
      <div className={`card p-6 border-t-4 bg-gradient-to-b from-gray-900 to-gray-950 ${isBuy ? 'border-t-emerald-400' : 'border-t-amber-400'}`}>
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-1">
              {t('pp.todayTitle')}
            </div>
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-extrabold text-white">{data?.symbol || symbol}</h2>
              <span className="text-2xl font-mono text-emerald-400 font-bold">
                ₹{data?.spot_price?.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 bg-gray-900 p-2.5 rounded-xl border border-gray-800">
            <DollarSign className="text-emerald-400 w-5 h-5" />
            <div className="text-left">
              <div className="text-[10px] text-secondary uppercase font-semibold">{t('pp.yourCapital')}</div>
              <div className="flex items-center gap-1">
                <span className="text-emerald-400 font-bold">₹</span>
                <input
                  type="number"
                  value={capital}
                  onChange={(e) => setCapital(Number(e.target.value))}
                  className="bg-transparent text-white font-mono font-bold text-base w-28 outline-none border-b border-emerald-500/50 focus:border-emerald-400"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Decision Banner */}
        <div className={`rounded-xl mb-6 p-4 flex flex-wrap items-center justify-between gap-3 border ${isBuy ? 'bg-emerald-500/10 border-emerald-500/40' : 'bg-amber-500/10 border-amber-500/40'}`}>
          <div className="flex items-center gap-3">
            {isBuy ? (
              <span className="w-11 h-11 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center"><TrendingUp size={22} /></span>
            ) : (
              <span className="w-11 h-11 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center"><AlertTriangle size={22} /></span>
            )}
            <div>
              <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{t('pp.decision')}</div>
              <div className={`text-2xl font-black ${isBuy ? 'text-emerald-400' : 'text-amber-400'}`}>
                {isBuy ? t('pp.buy') : t('pp.wait')} {isBuy ? <ArrowUpRight className="inline w-6 h-6" /> : <ArrowDownRight className="inline w-6 h-6" />}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-widest text-secondary font-semibold">{t('pp.contract')}</div>
            <div className="text-base font-bold text-white font-mono">{data?.option_contract}</div>
          </div>
        </div>

        {/* 4 Action Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 flex flex-col justify-between">
            <div className="text-xs text-emerald-300 font-semibold mb-2 flex items-center justify-between">
              <span>{t('pp.signal')}</span>
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400 mb-1">
              {isBuy ? t('pp.buyOrder') : t('pp.waitOrder')}
            </div>
            <div className="text-xs text-secondary">{data?.option_contract}</div>
          </div>

          <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 flex flex-col justify-between">
            <div className="text-xs text-secondary font-semibold mb-2">{t('pp.entryTarget')}</div>
            <div className="text-lg font-mono font-bold text-white mb-1">
              ₹{data?.entry_premium} ➔ <span className="text-emerald-400 font-extrabold">₹{data?.target_premium}</span>
            </div>
            <div className="text-xs text-rose-400">{t('pp.stopLoss')}: ₹{data?.stop_loss_premium}</div>
          </div>

          <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 flex flex-col justify-between">
            <div className="text-xs text-secondary font-semibold mb-2">{t('pp.lots')}</div>
            <div className="text-xl font-mono font-bold text-amber-400 mb-1">
              {sizing.recommended_lots} Lots ({sizing.total_quantity} Qty)
            </div>
            <div className="text-xs text-secondary">{t('pp.cost')}: ₹{sizing.investment_required?.toLocaleString()}</div>
          </div>

          <div className="p-4 rounded-xl bg-emerald-900/30 border border-emerald-500/50 flex flex-col justify-between">
            <div className="text-xs text-emerald-400 font-semibold mb-2">{t('pp.profit')}</div>
            <div className="text-2xl font-mono font-extrabold text-emerald-400 mb-1">
              +₹{sizing.potential_profit?.toLocaleString()}
            </div>
            <div className="text-xs text-emerald-300">{t('pp.riskReward')}: 1:2.5</div>
          </div>
        </div>

        {/* Win Confidence */}
        <div className="p-4 rounded-xl bg-gray-950 border border-gray-800">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-secondary font-semibold flex items-center gap-1.5">
              <ShieldCheck className="text-cyan-400 w-4 h-4" /> {t('pp.winProb')}
            </span>
            <span className={`font-mono text-base font-bold text-${winTone}-400`}>{winProb}%</span>
          </div>
          <div className="w-full h-3 bg-gray-900 rounded-full overflow-hidden border border-gray-800">
            <div
              className={`h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-1000`}
              style={{ width: `${winProb}%` }}
            />
          </div>
        </div>
      </div>

      {/* 5 Rules Checklist */}
      <div className="card p-5">
        <h3 className="card-title text-base text-white mb-4 flex items-center gap-2">
          <CheckCircle2 className="text-emerald-400 w-5 h-5" />
          {t('pp.rulesTitle')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {rules.map((r, idx) => (
            <div key={idx} className="p-3.5 rounded-lg bg-gray-950 border border-gray-800 flex items-start justify-between gap-3">
              <div>
                <div className="text-xs font-bold text-white mb-1">{r.rule}</div>
                <div className="text-[11px] text-secondary font-mono">{r.detail}</div>
              </div>
              <span className={`badge shrink-0 ${r.status === 'PASSED' ? 'badge-success' : 'badge-warning'}`}>
                {r.status === 'PASSED' ? t('pp.passed') : t('pp.caution')}
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
