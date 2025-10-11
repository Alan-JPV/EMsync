import requests
import json
import folium       # Library for creating interactive maps
import polyline     # Library to decode the route geometry

def get_fastest_route(api_key, start_coords, end_coords):
    """
    Fetches the fastest route from the OpenRouteService API.
    (This function is the same as before)
    """
    base_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
    body = {'coordinates': [start_coords, end_coords]}
    
    try:
        response = requests.post(base_url, headers=headers, data=json.dumps(body))
        if response.status_code == 200:
            print("✅ Successfully fetched route from ORS API.")
            return response.json()
        else:
            print(f"❌ Error fetching route. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# --- Main part of the script ---
if __name__ == "__main__":
    
    # --- CONFIGURATION ---
    ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImQ2MTEwMDY3MDU4ZTQxNjQ5M2JjODAwMDc5N2NmMjNlIiwiaCI6Im11cm11cjY0In0=" 
    start_point = (76.2828, 10.0815) # Varapuzha (lon, lat)
    end_point = (76.3053, 10.0535)   # Aster Medcity (lon, lat)
    
    # --- EXECUTION ---
    route_data = get_fastest_route(ORS_API_KEY, start_point, end_point)
    
    # --- PROCESSING & VISUALIZATION ---
    if route_data:
        # --- Extract the route geometry ---
        # The API returns the route as an encoded polyline string.
        encoded_polyline = route_data['routes'][0]['geometry']
        
        # Decode the polyline string into a list of [lat, lon] coordinates.
        # The polyline library decodes to (lat, lon) which is what folium needs.
        decoded_route = polyline.decode(encoded_polyline)

        # --- Create the map ---
        # Create a map object, centered at our starting point.
        # The location for Folium maps must be in (latitude, longitude) format.
        map_center = (start_point[1], start_point[0])
        route_map = folium.Map(location=map_center, zoom_start=14)

        # --- Add Markers for Start and End Points ---
        # Marker for the starting point (Ambulance location)
        folium.Marker(
            location=(start_point[1], start_point[0]),
            popup="Start: Varapuzha",
            icon=folium.Icon(color='green', icon='play')
        ).add_to(route_map)

        # Marker for the ending point (Hospital)
        folium.Marker(
            location=(end_point[1], end_point[0]),
            popup="End: Aster Medcity",
            icon=folium.Icon(color='red', icon='hospital-o', prefix='fa') # Using a Font-Awesome icon
        ).add_to(route_map)

        # --- Draw the Route on the Map ---
        # Create a PolyLine object with the decoded route coordinates.
        folium.PolyLine(
            locations=decoded_route,
            color='blue',
            weight=5,
            opacity=0.8
        ).add_to(route_map)

        # --- Save the Map to an HTML File ---
        # Save the map, which can be opened in any web browser.
        route_map.save("route_map.html")
        print("💾 Map has been saved to 'route_map.html'.")