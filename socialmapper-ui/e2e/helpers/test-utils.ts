import { Page } from '@playwright/test';

export async function mockAPIEndpoints(page: Page) {
  // Mock health check
  await page.route('**/api/v1/health', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({ 
        status: 'healthy',
        version: '0.1.0',
        timestamp: new Date().toISOString()
      })
    });
  });

  // Mock POI types
  await page.route('**/api/v1/poi/types', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        poi_types: [
          { type: 'amenity:library', name: 'Libraries', count: 150 },
          { type: 'amenity:school', name: 'Schools', count: 320 },
          { type: 'amenity:hospital', name: 'Hospitals', count: 45 },
          { type: 'shop:grocery', name: 'Grocery Stores', count: 280 }
        ]
      })
    });
  });

  // Mock census variables
  await page.route('**/api/v1/census/variables', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        variables: [
          { code: 'B01003_001E', name: 'Total Population', category: 'Demographics' },
          { code: 'B19013_001E', name: 'Median Household Income', category: 'Income' },
          { code: 'B25003_001E', name: 'Total Housing Units', category: 'Housing' }
        ]
      })
    });
  });
}

export async function waitForAnalysisComplete(page: Page, timeout = 60000) {
  // Wait for analysis to complete
  await page.waitForSelector('text=Analysis Complete', { timeout });
}

export async function fillLocationAnalysisForm(
  page: Page,
  location: string,
  poiType: string = 'Libraries',
  travelTime: number = 15,
  travelMode: string = 'Walking'
) {
  await page.fill('input[placeholder*="location"]', location);
  
  // Select POI type
  await page.click('text=Select POI Type');
  await page.click(`text=${poiType}`);
  
  // Set travel time
  await page.fill('input[type="number"]', travelTime.toString());
  
  // Select travel mode
  await page.click(`text=${travelMode}`);
}

export async function mockAnalysisWorkflow(page: Page, jobId: string = 'test-job-123') {
  // Mock create analysis
  await page.route('**/api/v1/analysis/location', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({ job_id: jobId })
    });
  });

  // Mock job status - return completed immediately
  await page.route(`**/api/v1/analysis/${jobId}/status`, route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        job_id: jobId,
        status: 'completed',
        progress: 100,
        message: 'Analysis complete'
      })
    });
  });

  // Mock results
  await page.route(`**/api/v1/results/${jobId}`, route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        job_id: jobId,
        results: {
          accessibility_score: 0.75,
          total_pois: 23,
          total_population: 45000,
          isochrones: {
            type: 'FeatureCollection',
            features: []
          }
        }
      })
    });
  });
}

export async function loginWithAPIKey(page: Page, apiKey: string) {
  await page.goto('/settings');
  await page.fill('input[placeholder*="API key"]', apiKey);
  await page.click('button:has-text("Save Settings")');
  await page.waitForSelector('text=Settings saved successfully');
}