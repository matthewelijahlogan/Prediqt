// script.js
console.log("🔧 script.js loaded");

const API_BASE =
  window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000'
    : 'https://prediqt.onrender.com';

async function predict() {
  const tickerInput = document.getElementById('tickerInput');
  const ticker = tickerInput.value.trim().toUpperCase();

  console.log("🏁 predict() started for ticker:", ticker);

  if (!ticker) {
    alert('Please enter a ticker symbol.');
    return;
  }

  // Show loading messages
  ['Hour', 'Day', 'Week', 'Month'].forEach(horizon => {
    document.getElementById(`prediction${horizon}`).textContent = 'Loading...';
  });

  const horizons = ['hour', 'day', 'week', 'month'];

  for (const horizon of horizons) {
    try {
      const response = await fetch(`${API_BASE}/predict/${ticker}?horizon=${horizon}`);
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      const outputId = `prediction${horizon.charAt(0).toUpperCase() + horizon.slice(1)}`;
      document.getElementById(outputId).textContent =
        `$${data.predicted_next_close.toFixed(2)} (MSE: ${data.model_mse.toFixed(4)})`;
    } catch (err) {
      const outputId = `prediction${horizon.charAt(0).toUpperCase() + horizon.slice(1)}`;
      document.getElementById(outputId).textContent = `Error: ${err.message}`;
    }
  }
}

// Attach event listener once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log("✅ DOM fully loaded");

  const predictBtn = document.getElementById('predictBtn');
  console.log("🔍 Button element:", predictBtn);

  if (predictBtn) {
    predictBtn.addEventListener('click', () => {
      console.log("🔘 Predict button clicked");
      predict();
    });
  } else {
    console.warn("⚠️ predictBtn not found in DOM");
  }
});
