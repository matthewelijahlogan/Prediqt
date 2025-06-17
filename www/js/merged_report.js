function displayMergedReport() {
  const container = document.getElementById("merged-accuracy-report");
  if (!container) return;

  const data = mergedAccuracyData;
  if (!data) {
    container.innerHTML = "<p>No data available.</p>";
    return;
  }

  container.innerHTML = `
    <h2>Merged Accuracy Report</h2>
    <p><strong>Last Updated:</strong> ${new Date(data.last_updated).toLocaleString()}</p>
    <p><strong>Total Predictions:</strong> ${data.total_predictions}</p>
    <p><strong>Overall Accuracy:</strong> ${(data.overall_accuracy * 100).toFixed(2)}%</p>
    <h3>Model Accuracies:</h3>
    <ul>
      ${Object.entries(data.model_accuracies).map(([model, acc]) => 
        `<li>${model}: ${(acc * 100).toFixed(2)}%</li>`
      ).join('')}
    </ul>
  `;
}
