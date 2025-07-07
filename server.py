from flask import Flask, render_template, jsonify, request 

# The Flask App 
# - it provides data and handles actions via API endpoints (seen below)
# - (1) The frontend uses JavaScript to make API requests to the Flask endpoints 
# - (2) The backend responds with JSON data
# - (3) Front end uses this data to update the UI 

# Example: Start Recording
# - (1) Frontend (JavaScript)sends POST request to /start_recording
# - (2) Backend (Flask) processes the request and returns JSON data
# - (3) Frontend (JavaScript) uses this data to update the UI 

# Example 2: Live Transcript:
# - (1) Frontend (JavaScript) periodically sends GET requests to /get_transcript
# - (2) Backend (Flask) responds with JSON data containing the live transcript
# - (3) Frontend (JavaScript) uses this data to update the UI 

# Creates an instance of the Flask class (aka application)
app = Flask(__name__)

# Defines a route for the route URL "/"
# - when a user visits the "/" URL, call the home() function 
# - under the hood Flask keeps a mapping or URLs to Python functions 
@app.route('/')
def home():
    return render_template("index.html") # Serves the html page 

@app.route("/start_recording", methods=['POST'])
def start_recordng():
    return jsonify({'status': 'Recording started...'})

@app.route("/stop_recording", methods=['POST'])
def stop_recording():
    return jsonify({'status': 'Recording stopped...'})

@app.route("/get_transcript")
def get_transcript():
    return jsonify(({'transcript': 'Live transcript:'}))

@app.route("/get_metrics")
def get_metrics():
    return jsonify({'wpm': 0, 'volume': 0, 'pitch': 0})

if __name__ == "__main__":
    app.run(debug=True) # Starts the Flask application in debug mode

# Flask will need to serve an HTML file, as well as request and display the metrics data 