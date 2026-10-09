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
  const automationModeEl = document.getElementById("automationMode");
  const automationProposalEl = document.getElementById("automationProposal");
  const automationNotionalEl = document.getElementById("automationNotional");

  // State variables
  let tickerPaused = false;
  let inputFocused = false;
  let lastHighlighted = null;
  let pauseTimer = null;
  let inputPauseTimer = null;
  let predictionInProgress = false;

  const escapeHtml = value => String(value).replace(/[&<>'"]/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);

  const horizonSuffix = {
    hour: "Hour",
    day: "Day",
    week: "Week",
    month: "Month"
  };

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
    const suffix = horizonSuffix[horizon];
    const signalEl = document.getElementById(`signal${suffix}`);
    const detailEl = document.getElementById(`detail${suffix}`);
    const cardEl = targetEl.closest(".prediction");
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
        targetEl.textContent = `$${result}`;
        flashValueChange(targetEl, parseFloat(result), oldVal);
      } else {
        targetEl.textContent = result;
      }
      const signal = data.signal || {};
      const action = ["BUY", "HOLD", "SELL"].includes(signal.action)
        ? signal.action
        : "HOLD";
      signalEl.textContent = action;
      signalEl.className = `decision ${action.toLowerCase()}`;
      cardEl.dataset.signal = action;
      const move = Number(signal.expected_move_percent);
      const confidence = Number(signal.confidence);
      detailEl.textContent = signal.expected_move_percent != null && Number.isFinite(move)
        ? `${move >= 0 ? "+" : ""}${move.toFixed(2)}% · ${confidence.toFixed(1)}% CONF`
        : "SIGNAL UNAVAILABLE";
      detailEl.title = signal.rationale || "Signal evidence unavailable";
      return data;
    } catch (err) {
      console.error(`Prediction failed for ${ticker} (${horizon}):`, err);
      targetEl.textContent = "N/A";
      signalEl.textContent = "HOLD";
      signalEl.className = "decision hold";
      cardEl.dataset.signal = "HOLD";
      detailEl.textContent = "MARKET FEED UNAVAILABLE";
      detailEl.title = err instanceof Error ? err.message : "Prediction request failed";
      return null;
    }
  }

  function renderComposite(results) {
    const signals = results.flatMap(result => result?.signal ? [result.signal] : []);
    const buyCount = signals.filter(signal => signal.action === "BUY").length;
    const sellCount = signals.filter(signal => signal.action === "SELL").length;
    const action = buyCount >= 2 && buyCount > sellCount
      ? "BUY"
      : sellCount >= 2 && sellCount > buyCount
        ? "SELL"
        : "HOLD";
    const moves = signals
      .flatMap(signal => signal.expected_move_percent == null
        ? []
        : [Number(signal.expected_move_percent)])
      .filter(Number.isFinite);
    const averageMove = moves.length
      ? moves.reduce((total, move) => total + move, 0) / moves.length
      : null;
    const compositeSignal = document.getElementById("compositeSignal");
    const compositeMove = document.getElementById("compositeMove");
    compositeSignal.textContent = action;
    compositeSignal.dataset.signal = action;
    compositeMove.textContent = averageMove == null
      ? "Signal evidence unavailable"
      : `${buyCount} BUY · ${sellCount} SELL · ${averageMove >= 0 ? "+" : ""}${averageMove.toFixed(2)}% avg move`;
    return { action, buyCount, sellCount, averageMove };
  }

  function renderAutomationProposal(proposal) {
    if (!proposal) return;
    const terminal = ["SUBMITTED", "REJECTED"].includes(proposal.status);
    const symbol = escapeHtml(proposal.symbol);
    const side = escapeHtml(proposal.side.toUpperCase());
    const rationale = escapeHtml(proposal.rationale || "Qualified composite signal");
    const error = proposal.error ? escapeHtml(proposal.error) : "";
    const proposalId = escapeHtml(proposal.proposal_id);
    automationProposalEl.innerHTML = `
      <span class="automation-state ${proposal.status === "SUBMITTED" ? "submitted" : ""}">${proposal.status.replaceAll("_", " ")}</span>
      <strong>${side} ${symbol}</strong>
      <div class="automation-order-grid">
        <div><span>SYMBOL</span><strong>${symbol}</strong></div>
        <div><span>SIDE</span><strong>${side}</strong></div>
        <div><span>NOTIONAL</span><strong>$${Number(proposal.notional).toFixed(2)}</strong></div>
      </div>
      <p>${rationale}</p>
      ${error ? `<p class="automation-error">${error}</p>` : ""}
      ${terminal ? "" : `<div class="automation-actions"><button class="approve-order" data-action="approve" data-id="${proposalId}">Approve paper order</button><button data-action="reject" data-id="${proposalId}">Reject</button></div>`}
    `;
  }

  async function loadAutomationMachine() {
    if (automationProposalEl.closest('section').hidden) return;
    try {
      const [statusResponse, proposalsResponse] = await Promise.all([
        fetch("/api/automation/status"),
        fetch("/api/automation/proposals")
      ]);
      const status = await statusResponse.json();
      const proposals = await proposalsResponse.json();
      automationModeEl.textContent = `PAPER · ${status.connected ? "CONNECTED" : "SETUP REQUIRED"}`;
      automationNotionalEl.max = String(status.maximum_notional || 100);
      if (proposals.items?.length) renderAutomationProposal(proposals.items[0]);
    } catch (error) {
      automationModeEl.textContent = "PAPER · OFFLINE";
    }
  }

  async function prepareAutomationProposal(ticker, composite) {
    if (automationProposalEl.closest('section').hidden) return;
    if (composite.action === "SELL") {
      automationProposalEl.innerHTML = '<span class="automation-state">EXIT RISK</span><strong>Sell automation is position-aware</strong><p>PredIQt will not create a sell order until the connected broker confirms an existing long position.</p>';
      return;
    }
    if (composite.action !== "BUY") {
      automationProposalEl.innerHTML = '<span class="automation-state">HOLD</span><strong>No qualified order queued</strong><p>The composite signal did not meet the two-horizon BUY gate.</p>';
      return;
    }

    const notional = Number(automationNotionalEl.value);
    const response = await fetch("/api/automation/proposals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: ticker,
        side: "buy",
        notional,
        rationale: `${composite.buyCount}/4 BUY horizons · ${composite.averageMove >= 0 ? "+" : ""}${composite.averageMove.toFixed(2)}% average expected move`
      })
    });
    const proposal = await response.json();
    if (!response.ok) throw new Error(proposal.detail || "Could not prepare order");
    renderAutomationProposal(proposal);
    if (window.Notification?.permission === "granted") {
      new Notification("PredIQt paper order ready", { body: `Approve ${proposal.side.toUpperCase()} ${proposal.symbol} · $${Number(proposal.notional).toFixed(2)}` });
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
      return true;
    } catch (err) {
      quotePriceEl.textContent = "Error";
      quoteChangeEl.textContent = "Error";
      quotePercentEl.textContent = "Error";
      quoteVolumeEl.textContent = "Error";
      quoteMarketCapEl.textContent = "Error";
      quoteSectorEl.textContent = "Error";
      return false;
    }
  }

  // Helper to fetch predictions and quotes for a ticker
  async function triggerPredictionAndQuote(ticker) {
    const [hour, day, week, month, quoteAvailable] = await Promise.all([
      fetchPrediction(ticker, "hour", "predictionHour"),
      fetchPrediction(ticker, "day", "predictionDay"),
      fetchPrediction(ticker, "week", "predictionWeek"),
      fetchPrediction(ticker, "month", "predictionMonth"),
      fetchQuote(ticker)
    ]);
    const composite = renderComposite([hour, day, week, month]);
    try {
      await prepareAutomationProposal(ticker, composite);
    } catch (error) {
      automationProposalEl.innerHTML = `<span class="automation-state error">AUTOMATION ERROR</span><strong>Proposal could not be prepared</strong><p class="automation-error">${escapeHtml(error instanceof Error ? error.message : "Unknown automation error")}</p>`;
    }
    return {
      signalCount: [hour, day, week, month].filter(Boolean).length,
      quoteAvailable
    };
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

    let outcome = { signalCount: 0, quoteAvailable: false };
    try {
      outcome = await triggerPredictionAndQuote(ticker);
    } finally {
      predictionInProgress = false;
      predictBtn.disabled = false;
      predictBtn.innerHTML = originalButtonMarkup;
      if (panelStatus) {
        panelStatus.innerHTML = outcome.signalCount
          ? `<i></i> ${outcome.signalCount}/4 signals ready`
          : "<i></i> Market feed unavailable";
      }
    }
  });

  automationProposalEl.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    button.disabled = true;
    const action = button.dataset.action;
    try {
      const response = await fetch(`/api/automation/proposals/${button.dataset.id}/${action}`, { method: "POST" });
      const proposal = await response.json();
      if (!response.ok) throw new Error(proposal.detail || `Could not ${action} order`);
      renderAutomationProposal(proposal);
    } catch (error) {
      const errorElement = automationProposalEl.querySelector(".automation-error") || document.createElement("p");
      errorElement.className = "automation-error";
      errorElement.textContent = error instanceof Error ? error.message : "Automation request failed";
      automationProposalEl.appendChild(errorElement);
      button.disabled = false;
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
  await loadAutomationMachine();
  startTickerScroll();

  // Check highlight every 100ms
  setInterval(checkHighlight, 100);
});
