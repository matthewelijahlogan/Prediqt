async function predict() {
  const ticker = document.getElementById("tickerInput").value.trim().toUpperCase();
  if (!ticker) {
    alert("Please enter a ticker symbol.");
    return;
  }
  
  // Clear previous predictions
  document.getElementById("predictionHour").textContent = "Loading...";
  document.getElementById("predictionDay").textContent = "Loading...";
  document.getElementById("predictionWeek").textContent = "Loading...";
  document.getElementById("predictionMonth").textContent = "Loading...";
  
  // Define the horizons you want predictions for
  const horizons = ["hour", "day", "week", "month"];
  
  // For each horizon, fetch prediction and update UI
  for (const horizon of horizons) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/predict/${ticker}?horizon=${horizon}`);
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      const data = await response.json();
      const outputId = `prediction${horizon.charAt(0).toUpperCase() + horizon.slice(1)}`;
      document.getElementById(outputId).textContent = `$${data.predicted_next_close.toFixed(2)} (MSE: ${data.model_mse.toFixed(4)})`;
    } catch (err) {
      const outputId = `prediction${horizon.charAt(0).toUpperCase() + horizon.slice(1)}`;
      document.getElementById(outputId).textContent = `Error: ${err.message}`;
    }
  }
}
