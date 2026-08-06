import React, { useState, useEffect } from 'react';
import { fetchPaperPortfolio, executePaperBuy, closePaperPosition, resetPaperAccount, fetchLiveQuote } from '../services/api';
import { ShoppingBag, XCircle, RefreshCw, TrendingUp, DollarSign, Activity } from 'lucide-react';

export default function PaperTrading() {
  const [portfolio, setPortfolio] = useState({ equity: 100000, balance: 100000, positions: [] });
  const [closedTrades, setClosedTrades] = useState([
    { id: 1, date: '2026-08-06 10:15', symbol: 'NIFTY 24650 CE', side: 'BUY', entry: 145.20, exit: 182.50, qty: 50, pnl: 1865.00, notes: 'Golden Rule #3 VWAP Crossover' }
  ]);
  
  // Trade Form State
  const [symbol, setSymbol] = useState('NIFTY 24650 CE');
  const [price, setPrice] = useState(155.20);
  const [lots, setLots] = useState(2); // Default 2 lots (50 Qty for NIFTY)
  const [lotSize, setLotSize] = useState(25);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const totalQty = lots * lotSize;
  const totalInvestment = price * totalQty;

  useEffect(() => {
    loadPortfolio();
    const interval = setInterval(updateLivePositionsPnL, 3000); // 3s live P&L tick
    return () => clearInterval(interval);
  }, []);

  const loadPortfolio = async () => {
    try {
      const data = await fetchPaperPortfolio();
      if (data && data.balance !== undefined) {
        setPortfolio(data);
      }
    } catch (e) {
      console.error("Error loading paper portfolio", e);
    }
  };

  const updateLivePositionsPnL = async () => {
    setPortfolio(prev => {
      if (!prev || !prev.positions || prev.positions.length === 0) return prev;
      let totalOpenPnL = 0;
      const updatedPos = prev.positions.map(pos => {
        // Random slight tick simulating live option premium tick
        const tick = (Math.random() * 2 - 0.95);
        const ltp = Math.max(1, Number((pos.current_price + tick).toFixed(2)));
        const pnl = Number(((ltp - pos.entry_price) * pos.quantity).toFixed(2));
        
        // Trailing Stop Loss Logic
        const pnlPercent = (ltp - pos.entry_price) / pos.entry_price * 100;
        const maxPnlPercent = Math.max(pos.max_pnl_percent || 0, pnlPercent);
        
        let tslTriggered = false;
        // If profit hit 15% or more, lock the stop loss at entry (0% profit)
        if (maxPnlPercent >= 15 && pnlPercent <= 0) {
           tslTriggered = true;
        }

        totalOpenPnL += pnl;
        return { ...pos, current_price: ltp, pnl: pnl, max_pnl_percent: maxPnlPercent, tsl_triggered: tslTriggered };
      });

      // Auto-close TSL triggered positions
      const triggeredPositions = updatedPos.filter(p => p.tsl_triggered);
      triggeredPositions.forEach(p => {
         // In a real app, this would call the API. For UI demo, we'll handle it below.
         handleClosePosition({...p, notes: 'TSL Hit - Protected Capital'});
      });

      return {
        ...prev,
        positions: updatedPos.filter(p => !p.tsl_triggered), // Remove auto-closed
        equity: Number((prev.balance + totalOpenPnL).toFixed(2))
      };
    });
  };

  const handleExecuteBuy = async (e) => {
    e.preventDefault();
    if (totalInvestment > portfolio.balance) {
      setMsg('❌ अपर्याप्त बैलेंस (Insufficient Balance)!');
      return;
    }

    setLoading(true);
    setMsg('');

    try {
      await executePaperBuy(symbol, price, totalQty);
      const newPos = {
        id: Date.now(),
        symbol: symbol,
        entry_price: price,
        current_price: price,
        quantity: totalQty,
        lots: lots,
        investment: totalInvestment,
        pnl: 0,
        max_pnl_percent: 0,
        tsl_triggered: false,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setPortfolio(prev => ({
        ...prev,
        balance: prev.balance - totalInvestment,
        positions: [...(prev.positions || []), newPos]
      }));

      setMsg('✅ ट्रेड सफलतापूर्वक निष्पादित (Buy Order Executed)!');
    } catch (err) {
      setMsg('❌ ट्रेड एरर: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClosePosition = async (pos) => {
    try {
      await closePaperPosition(pos.id, pos.current_price);
      const closedRecord = {
        id: pos.id,
        date: new Date().toLocaleString(),
        symbol: pos.symbol,
        side: 'BUY',
        entry: pos.entry_price,
        exit: pos.current_price,
        qty: pos.quantity,
        pnl: pos.pnl,
        notes: pos.notes || 'Target Met / Closed via Terminal'
      };

      setClosedTrades(prev => [closedRecord, ...prev]);
      setPortfolio(prev => {
        const remaining = (prev.positions || []).filter(p => p.id !== pos.id);
        const returnedCash = pos.investment + pos.pnl;
        const newBal = prev.balance + returnedCash;
        return {
          ...prev,
          balance: Number(newBal.toFixed(2)),
          positions: remaining
        };
      });
      setMsg(`🎉 ${pos.symbol} पोजीशन बंद की गई! P&L: ₹${pos.pnl}`);
    } catch (err) {
      console.error("Close position error", err);
    }
  };

  const handleResetAccount = async () => {
    try {
      await resetPaperAccount();
      setPortfolio({ equity: 100000, balance: 100000, positions: [] });
      setClosedTrades([]);
      setMsg('🔄 खाता ₹1,00,000 पर रीसेट कर दिया गया!');
    } catch (e) {
      console.error("Reset error", e);
    }
  };

  const totalOpenPnL = (portfolio.positions || []).reduce((acc, p) => acc + (p.pnl || 0), 0);

  return (
    <div className="paper-trading-container flex flex-col gap-6">
      
      {/* Portfolio Overview Header Cards */}
      <div className="card p-6 bg-gradient-to-r from-gray-900 via-gray-950 to-gray-900 border-l-4 border-cyan-500">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Activity className="text-cyan-400 w-5 h-5" /> 
              वर्चुअल ट्रेडिंग लाइव टर्मिनल (Live Practice Trading Terminal)
            </h2>
            <p className="text-secondary text-xs">
              वास्तविक बाज़ार दरों पर बिना जोखिम के ऑप्शन खरीद/बिक्री करके प्रैक्टिस करें।
            </p>
          </div>
          <button 
            onClick={handleResetAccount}
            className="btn flex items-center gap-1.5 text-xs text-rose-400 border-rose-500/30 hover:bg-rose-950/40"
          >
            <RefreshCw className="w-3.5 h-3.5" /> खाता रीसेट (Reset ₹1L)
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800">
            <div className="text-xs text-secondary font-semibold mb-1">कुल संपत्ति (Total Equity)</div>
            <div className="text-2xl font-mono font-bold text-white">
              ₹{portfolio.equity?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800">
            <div className="text-xs text-secondary font-semibold mb-1">उपलब्ध कैश (Available Balance)</div>
            <div className="text-2xl font-mono font-bold text-cyan-400">
              ₹{portfolio.balance?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800">
            <div className="text-xs text-secondary font-semibold mb-1">ओपन P&L (Floating P&L)</div>
            <div className={`text-2xl font-mono font-bold ${totalOpenPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {totalOpenPnL >= 0 ? '+' : ''}₹{totalOpenPnL.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>
      </div>

      {/* Trade Execution Terminal Form */}
      <div className="card p-5 border border-emerald-500/30">
        <h3 className="card-title text-base text-emerald-400 mb-4 flex items-center gap-2">
          <ShoppingBag className="w-5 h-5" /> 
          नया ऑर्डर डालें (Place Real-Time Paper Order)
        </h3>

        <form onSubmit={handleExecuteBuy} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
          <div>
            <label className="text-xs text-secondary block mb-1">कंट्रैक्ट / स्ट्राइक (Contract):</label>
            <input 
              type="text" 
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value)}
              className="bg-gray-950 text-white font-mono text-xs px-3 py-2 rounded border border-gray-800 w-full outline-none focus:border-emerald-400"
              placeholder="e.g. NIFTY 24650 CE"
              required
            />
          </div>

          <div>
            <label className="text-xs text-secondary block mb-1">प्रीमियम दर (Price ₹):</label>
            <input 
              type="number" 
              step="0.05"
              value={price} 
              onChange={(e) => setPrice(Number(e.target.value))}
              className="bg-gray-950 text-emerald-400 font-mono font-bold text-xs px-3 py-2 rounded border border-gray-800 w-full outline-none focus:border-emerald-400"
              required
            />
          </div>

          <div>
            <label className="text-xs text-secondary block mb-1">लॉट की संख्या (Lots):</label>
            <input 
              type="number" 
              min="1"
              max="50"
              value={lots} 
              onChange={(e) => setLots(Number(e.target.value))}
              className="bg-gray-950 text-amber-400 font-mono font-bold text-xs px-3 py-2 rounded border border-gray-800 w-full outline-none focus:border-emerald-400"
              required
            />
          </div>

          <div>
            <label className="text-xs text-secondary block mb-1">कुल लागत (Investment):</label>
            <div className="text-sm font-mono font-bold text-cyan-400 py-2">
              ₹{totalInvestment.toLocaleString()} ({totalQty} Qty)
            </div>
          </div>

          <div>
            <button 
              type="submit" 
              disabled={loading}
              className="btn btn-primary w-full py-2 flex items-center justify-center gap-2 font-bold text-xs"
            >
              <TrendingUp className="w-4 h-4" /> 
              {loading ? 'ऑर्डर जा रहा है...' : 'अभी खरीदें (BUY ORDER)'}
            </button>
          </div>
        </form>

        {msg && <div className="mt-3 text-xs font-semibold text-center text-cyan-300">{msg}</div>}
      </div>

      {/* Active Open Positions Table */}
      <div className="card p-5">
        <h3 className="card-title text-base text-white mb-4 flex items-center justify-between">
          <span>📈 सक्रिय पोजीशन (Active Open Positions)</span>
          <span className="text-xs font-mono text-secondary">
            {(portfolio.positions || []).length} Open
          </span>
        </h3>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>समय (Time)</th>
                <th>कंट्रैक्ट (Contract)</th>
                <th>मात्रा (Qty / Lots)</th>
                <th>बाय रेट (Entry)</th>
                <th>लाइव रेट (LTP)</th>
                <th>लाइव मुनाफा/घाटा (P&L ₹)</th>
                <th>एक्शन (Action)</th>
              </tr>
            </thead>
            <tbody>
              {(!portfolio.positions || portfolio.positions.length === 0) ? (
                <tr>
                  <td colSpan="7" className="text-center py-6 text-secondary italic">
                    कोई ओपन पोजीशन नहीं है। ऊपर दिए गए फ़ॉर्म से "अभी खरीदें" बटन दबाकर लाइव ट्रेड प्रैक्टिस करें!
                  </td>
                </tr>
              ) : (
                portfolio.positions.map((pos) => {
                  const pnl = pos.pnl || 0;
                  const isProfit = pnl >= 0;
                  return (
                    <tr key={pos.id}>
                      <td className="font-mono text-xs text-secondary">{pos.time || '10:30'}</td>
                      <td className="font-bold text-white">{pos.symbol}</td>
                      <td className="font-mono text-xs">{pos.quantity} ({pos.lots || 1} Lots)</td>
                      <td className="font-mono">₹{pos.entry_price}</td>
                      <td className="font-mono font-bold text-cyan-400">₹{pos.current_price}</td>
                      <td className={`font-mono font-bold ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isProfit ? '+' : ''}₹{pnl.toLocaleString()}
                      </td>
                      <td>
                        <button 
                          onClick={() => handleClosePosition(pos)}
                          className="btn text-xs px-2.5 py-1 text-rose-400 border-rose-500/40 hover:bg-rose-950/60"
                        >
                          पोजीशन बंद करें (Close)
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Closed Trade History Log */}
      <div className="card p-5">
        <h3 className="card-title text-base text-white mb-4">
          📜 पूरा किया गया ट्रेड इतिहास (Trade Journal & History)
        </h3>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>तारीख</th>
                <th>कंट्रैक्ट</th>
                <th>साइड</th>
                <th>एंट्री</th>
                <th>एग्जिट</th>
                <th>नेट P&L</th>
                <th>नोट्स</th>
              </tr>
            </thead>
            <tbody>
              {closedTrades.map((t) => (
                <tr key={t.id}>
                  <td className="text-xs font-mono text-secondary">{t.date}</td>
                  <td className="font-bold text-white">{t.symbol}</td>
                  <td><span className="badge badge-success">{t.side}</span></td>
                  <td className="font-mono">₹{t.entry}</td>
                  <td className="font-mono">₹{t.exit}</td>
                  <td className={`font-mono font-bold ${t.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {t.pnl >= 0 ? '+' : ''}₹{t.pnl}
                  </td>
                  <td className="text-xs text-secondary">{t.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
