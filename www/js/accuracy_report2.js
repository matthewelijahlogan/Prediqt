// accuracy_report2.js

function displayAccuracyReport2() {
  const container = document.getElementById('accuracy-report-2'); // Add a second container in HTML
  if (!container) return;

  container.innerHTML = ''; // clear

  const header = document.createElement('h2');
  header.textContent = 'Algorithm 2 Accuracy Report';
  container.appendChild(header);

  const lastUpdated = document.createElement('p');
  lastUpdated.textContent = 'Last Updated: ' + accuracyData2.last_updated;
  container.appendChild(lastUpdated);

  const totalPred = document.createElement('p');
  totalPred.textContent = 'Total Predictions: ' + accuracyData2.total_predictions;
  container.appendChild(totalPred);

  const overallAcc = document.createElement('p');
  overallAcc.textContent = 'Overall Accuracy: ' + (accuracyData2.overall_accuracy * 100).toFixed(2) + '%';
  container.appendChild(overallAcc);

  if (accuracyData2.model_accuracies && Object.keys(accuracyData2.model_accuracies).length > 0) {
    const modelHeader = document.createElement('h3');
    modelHeader.textContent = 'Model Accuracies';
    container.appendChild(modelHeader);

    const ul = document.createElement('ul');
    for (const [model, acc] of Object.entries(accuracyData2.model_accuracies)) {
      const li = document.createElement('li');
      li.textContent = `${model}: ${(acc * 100).toFixed(2)}%`;
      ul.appendChild(li);
    }
    container.appendChild(ul);
  }
}

window.onload = displayAccuracyReport2;
