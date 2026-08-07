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
import { useLanguage } from './i18n.jsx';
import { Crosshair, CandlestickChart, Filter, Coins, Brain, FlaskConical, ReceiptText, ShieldCheck, Gauge } from 'lucide-react';

const NAV_SECTIONS = [
  {
    labelKey: 'section.decisions',
    tabs: [
      { id: 'playbook', labelKey: 'tab.today', icon: Crosshair },
    ],
  },
  {
    labelKey: 'section.market',
    tabs: [
      { id: 'volume', labelKey: 'tab.chart', icon: CandlestickChart },
      { id: 'screener', labelKey: 'tab.screener', icon: Filter },
      { id: 'options', labelKey: 'tab.options', icon: Coins },
      { id: 'strategy', labelKey: 'tab.strategy', icon: Brain },
    ],
  },
  {
    labelKey: 'section.aiRisk',
    tabs: [
      { id: 'ai', labelKey: 'tab.ai', icon: FlaskConical },
      { id: 'backtest', labelKey: 'tab.backtest', icon: ReceiptText },
      { id: 'signal', labelKey: 'tab.signal', icon: ShieldCheck },
    ],
  },
  {
    labelKey: 'section.trading',
    tabs: [
      { id: 'paper', labelKey: 'tab.paper', icon: Gauge },
    ],
  },
];

function App() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState('playbook');
  const [symbol, setSymbol] = useState('NIFTY');

  const allTabs = NAV_SECTIONS.flatMap((s) => s.tabs);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'playbook':
        return <ProfitPlaybook symbol={symbol} />;
      case 'volume':
        return (
          <div className="grid-2col">
            <StockChart symbol={symbol} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <VolumeProfile symbol={symbol} />
              <AIInsights symbol={symbol} />
            </div>
          </div>
        );
      case 'screener':
        return <VolumeScreener />;
      case 'options':
        return <OptionsValuation symbol={symbol} />;
      case 'strategy':
        return <OptionsStrategy symbol={symbol} />;
      case 'ai':
        return <BrainDashboard />;
      case 'paper':
        return (
          <div className="grid-2col">
            <PaperTrading />
            <TradeJournal />
          </div>
        );
      case 'backtest':
        return <Backtesting symbol={symbol} />;
      case 'signal':
        return <SignalVerifier symbol={symbol} />;
      default:
        return <ProfitPlaybook symbol={symbol} />;
    }
  };

  return (
    <div className="app-container">
      <Navbar symbol={symbol} setSymbol={setSymbol} />

      <main className="main-content">
        <MarketSummary symbol={symbol} />

        <div className="tabs-nav" role="navigation" aria-label="Platform sections">
          {NAV_SECTIONS.map((section) => (
            <div key={section.labelKey} className="tabs-nav-group">
              <span className="tabs-nav-label">{t(section.labelKey)}</span>
              {section.tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(tab.id)}
                    aria-pressed={activeTab === tab.id}
                  >
                    <Icon size={15} />
                    {t(tab.labelKey)}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        <div className="tab-content animate-fade-up" key={activeTab}>
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
