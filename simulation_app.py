# Import the necessary libraries
import streamlit as st
import folium
import polyline
import requests
import json
import time
from streamlit_folium import st_folium

# --- Caching the API Function ---
@st.cache_data
def get_fastest_route(api_key, start_coords, end_coords):
    st.info("Fetching new route from OpenRouteService API...")
    base_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
    body = {'coordinates': [start_coords, end_coords]}
    
    try:
        response = requests.post(base_url, headers=headers, data=json.dumps(body))
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: Status {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: {e}")
        return None

# --- Main App ---

st.set_page_config(page_title="EMsync Simulation", layout="wide")

# --- UI Sidebar ---
with st.sidebar:
    st.header("🚑 EMsync Controls")
    
    locations = {"Varapuzha": (76.2828, 10.0815), "Edappally": (76.3115, 10.0248), "Kaloor": (76.2996, 9.9984)}
    
    # --- UPDATED HOSPITAL COORDINATES ---
    # Using the new coordinates you provided.
    hospitals = {
        "Aster Medcity": (76.27745, 10.04348),
        "Lourdes Hospital": (76.27742, 10.00668),
        "Amrita Hospital": (76.29250, 10.03264)
    }

    start_name = st.selectbox("Start Location", list(locations.keys()))
    end_name = st.selectbox("Destination Hospital", list(hospitals.keys()))

    start_point = locations[start_name]
    end_point = hospitals[end_name]

    st.divider()

    if 'simulation_started' not in st.session_state:
        st.session_state.simulation_started = False
        st.session_state.route_index = 0

    if st.button("▶️ Start Simulation"):
        st.session_state.simulation_started = True
        st.session_state.route_index = 0
    
    if st.button("⏹️ Reset"):
        st.session_state.simulation_started = False
        st.session_state.route_index = 0

# --- Main Panel: Map and Title ---
st.title("Live Ambulance Routing Simulation")

ORS_API_KEY = st.secrets["ORS_API_KEY"]
route_data = get_fastest_route(ORS_API_KEY, start_point, end_point)

if route_data:
    encoded_polyline = route_data['routes'][0]['geometry']
    decoded_route = polyline.decode(encoded_polyline)
    summary = route_data['routes'][0]['summary']
    distance_km = summary['distance'] / 1000
    duration_min = summary['duration'] / 60

    with st.sidebar:
        st.subheader("Route Details")
        st.metric("Distance", f"{distance_km:.2f} km")
        st.metric("Duration", f"{duration_min:.2f} min")
        
        is_complete = st.session_state.route_index >= len(decoded_route) - 1
        if st.session_state.simulation_started and not is_complete:
            st.info("Simulation in Progress...")
        elif is_complete:
             st.success("Simulation Complete!")
        else:
            st.info("Simulation Idle.")
        
    map_center = (start_point[1], start_point[0])
    route_map = folium.Map(location=map_center, zoom_start=13, tiles="cartodbpositron")

    folium.Marker(location=(start_point[1], start_point[0]), popup=start_name, icon=folium.Icon(color='green', icon='play')).add_to(route_map)
    folium.Marker(location=(end_point[1], end_point[0]), popup=end_name, icon=folium.Icon(color='red', icon='hospital-o', prefix='fa')).add_to(route_map)
    folium.PolyLine(locations=decoded_route, color='blue', weight=5).add_to(route_map)

    current_index = st.session_state.route_index
    
    if current_index >= len(decoded_route) - 1:
        current_index = len(decoded_route) - 1
        st.session_state.simulation_started = False

    current_coords = decoded_route[current_index]
    folium.Marker(location=current_coords, popup="Ambulance", icon=folium.Icon(color='orange', icon='ambulance', prefix='fa')).add_to(route_map)
    
    st_folium(route_map, width=1200, height=600, returned_objects=[])

    '''if current_index >= len(decoded_route) - 1:
        st.subheader("Mission Summary & Patient Report")
        
        # Mock data simulating your AI model's output
        severity = "Critical"
        icu_destination = "Medical ICU (MICU)"
        resource_needs = ["Ventilator", "Vasopressors"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Predicted Patient Severity", severity)
        with col2:
            st.metric("Suggested ICU Destination", icu_destination)
        with col3:
            st.metric("Predicted Resource Needs", ", ".join(resource_needs))
'''
    if st.session_state.simulation_started:
        st.session_state.route_index += 1 
        time.sleep(0.01)
        st.rerun()
else:
    st.warning("Could not fetch route.")