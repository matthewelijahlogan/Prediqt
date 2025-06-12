import { fetchTopLosers } from './api.js';

const listEl = document.querySelector(".stock-list");

(async () => {
  const losers = await fetchTopLosers();

  if (!losers || losers.length === 0) {
    listEl.innerHTML = "<li>No data available</li>";
  } else {
    listEl.innerHTML = "";
    losers.forEach(m => {
      const li = document.createElement("li");
      li.textContent = `$${m.ticker} - ${m.direction} (${m.predicted_next_close.toFixed(2)})`;
      listEl.appendChild(li);
    });
  }
})();
