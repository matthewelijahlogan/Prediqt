(() => {
  const status = document.getElementById('metricsStatus');
  const refresh = document.getElementById('refreshMetrics');
  const settle = document.getElementById('settleMetrics');
  const number = value => value == null ? 'Awaiting outcomes' : Number(value).toFixed(2);
  async function load(checkOutcomes = false) {
    refresh.disabled = settle.disabled = true;
    status.textContent = checkOutcomes ? 'Checking later completed bars...' : 'Loading observed metrics...';
    try {
      let checked;
      if (checkOutcomes) {
        const response = await fetch('/api/kingmaker/settle', {method: 'POST', signal: AbortSignal.timeout(120000)});
        if (!response.ok) throw new Error('Outcome check unavailable');
        checked = await response.json();
      }
      const response = await fetch('/api/kingmaker/metrics', {signal: AbortSignal.timeout(15000)});
      if (!response.ok) throw new Error('Metrics unavailable');
      const data = await response.json();
      const body = document.getElementById('metricsResults');
      body.replaceChildren();
      for (const [horizon, group] of Object.entries(data.horizons)) {
        const row = document.createElement('tr');
        for (const value of [horizon, group.recorded, group.pending, group.settled,
          number(group.mae_dollars), number(group.rmse_dollars), number(group.baseline_rmse_dollars),
          group.direction_accuracy == null ? 'Awaiting outcomes' : `${(group.direction_accuracy * 100).toFixed(1)}%`]) {
          const cell = document.createElement('td'); cell.textContent = value; row.append(cell);
        }
        body.append(row);
      }
      status.textContent = (checked ? `${checked.settled} newly settled; ${checked.errors.length} checks unavailable. ` : '') +
        (Object.keys(data.horizons).length ? 'Showing locally recorded first-seen forecasts. Pending outcomes are not scored.' : 'No forecasts recorded yet. Run a prediction or scan to start collecting.');
    } catch (error) {
      status.textContent = `${error.message}. Displayed metrics may be from the previous refresh.`;
    } finally { refresh.disabled = settle.disabled = false; }
  }
  refresh.addEventListener('click', () => load());
  settle.addEventListener('click', () => load(true));
  load();
})();
