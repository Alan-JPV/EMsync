# Import necessary libraries
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json       # <-- FIX 1: Import the json library
import polyline   # <-- FIX 2: Import the polyline library

load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")

app = Flask(__name__)
CORS(app)

def get_route_from_ors(start_coords, end_coords):
    if not ORS_API_KEY:
        return {"error": "API key not found."}
    base_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {'Authorization': ORS_API_KEY, 'Content-Type': 'application/json'}
    body = {'coordinates': [start_coords, end_coords]}
    
    try:
        response = requests.post(base_url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching route: {e}")
        return None

@app.route('/api/get_route', methods=['POST'])
def handle_get_route():
    data = request.get_json()
    if not data or 'start' not in data or 'end' not in data:
        return jsonify({"error": "Invalid request body."}), 400

    start_point = data['start']
    end_point = data['end']
    route_data = get_route_from_ors(start_point, end_point)

    if route_data and "error" not in route_data:
        # --- FIX 3: Decode the route here in the backend ---
        encoded_polyline = route_data['routes'][0]['geometry']
        # The polyline library decodes to (lat, lon) format, perfect for Leaflet
        decoded_route = polyline.decode(encoded_polyline)
        
        # Add the decoded route to our response
        route_data['decoded_route'] = decoded_route
        return jsonify(route_data)
    else:
        return jsonify({"error": "Failed to fetch route."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)