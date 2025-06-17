function displayMergedReport() {
  const container = document.getElementById('merged-accuracy-report');
  if (!container || typeof mergedAccuracyData === 'undefined') return;

  container.innerHTML = '';

  const header = document.createElement('h2');
  header.textContent = 'Merged Accuracy Report';
  container.appendChild(header);

  const lastUpdated = document.createElement('p');
  lastUpdated.textContent = 'Last Updated: ' + mergedAccuracyData.last_updated;
  container.appendChild(lastUpdated);

  const totalPred = document.createElement('p');
  totalPred.textContent = 'Total Predictions: ' + mergedAccuracyData.total_predictions;
  container.appendChild(totalPred);

  const overallAcc = document.createElement('p');
  overallAcc.textContent = 'Overall Accuracy: ' + (mergedAccuracyData.overall_accuracy * 100).toFixed(2) + '%';
  container.appendChild(overallAcc);

  const modelHeader = document.createElement('h3');
  modelHeader.textContent = 'Model Accuracies';
  container.appendChild(modelHeader);

  const ul = document.createElement('ul');
  for (const [model, acc] of Object.entries(mergedAccuracyData.model_accuracies)) {
    const li = document.createElement('li');
    li.textContent = `${model}: ${(acc * 100).toFixed(2)}%`;
    ul.appendChild(li);
  }
  container.appendChild(ul);
}
