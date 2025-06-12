const API_BASE_URL = window.API_BASE_URL || 'http://127.0.0.1:8000';

export async function fetchTopMovers() {
  const response = await fetch(`${API_BASE_URL}/top-movers`);
  const data = await response.json();
  return data.top_movers || [];
}
export async function fetchTopLosers() {
  const response = await fetch(`${API_BASE_URL}/top-losers`);
  const data = await response.json();
  return data.top_losers || [];
}
export async function fetchPrediction(ticker, horizon) {
  const response = await fetch(`${API_BASE_URL}/predict/${ticker}?horizon=${horizon}`);
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  const data = await response.json();
  return {
    predicted_next_close: data.predicted_next_close,
    model_mse: data.model_mse
  };
}
export async function fetchTickerData(ticker) {
  const response = await fetch(`${API_BASE_URL}/ticker/${ticker}`);
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  const data = await response.json();
  return {
    ticker: data.ticker,
    current_price: data.current_price,
    open_price: data.open_price,
    high_price: data.high_price,
    low_price: data.low_price,
    volume: data.volume
  };
}
