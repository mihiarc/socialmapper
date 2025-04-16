import folium
import geopandas as gpd
import yaml
from pathlib import Path

def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_isochrone_map(isochrone_dir: str, poi: dict, time_limits: list) -> folium.Map:
    """Create an interactive map with isochrones and POI."""
    # Create base map centered on POI
    m = folium.Map(
        location=[poi['latitude'], poi['longitude']],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Add POI marker
    folium.Marker(
        [poi['latitude'], poi['longitude']],
        popup=poi['name'],
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Color scheme for different isochrones
    colors = {
        30: '#ff0000',   # Red for 30 minutes
        60: '#ffa500',   # Orange for 60 minutes
        90: '#ffff00',   # Yellow for 90 minutes
        120: '#00ff00'   # Green for 120 minutes
    }
    
    # Add each isochrone to the map
    for time_limit in time_limits:
        isochrone_file = Path(isochrone_dir) / f'isochrone{time_limit}_walmart.geojson'
        if isochrone_file.exists():
            gdf = gpd.read_file(isochrone_file)
            
            # Convert to WGS84 for folium
            gdf = gdf.to_crs('EPSG:4326')
            
            # Add isochrone to map
            folium.GeoJson(
                gdf,
                style_function=lambda x: {
                    'fillColor': colors[time_limit],
                    'color': colors[time_limit],
                    'fillOpacity': 0.2,
                    'weight': 2
                },
                name=f'{time_limit} minutes',
                tooltip=f'Area reachable within {time_limit} minutes'
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def main():
    # Load configuration
    config = load_config()
    
    # Get settings
    settings = config['isochrone_settings']
    poi = config['point_of_interest']
    time_limits = settings['travel_time_limits']
    
    # Create map
    m = create_isochrone_map(settings['output_dir'], poi, time_limits)
    
    # Save map
    output_file = 'isochrone_map.html'
    m.save(output_file)
    print(f"Map saved as {output_file}")

if __name__ == "__main__":
    main() 