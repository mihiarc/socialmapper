# SocialMapper React UI

This directory contains the React frontend for the SocialMapper application.

## Overview

The SocialMapper UI is a modern React application that provides an interactive web interface for community accessibility analysis. It communicates with the SocialMapper backend through a REST API.

## Features

- Location-based POI analysis with interactive forms
- Custom POI upload and analysis
- Multi-modal travel time comparison (walk, bike, drive)
- Interactive maps with isochrone visualization
- Census demographic data integration
- Result export in multiple formats (CSV, GeoJSON, Parquet)

## API Client

The frontend includes a TypeScript API client (`src/services/apiClient.ts`) that provides:

- Type-safe methods for all API endpoints
- Automatic request cancellation and cleanup
- Progress tracking for long-running analyses
- Error handling with custom error types
- Configurable timeouts and polling intervals

### Basic Usage

```typescript
import { apiClient } from './services/apiClient';

// Submit an analysis
const response = await apiClient.analyzeLocation({
  location: 'Portland, OR',
  poi_type: 'amenity',
  poi_name: 'library',
  travel_time: 15,
  travel_mode: 'walk'
});

// Poll for results
const result = await apiClient.pollAnalysis(
  response.job_id,
  (status) => console.log(`Progress: ${status.progress * 100}%`)
);
```

### React Hook Usage

```typescript
import { useAnalysis } from './hooks/useAnalysis';

function MyComponent() {
  const {
    analyzeLocation,
    result,
    progress,
    isRunning,
    cancel
  } = useAnalysis({
    onComplete: (result) => console.log('Analysis complete!', result),
    onError: (error) => console.error('Analysis failed:', error)
  });
  
  // Submit analysis
  const handleSubmit = () => {
    analyzeLocation({
      location: 'Chicago, IL',
      poi_type: 'shop',
      poi_name: 'supermarket'
    });
  };
  
  return (
    <div>
      <button onClick={handleSubmit}>Start Analysis</button>
      {isRunning && (
        <div>
          <p>Progress: {progress * 100}%</p>
          <button onClick={cancel}>Cancel</button>
        </div>
      )}
      {result && <p>Found {result.poi_count} POIs</p>}
    </div>
  );
}
```

## Configuration

The application uses environment variables for configuration. Create a `.env` file:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=300000
VITE_POLL_INTERVAL=2000

# File Upload
VITE_MAX_FILE_SIZE_MB=10
VITE_ALLOWED_FILE_TYPES=.csv,.xlsx,.xls,.json,.geojson

# Map Settings
VITE_DEFAULT_MAP_LAT=45.5152
VITE_DEFAULT_MAP_LNG=-122.6784
VITE_DEFAULT_MAP_ZOOM=12

# Feature Flags
VITE_ENABLE_BATCH_ANALYSIS=false
VITE_ENABLE_EXPERIMENTAL=false
```

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Project Structure

```
src/
├── components/       # Reusable UI components
├── pages/           # Page components (tutorials)
├── services/        # API client and utilities
├── hooks/           # Custom React hooks
├── types/           # TypeScript type definitions
├── utils/           # Helper functions
├── config/          # Configuration files
└── App.tsx          # Main application component
```

## API Client Methods

### Analysis Methods

- `analyzeLocation(request)` - Submit location-based analysis
- `analyzeCustomPOIs(request)` - Submit custom POI analysis
- `getJobStatus(jobId)` - Get analysis job status
- `getAnalysisResult(jobId)` - Get complete analysis results
- `pollAnalysis(jobId, onProgress)` - Poll for analysis completion
- `exportResults(jobId, format)` - Export results in various formats
- `deleteResults(jobId)` - Delete analysis results

### Metadata Methods

- `getCensusVariables(group, search)` - Get available census variables
- `getPOITypes(category, search)` - Get available POI types
- `searchLocations(query)` - Search for geographic locations

### Utility Methods

- `checkHealth()` - Check API health status
- `cancelRequest(jobId)` - Cancel a specific request
- `cancelAllRequests()` - Cancel all ongoing requests

## Error Handling

The API client provides detailed error information through the `APIClientError` class:

```typescript
try {
  const result = await apiClient.analyzeLocation(request);
} catch (error) {
  if (error instanceof APIClientError) {
    console.error('API Error:', error.statusCode, error.apiError.message);
    
    switch (error.statusCode) {
      case 422:
        // Handle validation error
        break;
      case 429:
        // Handle rate limit
        break;
      default:
        // Handle other errors
    }
  }
}
```

## Testing

The API client includes comprehensive TypeScript types and can be easily tested:

```typescript
import { SocialMapperAPIClient } from './services/apiClient';

// Mock the fetch API
global.fetch = jest.fn();

// Test API calls
const client = new SocialMapperAPIClient('http://test.api');
await client.checkHealth();
```