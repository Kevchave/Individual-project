import {
  wpmChart,
  volumeChart,
  pitchChart,
  confidenceChart,
  silenceChart,
  wpmData,
  volumeData,
  pitchData,
  confidenceData,
  silenceData,
  timeLabels,
  startTime,
  setWpmChart,
  setVolumeChart,
  setPitchChart,
  setConfidenceChart,
  setSilenceChart,
  setStartTime
} from './state.js';

// Helper function to create a chart
function createChart(ctxId, label, borderColor, backgroundColor, yTitle, chartOptions) {
  const canvas = document.getElementById(ctxId);
  if (!canvas) {
    return null;
  }
  
  const ctx = canvas.getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: label,
        data: [],
        borderColor: borderColor,
        backgroundColor: backgroundColor,
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      ...chartOptions,
      scales: {
        ...chartOptions.scales,
        y: {
          ...chartOptions.scales.y,
          title: {
            display: true,
            text: yTitle
          }
        }
      }
    }
  });
}

// Initialize all charts
function initialiseCharts(currentTheme) {
  const isDark = currentTheme === 'dark';
  const textColor = isDark ? '#e0e0e0' : '#222';
  const gridColor = isDark ? '#444' : '#ddd';

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 },
    color: textColor,
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time (seconds)',
          color: textColor
        },
        grid: { color: gridColor },
        ticks: { color: textColor }
      },
      y: {
        display: true,
        beginAtZero: true,
        grid: { color: gridColor },
        ticks: { color: textColor }
      }
    },
    plugins: {
      legend: { display: false }
    }
  };

  if (wpmChart) wpmChart.destroy();
  if (volumeChart) volumeChart.destroy();
  if (pitchChart) pitchChart.destroy();
  if (confidenceChart) confidenceChart.destroy();
  if (silenceChart) silenceChart.destroy();

  // Only create charts if the canvas elements exist (dashboard page)
  const wpmChartInstance = createChart('wpmChart', 'WPM', '#0077cc', 'rgba(0, 119, 204, 0.1)', 'Words per Minute', chartOptions);
  const volumeChartInstance = createChart('volumeChart', 'Volume', '#28a745', 'rgba(40, 167, 69, 0.1)', 'Volume (dBFS)', chartOptions);
  const pitchChartInstance = createChart('pitchChart', 'Pitch Variance', '#dc3545', 'rgba(220, 53, 69, 0.1)', 'Pitch Variance (Hz)', chartOptions);
  const confidenceChartInstance = createChart('confidenceChart', 'Confidence', '#ffc107', 'rgba(255, 193, 7, 0.1)', 'Confidence Score', chartOptions);
  const silenceChartInstance = createChart('silenceChart', 'Silence Ratio', '#6f42c1', 'rgba(111, 66, 193, 0.1)', 'Silence Ratio', chartOptions);

  setWpmChart(wpmChartInstance);
  setVolumeChart(volumeChartInstance);
  setPitchChart(pitchChartInstance);
  setConfidenceChart(confidenceChartInstance);
  setSilenceChart(silenceChartInstance);
}

// Update charts with new data
function updateCharts(wpm, volume, pitch, confidence = null, silence = null) {
  if (!startTime) return;
  const currentTime = Math.floor((Date.now() - startTime) / 1000);

  wpmData.push(wpm);
  volumeData.push(volume);
  pitchData.push(pitch);
  confidenceData.push(confidence);
  silenceData.push(silence);
  timeLabels.push(currentTime);

  const maxPoints = 5;
  if (wpmData.length > maxPoints) {
    wpmData.shift(); // shift removes the first (oldest) element
    volumeData.shift();
    pitchData.shift();
    confidenceData.shift();
    silenceData.shift();
    timeLabels.shift();
  }

  if (wpmChart && wpmChart.data) {
    wpmChart.data.labels = timeLabels;          // Sets chart labels to current timeLabels 
    wpmChart.data.datasets[0].data = wpmData;   // Sets chart data to latest data array 
    wpmChart.update('none');                    // No animation 
  }

  if (volumeChart && volumeChart.data) {
    volumeChart.data.labels = timeLabels;
    volumeChart.data.datasets[0].data = volumeData;
    volumeChart.update('none');
  }
  
  if (pitchChart && pitchChart.data) {
    pitchChart.data.labels = timeLabels;
    pitchChart.data.datasets[0].data = pitchData;
    pitchChart.update('none');
  }

  if (confidenceChart && confidenceChart.data) {
    confidenceChart.data.labels = timeLabels;
    confidenceChart.data.datasets[0].data = confidenceData;
    confidenceChart.update('none');
  }

  if (silenceChart && silenceChart.data) {
    silenceChart.data.labels = timeLabels;
    silenceChart.data.datasets[0].data = silenceData;
    silenceChart.update('none');
  }
}

// Reset charts
function resetCharts() {
  wpmData.length = 0;     // Empties all arrays 
  volumeData.length = 0;
  pitchData.length = 0;
  confidenceData.length = 0;
  silenceData.length = 0;
  timeLabels.length = 0;
  setStartTime(null);
  [wpmChart, volumeChart, pitchChart, confidenceChart, silenceChart].forEach(chart => {
    if (chart && chart.data) {
      chart.data.labels = [];
      chart.data.datasets[0].data = [];
      chart.update();
    }
  });
}

export { initialiseCharts, updateCharts, resetCharts };
