/**
 * Example tests and usage for the SocialMapper API Client
 */

import { 
  SocialMapperAPIClient, 
  TravelMode, 
  GeographicLevel,
  ExportFormat,
  JobStatusEnum,
  APIClientError 
} from './apiClient';

// Example usage of the API client
async function exampleUsage() {
  // Create client instance
  const client = new SocialMapperAPIClient();
  
  try {
    // 1. Check API health
    console.log('Checking API health...');
    const health = await client.checkHealth();
    console.log('API Status:', health.status);
    console.log('API Version:', health.version);
    
    // 2. Get census variables
    console.log('\nFetching census variables...');
    const censusVars = await client.getCensusVariables('Demographics', undefined, 5);
    console.log(`Found ${censusVars.total_count} census variables`);
    censusVars.variables.forEach(v => {
      console.log(`  - ${v.code}: ${v.name}`);
    });
    
    // 3. Search for POI types
    console.log('\nSearching for library POI types...');
    const poiTypes = await client.getPOITypes(undefined, 'library');
    poiTypes.poi_types.forEach(poi => {
      console.log(`  - ${poi.type}:${poi.name} - ${poi.description}`);
    });
    
    // 4. Search for a location
    console.log('\nSearching for Portland...');
    const locations = await client.searchLocations('Portland', 5);
    locations.results.forEach(loc => {
      console.log(`  - ${loc.display_name} (${loc.latitude}, ${loc.longitude})`);
    });
    
    // 5. Submit an analysis request
    console.log('\nSubmitting analysis request...');
    const analysisResponse = await client.analyzeLocation({
      location: 'Portland, OR',
      poi_type: 'amenity',
      poi_name: 'library',
      travel_time: 15,
      travel_mode: TravelMode.WALK,
      geographic_level: GeographicLevel.BLOCK_GROUP,
      census_variables: ['B01003_001E', 'B19013_001E'],
      include_isochrones: true,
      include_demographics: true,
    });
    
    console.log(`Analysis job created: ${analysisResponse.job_id}`);
    console.log(`Status: ${analysisResponse.status}`);
    
    // 6. Poll for results with progress callback
    console.log('\nPolling for results...');
    const result = await client.pollAnalysis(
      analysisResponse.job_id,
      (status) => {
        console.log(`Progress: ${(status.progress * 100).toFixed(0)}% - ${status.message || 'Processing...'}`);
      }
    );
    
    console.log('\nAnalysis completed!');
    console.log(`POIs found: ${result.poi_count}`);
    console.log(`Analysis area: ${result.analysis_area_km2?.toFixed(2)} km²`);
    console.log(`Population covered: ${result.population_covered?.toLocaleString()}`);
    
    // 7. Export results
    console.log('\nExporting results as CSV...');
    const csvBlob = await client.exportResults(
      result.job_id,
      ExportFormat.CSV,
      false, // exclude isochrones from CSV
      true   // include demographics
    );
    console.log(`CSV export size: ${(csvBlob.size / 1024).toFixed(2)} KB`);
    
    // 8. Clean up
    console.log('\nDeleting results...');
    await client.deleteResults(result.job_id);
    console.log('Results deleted successfully');
    
  } catch (error) {
    if (error instanceof APIClientError) {
      console.error('API Error:', error.statusCode, error.apiError.message);
      if (error.apiError.details) {
        console.error('Details:', error.apiError.details);
      }
    } else {
      console.error('Unexpected error:', error);
    }
  }
}

// Example React hook usage
export function useExampleAPIClient() {
  const client = new SocialMapperAPIClient();
  
  // Example: Submit analysis with cancellation
  const submitAnalysisWithCancel = async (jobId: string) => {
    try {
      // Start analysis
      const response = await client.analyzeLocation({
        location: 'Chicago, IL',
        poi_type: 'shop',
        poi_name: 'supermarket',
        travel_time: 10,
        travel_mode: TravelMode.DRIVE,
      });
      
      // Poll for results (can be cancelled)
      const result = await client.pollAnalysis(response.job_id);
      return result;
      
    } catch (error) {
      if (error instanceof APIClientError && error.apiError.error_code === 'REQUEST_CANCELLED') {
        console.log('Analysis cancelled by user');
      } else {
        throw error;
      }
    }
  };
  
  // Cancel function
  const cancelAnalysis = (jobId: string) => {
    client.cancelRequest(jobId);
  };
  
  // Cleanup on unmount
  const cleanup = () => {
    client.cancelAllRequests();
  };
  
  return {
    submitAnalysisWithCancel,
    cancelAnalysis,
    cleanup,
  };
}

// Unit test examples
describe('SocialMapperAPIClient', () => {
  let client: SocialMapperAPIClient;
  
  beforeEach(() => {
    client = new SocialMapperAPIClient('http://test.api', 'test-key');
  });
  
  afterEach(() => {
    client.cancelAllRequests();
  });
  
  test('creates client with custom configuration', () => {
    const customClient = new SocialMapperAPIClient(
      'https://api.example.com',
      'my-api-key',
      30000
    );
    expect(customClient).toBeDefined();
  });
  
  test('handles API errors correctly', async () => {
    // Mock fetch to return an error
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({
        error_code: 'RESOURCE_NOT_FOUND',
        message: 'Job not found',
        timestamp: '2024-01-01T00:00:00Z',
      }),
    });
    
    await expect(client.getJobStatus('invalid-id')).rejects.toThrow(APIClientError);
  });
  
  test('cancels requests by job ID', () => {
    const jobId = 'test-job-123';
    
    // Start a request (mocked)
    global.fetch = jest.fn().mockImplementation(() => 
      new Promise((resolve) => {
        setTimeout(() => resolve({ ok: true, json: async () => ({}) }), 5000);
      })
    );
    
    // Start request
    const promise = client.getJobStatus(jobId);
    
    // Cancel it immediately
    client.cancelRequest(jobId);
    
    // Should throw cancellation error
    expect(promise).rejects.toThrow('Request was cancelled');
  });
});

// Export for running the example
if (typeof window === 'undefined') {
  // Node.js environment
  exampleUsage().catch(console.error);
}