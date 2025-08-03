# SocialMapper TypeScript API Client

A TypeScript client library for interacting with the SocialMapper API backend.

## Features

- Full TypeScript support with comprehensive type definitions
- Automatic request/response handling with proper error management
- Built-in polling functionality for long-running jobs
- Abort controller support for request cancellation
- Configurable timeout and error callbacks
- File upload support for custom POI analysis
- Export and download utilities

## Installation

The client is part of the SocialMapper UI package. To use it in your React components:

```typescript
import { SocialMapperAPIClient } from './services';
import { TravelMode, ExportFormat } from './types';
```

## Basic Usage

### Initialize the Client

```typescript
const client = new SocialMapperAPIClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-api-key', // Optional
  timeout: 30000, // 30 seconds
  onError: (error) => {
    console.error('API Error:', error);
  }
});
```

### Create a Location Analysis

```typescript
const response = await client.createLocationAnalysis({
  location: 'Portland, OR',
  census_variables: ['B01003_001E'], // Total population
  travel_mode: TravelMode.Walk,
  travel_time_minutes: 15,
  poi_types: ['amenity:library']
});

// Poll for results
const results = await client.pollJobStatus(
  response.job_id,
  (status) => {
    console.log(`Progress: ${status.progress * 100}%`);
  }
);
```

### Search Locations

```typescript
const locations = await client.searchLocations({
  q: 'Portland',
  limit: 5,
  country: 'US'
});
```

### Get Metadata

```typescript
// Census variables
const censusVars = await client.getCensusVariables({
  group: 'Demographics',
  search: 'income'
});

// POI types
const poiTypes = await client.getPOITypes({
  category: 'Healthcare'
});
```

### Export Results

```typescript
// Direct download
await client.downloadExport(
  jobId,
  ExportFormat.CSV,
  'analysis-results.csv'
);

// Or get as blob
const blob = await client.exportResults(
  jobId,
  ExportFormat.GeoJSON,
  true, // include isochrones
  true  // include demographics
);
```

## API Methods

### Analysis Methods
- `createLocationAnalysis(request)` - Create a location-based analysis
- `createBatchAnalysis(request)` - Create a batch analysis for multiple locations
- `createCustomPOIAnalysis(request)` - Upload and analyze custom POIs
- `getJobStatus(jobId)` - Get the status of an analysis job
- `cancelJob(jobId)` - Cancel a running job

### Results Methods
- `getAnalysisResults(jobId)` - Get complete analysis results
- `exportResults(jobId, format, includeIsochrones, includeDemographics)` - Export as blob
- `createExportJob(jobId, request)` - Create async export job
- `deleteResults(jobId)` - Delete results and clean up
- `downloadExport(jobId, format, filename)` - Download export directly

### Metadata Methods
- `getCensusVariables(params)` - Get available census variables
- `getPOITypes(params)` - Get available POI types
- `searchLocations(params)` - Search for geographic locations

### Utility Methods
- `checkHealth()` - Check API health status
- `pollJobStatus(jobId, onProgress, pollInterval)` - Poll until job completes

## Error Handling

The client provides multiple levels of error handling:

```typescript
// Global error handler
const client = new SocialMapperAPIClient({
  baseURL: 'http://localhost:8000',
  onError: (error) => {
    // Handle all API errors
    notifyUser(error.message);
  }
});

// Per-request error handling
try {
  const results = await client.getAnalysisResults(jobId);
} catch (error) {
  if (error.message.includes('timeout')) {
    // Handle timeout
  } else {
    // Handle other errors
  }
}
```

## TypeScript Types

All request and response types are available:

```typescript
import {
  AnalysisRequest,
  AnalysisResponse,
  JobStatus,
  AnalysisResult,
  CensusVariable,
  POIType,
  LocationSearchResult,
  TravelMode,
  JobStatusEnum,
  ExportFormat
} from './types';
```

## Integration with React

Example React hook usage:

```typescript
import { useState, useCallback } from 'react';
import { SocialMapperAPIClient } from '../services';
import { AnalysisResult, JobStatus } from '../types';

export function useAnalysis() {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const client = new SocialMapperAPIClient({
    baseURL: import.meta.env.VITE_API_URL,
    onError: (err) => setError(err.message)
  });

  const runAnalysis = useCallback(async (request: AnalysisRequest) => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      const response = await client.createLocationAnalysis(request);
      
      const results = await client.pollJobStatus(
        response.job_id,
        (status: JobStatus) => {
          setProgress(status.progress);
        }
      );
      
      setResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [client]);

  return { runAnalysis, loading, progress, results, error };
}
```

## Development

To run tests:

```bash
npm test src/services/SocialMapperAPIClient.test.ts
```

## License

Part of the SocialMapper project.