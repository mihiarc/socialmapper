/**
 * MapSelector Component - Interactive location selection with Mapbox
 * Allows users to search by address or click on map to select locations
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Card, Input, Button, List, Typography, Space, Spin, message } from 'antd';
import { SearchOutlined, EnvironmentOutlined, AimOutlined } from '@ant-design/icons';
import mapboxgl from 'mapbox-gl';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateConfiguration } from '@/store/slices/analysisSlice';
import type { LocationSearchResult } from '@/types/api';

const { Title, Text } = Typography;
const { Search } = Input;

// Mapbox access token should be set via environment variable
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

interface MapSelectorProps {
  onLocationSelect?: (location: LocationSearchResult) => void;
  selectedLocation?: string;
}

/**
 * Interactive map component for location selection
 * Features address search, click-to-select, and popular location suggestions
 */
const MapSelector: React.FC<MapSelectorProps> = ({
  onLocationSelect,
  selectedLocation
}) => {
  const dispatch = useAppDispatch();
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const marker = useRef<mapboxgl.Marker | null>(null);
  
  const [searchResults, setSearchResults] = useState<LocationSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Popular location suggestions
  const popularLocations: LocationSearchResult[] = [
    {
      display_name: 'New York City, NY, USA',
      city: 'New York City',
      state: 'NY',
      country: 'USA',
      latitude: 40.7128,
      longitude: -74.0060,
      importance: 0.9,
      place_type: 'city'
    },
    {
      display_name: 'San Francisco, CA, USA',
      city: 'San Francisco',
      state: 'CA', 
      country: 'USA',
      latitude: 37.7749,
      longitude: -122.4194,
      importance: 0.8,
      place_type: 'city'
    },
    {
      display_name: 'Chicago, IL, USA',
      city: 'Chicago',
      state: 'IL',
      country: 'USA', 
      latitude: 41.8781,
      longitude: -87.6298,
      importance: 0.8,
      place_type: 'city'
    },
    {
      display_name: 'Austin, TX, USA',
      city: 'Austin',
      state: 'TX',
      country: 'USA',
      latitude: 30.2672,
      longitude: -97.7431,
      importance: 0.7,
      place_type: 'city'
    }
  ];

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    if (!MAPBOX_TOKEN) {
      message.error('Mapbox token not configured. Please set VITE_MAPBOX_TOKEN environment variable.');
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-98.5795, 39.8283], // Geographic center of US
      zoom: 4,
      // Enable touch interactions for mobile
      touchZoomRotate: true,
      touchPitch: false,
      dragRotate: false
    });

    // Add navigation controls with compact option for mobile
    map.current.addControl(
      new mapboxgl.NavigationControl({
        showCompass: false,
        visualizePitch: false
      }),
      window.innerWidth <= 768 ? 'bottom-right' : 'top-right'
    );

    // Add geolocate control for mobile
    if (window.innerWidth <= 768) {
      map.current.addControl(
        new mapboxgl.GeolocateControl({
          positionOptions: {
            enableHighAccuracy: true
          },
          trackUserLocation: false,
          showUserHeading: false
        }),
        'bottom-right'
      );
    }

    // Handle map clicks for location selection
    map.current.on('click', (e) => {
      const { lng, lat } = e.lngLat;
      handleMapClick(lat, lng);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update bounding box visual on map
  const updateBoundingBoxVisual = useCallback((bounds: [number, number, number, number]) => {
    if (!map.current) return;
    
    const sourceId = 'bounding-box';
    const layerId = 'bounding-box-fill';
    
    const [minLng, minLat, maxLng, maxLat] = bounds;
    
    const data = {
      type: 'Feature' as const,
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[
          [minLng, minLat],
          [maxLng, minLat],
          [maxLng, maxLat],
          [minLng, maxLat],
          [minLng, minLat]
        ]]
      },
      properties: {}
    };
    
    if (map.current.getSource(sourceId)) {
      (map.current.getSource(sourceId) as mapboxgl.GeoJSONSource).setData(data);
    } else {
      map.current.addSource(sourceId, {
        type: 'geojson',
        data: data
      });
      
      map.current.addLayer({
        id: layerId,
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': '#1890ff',
          'fill-opacity': 0.2
        }
      });
      
      map.current.addLayer({
        id: 'bounding-box-outline',
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#1890ff',
          'line-width': 2
        }
      });
    }
  }, []);

  // Handle map click location selection
  const handleMapClick = useCallback(async (lat: number, lng: number) => {
    try {
      // Reverse geocoding to get address from coordinates
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${lng},${lat}.json?access_token=${MAPBOX_TOKEN}&types=place,locality,neighborhood`
      );
      const data = await response.json();
      
      if (data.features && data.features.length > 0) {
        const feature = data.features[0];
        const location: LocationSearchResult = {
          display_name: feature.place_name,
          city: feature.context?.find((c: any) => c.id.startsWith('place'))?.text,
          state: feature.context?.find((c: any) => c.id.startsWith('region'))?.text,
          country: feature.context?.find((c: any) => c.id.startsWith('country'))?.text || 'USA',
          latitude: lat,
          longitude: lng,
          importance: 0.5,
          place_type: feature.place_type?.[0]
        };
        
        selectLocation(location);
      }
    } catch (error) {
      console.error('Reverse geocoding failed:', error);
      message.error('Failed to get location details');
    }
  }, []);

  // Search for locations using Mapbox Geocoding API
  const searchLocations = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&country=US&types=place,locality,neighborhood,address&limit=5`
      );
      const data = await response.json();
      
      if (data.features) {
        const results: LocationSearchResult[] = data.features.map((feature: any) => ({
          display_name: feature.place_name,
          city: feature.context?.find((c: any) => c.id.startsWith('place'))?.text,
          state: feature.context?.find((c: any) => c.id.startsWith('region'))?.text,
          country: feature.context?.find((c: any) => c.id.startsWith('country'))?.text || 'USA',
          latitude: feature.center[1],
          longitude: feature.center[0],
          importance: feature.relevance,
          place_type: feature.place_type?.[0]
        }));
        
        setSearchResults(results);
      }
    } catch (error) {
      console.error('Location search failed:', error);
      message.error('Location search failed');
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Select a location and update map/state
  const selectLocation = useCallback((location: LocationSearchResult) => {
    // Update Redux state
    dispatch(updateConfiguration({ 
      location: location.display_name 
    }));

    // Update map view
    if (map.current) {
      map.current.flyTo({
        center: [location.longitude, location.latitude],
        zoom: 12
      });

      // Remove existing marker
      if (marker.current) {
        marker.current.remove();
      }

      // Add new marker
      marker.current = new mapboxgl.Marker({
        color: '#1890ff'
      })
        .setLngLat([location.longitude, location.latitude])
        .addTo(map.current);
    }

    // Clear search results
    setSearchResults([]);
    setSearchQuery('');

    // Callback to parent component
    onLocationSelect?.(location);
    
    message.success(`Location selected: ${location.display_name}`);
  }, [dispatch, onLocationSelect]);

  // Get user's current location
  const getCurrentLocation = useCallback(() => {
    if (!navigator.geolocation) {
      message.error('Geolocation is not supported by this browser');
      return;
    }

    message.loading('Getting your location...', 0);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        message.destroy();
        const { latitude, longitude } = position.coords;
        handleMapClick(latitude, longitude);
      },
      (error) => {
        message.destroy();
        message.error('Failed to get your location');
        console.error('Geolocation error:', error);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  }, [handleMapClick]);

  return (
    <div className="map-selector">
      <Title level={4}>Select Location</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        Search for an address, click on the map, or choose from popular locations
      </Text>

      <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
        <Search
          placeholder="Search for an address or place..."
          prefix={<SearchOutlined />}
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            searchLocations(e.target.value);
          }}
          loading={isSearching}
          style={{ marginBottom: 8 }}
        />

        <Button 
          type="dashed" 
          icon={<AimOutlined />} 
          onClick={getCurrentLocation}
          style={{ alignSelf: 'flex-start' }}
        >
          Use My Current Location
        </Button>
      </Space>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <Card 
          size="small" 
          style={{ marginBottom: 16, maxHeight: 200, overflow: 'auto' }}
          title="Search Results"
        >
          <List
            size="small"
            dataSource={searchResults}
            renderItem={(location) => (
              <List.Item
                actions={[
                  <Button 
                    type="link" 
                    size="small"
                    onClick={() => selectLocation(location)}
                  >
                    Select
                  </Button>
                ]}
              >
                <List.Item.Meta
                  avatar={<EnvironmentOutlined />}
                  title={location.display_name}
                  description={`${location.city ? location.city + ', ' : ''}${location.state}`}
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* Map Container - Mobile Responsive */}
      <Card 
        style={{ marginBottom: 16 }}
        title="Interactive Map"
        extra={selectedLocation && (
          <Text type="success" style={{ 
            fontSize: window.innerWidth <= 576 ? '12px' : '14px',
            display: 'block',
            maxWidth: window.innerWidth <= 576 ? '150px' : 'auto',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {selectedLocation}
          </Text>
        )}
      >
        <div 
          ref={mapContainer}
          style={{ 
            width: '100%', 
            height: window.innerWidth <= 576 ? '300px' : '400px',
            borderRadius: '6px',
            touchAction: 'none' // Better touch handling on mobile
          }}
        />
        {window.innerWidth <= 576 && (
          <Text type="secondary" style={{ 
            fontSize: '11px', 
            marginTop: '8px',
            display: 'block',
            textAlign: 'center'
          }}>
            Tap on the map or use search to select a location
          </Text>
        )}
      </Card>

      {/* Popular Locations - Mobile Optimized */}
      <Card 
        title="Popular Locations" 
        size="small"
        bodyStyle={{ padding: window.innerWidth <= 576 ? '8px' : '16px' }}
      >
        <List
          grid={{ 
            gutter: window.innerWidth <= 576 ? 4 : 8, 
            xs: 1, 
            sm: 2, 
            md: 2 
          }}
          size="small"
          dataSource={popularLocations}
          renderItem={(location) => (
            <List.Item style={{ marginBottom: window.innerWidth <= 576 ? '4px' : '8px' }}>
              <Button
                type="text"
                icon={<EnvironmentOutlined />}
                onClick={() => selectLocation(location)}
                style={{ 
                  width: '100%', 
                  textAlign: 'left', 
                  height: 'auto',
                  whiteSpace: 'normal',
                  fontSize: window.innerWidth <= 576 ? '12px' : '14px',
                  padding: window.innerWidth <= 576 ? '4px 8px' : '4px 15px'
                }}
              >
                {location.display_name}
              </Button>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default React.memo(MapSelector);