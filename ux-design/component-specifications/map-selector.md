# MapSelector Component Specification
## Project 1.2 - Interactive Location Selection Component

**Date**: August 10, 2025  
**Component Type**: Interactive Map + Search Interface  
**Priority**: Critical Path - Step 1 of QueryWizard  
**Integration**: React + Mapbox GL + Geocoding API + Accessibility

---

## Component Overview

The MapSelector component provides an intuitive, accessible interface for selecting analysis locations. It combines interactive map functionality with search capabilities, smart suggestions, and clear visual feedback to help users confidently choose their analysis area.

### Success Criteria
- **90%+ location selection success rate** for first-time users
- **<30 seconds average** location selection time
- **Clear confidence indicators** for geocoding results
- **Full keyboard accessibility** for screen reader users

---

## Component Interface

### TypeScript Interface

```typescript
interface MapSelectorProps {
  // Value and change handling
  value?: LocationValue | null;
  onChange: (location: LocationValue) => void;
  onAreaChange?: (area: number, population: number) => void;
  
  // Configuration
  placeholder?: string;
  showPopularLocations?: boolean;
  showRecentLocations?: boolean;
  maxSuggestions?: number;
  
  // Map configuration
  initialCenter?: [number, number]; // [lng, lat]
  initialZoom?: number;
  bounds?: BoundingBox;
  height?: string | number;
  
  // Features
  allowBoundingBoxSelection?: boolean;
  showDataAvailabilityIndicator?: boolean;
  showPopulationEstimate?: boolean;
  
  // Accessibility
  accessibilityLabel?: string;
  alternativeInterface?: boolean;
  
  // Styling
  className?: string;
  style?: React.CSSProperties;
}

interface LocationValue {
  // Basic location info
  address: string;
  displayName: string;
  coordinates: [number, number]; // [lng, lat]
  
  // Geographic bounds
  boundingBox: BoundingBox;
  center: [number, number];
  
  // Metadata
  confidence: GeocodeConfidence;
  placeType: PlaceType;
  country: string;
  state?: string;
  city?: string;
  
  // Analysis context
  estimatedArea?: number; // square kilometers
  estimatedPopulation?: number;
  dataAvailable?: boolean;
  censusGeographies?: string[]; // Available geographic levels
}

type GeocodeConfidence = 'high' | 'medium' | 'low';
type PlaceType = 'address' | 'street' | 'neighborhood' | 'city' | 'county' | 'state' | 'postal_code';

interface BoundingBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

interface PopularLocation {
  id: string;
  name: string;
  displayName: string;
  coordinates: [number, number];
  category: 'urban' | 'suburban' | 'rural' | 'university';
  usageCount: number;
  lastUsed?: string;
}
```

---

## Visual Design Specification

### Component Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Search Location                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔍 Enter city, address, or ZIP code                    │ │
│ │                                           [Clear] [📍] │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Popular Locations:                                          │
│ [Denver, CO] [Austin, TX] [Portland, OR] [Atlanta, GA]      │
│                                                             │
│ ┌─────────── Interactive Map (400px height) ─────────────┐  │
│ │                                                        │  │
│ │  • Click anywhere to select location                  │  │
│ │  • Drag to pan, scroll to zoom                        │  │
│ │  • Search results highlighted in blue                 │  │
│ │  • Selected area outlined with dashed border          │  │
│ │                                                        │  │
│ │  ┌─ Map Controls ─┐                                   │  │
│ │  │ [+] Zoom In    │                                   │  │
│ │  │ [-] Zoom Out   │                                   │  │
│ │  │ [📍] My Location│                                   │  │
│ │  │ [⚙️] Layer      │                                   │  │
│ │  └───────────────┘                                   │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ Selection Summary ─────────────────────────────────────┐ │
│ │ ✅ Selected: Denver, Colorado                           │ │
│ │    Confidence: High (exact city match)                 │ │
│ │    Analysis area: ~180 square miles                    │ │
│ │    Estimated population: ~2.8M people                  │ │
│ │    📊 Good data availability                           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Alternative: [Enter coordinates manually]                   │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout
```
┌─────────────────────┐
│ Search Location     │
│ ┌─────────────────┐ │
│ │🔍 Enter city... │ │
│ └─────────────────┘ │
│                     │
│ Popular:            │
│ [Denver] [Austin]   │
│ [Portland] [More]   │
│                     │
│ ┌─── Map (300px) ─┐ │
│ │                 │ │
│ │   Touch to      │ │
│ │   select        │ │
│ │                 │ │
│ │  [+][-][📍]     │ │
│ └─────────────────┘ │
│                     │
│ ✅ Denver, CO       │
│ ~180 sq miles       │
│ ~2.8M people        │
│                     │
│ [Text Input Mode]   │
└─────────────────────┘
```

---

## Interactive Map Implementation

### Mapbox Integration

```typescript
import MapboxGL from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapboxMapProps {
  center: [number, number];
  zoom: number;
  onLocationSelect: (coordinates: [number, number]) => void;
  selectedLocation?: LocationValue;
  searchResults?: LocationSearchResult[];
  height: string | number;
  accessibilityLabel?: string;
}

const MapboxMap: React.FC<MapboxMapProps> = ({
  center,
  zoom,
  onLocationSelect,
  selectedLocation,
  searchResults,
  height,
  accessibilityLabel = "Interactive location selection map"
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<MapboxGL.Map | null>(null);
  
  useEffect(() => {
    if (!mapContainer.current) return;

    // Initialize Mapbox map
    map.current = new MapboxGL.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11', // Accessible light theme
      center,
      zoom,
      accessToken: process.env.REACT_APP_MAPBOX_TOKEN
    });

    // Add accessibility features
    map.current.addControl(new MapboxGL.NavigationControl(), 'top-right');
    map.current.addControl(new MapboxGL.GeolocateControl({
      positionOptions: { enableHighAccuracy: true },
      trackUserLocation: true,
      showUserHeading: true
    }), 'top-right');

    // Handle click events
    map.current.on('click', (e) => {
      const coordinates: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      onLocationSelect(coordinates);
    });

    // Keyboard navigation
    map.current.getCanvasContainer().addEventListener('keydown', (e) => {
      handleMapKeyNavigation(e, map.current!);
    });

    return () => map.current?.remove();
  }, []);

  // Update map when props change
  useEffect(() => {
    if (map.current && selectedLocation) {
      updateSelectedLocationDisplay(map.current, selectedLocation);
    }
  }, [selectedLocation]);

  return (
    <div 
      ref={mapContainer}
      style={{ height }}
      role="application"
      aria-label={accessibilityLabel}
      tabIndex={0}
    />
  );
};

// Keyboard navigation for accessibility
const handleMapKeyNavigation = (e: KeyboardEvent, map: MapboxGL.Map) => {
  const panDistance = 0.01; // degrees
  const center = map.getCenter();

  switch (e.key) {
    case 'ArrowUp':
      e.preventDefault();
      map.setCenter([center.lng, center.lat + panDistance]);
      break;
    case 'ArrowDown':
      e.preventDefault();
      map.setCenter([center.lng, center.lat - panDistance]);
      break;
    case 'ArrowLeft':
      e.preventDefault();
      map.setCenter([center.lng - panDistance, center.lat]);
      break;
    case 'ArrowRight':
      e.preventDefault();
      map.setCenter([center.lng + panDistance, center.lat]);
      break;
    case '+':
    case '=':
      e.preventDefault();
      map.zoomIn();
      break;
    case '-':
      e.preventDefault();
      map.zoomOut();
      break;
    case 'Enter':
    case ' ':
      e.preventDefault();
      // Select current center point
      const coords: [number, number] = [center.lng, center.lat];
      // Trigger selection callback
      break;
  }
};
```

### Visual Indicators

```typescript
const updateSelectedLocationDisplay = (map: MapboxGL.Map, location: LocationValue) => {
  // Clear existing selection
  if (map.getLayer('selected-area')) {
    map.removeLayer('selected-area');
    map.removeSource('selected-area');
  }

  // Add bounding box visualization
  const bbox = location.boundingBox;
  const coordinates = [[
    [bbox.west, bbox.north],
    [bbox.east, bbox.north],
    [bbox.east, bbox.south],
    [bbox.west, bbox.south],
    [bbox.west, bbox.north]
  ]];

  map.addSource('selected-area', {
    type: 'geojson',
    data: {
      type: 'Feature',
      properties: {
        confidence: location.confidence
      },
      geometry: {
        type: 'Polygon',
        coordinates
      }
    }
  });

  // Style based on confidence
  const borderColor = {
    high: '#52c41a',    // Green for high confidence
    medium: '#fa8c16',  // Orange for medium confidence  
    low: '#ff4d4f'      // Red for low confidence
  }[location.confidence];

  map.addLayer({
    id: 'selected-area',
    type: 'line',
    source: 'selected-area',
    paint: {
      'line-color': borderColor,
      'line-width': 3,
      'line-dasharray': [2, 2]
    }
  });

  // Add center point marker
  new MapboxGL.Marker({
    color: borderColor
  })
  .setLngLat(location.coordinates)
  .addTo(map);

  // Fit map to bounding box
  map.fitBounds([
    [bbox.west, bbox.south],
    [bbox.east, bbox.north]
  ], { padding: 50 });
};
```

---

## Search Functionality

### Geocoding Integration

```typescript
interface GeocodingService {
  searchLocations(query: string, options?: GeocodingOptions): Promise<LocationSearchResult[]>;
  reverseGeocode(coordinates: [number, number]): Promise<LocationValue>;
  validateLocation(location: LocationValue): Promise<LocationValidation>;
}

interface GeocodingOptions {
  maxResults?: number;
  biasTowards?: [number, number]; // Bias towards coordinates
  countryCode?: string;
  placeTypes?: PlaceType[];
  bounds?: BoundingBox;
}

interface LocationSearchResult {
  address: string;
  displayName: string;
  coordinates: [number, number];
  confidence: GeocodeConfidence;
  placeType: PlaceType;
  relevance: number; // 0-1 relevance score
  matchedTerms: string[];
}

// Mapbox Geocoding API integration
class MapboxGeocodingService implements GeocodingService {
  private apiKey: string;
  
  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async searchLocations(query: string, options: GeocodingOptions = {}): Promise<LocationSearchResult[]> {
    const params = new URLSearchParams({
      access_token: this.apiKey,
      q: query,
      limit: String(options.maxResults || 5),
      autocomplete: 'true',
      language: 'en'
    });

    if (options.countryCode) {
      params.set('country', options.countryCode);
    }

    if (options.placeTypes) {
      params.set('types', options.placeTypes.join(','));
    }

    if (options.bounds) {
      const { west, south, east, north } = options.bounds;
      params.set('bbox', `${west},${south},${east},${north}`);
    }

    try {
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places?${params}`
      );
      
      if (!response.ok) {
        throw new Error(`Geocoding failed: ${response.statusText}`);
      }

      const data = await response.json();
      return this.parseGeocodingResults(data.features);
    } catch (error) {
      console.error('Geocoding error:', error);
      throw error;
    }
  }

  private parseGeocodingResults(features: any[]): LocationSearchResult[] {
    return features.map(feature => ({
      address: feature.place_name,
      displayName: this.createDisplayName(feature),
      coordinates: feature.center,
      confidence: this.calculateConfidence(feature),
      placeType: this.mapPlaceType(feature.place_type[0]),
      relevance: feature.relevance,
      matchedTerms: feature.matching_text ? [feature.matching_text] : []
    }));
  }

  private calculateConfidence(feature: any): GeocodeConfidence {
    const relevance = feature.relevance;
    const hasExactMatch = feature.properties?.accuracy === 'rooftop';
    
    if (relevance > 0.9 || hasExactMatch) return 'high';
    if (relevance > 0.6) return 'medium';
    return 'low';
  }
}
```

### Search Input Component

```typescript
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onLocationSelect: (location: LocationSearchResult) => void;
  placeholder?: string;
  disabled?: boolean;
  showCurrentLocation?: boolean;
  recentSearches?: string[];
}

const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  onLocationSelect,
  placeholder = "Enter city, address, or ZIP code",
  disabled = false,
  showCurrentLocation = true,
  recentSearches = []
}) => {
  const [searchResults, setSearchResults] = useState<LocationSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  
  const geocodingService = useMemo(() => 
    new MapboxGeocodingService(process.env.REACT_APP_MAPBOX_TOKEN!), 
    []
  );

  // Debounced search
  const debouncedSearch = useMemo(
    () => debounce(async (query: string) => {
      if (query.length < 3) {
        setSearchResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const results = await geocodingService.searchLocations(query, {
          maxResults: 5,
          placeTypes: ['place', 'locality', 'neighborhood', 'address']
        });
        setSearchResults(results);
        setShowDropdown(true);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    [geocodingService]
  );

  useEffect(() => {
    debouncedSearch(value);
  }, [value, debouncedSearch]);

  const handleResultSelect = (result: LocationSearchResult) => {
    onLocationSelect(result);
    setShowDropdown(false);
    setSearchResults([]);
    onChange(result.displayName);
  };

  const handleCurrentLocation = () => {
    if (!navigator.geolocation) {
      // Show error message
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const coordinates: [number, number] = [
          position.coords.longitude,
          position.coords.latitude
        ];
        
        try {
          const location = await geocodingService.reverseGeocode(coordinates);
          const result: LocationSearchResult = {
            address: location.address,
            displayName: location.displayName,
            coordinates: location.coordinates,
            confidence: location.confidence,
            placeType: location.placeType,
            relevance: 1.0,
            matchedTerms: []
          };
          handleResultSelect(result);
        } catch (error) {
          console.error('Current location error:', error);
        }
      },
      (error) => {
        console.error('Geolocation error:', error);
        // Show user-friendly error message
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  return (
    <div className="search-input-container" style={{ position: 'relative' }}>
      <Input
        ref={searchInputRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        prefix={<SearchOutlined />}
        suffix={
          <Space>
            {isLoading && <Spin size="small" />}
            {showCurrentLocation && (
              <Button
                type="link"
                size="small"
                icon={<AimOutlined />}
                onClick={handleCurrentLocation}
                title="Use my current location"
              />
            )}
            {value && (
              <Button
                type="link" 
                size="small"
                icon={<CloseOutlined />}
                onClick={() => {
                  onChange('');
                  setShowDropdown(false);
                }}
                title="Clear search"
              />
            )}
          </Space>
        }
        onFocus={() => {
          if (searchResults.length > 0) {
            setShowDropdown(true);
          }
        }}
        onBlur={() => {
          // Delay hiding dropdown to allow for clicks
          setTimeout(() => setShowDropdown(false), 200);
        }}
      />

      {showDropdown && (searchResults.length > 0 || recentSearches.length > 0) && (
        <div className="search-dropdown">
          {searchResults.length > 0 && (
            <div className="search-section">
              <div className="search-section-header">Search Results</div>
              {searchResults.map((result, index) => (
                <SearchResultItem
                  key={index}
                  result={result}
                  onSelect={handleResultSelect}
                />
              ))}
            </div>
          )}

          {searchResults.length === 0 && recentSearches.length > 0 && (
            <div className="search-section">
              <div className="search-section-header">Recent Searches</div>
              {recentSearches.map((search, index) => (
                <div
                  key={index}
                  className="search-result-item recent"
                  onClick={() => onChange(search)}
                >
                  <ClockCircleOutlined /> {search}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

### Search Result Display

```typescript
interface SearchResultItemProps {
  result: LocationSearchResult;
  onSelect: (result: LocationSearchResult) => void;
}

const SearchResultItem: React.FC<SearchResultItemProps> = ({ result, onSelect }) => {
  const confidenceIcon = {
    high: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    medium: <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />,
    low: <InfoCircleOutlined style={{ color: '#ff4d4f' }} />
  }[result.confidence];

  const placeTypeLabel = {
    address: 'Address',
    street: 'Street',
    neighborhood: 'Neighborhood', 
    city: 'City',
    county: 'County',
    state: 'State',
    postal_code: 'ZIP Code'
  }[result.placeType];

  return (
    <div 
      className="search-result-item"
      onClick={() => onSelect(result)}
      role="option"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(result);
        }
      }}
    >
      <div className="result-main">
        <div className="result-name">{result.displayName}</div>
        <div className="result-details">
          <span className="place-type">{placeTypeLabel}</span>
          <span className="confidence">
            {confidenceIcon} {result.confidence} confidence
          </span>
        </div>
      </div>
      <div className="result-coordinates">
        {result.coordinates[1].toFixed(4)}, {result.coordinates[0].toFixed(4)}
      </div>
    </div>
  );
};
```

---

## Popular Locations Feature

### Popular Locations Data

```typescript
interface PopularLocationsService {
  getPopularLocations(category?: string): Promise<PopularLocation[]>;
  recordLocationUsage(location: LocationValue): Promise<void>;
  getUserRecentLocations(userId?: string): Promise<PopularLocation[]>;
}

// Popular locations curated for accessibility analysis
const defaultPopularLocations: PopularLocation[] = [
  {
    id: 'denver-co',
    name: 'Denver',
    displayName: 'Denver, Colorado',
    coordinates: [-104.9903, 39.7392],
    category: 'urban',
    usageCount: 1247
  },
  {
    id: 'austin-tx',
    name: 'Austin',
    displayName: 'Austin, Texas', 
    coordinates: [-97.7431, 30.2672],
    category: 'urban',
    usageCount: 986
  },
  {
    id: 'portland-or',
    name: 'Portland',
    displayName: 'Portland, Oregon',
    coordinates: [-122.6765, 45.5152],
    category: 'urban',
    usageCount: 834
  },
  {
    id: 'atlanta-ga',
    name: 'Atlanta',
    displayName: 'Atlanta, Georgia',
    coordinates: [-84.3880, 33.7490],
    category: 'urban', 
    usageCount: 756
  },
  {
    id: 'chapel-hill-nc',
    name: 'Chapel Hill',
    displayName: 'Chapel Hill, North Carolina',
    coordinates: [-79.0558, 35.9132],
    category: 'university',
    usageCount: 423
  },
  {
    id: 'fresno-ca',
    name: 'Fresno',
    displayName: 'Fresno, California',
    coordinates: [-119.7871, 36.7378],
    category: 'suburban',
    usageCount: 312
  }
];

const PopularLocations: React.FC<{
  onLocationSelect: (location: PopularLocation) => void;
  category?: string;
  maxCount?: number;
}> = ({ onLocationSelect, category, maxCount = 6 }) => {
  const [locations, setLocations] = useState<PopularLocation[]>([]);
  
  useEffect(() => {
    // Filter and sort locations
    let filtered = defaultPopularLocations;
    if (category) {
      filtered = filtered.filter(loc => loc.category === category);
    }
    
    filtered = filtered
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, maxCount);
    
    setLocations(filtered);
  }, [category, maxCount]);

  return (
    <div className="popular-locations">
      <div className="popular-locations-label">Popular Locations:</div>
      <div className="popular-locations-list">
        {locations.map((location) => (
          <Button
            key={location.id}
            type="default"
            size="small"
            onClick={() => onLocationSelect(location)}
            className="popular-location-button"
          >
            {location.name}
          </Button>
        ))}
      </div>
    </div>
  );
};
```

---

## Data Availability Integration

### Location Validation

```typescript
interface LocationValidation {
  isValid: boolean;
  dataAvailable: boolean;
  censusGeographies: string[];
  poiDataQuality: 'excellent' | 'good' | 'fair' | 'poor';
  warnings: string[];
  recommendations: string[];
  estimatedProcessingTime: number; // seconds
}

const useLocationValidation = () => {
  const validateLocation = useCallback(async (location: LocationValue): Promise<LocationValidation> => {
    // Check data availability for the location
    const validation: LocationValidation = {
      isValid: true,
      dataAvailable: true,
      censusGeographies: ['block_group', 'tract', 'county'],
      poiDataQuality: 'good',
      warnings: [],
      recommendations: [],
      estimatedProcessingTime: 180
    };

    // Area size validation
    const area = calculateArea(location.boundingBox);
    if (area > 1000) { // 1000 sq km
      validation.warnings.push('Large analysis area may take longer to process');
      validation.estimatedProcessingTime = Math.min(area * 0.5, 600); // Cap at 10 minutes
    }

    // Population density check
    if (location.estimatedPopulation && area) {
      const density = location.estimatedPopulation / area;
      if (density < 10) {
        validation.warnings.push('Rural areas may have limited POI data');
        validation.poiDataQuality = 'fair';
      }
    }

    // Check census data availability
    try {
      const censusAvailable = await checkCensusDataAvailability(location.boundingBox);
      if (!censusAvailable) {
        validation.dataAvailable = false;
        validation.warnings.push('Limited census data available for this area');
      }
    } catch (error) {
      validation.warnings.push('Unable to verify data availability');
    }

    return validation;
  }, []);

  return { validateLocation };
};

const LocationValidationSummary: React.FC<{
  location: LocationValue;
  validation?: LocationValidation;
}> = ({ location, validation }) => {
  if (!validation) {
    return (
      <div className="location-summary loading">
        <Spin size="small" /> Validating location...
      </div>
    );
  }

  const confidenceColor = {
    high: '#52c41a',
    medium: '#fa8c16', 
    low: '#ff4d4f'
  }[location.confidence];

  const dataQualityIcon = {
    excellent: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    good: <CheckCircleOutlined style={{ color: '#1890ff' }} />,
    fair: <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />,
    poor: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
  }[validation.poiDataQuality];

  return (
    <div className="location-validation-summary">
      <div className="summary-header">
        <CheckCircleOutlined style={{ color: confidenceColor }} />
        <span className="location-name">Selected: {location.displayName}</span>
      </div>
      
      <div className="summary-details">
        <div className="detail-row">
          <span className="label">Confidence:</span>
          <span className={`value confidence-${location.confidence}`}>
            {location.confidence} ({getConfidenceDescription(location.confidence)})
          </span>
        </div>

        {location.estimatedArea && (
          <div className="detail-row">
            <span className="label">Analysis area:</span>
            <span className="value">~{Math.round(location.estimatedArea)} square miles</span>
          </div>
        )}

        {location.estimatedPopulation && (
          <div className="detail-row">
            <span className="label">Estimated population:</span>
            <span className="value">~{formatPopulation(location.estimatedPopulation)} people</span>
          </div>
        )}

        <div className="detail-row">
          <span className="label">Data availability:</span>
          <span className="value">
            {dataQualityIcon} {validation.poiDataQuality} data quality
          </span>
        </div>
      </div>

      {validation.warnings.length > 0 && (
        <div className="validation-warnings">
          {validation.warnings.map((warning, index) => (
            <div key={index} className="warning-item">
              <ExclamationCircleOutlined /> {warning}
            </div>
          ))}
        </div>
      )}

      {validation.recommendations.length > 0 && (
        <div className="validation-recommendations">
          {validation.recommendations.map((rec, index) => (
            <div key={index} className="recommendation-item">
              <InfoCircleOutlined /> {rec}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const getConfidenceDescription = (confidence: GeocodeConfidence): string => {
  switch (confidence) {
    case 'high': return 'exact city match';
    case 'medium': return 'good area match';
    case 'low': return 'approximate location';
  }
};

const formatPopulation = (population: number): string => {
  if (population > 1000000) {
    return (population / 1000000).toFixed(1) + 'M';
  } else if (population > 1000) {
    return (population / 1000).toFixed(0) + 'K';
  } else {
    return population.toString();
  }
};
```

---

## Accessibility Implementation

### Keyboard Navigation

```typescript
const useMapKeyboardNavigation = (mapRef: React.RefObject<MapboxGL.Map>) => {
  useEffect(() => {
    const handleKeydown = (e: KeyboardEvent) => {
      if (!mapRef.current) return;
      
      const map = mapRef.current;
      const panDistance = 0.01;
      const center = map.getCenter();

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          map.panTo([center.lng, center.lat + panDistance]);
          announceToScreenReader(`Panned north to ${formatCoordinates([center.lng, center.lat + panDistance])}`);
          break;
          
        case 'ArrowDown':
          e.preventDefault(); 
          map.panTo([center.lng, center.lat - panDistance]);
          announceToScreenReader(`Panned south to ${formatCoordinates([center.lng, center.lat - panDistance])}`);
          break;
          
        case 'ArrowLeft':
          e.preventDefault();
          map.panTo([center.lng - panDistance, center.lat]);
          announceToScreenReader(`Panned west to ${formatCoordinates([center.lng - panDistance, center.lat])}`);
          break;
          
        case 'ArrowRight':
          e.preventDefault();
          map.panTo([center.lng + panDistance, center.lat]);
          announceToScreenReader(`Panned east to ${formatCoordinates([center.lng + panDistance, center.lat])}`);
          break;
          
        case '+':
        case '=':
          e.preventDefault();
          map.zoomIn();
          announceToScreenReader(`Zoomed in to level ${Math.round(map.getZoom())}`);
          break;
          
        case '-':
          e.preventDefault();
          map.zoomOut();
          announceToScreenReader(`Zoomed out to level ${Math.round(map.getZoom())}`);
          break;
          
        case 'Enter':
        case ' ':
          e.preventDefault();
          const coords: [number, number] = [center.lng, center.lat];
          // Trigger location selection
          announceToScreenReader(`Selected location at ${formatCoordinates(coords)}`);
          break;
      }
    };

    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, [mapRef]);
};

const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

const formatCoordinates = (coords: [number, number]): string => {
  return `latitude ${coords[1].toFixed(4)}, longitude ${coords[0].toFixed(4)}`;
};
```

### Alternative Text Interface

```typescript
interface AlternativeLocationInputProps {
  onLocationSubmit: (location: LocationValue) => void;
  className?: string;
}

const AlternativeLocationInput: React.FC<AlternativeLocationInputProps> = ({
  onLocationSubmit,
  className
}) => {
  const [address, setAddress] = useState('');
  const [coordinates, setCoordinates] = useState<[number, number] | null>(null);
  const [inputMode, setInputMode] = useState<'address' | 'coordinates'>('address');
  const [isLoading, setIsLoading] = useState(false);

  const geocodingService = useMemo(() => 
    new MapboxGeocodingService(process.env.REACT_APP_MAPBOX_TOKEN!), 
    []
  );

  const handleAddressSubmit = async () => {
    if (!address.trim()) return;

    setIsLoading(true);
    try {
      const results = await geocodingService.searchLocations(address);
      if (results.length > 0) {
        const result = results[0];
        const location: LocationValue = {
          address: result.address,
          displayName: result.displayName,
          coordinates: result.coordinates,
          confidence: result.confidence,
          placeType: result.placeType,
          boundingBox: await estimateBoundingBox(result.coordinates),
          center: result.coordinates,
          country: 'US' // TODO: Extract from geocoding result
        };
        onLocationSubmit(location);
      }
    } catch (error) {
      console.error('Geocoding failed:', error);
      // Show error message
    } finally {
      setIsLoading(false);
    }
  };

  const handleCoordinatesSubmit = async () => {
    if (!coordinates) return;

    setIsLoading(true);
    try {
      const location = await geocodingService.reverseGeocode(coordinates);
      onLocationSubmit(location);
    } catch (error) {
      console.error('Reverse geocoding failed:', error);
      // Show error message
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card title="Alternative Location Input" className={className}>
      <div className="alternative-input-mode">
        <Radio.Group
          value={inputMode}
          onChange={(e) => setInputMode(e.target.value)}
        >
          <Radio.Button value="address">Address or Place Name</Radio.Button>
          <Radio.Button value="coordinates">Coordinates</Radio.Button>
        </Radio.Group>
      </div>

      {inputMode === 'address' && (
        <div className="address-input">
          <Input.Search
            placeholder="Enter city, address, or ZIP code"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            onSearch={handleAddressSubmit}
            loading={isLoading}
            enterButton="Find Location"
          />
        </div>
      )}

      {inputMode === 'coordinates' && (
        <div className="coordinates-input">
          <Input.Group compact>
            <Input
              style={{ width: '50%' }}
              placeholder="Latitude (e.g., 39.7392)"
              onChange={(e) => {
                const lat = parseFloat(e.target.value);
                if (!isNaN(lat) && coordinates) {
                  setCoordinates([coordinates[0], lat]);
                } else if (!isNaN(lat)) {
                  setCoordinates([-104.9903, lat]); // Default longitude
                }
              }}
            />
            <Input
              style={{ width: '50%' }}
              placeholder="Longitude (e.g., -104.9903)"
              onChange={(e) => {
                const lng = parseFloat(e.target.value);
                if (!isNaN(lng) && coordinates) {
                  setCoordinates([lng, coordinates[1]]);
                } else if (!isNaN(lng)) {
                  setCoordinates([lng, 39.7392]); // Default latitude
                }
              }}
            />
          </Input.Group>
          <Button 
            type="primary" 
            onClick={handleCoordinatesSubmit}
            loading={isLoading}
            disabled={!coordinates}
            style={{ marginTop: 8 }}
          >
            Use These Coordinates
          </Button>
        </div>
      )}

      <div className="input-help">
        <Typography.Text type="secondary">
          {inputMode === 'address' 
            ? 'Enter any address, city name, or ZIP code to find the location.'
            : 'Enter decimal coordinates (latitude, longitude). Example: 39.7392, -104.9903'
          }
        </Typography.Text>
      </div>
    </Card>
  );
};
```

---

## Component Integration

### Main MapSelector Component

```typescript
const MapSelector: React.FC<MapSelectorProps> = ({
  value,
  onChange,
  onAreaChange,
  placeholder = "Enter city, address, or ZIP code",
  showPopularLocations = true,
  showRecentLocations = true,
  initialCenter = [-98.5795, 39.8283], // Center of US
  initialZoom = 4,
  height = 400,
  allowBoundingBoxSelection = false,
  showDataAvailabilityIndicator = true,
  showPopulationEstimate = true,
  accessibilityLabel = "Select location for accessibility analysis",
  alternativeInterface = false,
  className = '',
  style = {}
}) => {
  const [searchValue, setSearchValue] = useState('');
  const [validation, setValidation] = useState<LocationValidation | null>(null);
  const [showAlternativeInput, setShowAlternativeInput] = useState(alternativeInterface);
  
  const { validateLocation } = useLocationValidation();
  const geocodingService = useMemo(() => 
    new MapboxGeocodingService(process.env.REACT_APP_MAPBOX_TOKEN!), 
    []
  );

  // Validate location when it changes
  useEffect(() => {
    if (value) {
      validateLocation(value).then(setValidation);
    } else {
      setValidation(null);
    }
  }, [value, validateLocation]);

  // Update area information when location changes
  useEffect(() => {
    if (value && validation && onAreaChange) {
      const area = value.estimatedArea || 0;
      const population = value.estimatedPopulation || 0;
      onAreaChange(area, population);
    }
  }, [value, validation, onAreaChange]);

  const handleSearchResultSelect = async (result: LocationSearchResult) => {
    try {
      const location: LocationValue = {
        address: result.address,
        displayName: result.displayName,
        coordinates: result.coordinates,
        confidence: result.confidence,
        placeType: result.placeType,
        boundingBox: await estimateBoundingBox(result.coordinates, result.placeType),
        center: result.coordinates,
        country: 'US', // TODO: Extract from result
        estimatedArea: await estimateArea(result.coordinates, result.placeType),
        estimatedPopulation: await estimatePopulation(result.coordinates, result.placeType)
      };
      
      onChange(location);
      setSearchValue(result.displayName);
    } catch (error) {
      console.error('Error creating location value:', error);
    }
  };

  const handleMapLocationSelect = async (coordinates: [number, number]) => {
    try {
      const location = await geocodingService.reverseGeocode(coordinates);
      onChange(location);
      setSearchValue(location.displayName);
    } catch (error) {
      console.error('Reverse geocoding failed:', error);
    }
  };

  const handlePopularLocationSelect = (popular: PopularLocation) => {
    const location: LocationValue = {
      address: popular.displayName,
      displayName: popular.displayName,
      coordinates: popular.coordinates,
      confidence: 'high',
      placeType: 'city',
      boundingBox: { north: 0, south: 0, east: 0, west: 0 }, // Will be filled by validation
      center: popular.coordinates,
      country: 'US'
    };
    
    onChange(location);
    setSearchValue(popular.displayName);
  };

  return (
    <div className={`map-selector ${className}`} style={style}>
      <div className="map-selector-header">
        <SearchInput
          value={searchValue}
          onChange={setSearchValue}
          onLocationSelect={handleSearchResultSelect}
          placeholder={placeholder}
          showCurrentLocation={true}
        />

        {showPopularLocations && (
          <PopularLocations 
            onLocationSelect={handlePopularLocationSelect}
            maxCount={6}
          />
        )}
      </div>

      <div className="map-selector-content">
        <MapboxMap
          center={value?.coordinates || initialCenter}
          zoom={value ? 10 : initialZoom}
          onLocationSelect={handleMapLocationSelect}
          selectedLocation={value}
          height={height}
          accessibilityLabel={accessibilityLabel}
        />

        {value && (
          <LocationValidationSummary
            location={value}
            validation={validation}
          />
        )}
      </div>

      <div className="map-selector-footer">
        <Button
          type="link"
          size="small"
          onClick={() => setShowAlternativeInput(!showAlternativeInput)}
        >
          {showAlternativeInput ? 'Use map interface' : 'Enter coordinates manually'}
        </Button>
      </div>

      {showAlternativeInput && (
        <AlternativeLocationInput
          onLocationSubmit={(location) => {
            onChange(location);
            setSearchValue(location.displayName);
            setShowAlternativeInput(false);
          }}
        />
      )}
    </div>
  );
};

export default MapSelector;
```

---

## Testing Strategy

### Component Testing

```typescript
describe('MapSelector', () => {
  describe('Location Search', () => {
    it('should show search results when typing', async () => {
      render(<MapSelector onChange={jest.fn()} />);
      
      const searchInput = screen.getByPlaceholderText(/enter city/i);
      await userEvent.type(searchInput, 'Denver');
      
      await waitFor(() => {
        expect(screen.getByText(/Denver, Colorado/i)).toBeInTheDocument();
      });
    });

    it('should select location from search results', async () => {
      const onChange = jest.fn();
      render(<MapSelector onChange={onChange} />);
      
      const searchInput = screen.getByPlaceholderText(/enter city/i);
      await userEvent.type(searchInput, 'Denver');
      
      await waitFor(() => {
        const result = screen.getByText(/Denver, Colorado/i);
        userEvent.click(result);
      });
      
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          displayName: 'Denver, Colorado',
          coordinates: expect.any(Array)
        })
      );
    });
  });

  describe('Popular Locations', () => {
    it('should show popular location buttons', () => {
      render(<MapSelector onChange={jest.fn()} showPopularLocations={true} />);
      
      expect(screen.getByRole('button', { name: /denver/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /austin/i })).toBeInTheDocument();
    });

    it('should select popular location when clicked', async () => {
      const onChange = jest.fn();
      render(<MapSelector onChange={onChange} showPopularLocations={true} />);
      
      await userEvent.click(screen.getByRole('button', { name: /denver/i }));
      
      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({
          displayName: 'Denver, Colorado'
        })
      );
    });
  });

  describe('Accessibility', () => {
    it('should support keyboard navigation', async () => {
      render(<MapSelector onChange={jest.fn()} />);
      
      const mapContainer = screen.getByRole('application');
      mapContainer.focus();
      
      await userEvent.keyboard('{ArrowUp}');
      
      // Map should pan north
      expect(mapContainer).toHaveFocus();
    });

    it('should have proper ARIA labels', () => {
      render(<MapSelector onChange={jest.fn()} />);
      
      expect(screen.getByRole('application')).toHaveAttribute('aria-label');
      expect(screen.getByRole('searchbox')).toBeInTheDocument();
    });

    it('should announce changes to screen readers', async () => {
      const onChange = jest.fn();
      render(<MapSelector onChange={onChange} />);
      
      // Simulate location selection
      // Verify aria-live announcements
    });
  });

  describe('Data Validation', () => {
    it('should validate location data availability', async () => {
      const onChange = jest.fn();
      render(<MapSelector onChange={onChange} />);
      
      // Select a location
      const searchInput = screen.getByPlaceholderText(/enter city/i);
      await userEvent.type(searchInput, 'Denver');
      
      await waitFor(() => {
        const result = screen.getByText(/Denver, Colorado/i);
        userEvent.click(result);
      });
      
      // Should show validation summary
      await waitFor(() => {
        expect(screen.getByText(/data availability/i)).toBeInTheDocument();
      });
    });
  });
});
```

---

*This MapSelector component specification provides a comprehensive, accessible, and user-friendly interface for location selection that forms the foundation of the spatial analysis configuration experience.*