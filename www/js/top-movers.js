import { fetchTopMovers } from './api.js';

const listEl = document.querySelector(".stock-list");

(async () => {
  const movers = await fetchTopMovers();
  const gainers = movers.filter(m => m.direction === "Up");

  if (gainers.length === 0) {
    listEl.innerHTML = "<li>No data available</li>";
  } else {
    listEl.innerHTML = "";
    gainers.forEach(m => {
      const li = document.createElement("li");
      li.textContent = `$${m.ticker} - ${m.direction} (${m.predicted_next_close.toFixed(2)})`;
      listEl.appendChild(li);
    });
  }
})();
