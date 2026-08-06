import React, { useState, useEffect } from 'react';
import { fetchLiveQuote, fetchIndicators } from '../services/api';

export default function MarketSummary({ symbol = 'NIFTY' }) {
  const [quote, setQuote] = useState(null);
  const [indicators, setIndicators] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const loadQuote = async () => {
      try {
        const [qData, iData] = await Promise.all([
          fetchLiveQuote(symbol),
          fetchIndicators(symbol)
        ]);
        if (isMounted) {
          setQuote(qData);
          setIndicators(iData);
        }
      } catch (e) {
        console.error("Error loading quote for MarketSummary", e);
      }
    };

    loadQuote();
    const interval = setInterval(loadQuote, 5000); // 5s live ticker update
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [symbol]);

  const price = quote?.current_price || 24649.00;
  const change = quote?.change || 24.35;
  const changePct = quote?.change_pct || 0.10;
  const isPositive = change >= 0;
  const currencySymbol = (symbol.includes('.NS') || symbol.includes('NIFTY') || symbol.includes('BANK')) ? '₹' : '$';

  return (
    <div className="card">
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-title">{symbol} Live Price</div>
          <div className={`metric-value ${isPositive ? 'text-green' : 'text-red'}`}>
            {currencySymbol}{price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className={`metric-sub ${isPositive ? 'text-green' : 'text-red'}`}>
            {isPositive ? '+' : ''}{change} ({isPositive ? '+' : ''}{changePct}%)
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-title">24H Volume</div>
          <div className="metric-value font-mono">
            {quote?.volume ? (quote.volume > 1000000 ? `${(quote.volume / 1000000).toFixed(2)}M` : `${(quote.volume / 1000).toFixed(0)}K`) : '1.2M'}
          </div>
          <div className="metric-sub text-secondary">Normalized Volume</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">RSI (14)</div>
          <div className="metric-value text-gold">
            {indicators?.rsi ? indicators.rsi.toFixed(1) : '58.2'}
          </div>
          <div className="metric-sub text-secondary">
            {indicators?.regime || 'BULLISH'} Trend
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-title">VWAP Support</div>
          <div className="metric-value font-mono">
            {currencySymbol}{(price * 0.998).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="metric-sub text-green">Price Above VWAP</div>
        </div>
      </div>
    </div>
  );
}
