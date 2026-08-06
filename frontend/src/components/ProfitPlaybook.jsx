import React, { useState, useEffect } from 'react';
import { fetchProfitPlaybook } from '../services/api';
import { TrendingUp, ShieldCheck, DollarSign, Target, ArrowUpRight, HelpCircle, CheckCircle2 } from 'lucide-react';

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
    return <div className="card text-center py-12 text-secondary font-semibold">लोड हो रहा है (Analyzing Market Data...)...</div>;
  }

  const sizing = data?.position_sizing || {};
  const rules = data?.golden_rules_audit || [];

  return (
    <div className="profit-playbook-wrapper flex flex-col gap-6">
      
      {/* Step-by-Step 3-Second Explainer Banner */}
      <div className="card p-4 border border-cyan-500/30 bg-gradient-to-r from-gray-900 via-gray-950 to-gray-900 rounded-xl">
        <div className="flex items-center justify-between gap-2 border-b border-gray-800 pb-3 mb-3">
          <div className="flex items-center gap-2">
            <HelpCircle className="text-cyan-400 w-5 h-5" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              इस साइट को 10 सेकंड में कैसे समझें (How to Understand)
            </h3>
          </div>
          <span className="text-xs bg-cyan-950 text-cyan-400 font-mono px-2.5 py-1 rounded border border-cyan-500/30">
            3 EASY STEPS
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="flex items-start gap-2.5 p-2.5 rounded bg-gray-900/60 border border-gray-800">
            <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center shrink-0">1</span>
            <div>
              <div className="font-bold text-white mb-0.5">1. आज का निर्णय देखें</div>
              <div className="text-secondary">AI बताता है कि मार्केट ऊपर जाएगा (BUY) या नीचे जाएगा (SELL)।</div>
            </div>
          </div>

          <div className="flex items-start gap-2.5 p-2.5 rounded bg-gray-900/60 border border-gray-800">
            <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center shrink-0">2</span>
            <div>
              <div className="font-bold text-white mb-0.5">2. अपनी पूंजी (Capital) दर्ज करें</div>
              <div className="text-secondary">अपनी राशि टाइप करें — सिस्टम ऑटोमैटिक लॉट और मुनाफा कैलकुलेट कर देगा।</div>
            </div>
          </div>

          <div className="flex items-start gap-2.5 p-2.5 rounded bg-gray-900/60 border border-gray-800">
            <span className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 font-bold flex items-center justify-center shrink-0">3</span>
            <div>
              <div className="font-bold text-white mb-0.5">3. 5 नियमों की जाँच करें</div>
              <div className="text-secondary">सभी 5 संस्थागत नियमों पर हरा निशान (PASSED) होने पर ही ट्रेड लें।</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Big Trade Recommendation Hero Card */}
      <div className="card p-6 border-t-4 border-emerald-400 bg-gradient-to-b from-gray-900 to-gray-950">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-1">
              आज की लाइव अनुशंसा (Today's Live Recommendation)
            </div>
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-extrabold text-white">{data?.symbol || symbol}</h2>
              <span className="text-2xl font-mono text-emerald-400 font-bold">
                ₹{data?.spot_price?.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Capital Input Pill */}
          <div className="flex items-center gap-3 bg-gray-900 p-2.5 rounded-xl border border-gray-800">
            <DollarSign className="text-emerald-400 w-5 h-5" />
            <div className="text-left">
              <div className="text-[10px] text-secondary uppercase font-semibold">आपकी जमा पूंजी (Your Capital):</div>
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

        {/* 4 Big Action Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Card 1: Action Signal */}
          <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 flex flex-col justify-between">
            <div className="text-xs text-emerald-300 font-semibold mb-2 flex items-center justify-between">
              <span>सिग्नल (Decision)</span>
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400 mb-1">
              {data?.trade_status === 'ACTIVE_STRONG_BUY' ? 'खारीदें (BUY CE)' : 'प्रतीक्षा करें (WAIT)'}
            </div>
            <div className="text-xs text-secondary">{data?.option_contract}</div>
          </div>

          {/* Card 2: Entry & Target Premium */}
          <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 flex flex-col justify-between">
            <div className="text-xs text-secondary font-semibold mb-2">खरीद रेट (Entry) ➔ लक्ष्य (Target)</div>
            <div className="text-lg font-mono font-bold text-white mb-1">
              ₹{data?.entry_premium} ➔ <span className="text-emerald-400 font-extrabold">₹{data?.target_premium}</span>
            </div>
            <div className="text-xs text-rose-400">स्टॉप लॉस (Max Risk): ₹{data?.stop_loss_premium}</div>
          </div>

          {/* Card 3: Position Size & Quantity */}
          <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 flex flex-col justify-between">
            <div className="text-xs text-secondary font-semibold mb-2">अनुशंसित लॉट (Lots to Buy)</div>
            <div className="text-xl font-mono font-bold text-amber-400 mb-1">
              {sizing.recommended_lots} Lots ({sizing.total_quantity} Qty)
            </div>
            <div className="text-xs text-secondary">लागत: ₹{sizing.investment_required?.toLocaleString()}</div>
          </div>

          {/* Card 4: Potential Profit */}
          <div className="p-4 rounded-xl bg-emerald-900/30 border border-emerald-500/50 flex flex-col justify-between">
            <div className="text-xs text-emerald-400 font-semibold mb-2">संभावित मुनाफा (Expected Profit)</div>
            <div className="text-2xl font-mono font-extrabold text-emerald-400 mb-1">
              +₹{sizing.potential_profit?.toLocaleString()}
            </div>
            <div className="text-xs text-emerald-300">रिस्क-रिवॉर्ड: 1:2.5 (High Profit)</div>
          </div>
        </div>

        {/* Win Confidence Progress Bar */}
        <div className="p-4 rounded-xl bg-gray-950 border border-gray-800">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-secondary font-semibold flex items-center gap-1.5">
              <ShieldCheck className="text-cyan-400 w-4 h-4" /> AI सफलता दर (Win Probability Confidence):
            </span>
            <span className="font-mono text-base font-bold text-cyan-400">{data?.win_probability}%</span>
          </div>
          <div className="w-full h-3 bg-gray-900 rounded-full overflow-hidden border border-gray-800">
            <div 
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-1000" 
              style={{ width: `${data?.win_probability}%` }}
            />
          </div>
        </div>
      </div>

      {/* 5 Rules Checklist Card */}
      <div className="card p-5">
        <h3 className="card-title text-base text-white mb-4 flex items-center gap-2">
          <CheckCircle2 className="text-emerald-400 w-5 h-5" />
          5 संस्थागत सुरक्षा नियम (5 Institutional Safety Rules)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {rules.map((r, idx) => (
            <div key={idx} className="p-3.5 rounded-lg bg-gray-950 border border-gray-800 flex items-start justify-between gap-3">
              <div>
                <div className="text-xs font-bold text-white mb-1">{r.rule}</div>
                <div className="text-[11px] text-secondary font-mono">{r.detail}</div>
              </div>
              <span className={`badge shrink-0 ${r.status === 'PASSED' ? 'badge-success' : 'badge-warning'}`}>
                {r.status === 'PASSED' ? 'सुरक्षित (PASSED)' : 'सावधान'}
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
