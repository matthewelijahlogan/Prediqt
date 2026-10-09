(() => {
  const $ = id => document.getElementById(id);
  const form = $('opportunityForm');
  if (!form) return;
  let board = null, selected = null;
  const fmt = (n, digits = 2) => Number(n).toFixed(digits);
  function element(tag, text, cls) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  }
  function svgNode(tag, attrs, text) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function canvas(container, label, height = 190) {
    const svg = svgNode('svg', {viewBox: `0 0 600 ${height}`, role: 'img', 'aria-label': label});
    svg.append(svgNode('title', {}, label));
    $(container).replaceChildren(svg);
    return svg;
  }
  function bars(container, values, label) {
    const svg = canvas(container, label, 40 * values.length + 25);
    const maximum = Math.max(1, ...values.map(v => Math.abs(v.value)));
    values.forEach((v, i) => {
      const y = i * 40 + 20;
      svg.append(svgNode('text', {x: 5, y, fill: '#b9c9c5', 'font-size': 13}, v.label));
      svg.append(svgNode('rect', {x: 150, y: y - 13, width: Math.abs(v.value) / maximum * 330,
        height: 18, rx: 3, fill: v.value < 0 ? '#f17686' : '#65e8b2'}));
      svg.append(svgNode('text', {x: 495, y, fill: '#fff', 'font-size': 13}, v.display || fmt(v.value)));
    });
  }
  function scenario() {
    if (!selected || !board) return;
    const amount = Number($('scenarioAmount').value);
    if (!Number.isFinite(amount) || amount <= 0 || amount > 10000000) {
      $('scenarioText').textContent = 'Enter an amount between $1 and $10,000,000.';
      $('scenarioChart').replaceChildren(); return;
    }
    const cost = amount * board.round_trip_cost_bps / 10000;
    const profit = price => amount * (price / selected.last_price - 1) - cost;
    const values = [{label: 'Lower RMSE case', value: profit(selected.error_band.low)},
      {label: 'Model target', value: profit(selected.target)},
      {label: 'Upper RMSE case', value: profit(selected.error_band.high)}];
    bars('scenarioChart', values.map(v => ({...v, display: `$${fmt(v.value)}`})), 'Estimated scenario profit or loss after assumed costs');
    $('scenarioText').textContent = `${fmt(amount / selected.last_price, 4)} hypothetical shares × (scenario price − $${fmt(selected.last_price)}) − $${fmt(cost)} assumed round-trip cost. Model-target net P/L: $${fmt(values[1].value)}. No taxes included.`;
  }
  function detail(item) {
    selected = item;
    $('deskDetail').hidden = false;
    $('detailTitle').textContent = `${item.ticker} / ${board.horizon.toUpperCase()} / ${item.driver_status}`;
    const history = item.history;
    const prices = history.map(p => p.close);
    const low = Math.min(...prices, item.error_band.low);
    const high = Math.max(...prices, item.error_band.high);
    const span = Math.max(high - low, item.last_price * 0.005);
    const y = price => 155 - (price - low) / span * 120;
    const x = index => 60 + index / history.length * 485;
    const svg = canvas('priceChart', `${item.ticker}: observed closes, forecast target and historical RMSE range`);
    [low, (high+low)/2, high].forEach(price => {
      svg.append(svgNode('line', {x1: 60, x2: 560, y1: y(price), y2: y(price), stroke: '#243a37'}));
      svg.append(svgNode('text', {x: 0, y: y(price)+4, fill: '#b9c9c5', 'font-size': 12}, `$${fmt(price)}`));
    });
    svg.append(svgNode('polyline', {points: prices.map((p, i) => `${x(i)},${y(p)}`).join(' '), fill: 'none', stroke: '#65e8b2', 'stroke-width': 2}));
    const last = history.length-1;
    svg.append(svgNode('line', {x1: x(last), y1: y(prices[last]), x2: x(last+1), y2: y(item.target), stroke: '#dfbd69', 'stroke-width': 2, 'stroke-dasharray': '5 4'}));
    svg.append(svgNode('line', {x1: x(last+1), x2: x(last+1), y1: y(item.error_band.low), y2: y(item.error_band.high), stroke: '#dfbd69', 'stroke-width': 6, opacity: 0.45}));
    svg.append(svgNode('text', {x: 60, y: 180, fill: '#b9c9c5', 'font-size': 12}, 'Observed closes → gold forecast / RMSE range'));
    bars('scoreChart', Object.entries(item.score_components).map(([label, value]) => ({label, value})), 'Movement score contributions, not probabilities');
    $('detailEvidence').textContent = `Movement score ${fmt(item.movement_score)}/100 · quality ${fmt(item.forecast.validation_confidence, 1)}/100 · forecast ${fmt(item.forecast_move_percent)}% · estimated net long move ${fmt(item.estimated_net_move_percent)}% · 20-bar volatility ${fmt(item.volatility_20_bars_percent)}% · relative volume ${item.relative_volume === null ? 'unavailable' : `${fmt(item.relative_volume)}×`} · ${item.forecast.data_quality.provider} · origin ${item.forecast.evidence.last_bar_at}. ${item.forecast.signal.rationale} ${item.error_band.label}.`;
    scenario();
  }
  function list(id, items, movers) {
    const parent = $(id); parent.replaceChildren();
    if (!items.length) {parent.append(element('li', 'No usable candidates. Missing evidence is not replaced with fabricated rankings.')); return;}
    items.forEach((item, i) => {
      const button = element('button', undefined, 'desk-candidate'); button.type = 'button';
      button.append(element('strong', `${String(i+1).padStart(2, '0')} / ${item.ticker}`),
        element('span', movers ? `MOVEMENT ${fmt(item.movement_score)} / 100` : item.driver_status, movers ? 'desk-speculative' : 'desk-signal'),
        element('span', `Forecast ${fmt(item.forecast_move_percent)}% · last $${fmt(item.last_price)} · quality ${fmt(item.forecast.validation_confidence, 1)}/100`));
      button.addEventListener('click', () => detail(item));
      const li = element('li'); li.append(button); parent.append(li);
    });
  }
  form.addEventListener('submit', async event => {
    event.preventDefault(); const button = form.querySelector('button'); button.disabled = true;
    $('deskStatus').textContent = 'Starting a bounded market scan...';
    try {
      const response = await fetch('/api/kingmaker/opportunities', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tickers: $('deskSymbols').value, horizon: $('deskHorizon').value, cost_bps: Number($('deskCosts').value)})});
      const start = await response.json();
      if (!response.ok) throw new Error(typeof start.detail === 'string' ? start.detail : 'Check symbols and cost assumption.');
      let job;
      const deadline = Date.now() + 15*60*1000;
      do {
        if (Date.now() > deadline) throw new Error('Scan still running. Retry to reconnect to its progress.');
        await new Promise(resolve => setTimeout(resolve, 2000));
        const poll = await fetch(`/api/kingmaker/opportunities/${encodeURIComponent(start.job_id)}`);
        job = await poll.json();
        if (!poll.ok || job.status === 'failed') throw new Error(job.error || job.detail || 'Scan unavailable');
        $('deskStatus').textContent = `Evaluated ${job.completed}/${job.total} symbols. Provider work stays separate from this page.`;
      } while (job.status !== 'complete');
      board = job.result;
      $('driversHeading').textContent = board.horizon === 'day' ? 'Top 10 daily drivers' : `Top 10 ${board.horizon} drivers`;
      list('bigMovers', board.big_movers, true); list('dailyDrivers', board.daily_drivers, false);
      $('deskMethod').textContent = board.methodology;
      $('deskStatus').textContent = `${board.evaluated}/${board.universe.length} usable · ${board.errors.length} unavailable · snapshot ${board.generated_at}. ` + board.errors.map(e => e.ticker).join(', ');
      $('exportWatchlist').disabled = !board.evaluated;
      const first = board.daily_drivers[0] || board.big_movers[0];
      if (first) detail(first); else {selected = null; $('deskDetail').hidden = true;}
    } catch (error) { $('deskStatus').textContent = `Scan failed: ${error.message}. Any previous results retain their original timestamp.`; }
    finally {button.disabled = false;}
  });
  $('scenarioAmount').addEventListener('input', scenario);
  $('exportWatchlist').addEventListener('click', () => {
    if (!board) return;
    const rows = [['symbol','list','rank','signal','forecast_move_percent','movement_score','provider','origin_bar']];
    for (const [name, items] of [['big_movers', board.big_movers], ['daily_drivers', board.daily_drivers]])
      items.forEach((item, i) => rows.push([item.ticker, name, i+1, item.driver_status, item.forecast_move_percent, item.movement_score, item.forecast.data_quality.provider, item.forecast.evidence.last_bar_at]));
    const csv = rows.map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
    const a = element('a'); a.href = url; a.download = 'kingmaker-watchlist.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  fetch('/api/kingmaker/webull/status').then(r => {if (!r.ok) throw new Error(); return r.json();}).then(status => {
    $('webullStatus').textContent = `Webull data: ${status.configured ? 'credentials configured; access not yet verified' : 'API setup required'} · execution: manual in Webull. ${status.note}`;
  }).catch(() => {$('webullStatus').textContent = 'Webull connection status unavailable. Manual watchlist export remains available.';});
})();
