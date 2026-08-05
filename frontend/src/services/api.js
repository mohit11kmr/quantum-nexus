const BASE_URL = import.meta.env.VITE_API_URL || 'https://quantum-nexus-api.onrender.com';

const fetchWithTimeout = async (url, options = {}) => {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  } catch (error) {
    clearTimeout(id);
    console.warn(`Fetch to ${url} failed, using fallback data. Error:`, error);
    throw error;
  }
};

export const fetchPopularStocks = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/stocks/popular`); }
  catch { return ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD']; }
};

export const fetchStockAnalysis = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/analysis/${symbol}`); }
  catch { return { symbol, price: 150.00, change: 1.5, volume: 1000000, rsi: 55, vwap: 149.5 }; }
};

export const fetchLiveQuote = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/quote/${symbol}`); }
  catch { return { price: 150.00 + Math.random(), changePercent: 1.2, isMarketOpen: true }; }
};

export const fetchOptionsValuation = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/options/${symbol}`); }
  catch { 
    return {
      calls: [{ strike: 150, premium: 5.2, fairValue: 4.8, delta: 0.55, theta: -0.04, status: 'EXPENSIVE' }],
      puts: [{ strike: 145, premium: 3.1, fairValue: 3.5, delta: -0.4, theta: -0.03, status: 'CHEAP' }]
    };
  }
};

export const fetchOptionsStrategy = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/strategy/${symbol}`); }
  catch { return { setup: 'Bull Call Spread', entry: 150, target: 160, stop: 145, confidence: 85, quality: 'A' }; }
};

export const fetchPaperPortfolio = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/paper/portfolio`); }
  catch { return { balance: 100000, equity: 105000, positions: [] }; }
};

export const executePaperBuy = async (trade) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/paper/buy`, { method: 'POST', body: JSON.stringify(trade) }); }
  catch { return { success: true, tradeId: Date.now() }; }
};

export const closePaperPosition = async (id) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/paper/close/${id}`, { method: 'POST' }); }
  catch { return { success: true }; }
};

export const resetPaperAccount = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/paper/reset`, { method: 'POST' }); }
  catch { return { success: true }; }
};

export const fetchBrainStatus = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/brain/status`); }
  catch { return { accuracy: 82, epochs: 150, memory: '1.2GB', learningRate: 0.001 }; }
};

export const fetchBrainScenarios = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/brain/scenarios`); }
  catch { return [{ name: 'Tech Bull Run', probability: 0.6 }, { name: 'Market Correction', probability: 0.3 }]; }
};

export const optimizeBrain = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/brain/optimize`, { method: 'POST' }); }
  catch { return { success: true }; }
};

export const fetchVolumeScreener = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/screener/volume`); }
  catch { return [{ symbol: 'NVDA', surge: '+250%', price: 450, rsi: 72 }]; }
};

export const runBacktest = async (params) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/backtest`, { method: 'POST', body: JSON.stringify(params) }); }
  catch { return { winRate: 65, profitFactor: 1.8, maxDrawdown: 12, equityCurve: [{date: '2023', val: 10000}, {date: '2024', val: 12000}] }; }
};

export const fetchMonteCarloSimulation = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/montecarlo/${symbol}`); }
  catch { return { var95: -5.2, var99: -8.1, cvar: -9.5, median: 2.1, histogram: [{bin: -10, count: 5}, {bin: 0, count: 40}, {bin: 10, count: 10}] }; }
};

export const fetchStressTest = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/stress/${symbol}`); }
  catch { return [{ scenario: '2008 Crash', maxLoss: -35, recoveryDays: 120, severity: 'HIGH' }]; }
};

export const fetchSignalVerification = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/verify/${symbol}`); }
  catch { return { techScore: 85, greekScore: 70, marketScore: 90, confidence: 82, rating: 'EXCELLENT' }; }
};

export const fetchSignalGeneration = async () => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/signals`); }
  catch { return [{ symbol: 'AAPL', type: 'BUY', confidence: 90 }]; }
};

export const fetchIndicators = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/indicators/${symbol}`); }
  catch { return { rsi: 55, macd: 1.2, bollinger: 'Middle' }; }
};

export const fetchPatterns = async (symbol) => {
  try { return await fetchWithTimeout(`${BASE_URL}/api/patterns/${symbol}`); }
  catch { return [{ name: 'Bull Flag', reliability: 'High' }]; }
};
