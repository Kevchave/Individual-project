// This enres the JS code only runs once the HTML is fully loaded 
document.addEventListener('DOMContentLoaded', function(){
    // Get references to the HTML elements 
    const startBtn = document.getElementById('startBtn');
    const transcriptBox = document.getElementById('transcript-box');

    // Add a click event listener to the Start Recording button 
    startBtn.addEventListener('click', function(){
        // Sends a POST request to Flask backend after a click to /start_recording
        // - use fetch to communicate with the Flask backend 
        // - method can be GET, POST, PUT, DELETE, etc. 
        fetch('/start_recording', {method: 'POST'})

        // Wait for Flask response and parse it as JSON 
        .then(response => response.json())

        // Update the transcript box with the status from the Flask response 
        .then(data => {transcriptBox.textContent = data.status;})

        // If there's an error, update the transcript box with an error message 
        .catch(error => {transcriptBox.textContent = 'Error starting recording.';
            console.error('Error starting recording:', error);
        });
    })
});
