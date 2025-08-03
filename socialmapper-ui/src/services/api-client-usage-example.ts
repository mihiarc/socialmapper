/**
 * Example usage of the SocialMapperAPIClient with enhanced polling functionality
 */

import { SocialMapperAPIClient } from './SocialMapperAPIClient';
import { TravelMode, ExportFormat } from '../types/api';

// Initialize the API client
const apiClient = new SocialMapperAPIClient({
  baseURL: 'http://localhost:8000',
  apiKey: process.env.REACT_APP_API_KEY,
  timeout: 30000,
  onError: (error) => {
    console.error('API Error:', error.error_code, error.message);
  }
});

// Example 1: Basic location analysis with polling
async function analyzeLocation() {
  try {
    // Create analysis job
    const response = await apiClient.createLocationAnalysis({
      location: 'Portland, OR',
      travel_mode: TravelMode.Walk,
      travel_time_minutes: 15,
      census_variables: ['B01003_001E', 'B19013_001E'],
      poi_types: ['amenity:library', 'amenity:school']
    });

    console.log('Job created:', response.job_id);

    // Poll for results with progress updates
    const results = await apiClient.pollJobStatus(
      response.job_id,
      (status) => {
        console.log(`Progress: ${(status.progress * 100).toFixed(0)}%`);
      }
    );

    console.log('Analysis complete!');
    console.log('POI Count:', results.poi_count);
    console.log('Population Covered:', results.population_covered);
    console.log('Demographics:', results.demographics);

    // Export results
    await apiClient.downloadExport(response.job_id, ExportFormat.CSV);
  } catch (error) {
    console.error('Analysis failed:', error);
  }
}

// Example 2: Cancellable analysis with abort controller
async function cancellableAnalysis() {
  try {
    // Create analysis job
    const response = await apiClient.createLocationAnalysis({
      location: 'Chicago, IL',
      travel_mode: TravelMode.Transit,
      travel_time_minutes: 30
    });

    // Create polling controller
    const controller = apiClient.createPollingController(
      response.job_id,
      (status) => {
        console.log(`Job ${status.job_id}: ${status.status} (${(status.progress * 100).toFixed(0)}%)`);
      }
    );

    // Set up cancellation after 10 seconds
    setTimeout(() => {
      console.log('Cancelling analysis...');
      controller.abort();
    }, 10000);

    try {
      const results = await controller.promise;
      console.log('Analysis complete:', results);
    } catch (error) {
      if (error.message === 'Polling aborted') {
        console.log('Analysis was cancelled by user');
        // Optionally cancel the job on the server
        await apiClient.cancelJob(response.job_id);
      } else {
        throw error;
      }
    }
  } catch (error) {
    console.error('Analysis failed:', error);
  }
}

// Example 3: Batch analysis with custom POI file
async function batchAnalysisWithCustomPOIs() {
  try {
    // First, get available census variables
    const censusVars = await apiClient.getCensusVariables({
      group: 'Demographics',
      limit: 10
    });
    console.log('Available census variables:', censusVars.variables);

    // Create custom POI file
    const csvContent = `name,latitude,longitude
Community Center,45.5152,-122.6784
Food Bank,45.5200,-122.6800
Health Clinic,45.5100,-122.6750`;
    
    const poiFile = new File([csvContent], 'custom_pois.csv', { type: 'text/csv' });

    // Create custom POI analysis
    const response = await apiClient.createCustomPOIAnalysis({
      location: 'Portland, OR',
      poi_file: poiFile,
      travel_mode: TravelMode.Walk,
      travel_time_minutes: 20,
      census_variables: censusVars.variables.slice(0, 3).map(v => v.code),
      name_column: 'name',
      lat_column: 'latitude',
      lon_column: 'longitude'
    });

    // Poll with custom interval
    const results = await apiClient.pollJobStatus(
      response.job_id,
      (status) => {
        if (status.message) {
          console.log(status.message);
        }
      },
      1000 // Poll every second
    );

    console.log('Custom POI analysis complete:', results);
  } catch (error) {
    console.error('Batch analysis failed:', error);
  }
}

// Example 4: Search locations and analyze
async function searchAndAnalyze() {
  try {
    // Search for locations
    const searchResults = await apiClient.searchLocations({
      q: 'Durham',
      limit: 5
    });

    console.log('Found locations:');
    searchResults.results.forEach((loc, i) => {
      console.log(`${i + 1}. ${loc.display_name} (${loc.latitude}, ${loc.longitude})`);
    });

    if (searchResults.results.length > 0) {
      // Analyze the first result
      const location = searchResults.results[0];
      const response = await apiClient.createLocationAnalysis({
        location: location.display_name,
        travel_mode: TravelMode.Bike,
        travel_time_minutes: 10,
        poi_types: ['leisure:park']
      });

      // Use abort signal for polling
      const abortController = new AbortController();
      
      // Cancel if user navigates away
      window.addEventListener('beforeunload', () => abortController.abort());

      const results = await apiClient.pollJobStatus(
        response.job_id,
        undefined,
        2000,
        abortController.signal
      );

      console.log('Park accessibility analysis:', results);
    }
  } catch (error) {
    console.error('Search and analyze failed:', error);
  }
}

// Example 5: Get POI types and filter
async function explorePOITypes() {
  try {
    // Get all POI categories
    const poiResponse = await apiClient.getPOITypes();
    console.log('POI Categories:', poiResponse.categories);

    // Get healthcare POIs
    const healthcarePOIs = await apiClient.getPOITypes({
      category: 'Healthcare',
      limit: 20
    });

    console.log('Healthcare POI Types:');
    healthcarePOIs.poi_types.forEach(poi => {
      console.log(`- ${poi.type}:${poi.name} - ${poi.description}`);
      if (poi.common_names) {
        console.log(`  Also known as: ${poi.common_names.join(', ')}`);
      }
    });

    // Search for specific POI
    const librarySearch = await apiClient.getPOITypes({
      search: 'library'
    });
    console.log('Library POI:', librarySearch.poi_types[0]);
  } catch (error) {
    console.error('POI exploration failed:', error);
  }
}

// Export functions for use in React components
export {
  analyzeLocation,
  cancellableAnalysis,
  batchAnalysisWithCustomPOIs,
  searchAndAnalyze,
  explorePOITypes
};