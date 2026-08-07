import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { runBacktest } from '../services/api';
import { useLanguage } from '../i18n.jsx';
import { Play, Activity, Percent, TrendingDown, Timer, BarChart3, SlidersHorizontal } from 'lucide-react';

const SCENARIOS = {
  balanced: {
    labelKey: 'bt.scenarioBalanced',
    descKey: 'bt.scenarioBalancedDesc',
    params: { volumeMultiplier: 2.0, holdingDays: 5, stopLossPct: 2.0, takeProfitPct: 6.0, initialCapital: 100000, costPerTradePct: 0.15 },
  },
  conservative: {
    labelKey: 'bt.scenarioConservative',
    descKey: 'bt.scenarioConservativeDesc',
    params: { volumeMultiplier: 2.5, holdingDays: 10, stopLossPct: 1.5, takeProfitPct: 8.0, initialCapital: 100000, costPerTradePct: 0.15 },
  },
  aggressive: {
    labelKey: 'bt.scenarioAggressive',
    descKey: 'bt.scenarioAggressiveDesc',
    params: { volumeMultiplier: 1.5, holdingDays: 3, stopLossPct: 3.0, takeProfitPct: 9.0, initialCapital: 100000, costPerTradePct: 0.15 },
  },
};

const PARAM_FIELDS = [
  { key: 'holdingDays', labelKey: 'bt.holdingDays', step: 1, min: 1, max: 30 },
  { key: 'volumeMultiplier', labelKey: 'bt.volumeMult', step: 0.1, min: 1.0, max: 5.0 },
  { key: 'stopLossPct', labelKey: 'bt.stopLoss', step: 0.1, min: 0.5, max: 5.0 },
  { key: 'takeProfitPct', labelKey: 'bt.takeProfit', step: 0.5, min: 2.0, max: 20.0 },
  { key: 'initialCapital', labelKey: 'bt.capital', step: 10000, min: 10000, max: 5000000 },
  { key: 'costPerTradePct', labelKey: 'bt.cost', step: 0.05, min: 0.05, max: 1.0 },
];

export default function Backtesting({ symbol }) {
  const { t } = useLanguage();
  const [scenario, setScenario] = React.useState('balanced');
  const [params, setParams] = React.useState(SCENARIOS.balanced.params);
  const [result, setResult] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const loadBacktest = async (sym, p) => {
    setLoading(true);
    setError(null);
    try {
      const res = await runBacktest(sym, p);
      setResult(res);
    } catch (e) {
      setError(t('bt.error'));
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (symbol) {
      setScenario('balanced');
      const preset = SCENARIOS.balanced.params;
      setParams(preset);
      loadBacktest(symbol, preset);
    }
  }, [symbol]);

  const handleScenarioChange = (e) => {
    const key = e.target.value;
    setScenario(key);
    if (SCENARIOS[key]) {
      setParams({ ...SCENARIOS[key].params });
      setResult(null);
    }
  };

  const handleParamChange = (key, value) => {
    setScenario('custom');
    setParams((prev) => ({ ...prev, [key]: Number(value) }));
  };

  const handleRun = () => {
    loadBacktest(symbol, params);
  };

  const activeScenario = SCENARIOS[scenario];
  const chartData = result?.equityCurve?.map((p) => ({
    date: String(p.date || '').slice(0, 10),
    equity: p.equity,
  })) || [];

  const winRate = result?.winRatePct ?? 0;
  const totalReturn = result?.totalReturnPct ?? 0;
  const maxDrawdown = result?.maxDrawdownPct ?? 0;
  const sharpe = result?.sharpeRatio ?? 0;
  const totalTrades = result?.totalTrades ?? 0;
  const costPerTrade = result?.costPerTradePct ?? params.costPerTradePct;

  const metrics = [
    { icon: Percent, label: t('bt.winRate'), value: `${winRate}%`, tone: 'text-emerald-400', sub: t('bt.winsLosses', { wins: result?.winningTrades ?? 0, losses: result?.losingTrades ?? 0 }) },
    { icon: BarChart3, label: t('bt.totalReturn'), value: `${totalReturn > 0 ? '+' : ''}${totalReturn}%`, tone: totalReturn >= 0 ? 'text-emerald-400' : 'text-rose-400', sub: t('bt.cagr', { cagr: result?.cagrPct ?? 0 }) },
    { icon: TrendingDown, label: t('bt.maxDrawdown'), value: `${maxDrawdown}%`, tone: 'text-rose-400', sub: t('bt.calmar', { calmar: result?.calmarRatio ?? 0 }) },
    { icon: Activity, label: t('bt.sharpe'), value: sharpe, tone: sharpe >= 1 ? 'text-emerald-400' : 'text-amber-400', sub: t('bt.annualised') },
    { icon: Timer, label: t('bt.trades'), value: totalTrades, tone: 'text-cyan-400', sub: t('bt.costSide', { cost: costPerTrade }) },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">{t('bt.title')}</div>
        <button className="btn btn-primary" onClick={handleRun} disabled={loading}>
          <Play size={15} /> {loading ? t('bt.running') : t('bt.run')}
        </button>
      </div>

      <p className="text-xs text-secondary mb-4">
        {t('bt.desc', { symbol, cost: costPerTrade })}
      </p>

      {result?.signalType && (
        <div className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full border mb-4 ${result.signalType === 'VOLUME_SURGE' ? 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30' : 'text-violet-400 bg-violet-500/10 border-violet-500/30'}`}>
          {result.signalType === 'VOLUME_SURGE' ? t('bt.signalVolume') : t('bt.signalPrice')}
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm mb-4">
          {error}
        </div>
      )}

      {/* Scenario Selector */}
      <div className="rounded-xl border border-gray-800 bg-gray-950/50 p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 text-xs text-secondary font-semibold uppercase tracking-widest">
            <SlidersHorizontal className="text-cyan-400 w-4 h-4" />
            {t('bt.scenario')}
          </div>
          <select
            value={scenario}
            onChange={handleScenarioChange}
            className="bg-gray-900 text-white text-sm font-semibold border border-gray-700 rounded-lg px-3 py-2 outline-none focus:border-cyan-400 cursor-pointer"
          >
            {Object.keys(SCENARIOS).map((key) => (
              <option key={key} value={key}>{t(SCENARIOS[key].labelKey)}</option>
            ))}
            {scenario === 'custom' && (
              <option value="custom" disabled>{t('bt.scenarioCustom')}</option>
            )}
          </select>
        </div>

        <div className="text-[11px] text-cyan-300/80 font-mono mb-4">
          {activeScenario ? t(activeScenario.descKey) : t('bt.scenarios.custom')}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {PARAM_FIELDS.map((f) => (
            <div key={f.key} className="p-3 rounded-lg bg-gray-900/70 border border-gray-800">
              <label className="block text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1.5">
                {t(f.labelKey)}
              </label>
              <input
                type="number"
                value={params[f.key]}
                min={f.min}
                max={f.max}
                step={f.step}
                onChange={(e) => handleParamChange(f.key, e.target.value)}
                className="w-full bg-transparent text-white font-mono font-bold text-sm outline-none border-b border-gray-700 focus:border-cyan-400"
              />
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        {metrics.map((m) => (
          <div key={m.label} className="p-4 rounded-xl bg-gray-950/70 border border-gray-800">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-secondary font-semibold mb-1.5">
              <m.icon size={12} className={m.tone} />
              {m.label}
            </div>
            <div className={`text-xl font-bold font-mono ${m.tone}`}>{m.value}</div>
            <div className="text-[11px] text-secondary mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-950/50 p-4">
        <div className="text-xs text-secondary font-semibold mb-3 uppercase tracking-widest">{t('bt.equityCurve')}</div>
        <div style={{ height: '320px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" stroke="var(--text-secondary)" tick={{ fontSize: 10 }} minTickGap={40} />
              <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 10 }} domain={['auto', 'auto']} width={70} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', borderRadius: 10 }}
                formatter={(value) => [`₹${Number(value).toLocaleString()}`, 'Equity']}
              />
              <Area type="monotone" dataKey="equity" stroke="var(--accent-blue)" fillOpacity={1} fill="url(#colorVal)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
