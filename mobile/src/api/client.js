const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  let data = null;

  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    const message = data?.detail || data?.error || `${response.status} ${response.statusText}`;
    throw new Error(message);
  }

  return data;
}

export function fetchPrediction(ticker, horizon) {
  return request(`/predict/${encodeURIComponent(ticker)}?horizon=${encodeURIComponent(horizon)}`);
}

export function fetchQuote(ticker) {
  return request(`/api/quote?ticker=${encodeURIComponent(ticker)}`);
}

export function fetchTickerTape() {
  return request('/api/ticker-tape');
}

export function fetchNews() {
  return request('/api/news');
}

export { API_BASE_URL };
