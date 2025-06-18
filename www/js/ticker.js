document.addEventListener("DOMContentLoaded", async () => {
  // Elements references
  const tickerEl = document.getElementById("newsTicker");
  const tickerBar = document.querySelector(".ticker-bar");
  const inputEl = document.getElementById("tickerInput");
  const predictBtn = document.getElementById("predictBtn");

  // UI elements for predictions & quotes
  const predictionHourEl = document.getElementById("predictionHour");
  const predictionDayEl = document.getElementById("predictionDay");
  const predictionWeekEl = document.getElementById("predictionWeek");
  const predictionMonthEl = document.getElementById("predictionMonth");

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

  tickerEl.innerHTML = "Loading...";

  // Load ticker tape symbols and prices into tickerEl
  async function loadTickerTape() {
    try {
      const res = await fetch("/api/ticker-tape");
      const data = await res.json();
      tickerEl.innerHTML = ""; // Clear loading

      data.tickers.forEach(t => {
        const span = document.createElement("span");
        span.classList.add("ticker-symbol");
        span.textContent = `${t.symbol} $${t.price}  `;
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
        offset -= 0.3; // Lower is slower (0.1 = very slow)
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

        // Extract ticker symbol text (before space)
        const ticker = sym.textContent.split(" ")[0];
        // Dispatch custom event for active ticker symbol
        window.dispatchEvent(
          new CustomEvent("tickerSymbolActive", {
            detail: ticker
          })
        );

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
      const result = data.predicted_next_close?.toFixed(2) ?? "N/A";
      targetEl.textContent = result;
    } catch (err) {
      targetEl.textContent = "Error";
    }
  }

  // Fetch quote data for ticker and update quote elements
  async function fetchQuote(ticker) {
    try {
      const res = await fetch(`/api/quote?ticker=${ticker}`);
      const data = await res.json();

      quotePriceEl.textContent = data.price ?? "-";
      quoteChangeEl.textContent = data.change ?? "-";
      quotePercentEl.textContent = data.percent_change?.toFixed(2) + "%" ?? "-";
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

  // On button click, get ticker input and fetch predictions & quote
  predictBtn.addEventListener("click", () => {
    const ticker = inputEl.value.trim().toUpperCase();
    if (!ticker) return;

    fetchPrediction(ticker, "hour", "predictionHour");
    fetchPrediction(ticker, "day", "predictionDay");
    fetchPrediction(ticker, "week", "predictionWeek");
    fetchPrediction(ticker, "month", "predictionMonth");
    fetchQuote(ticker);
  });

  // On tickerSymbolActive event (when highlighted), fetch data for that ticker
  window.addEventListener("tickerSymbolActive", e => {
    const ticker = e.detail;
    fetchPrediction(ticker, "hour", "predictionHour");
    fetchPrediction(ticker, "day", "predictionDay");
    fetchPrediction(ticker, "week", "predictionWeek");
    fetchPrediction(ticker, "month", "predictionMonth");
    fetchQuote(ticker);
  });

  // Handle input focus — pause ticker for 2 minutes
  inputEl.addEventListener("focus", () => {
    inputFocused = true;
    pauseTicker();
    clearTimeout(inputPauseTimer); // clear any previous
    inputPauseTimer = setTimeout(() => {
      inputFocused = false;
      resumeTicker();
    }, 2 * 60 * 1000); // 2 minutes
  });

  // Do not resume immediately on blur — wait for timer
  inputEl.addEventListener("blur", () => {
    // Intentionally empty to respect the 2-minute delay
  });

  // Initial load
  await loadTickerTape();
  startTickerScroll(); // ✅ Start the JS scroll loop

  // Check highlights every 100ms
  setInterval(checkHighlight, 100);
});
