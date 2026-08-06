import React, { useState, useEffect } from 'react';
import { fetchProfitPlaybook } from '../services/api';
import { TrendingUp, ShieldCheck, DollarSign, Target, Clock, AlertTriangle, Cpu, Percent } from 'lucide-react';

export default function ProfitPlaybook({ symbol }) {
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
    return <div className="card text-center py-8 text-secondary">Loading Wealth Creation Engine...</div>;
  }

  const sizing = data?.position_sizing || {};
  const rules = data?.golden_rules_audit || [];

  return (
    <div className="profit-playbook-wrapper flex flex-col gap-6">
      {/* Header Banner */}
      <div className="card p-6 border-l-4 border-emerald-500 bg-gradient-to-r from-emerald-950/30 to-gray-900">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="text-emerald-400 w-6 h-6" />
              <h2 className="text-2xl font-bold text-emerald-400">Institutional Wealth Creation Playbook</h2>
            </div>
            <p className="text-secondary text-sm">
              5-Rule Quantitative Formula for Option Buying & High-Probability Profit Generation
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-secondary">Capital (₹):</span>
            <input 
              type="number" 
              value={capital} 
              onChange={(e) => setCapital(Number(e.target.value))}
              className="bg-gray-950 text-emerald-400 font-mono text-sm px-3 py-1.5 rounded border border-emerald-500/30 w-32 outline-none focus:border-emerald-400"
            />
          </div>
        </div>
      </div>

      {/* Main Trade Signal Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-5 md:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="badge badge-success px-3 py-1 font-bold text-xs flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5" /> {data?.trade_status || "STRONG_BUY"}
              </span>
              <span className="text-xs text-secondary">Contract: <strong className="text-emerald-400">{data?.option_contract}</strong></span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 my-4 p-4 rounded-lg bg-gray-950/60 border border-gray-800">
              <div>
                <div className="text-xs text-secondary mb-1">Spot Price</div>
                <div className="text-lg font-mono font-bold text-white">₹{data?.spot_price}</div>
              </div>
              <div>
                <div className="text-xs text-secondary mb-1">Entry Premium</div>
                <div className="text-lg font-mono font-bold text-cyan-400">₹{data?.entry_premium}</div>
              </div>
              <div>
                <div className="text-xs text-secondary mb-1">Target (1:2.5)</div>
                <div className="text-lg font-mono font-bold text-emerald-400">₹{data?.target_premium}</div>
              </div>
              <div>
                <div className="text-xs text-secondary mb-1">Stop Loss</div>
                <div className="text-lg font-mono font-bold text-rose-400">₹{data?.stop_loss_premium}</div>
              </div>
            </div>

            {/* Position Sizer Result */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs mt-2">
              <div className="p-2.5 rounded bg-gray-900/80 border border-gray-800">
                <span className="text-secondary block">Lots to Buy:</span>
                <span className="font-mono text-sm text-amber-400 font-bold">{sizing.recommended_lots} Lots ({sizing.total_quantity} Qty)</span>
              </div>
              <div className="p-2.5 rounded bg-gray-900/80 border border-gray-800">
                <span className="text-secondary block">Capital Required:</span>
                <span className="font-mono text-sm text-cyan-400 font-bold">₹{sizing.investment_required?.toLocaleString()}</span>
              </div>
              <div className="p-2.5 rounded bg-emerald-950/40 border border-emerald-500/30">
                <span className="text-emerald-400 block font-semibold">Expected Profit:</span>
                <span className="font-mono text-base text-emerald-400 font-bold">+₹{sizing.potential_profit?.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Win Probability Card */}
        <div className="card p-5 flex flex-col items-center justify-center text-center border-l-4 border-cyan-500">
          <div className="relative flex items-center justify-center my-3">
            <div className="w-28 h-28 rounded-full border-4 border-cyan-500/20 flex items-center justify-center">
              <div className="text-2xl font-bold font-mono text-cyan-400">
                {data?.win_probability}%
              </div>
            </div>
          </div>
          <div className="text-sm font-semibold text-white mb-1 flex items-center gap-1">
            <Cpu className="w-4 h-4 text-cyan-400" /> AI Swarm Win Confidence
          </div>
          <p className="text-xs text-secondary px-2">
            Multi-model ensemble probability score based on 16 quantitative market factors.
          </p>
        </div>
      </div>

      {/* 5 Golden Rules Compliance Table */}
      <div className="card p-5">
        <h3 className="card-title text-base text-white mb-4 flex items-center gap-2">
          <ShieldCheck className="text-emerald-400 w-5 h-5" />
          5 Golden Rules Compliance Checklist
        </h3>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rule Name</th>
                <th>Status</th>
                <th>Institutional Logic & Parameter Detail</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r, idx) => (
                <tr key={idx}>
                  <td className="font-semibold text-white">{r.rule}</td>
                  <td>
                    <span className={`badge ${
                      r.status === 'PASSED' ? 'badge-success' : 'badge-warning'
                    }`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="text-secondary text-xs font-mono">{r.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
