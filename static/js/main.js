// This ensures the JS code only runs once the HTML is fully loaded 
document.addEventListener('DOMContentLoaded', function(){
    // Get references to the HTML elements 
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    const transcriptBox = document.getElementById('transcript-box');
    const wpmValue = document.getElementById('wpm-value');
    const volumeValue = document.getElementById('volume-value');
    const pitchValue = document.getElementById('pitch-value');
    
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');

    // Theme management
    let currentTheme = localStorage.getItem('theme') || 'light';
    
    // Initialize theme
    function initializeTheme() {
        document.documentElement.setAttribute('data-theme', currentTheme);
        updateThemeUI();
    }
    
    // Update theme UI elements
    function updateThemeUI() {
        if (currentTheme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Light Mode';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Dark Mode';
        }
    }
    
    // Toggle theme function
    function toggleTheme() {
        currentTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        localStorage.setItem('theme', currentTheme);
        updateThemeUI();
        
        // Update chart colors for dark mode
        updateChartColors();
    }
    
    // Update chart colors based on theme
    function updateChartColors() {
        const isDark = currentTheme === 'dark';
        const textColor = isDark ? '#e0e0e0' : '#222';
        const gridColor = isDark ? '#444' : '#ddd';
        
        if (wpmChart) {
            wpmChart.options.color = textColor;
            wpmChart.options.scales.x.grid.color = gridColor;
            wpmChart.options.scales.x.ticks.color = textColor;
            wpmChart.options.scales.y.grid.color = gridColor;
            wpmChart.options.scales.y.ticks.color = textColor;
            wpmChart.update('none');
        }
        if (volumeChart) {
            volumeChart.options.color = textColor;
            volumeChart.options.scales.x.grid.color = gridColor;
            volumeChart.options.scales.x.ticks.color = textColor;
            volumeChart.options.scales.y.grid.color = gridColor;
            volumeChart.options.scales.y.ticks.color = textColor;
            volumeChart.update('none');
        }
        if (pitchChart) {
            pitchChart.options.color = textColor;
            pitchChart.options.scales.x.grid.color = gridColor;
            pitchChart.options.scales.x.ticks.color = textColor;
            pitchChart.options.scales.y.grid.color = gridColor;
            pitchChart.options.scales.y.ticks.color = textColor;
            pitchChart.update('none');
        }
    }
    
    // Initialize theme on load
    initializeTheme();
    
    // Add event listener for theme toggle
    themeToggle.addEventListener('click', toggleTheme);

    let metricsMode = "live"
    let transcriptInterval = null;
    let metricsInterval = null;
    let isPaused = false;

    // Chart Variables 
    let wpmChart, volumeChart, pitchChart;  //Chart.js objects that control each graph 
    let wpmData = [], volumeData = [], pitchData = []; // Arrays storing the actual 
    let timeLabels = []; 
    let startTime = null; 

    // Initialise the charts 
    function initialiseCharts() {

        // Get theme-aware colors
        const isDark = currentTheme === 'dark';
        const textColor = isDark ? '#e0e0e0' : '#222';
        const gridColor = isDark ? '#444' : '#ddd';
        
        //Shared configuration for all three charts 
        const chartOptions = {
            responsive: true, // Charts resize with the window 
            maintainAspectRatio: false, 
            animation: { duration: 0 }, // No animations for smooth real-time updates 
            color: textColor,
            scales: {
                x: {
                    display: true, // Show the axis 
                    title: {
                        display: true, // Show the title 
                        text: 'Time (seconds)', // Set the title
                        color: textColor
                    },
                    grid: { color: gridColor },
                    ticks: { color: textColor }
                }, 
                y: {
                    display: true, // Show the axis 
                    beginAtZero: true, // Begin at 0
                    grid: { color: gridColor },
                    ticks: { color: textColor }
                }
            }, 
            plugins: {
                legend: { display: false } // Disable the legend
            }
        };

        if (wpmChart) wpmChart.destroy();
        if (volumeChart) volumeChart.destroy();
        if (pitchChart) pitchChart.destroy();

        // WPM Chart 
        const wpmCtx = document.getElementById('wpmChart').getContext('2d');
        wpmChart = new Chart(wpmCtx, { // Create a new chart.js instance, passing the canvas context and configuration object
            type: 'line', // Specify line chart
            data: {
                labels: [], 
                datasets: [{  // Define the data series
                    label: 'WPM', 
                    data: [], 
                    borderColor: '#0077cc', 
                    backgroundColor: 'rgba(0, 119, 204, 0.1)', 
                    borderWidth: 2,     // Thickness of the line in pixels 
                    fill: true,         // Fill area under the line
                    tension: 0.4        // Smooth curves (instead of straight)
                }] 
            }, 
            // Copy pre-defined chart options 
            options: {
                ...chartOptions, 
                scales: {
                    ...chartOptions.scales, 
                    y: {
                        ...chartOptions.scales.y, 
                        title: {
                            display: true, 
                            text: 'Words per Minute'
                        }
                    }
                }
            }
        });

        // Volume Chart 
        const volumeCtx = document.getElementById('volumeChart').getContext('2d');
        volumeChart = new Chart(volumeCtx, {
            type: 'line', 
            data: {
                labels: [], 
                datasets: [{
                    label: 'Volume', 
                    data: [], 
                    borderColor: '#28a745', 
                    backgroundColor: 'rgba(40, 167, 69, 0.1)', 
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
                            text: 'Volume (dBFS)'
                        }
                    }
                }
            }
        });

        // Pitch Chart 
        const pitchCtx = document.getElementById('pitchChart').getContext('2d');
        pitchChart = new Chart(pitchCtx, {
            type: 'line', 
            data: {
                labels: [], 
                datasets: [{
                    label: 'Pitch Variance', 
                    data: [], 
                    borderColor: '#dc3545', 
                    backgroundColor: 'rgba(220, 53, 69, 0.1)', 
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
                            text: 'Pitch Variance (Hz)'
                        }
                    }
                }
            }
        });
    }

    // Update charts with new data 
    function updateCharts(wpm, volume, pitch) {
        if (!startTime) return;
        
        // Calculates time since recording staretd
        const currentTime = Math.floor((Date.now() - startTime) / 1000);

        // Add new data points to the end of arrays
        wpmData.push(wpm);
        volumeData.push(volume);
        pitchData.push(pitch);
        timeLabels.push(currentTime);

        // Keep last 50 data points for performance
        const maxPoints = 5; 
        if (wpmData.length > maxPoints) {
            // Shift removes the first (oldest) element
            wpmData.shift(); 
            volumeData.shift(); 
            pitchData.shift(); 
            timeLabels.shift(); 
        }

        console.log('Updating charts with:', { wpm, volume, pitch, currentTime });

        if (wpmChart) {
            wpmChart.data.labels = timeLabels;        // Updates the x axis with the time array 
            wpmChart.data.datasets[0].data = wpmData; // Updates the y axis with the WPM value
            wpmChart.update('none');                  // Redraws the chart with new data 
        }

        if (volumeChart) {
            volumeChart.data.labels = timeLabels; 
            volumeChart.data.datasets[0].data = volumeData; 
            volumeChart.update('none'); 
        }

        if (pitchChart) {
            pitchChart.data.labels = timeLabels; 
            pitchChart.data.datasets[0].data = pitchData; 
            pitchChart.update('none'); 
        }
    }

    // Reset charts 
    function resetCharts() {
        wpmData = []; 
        volumeData = []; 
        pitchData = []; 
        timeLabels = []; 
        startTime = null; 

        if (wpmChart) {
            wpmChart.data.labels = []; 
            wpmChart.data.datasets[0].data = []; 
            wpmChart.update(); 
        }

        if (volumeChart) {
            volumeChart.data.labels = []; 
            volumeChart.data.datasets[0].data = []; 
            volumeChart.update(); 
        }

        if (pitchChart) {
            pitchChart.data.labels = []; 
            pitchChart.data.datasets[0].data = []; 
            pitchChart.update(); 
        }
    }

    function pollTranscript(){
        fetch('/get_live_transcript')
        .then(response => response.json())
        .then(data => {
            transcriptBox.textContent = data.transcript; 
        });
    }

    function pollMetrics() {
        fetch('/get_live_metrics')
        .then(response => response.json())
        .then(data => {
            console.log('Received metrics:', data);
            wpmValue.textContent = data.wpm.toFixed(2)
            volumeValue.textContent = data.volume.toFixed(2)
            pitchValue.textContent = data.pitch.toFixed(2)
            
            // Update charts with new data only if not paused
            if (!isPaused) {
                updateCharts(data.wpm, data.volume, data.pitch);
            } else {
                console.log('Recording is paused, skipping chart update');
            }
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
        });
    }

    function togglePauseResume() {
        const btn = document.getElementById('pauseResumeBtn');
        if (!isPaused) {
            pauseRecording();
        } else {
            resumeRecording(); 
        }
    }

    function updateMetricsDisplay() {
        if (metricsMode === "live") {
            // Update the labels
            document.getElementById('wpm-label').textContent = 'Words per Minute';
            document.getElementById('volume-label').textContent = 'Volume (dBFS)';
            document.getElementById('pitch-label').textContent = 'Pitch Variance (Hz)';
        } else {
            // Update the labels
            document.getElementById('wpm-label').textContent = 'Average Words per Minute';
            document.getElementById('volume-label').textContent = 'Average Volume (dBFS)';
            document.getElementById('pitch-label').textContent = 'Average Pitch Variance (Hz)';
        }
    }

    function pauseRecording(){
        fetch('/pause_recording', {method: 'POST'})
        .then(response => {
            if (response.ok) {
                isPaused = true; 
                document.getElementById('pauseResumeBtn').textContent = "Resume";
            } else {
                alert ("Failed to pause recording.");
            }
        })
        .catch(error => {
            console.error("Error pausing:", error);
            alert("Error pausing recording.");
        });
    }

    function resumeRecording(){
        fetch('/resume_recording', {method: 'POST'})
        .then(response => {
            if (response.ok) {
                isPaused = false; 
                document.getElementById('pauseResumeBtn').textContent = "Pause"
            } else {
                alert("Failed to resume recording.");
            }
        })
        .catch(error => {
            console.error("Error resuming:", error);
            alert("Error resuming recording.");
        });
    }

    // Add a click event listener to the Start Recording button 
    // - structure wise, the function can be deigined separately for clarity and modularity
    startBtn.addEventListener('click', function(){
        metricsMode = "live"
        updateMetricsDisplay();

        // Initialize charts and reset data
        initialiseCharts();
        resetCharts(); 

        startTime = Date.now();
        console.log('Recording started, startTime:', startTime);

        // Sends a POST request to Flask backend after a click to /start_recording
        // - use fetch to communicate with the Flask backend 
        // - method can be GET, POST, PUT, DELETE, etc. 
    
        fetch('/start_recording', {method: 'POST'})

        // Wait for Flask response and parse it as JSON 
        .then(response => response.json())

        // Update the transcript box with the status from the Flask response 
        .then(data => {
            transcriptBox.textContent = data.status;
            if (!transcriptInterval && !metricsInterval) {
                // Poll for updates every 3 seconds 
                transcriptInterval = setInterval(pollTranscript, 1500);
                metricsInterval = setInterval(pollMetrics, 6000);
            }
        })

        // If there's an error, update the transcript box with an error message 
        .catch(error => {transcriptBox.textContent = 'Error starting recording.';
            console.error('Error starting recording:', error);
        });
    });

    if (stopBtn) {
        stopBtn.addEventListener('click', function(){
            metricsMode = "average"
            updateMetricsDisplay();

            fetch('/stop_recording', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                transcriptBox.textContent = data.status;
                
                if (transcriptInterval) {
                    clearInterval(transcriptInterval);
                    transcriptInterval = null;
                }
                
                if (metricsInterval) {
                    clearInterval(metricsInterval);
                    metricsInterval = null;
                }

                // Reset charts when stopping 
                resetCharts(); 

                // Fetch the final transcript and metrics 
                fetch('/get_final_transcript')
                .then(response => response.json())
                .then(data => {
                    transcriptBox.textContent = data.transcript; 
                });

                fetch('/get_average_metrics')
                .then(response => response.json())
                .then(data => {
                    // Update the values 
                    wpmValue.textContent = data.average_wpm.toFixed(2);
                    volumeValue.textContent = data.average_volume.toFixed(2);
                    pitchValue.textContent = data.average_pitch.toFixed(2);
                });
            })
            .catch(error => {
                transcriptBox.textContent = 'Error stopping recording.';
                console.error('Error stopping recording:', error);
            });
        });
    }

    document.getElementById('pauseResumeBtn').addEventListener('click', togglePauseResume);

    // Maybe add a non existent route error handling 
    // If JS requests non-existent route
    // fetch('/nonexistent_route')
    // .then(response => {
    // if (!response.ok) {
    //     console.log('Error:', response.status); // 404
    // }
    // });
});