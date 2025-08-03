import { SocialMapperAPIClient } from './SocialMapperAPIClient';
import { TravelMode, ExportFormat } from '../types/api';

// Example usage of the SocialMapper API Client

async function runAnalysisExample() {
  // Initialize the client
  const client = new SocialMapperAPIClient({
    baseURL: 'http://localhost:8000',
    apiKey: process.env.VITE_API_KEY, // Optional API key
    timeout: 60000, // 60 second timeout
    onError: (error) => {
      console.error('API Error:', error.message);
    }
  });

  try {
    // 1. Check API health
    const health = await client.checkHealth();
    console.log('API Health:', health);

    // 2. Search for a location
    const locations = await client.searchLocations({
      q: 'Portland',
      limit: 5
    });
    console.log('Found locations:', locations.results);

    // 3. Get available census variables
    const censusVars = await client.getCensusVariables({
      group: 'Demographics',
      limit: 10
    });
    console.log('Census variables:', censusVars.variables);

    // 4. Get POI types
    const poiTypes = await client.getPOITypes({
      category: 'Healthcare'
    });
    console.log('Healthcare POI types:', poiTypes.poi_types);

    // 5. Create a location analysis
    const analysisResponse = await client.createLocationAnalysis({
      location: 'Portland, OR',
      census_variables: ['B01003_001E', 'B19013_001E'], // Total pop, median income
      travel_mode: TravelMode.Walk,
      travel_time_minutes: 15,
      poi_types: ['amenity:library', 'amenity:school']
    });
    console.log('Analysis started:', analysisResponse.job_id);

    // 6. Poll for results with progress updates
    const results = await client.pollJobStatus(
      analysisResponse.job_id,
      (status) => {
        console.log(`Progress: ${(status.progress * 100).toFixed(0)}%`);
      }
    );
    console.log('Analysis complete:', results);

    // 7. Export results
    await client.downloadExport(
      analysisResponse.job_id,
      ExportFormat.CSV,
      'portland_analysis.csv'
    );

    // 8. Clean up
    await client.deleteResults(analysisResponse.job_id);
    console.log('Results deleted');

  } catch (error) {
    console.error('Error:', error);
  }
}

// Example: Custom POI analysis
async function customPOIExample() {
  const client = new SocialMapperAPIClient({
    baseURL: 'http://localhost:8000'
  });

  // Assume we have a file input element
  const fileInput = document.getElementById('poi-file') as HTMLInputElement;
  const file = fileInput.files?.[0];

  if (!file) {
    console.error('No file selected');
    return;
  }

  try {
    const response = await client.createCustomPOIAnalysis({
      location: 'Chicago, IL',
      poi_file: file,
      census_variables: ['B01003_001E'],
      travel_mode: TravelMode.Drive,
      travel_time_minutes: 20,
      name_column: 'name',
      lat_column: 'latitude',
      lon_column: 'longitude'
    });

    console.log('Custom POI analysis started:', response.job_id);

    // Poll for results
    const results = await client.pollJobStatus(response.job_id);
    console.log('Custom POI analysis results:', results);

  } catch (error) {
    console.error('Custom POI analysis error:', error);
  }
}

// Example: Batch analysis
async function batchAnalysisExample() {
  const client = new SocialMapperAPIClient({
    baseURL: 'http://localhost:8000'
  });

  try {
    const response = await client.createBatchAnalysis({
      locations: ['Portland, OR', 'Chicago, IL', 'Durham, NC'],
      census_variables: ['B01003_001E'],
      travel_mode: TravelMode.Transit,
      travel_time_minutes: 30,
      poi_types: ['amenity:hospital']
    });

    console.log('Batch analysis started:', response.job_id);

    // Poll with custom interval
    const results = await client.pollJobStatus(
      response.job_id,
      (status) => {
        console.log(`Batch progress: ${status.message || status.progress}`);
      },
      5000 // Poll every 5 seconds for batch jobs
    );

    console.log('Batch analysis complete:', results);

  } catch (error) {
    console.error('Batch analysis error:', error);
  }
}

// Export the examples for use in React components
export { runAnalysisExample, customPOIExample, batchAnalysisExample };