// accuracy_report.js//

function displayAccuracyReport() {
  const container = document.getElementById('accuracy-report');
  if (!container || typeof accuracyData !== 'object') return;

  container.innerHTML = ''; // Clear existing content

  // --- Header
  const header = document.createElement('h2');
  header.textContent = 'Algorithm Accuracy Report';
  container.appendChild(header);

  // --- Last Updated
  const lastUpdated = document.createElement('p');
  lastUpdated.textContent = 'Last Updated: ' + (accuracyData.last_updated || 'Unknown');
  container.appendChild(lastUpdated);

  // --- Total Predictions
  const totalPred = document.createElement('p');
  totalPred.textContent = 'Total Predictions: ' + (accuracyData.total_predictions ?? 'N/A');
  container.appendChild(totalPred);

  // --- Overall Accuracy
  const overallAcc = document.createElement('p');
  if (typeof accuracyData.overall_accuracy === 'number') {
    overallAcc.textContent = 'Overall Accuracy: ' + (accuracyData.overall_accuracy * 100).toFixed(2) + '%';
  } else {
    overallAcc.textContent = 'Overall Accuracy: N/A';
  }
  container.appendChild(overallAcc);

  // --- Predictions within 1% error
  if (typeof accuracyData.within_1_percent === 'number') {
    const withinOnePercent = document.createElement('p');
    withinOnePercent.textContent = 'Predictions within 1% error: ' + (accuracyData.within_1_percent * 100).toFixed(2) + '%';
    container.appendChild(withinOnePercent);
  }

  // --- Per-Model Accuracy
  const modelAccuracies = accuracyData.model_accuracies;
  if (modelAccuracies && typeof modelAccuracies === 'object' && Object.keys(modelAccuracies).length > 0) {
    const modelHeader = document.createElement('h3');
    modelHeader.textContent = 'Model Accuracies';
    container.appendChild(modelHeader);

    const ul = document.createElement('ul');

    // Sort models alphabetically for consistent order
    const sortedModels = Object.keys(modelAccuracies).sort();

    sortedModels.forEach((model) => {
      const acc = modelAccuracies[model];
      const li = document.createElement('li');
      li.textContent = `${model}: ${typeof acc === 'number' ? (acc * 100).toFixed(2) + '%' : 'N/A'}`;
      ul.appendChild(li);
    });

    container.appendChild(ul);
  }
}

// Automatically run when page loads
window.onload = displayAccuracyReport;
