const scanForm = document.getElementById("kingmakerScan");
scanForm.addEventListener("submit", async event => {
  event.preventDefault();
  const button = scanForm.querySelector("button");
  const status = document.getElementById("scanStatus");
  const body = document.getElementById("scanResults");
  button.disabled = true;
  body.replaceChildren();
  status.textContent = "Fetching market history and validating models...";
  try {
    const params = new URLSearchParams({
      tickers: document.getElementById("scanSymbols").value,
      horizon: document.getElementById("scanHorizon").value
    });
    const response = await fetch(`/api/kingmaker/scan?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Check your symbols and horizon.");
    for (const item of data.items) {
      const row = document.createElement("tr");
      const evidence = item.evidence;
      const skill = evidence.baseline_return_mse > 0
        ? 100 * (1 - evidence.return_mse / evidence.baseline_return_mse) : 0;
      const values = [item.ticker, item.signal.action,
        `$${item.predicted_next_close.toFixed(2)}`,
        `${item.signal.expected_move_percent.toFixed(2)}%`,
        `${item.validation_confidence.toFixed(1)}/100`,
        `${skill.toFixed(1)}% error reduction vs no-change; ${evidence.validation_samples} samples; ${item.data_quality.provider}`];
      for (const value of values) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      }
      row.title = item.signal.rationale;
      body.appendChild(row);
    }
    status.textContent = `${data.qualified_count} qualified of ${data.items.length} evaluated. ` +
      (data.errors.length ? data.errors.map(item => `${item.ticker}: ${item.error}`).join("; ") : "Scan complete.");
  } catch (error) {
    status.textContent = `Scan failed: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});
