document.addEventListener("DOMContentLoaded", async () => {
  // Elements references
  const tickerEl = document.getElementById("newsTicker");
  const inputEl = document.getElementById("tickerInput");
  const predictBtn = document.getElementById("predictBtn");
  const panelStatus = document.querySelector(".panel-status");

  const quotePriceEl = document.getElementById("quotePrice");
  const quoteChangeEl = document.getElementById("quoteChange");
  const quotePercentEl = document.getElementById("quotePercent");
  const quoteVolumeEl = document.getElementById("quoteVolume");
  const quoteMarketCapEl = document.getElementById("quoteMarketCap");
  const quoteSectorEl = document.getElementById("quoteSector");

  // State variables
  let tickerPaused = false;
  let inputFocused = false;
  let lastHighlighted = null;
  let pauseTimer = null;
  let inputPauseTimer = null;
  let predictionInProgress = false;

  tickerEl.innerHTML = "Loading...";

  // Flash color helper
  function flashValueChange(el, newVal, oldVal) {
    const cls = newVal > oldVal ? 'flash-up' : 'flash-down';
    el.classList.remove('flash-up', 'flash-down');
    // Trigger reflow to restart animation
    void el.offsetWidth;
    el.classList.add(cls);
  }

  // Load ticker tape symbols and prices into tickerEl
  async function loadTickerTape() {
    try {
      const res = await fetch("/api/ticker-tape");
      const data = await res.json();
      tickerEl.innerHTML = ""; // Clear loading

      data.tickers.forEach(t => {
        const span = document.createElement("span");
        span.classList.add("ticker-symbol");
        span.textContent = `${t.symbol} $${t.price}`;
        // Selecting a ticker only populates the input. Predictions are made
        // exclusively by clicking the Predict button.
        span.addEventListener("click", () => {
          inputEl.value = t.symbol;
        });
        tickerEl.appendChild(span);
      });
    } catch (err) {
      tickerEl.innerHTML = "Error loading ticker data.";
      console.error(err);
    }
  }

  // Pause/resume ticker animation helpers
  function pauseTicker() {
    tickerPaused = true;
  }

  function resumeTicker() {
    if (!inputFocused) {
      tickerPaused = false;
    }
  }

  // JS-powered smooth ticker scroll
  function startTickerScroll() {
    let offset = window.innerWidth;

    function scrollStep() {
      if (!tickerPaused && !inputFocused) {
        offset -= 0.6; // Lower is slower (0.1 = very slow)
        if (offset < -tickerEl.scrollWidth) {
          offset = window.innerWidth;
        }
        tickerEl.style.transform = `translateX(${offset}px)`;
      }
      requestAnimationFrame(scrollStep);
    }

    scrollStep();
  }

  // Check which ticker symbol is near center and highlight it
  function checkHighlight() {
    if (tickerPaused || inputFocused) return;

    const highlightX = window.innerWidth / 2;
    const symbols = document.querySelectorAll(".ticker-symbol");
    symbols.forEach(sym => {
      const rect = sym.getBoundingClientRect();
      if (
        rect.left < highlightX + 20 &&
        rect.left > highlightX - 20 &&
        lastHighlighted !== sym
      ) {
        // Remove previous highlights
        symbols.forEach(s => s.classList.remove("highlighted"));
        // Highlight current symbol
        sym.classList.add("highlighted");
        lastHighlighted = sym;

        // Pause ticker for 15 seconds then resume
        pauseTicker();
        clearTimeout(pauseTimer);
        pauseTimer = setTimeout(() => {
          resumeTicker();
        }, 15000);
      }
    });
  }

  // Fetch prediction for a ticker and horizon, update target element with results
  async function fetchPrediction(ticker, horizon, targetId) {
    const targetEl = document.getElementById(targetId);
    targetEl.innerHTML = '<span class="spinner"></span>'; // show spinner

    try {
      const res = await fetch(`/predict/${ticker}?horizon=${horizon}`);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `Prediction request failed (${res.status})`);
      }

      const predictedClose = Number(data.predicted_next_close);
      const result = data.predicted_next_close != null && Number.isFinite(predictedClose)
        ? predictedClose.toFixed(2)
        : "N/A";

      // Animate value change with color flash if numeric
      if (result !== "N/A" && result !== "Error") {
        const oldVal = parseFloat(targetEl.textContent) || 0;
        targetEl.textContent = result;
        flashValueChange(targetEl, parseFloat(result), oldVal);
      } else {
        targetEl.textContent = result;
      }
    } catch (err) {
      console.error(`Prediction failed for ${ticker} (${horizon}):`, err);
      targetEl.textContent = "N/A";
    }
  }

  // Fetch quote data for ticker and update quote elements
  async function fetchQuote(ticker) {
    try {
      const res = await fetch(`/api/quote?ticker=${ticker}`);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.error || `Quote request failed (${res.status})`);
      }

      if (data.price != null && Number.isFinite(Number(data.price))) {
        const price = Number(data.price);
        const oldVal = parseFloat(quotePriceEl.textContent.replace(/[^\d.-]/g, '')) || 0;
        quotePriceEl.textContent = price.toFixed(2);
        flashValueChange(quotePriceEl, price, oldVal);
      }

      if (data.change != null && Number.isFinite(Number(data.change))) {
        const change = Number(data.change);
        const oldVal = parseFloat(quoteChangeEl.textContent.replace(/[^\d.-]/g, '')) || 0;
        quoteChangeEl.textContent = change.toFixed(2);
        flashValueChange(quoteChangeEl, change, oldVal);
      }

      if (data.percent_change != null && Number.isFinite(Number(data.percent_change))) {
        const percentChange = Number(data.percent_change);
        const oldVal = parseFloat(quotePercentEl.textContent.replace(/[^\d.-]/g, '')) || 0;
        quotePercentEl.textContent = percentChange.toFixed(2) + "%";
        flashValueChange(quotePercentEl, percentChange, oldVal);
      }

      quoteVolumeEl.textContent = data.volume?.toLocaleString() ?? "-";
      quoteMarketCapEl.textContent = data.market_cap?.toLocaleString() ?? "-";
      quoteSectorEl.textContent = data.sector ?? "-";
    } catch (err) {
      quotePriceEl.textContent = "Error";
      quoteChangeEl.textContent = "Error";
      quotePercentEl.textContent = "Error";
      quoteVolumeEl.textContent = "Error";
      quoteMarketCapEl.textContent = "Error";
      quoteSectorEl.textContent = "Error";
    }
  }

  // Helper to fetch predictions and quotes for a ticker
  async function triggerPredictionAndQuote(ticker) {
    await Promise.all([
      fetchPrediction(ticker, "hour", "predictionHour"),
      fetchPrediction(ticker, "day", "predictionDay"),
      fetchPrediction(ticker, "week", "predictionWeek"),
      fetchPrediction(ticker, "month", "predictionMonth"),
      fetchQuote(ticker)
    ]);
  }

  // Button click event to predict ticker
  predictBtn.addEventListener("click", async () => {
    if (predictionInProgress) return;

    const ticker = inputEl.value.trim().toUpperCase();
    if (!ticker) return;

    predictionInProgress = true;
    predictBtn.disabled = true;
    const originalButtonMarkup = predictBtn.innerHTML;
    predictBtn.textContent = "Predicting...";
    if (panelStatus) {
      panelStatus.innerHTML = "<i></i> Analyzing signal";
    }

    try {
      await triggerPredictionAndQuote(ticker);
    } finally {
      predictionInProgress = false;
      predictBtn.disabled = false;
      predictBtn.innerHTML = originalButtonMarkup;
      if (panelStatus) {
        panelStatus.innerHTML = "<i></i> Signal ready";
      }
    }
  });

  // Input focus handling: pause ticker for 2 minutes
  inputEl.addEventListener("focus", () => {
    inputFocused = true;
    pauseTicker();
    clearTimeout(inputPauseTimer);
    inputPauseTimer = setTimeout(() => {
      inputFocused = false;
      resumeTicker();
    }, 2 * 60 * 1000);
  });

  // Blur intentionally empty to respect 2-min pause on focus
  inputEl.addEventListener("blur", () => {});

  // Initial load
  await loadTickerTape();
  startTickerScroll();

  // Check highlight every 100ms
  setInterval(checkHighlight, 100);
});
