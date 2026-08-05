import React from 'react';

export default function MarketSummary({ symbol }) {
  return (
    <div className="card">
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-title">{symbol} Price</div>
          <div className="metric-value text-green">$150.00</div>
          <div className="metric-sub text-green">+1.5%</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">24H Volume</div>
          <div className="metric-value">1.2M</div>
          <div className="metric-sub text-secondary">Avg: 900K</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">RSI (14)</div>
          <div className="metric-value text-gold">55.4</div>
          <div className="metric-sub text-secondary">Neutral</div>
        </div>
        <div className="metric-card">
          <div className="metric-title">VWAP</div>
          <div className="metric-value">$149.50</div>
          <div className="metric-sub text-green">Above VWAP</div>
        </div>
      </div>
    </div>
  );
}
