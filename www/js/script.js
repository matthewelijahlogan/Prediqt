// script.js
console.log("🔧 script.js loaded");

const API_BASE =
  window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000'
    : 'https://prediqt.onrender.com';

// Predict function with spinner inline in each prediction span
async function predict() {
  const tickerInput = document.getElementById('tickerInput');
  const ticker = tickerInput.value.trim().toUpperCase();

  if (!ticker) {
    alert('Please enter a ticker symbol.');
    return;
  }

  const horizons = ['hour', 'day', 'week', 'month'];

  // Show spinner in each prediction spot while loading
  horizons.forEach(horizon => {
    const outputId = `prediction${horizon.charAt(0).toUpperCase() + horizon.slice(1)}`;
    const elem = document.getElementById(outputId);
    elem.innerHTML = `<span class="spinner" aria-label="loading"></span>`;
  });

  // Fetch predictions sequentially (can be parallelized if needed)
  for (const horizon of horizons) {
    const outputId = `prediction${horizon.charAt(0).toUpperCase() + horizon.slice(1)}`;
    const elem = document.getElementById(outputId);

    try {
      const response = await fetch(`${API_BASE}/predict/${ticker}?horizon=${horizon}`);

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();

      elem.textContent = `$${data.predicted_next_close.toFixed(2)} (MSE: ${data.model_mse.toFixed(4)})`;
    } catch (err) {
      elem.textContent = `Error: ${err.message}`;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  console.log("✅ DOM fully loaded");

  const predictBtn = document.getElementById('predictBtn');
  if (predictBtn) {
    predictBtn.addEventListener('click', () => {
      console.log("🔘 Predict button clicked");
      predict();
    });
  } else {
    console.warn("⚠️ predictBtn not found in DOM");
  }
});

window.addEventListener("load", () => {
  const splash = document.getElementById("splashScreen");
  if (!splash) return;

  // Step 1: Fade in
  splash.style.opacity = 1;

  // Step 2: Wait, then fade out
  setTimeout(() => {
    splash.style.transition = "opacity 1.5s ease";
    splash.style.opacity = 0;

    // Step 3: Remove from DOM after fade-out completes
    setTimeout(() => splash.remove(), 1500);
  }, 2000); // 2 second delay before fading out
});

