import React, { useState } from 'react';
import Navbar from './components/Navbar';
import MarketSummary from './components/MarketSummary';
import StockChart from './components/StockChart';
import VolumeProfile from './components/VolumeProfile';
import VolumeScreener from './components/VolumeScreener';
import OptionsValuation from './components/OptionsValuation';
import OptionsStrategy from './components/OptionsStrategy';
import AIInsights from './components/AIInsights';
import BrainDashboard from './components/BrainDashboard';
import PaperTrading from './components/PaperTrading';
import Backtesting from './components/Backtesting';
import MonteCarloPanel from './components/MonteCarloPanel';
import StressTester from './components/StressTester';
import SignalVerifier from './components/SignalVerifier';
import TradeJournal from './components/TradeJournal';
import ProfitPlaybook from './components/ProfitPlaybook';

const TABS = [
  { id: 'playbook', label: '💰 Wealth Creation Playbook' },
  { id: 'volume', label: '📊 Volume Analytics' },
  { id: 'screener', label: '🔍 Volume Surge Screener' },
  { id: 'options', label: '🏷️ Options Valuation' },
  { id: 'strategy', label: '🎯 Options Strategy Engine' },
  { id: 'ai', label: '🧠 AI Brain & Zero-Loss' },
  { id: 'paper', label: '📝 Paper Trading' },
  { id: 'backtest', label: '▶️ Strategy Backtester' },
  { id: 'montecarlo', label: '🎲 Monte Carlo VaR' },
  { id: 'stress', label: '⚡ Stress Tester' },
  { id: 'signal', label: '✅ Signal Verifier' }
];

function App() {
  const [activeTab, setActiveTab] = useState('playbook');
  const [symbol, setSymbol] = useState('NIFTY');

  return (
    <div className="app-container">
      <Navbar symbol={symbol} setSymbol={setSymbol} />
      
      <main className="main-content">
        <MarketSummary symbol={symbol} />
        
        <div className="tabs-header">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="tab-content">
          {activeTab === 'playbook' && <ProfitPlaybook symbol={symbol} />}
          {activeTab === 'volume' && (
            <div className="grid-2col">
              <StockChart symbol={symbol} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <VolumeProfile symbol={symbol} />
                <AIInsights symbol={symbol} />
              </div>
            </div>
          )}
          {activeTab === 'screener' && <VolumeScreener />}
          {activeTab === 'options' && <OptionsValuation symbol={symbol} />}
          {activeTab === 'strategy' && <OptionsStrategy symbol={symbol} />}
          {activeTab === 'ai' && <BrainDashboard />}
          {activeTab === 'paper' && (
            <div className="grid-2col">
              <PaperTrading />
              <TradeJournal />
            </div>
          )}
          {activeTab === 'backtest' && <Backtesting symbol={symbol} />}
          {activeTab === 'montecarlo' && <MonteCarloPanel symbol={symbol} />}
          {activeTab === 'stress' && <StressTester symbol={symbol} />}
          {activeTab === 'signal' && <SignalVerifier symbol={symbol} />}
        </div>
      </main>
    </div>
  );
}

export default App;
