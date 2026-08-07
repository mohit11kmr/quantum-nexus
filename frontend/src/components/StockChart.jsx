import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchStockAnalysis } from '../services/api';
import useLiveTicker from '../hooks/useLiveTicker';

const UP = '#34d399';
const DOWN = '#fb7185';

function toUtcSec(value) {
  const t = typeof value === 'string' ? value.replace(' ', 'T') : value;
  const ms = new Date(t).getTime();
  return Number.isFinite(ms) ? Math.floor(ms / 1000) : null;
}

export default function StockChart({ symbol = 'NIFTY' }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volSeriesRef = useRef(null);
  const liveSeriesRef = useRef(null);
  const [livePrice, setLivePrice] = useState(null);
  const [lastCandleTime, setLastCandleTime] = useState(null);

  const { tick, connected } = useLiveTicker(symbol);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const chart = createChart(el, {
      autoSize: true,
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: 'rgba(148,163,184,0.9)',
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.08)' },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.08)',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        vertLine: { color: 'rgba(148,163,184,0.4)', labelBackgroundColor: '#1e293b' },
        horzLine: { color: 'rgba(148,163,184,0.4)', labelBackgroundColor: '#1e293b' },
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: UP,
      downColor: DOWN,
      borderUpColor: UP,
      borderDownColor: DOWN,
      wickUpColor: UP,
      wickDownColor: DOWN,
    });
    const volSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    chart.priceScale('').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    const liveSeries = chart.addLineSeries({
      color: '#38bdf8',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      priceLineColor: '#38bdf8',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volSeriesRef.current = volSeries;
    liveSeriesRef.current = liveSeries;

    let cancelled = false;
    fetchStockAnalysis(symbol).then((data) => {
      if (cancelled) return;
      const rows = Array.isArray(data?.candles) ? data.candles : [];
      const candles = [];
      const volumes = [];
      rows.forEach((r) => {
        const time = toUtcSec(r.Date);
        if (time == null) return;
        const open = Number(r.Open), high = Number(r.High), low = Number(r.Low), close = Number(r.Close);
        if (![open, high, low, close].every(Number.isFinite)) return;
        candles.push({ time, open, high, low, close });
        const up = close >= open;
        volumes.push({ time, value: Number(r.Volume) || 0, color: up ? 'rgba(52,211,153,0.35)' : 'rgba(251,113,133,0.35)' });
      });
      if (candles.length) {
        candleSeries.setData(candles);
        volSeries.setData(volumes);
        setLastCandleTime(candles[candles.length - 1].time);
        chart.timeScale().fitContent();
      }
    });

    return () => {
      cancelled = true;
      chart.remove();
      chartRef.current = null;
    };
  }, [symbol]);

  // Feed live ticks into the overlay line + header.
  useEffect(() => {
    if (!tick || typeof tick.price !== 'number') return;
    setLivePrice(tick.price);
    const liveSeries = liveSeriesRef.current;
    if (!liveSeries) return;
    const time = tick.timestamp ? Math.floor(tick.timestamp) : Math.floor(Date.now() / 1000);
    liveSeries.update({ time, value: tick.price });
  }, [tick]);

  const currencySymbol = (symbol.includes('.NS') || symbol.includes('NIFTY') || symbol.includes('BANK')) ? '₹' : '$';
  const price = livePrice ?? (tick?.price ?? 0);

  return (
    <div className="card" style={{ height: '500px' }}>
      <div className="card-header">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span>{symbol} Real-Time Chart</span>
          {price > 0 && <span className="font-mono text-emerald-400">{currencySymbol}{price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>}
        </div>
        <span className={`badge ${connected ? 'badge-success' : 'badge-warning'}`}>
          {connected ? '● LIVE' : 'RECONNECTING'}
        </span>
      </div>
      <div ref={containerRef} style={{ width: '100%', height: 'calc(100% - 56px)' }} />
    </div>
  );
}
