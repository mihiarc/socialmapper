import { test, expect } from '@playwright/test';

test.describe('Travel Modes Comparison', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/travel-modes');
  });

  test('should compare multiple travel modes', async ({ page }) => {
    // Fill in location
    await page.fill('input[placeholder*="location"]', 'Seattle, WA');
    
    // Select travel modes
    await page.check('text=Walking');
    await page.check('text=Biking');
    await page.check('text=Driving');
    
    // Set travel time
    await page.fill('input[type="number"]', '20');
    
    // Mock API responses for each mode
    await page.route('**/api/v1/analysis/location', async route => {
      const request = route.request();
      const data = await request.postDataJSON();
      
      // Return different results based on travel mode
      const jobId = `job-${data.travel_mode}-${Date.now()}`;
      route.fulfill({
        status: 200,
        body: JSON.stringify({ job_id: jobId })
      });
    });
    
    // Mock job status responses
    await page.route('**/api/v1/analysis/*/status', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ 
          status: 'completed',
          progress: 100
        })
      });
    });
    
    // Mock results
    await page.route('**/api/v1/results/*', route => {
      const url = route.request().url();
      let mode = 'walk';
      if (url.includes('drive')) mode = 'drive';
      else if (url.includes('bike')) mode = 'bike';
      
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          results: {
            accessibility_score: mode === 'drive' ? 0.85 : mode === 'bike' ? 0.65 : 0.45,
            total_pois: mode === 'drive' ? 25 : mode === 'bike' ? 18 : 12,
            travel_mode: mode
          }
        })
      });
    });
    
    // Start analysis
    await page.click('button:has-text("Analyze Travel Modes")');
    
    // Wait for results
    await expect(page.locator('text=Comparison Results')).toBeVisible({ timeout: 30000 });
    
    // Verify all three modes are shown
    await expect(page.locator('text=Walking')).toBeVisible();
    await expect(page.locator('text=Biking')).toBeVisible();
    await expect(page.locator('text=Driving')).toBeVisible();
    
    // Verify scores are displayed
    await expect(page.locator('text=0.85')).toBeVisible(); // Drive score
    await expect(page.locator('text=0.65')).toBeVisible(); // Bike score
    await expect(page.locator('text=0.45')).toBeVisible(); // Walk score
  });

  test('should require at least one travel mode', async ({ page }) => {
    // Fill location
    await page.fill('input[placeholder*="location"]', 'Portland, OR');
    
    // Try to uncheck all modes (if possible)
    const walkCheckbox = page.locator('input[type="checkbox"]:near(:text("Walking"))');
    const bikeCheckbox = page.locator('input[type="checkbox"]:near(:text("Biking"))');
    const driveCheckbox = page.locator('input[type="checkbox"]:near(:text("Driving"))');
    const transitCheckbox = page.locator('input[type="checkbox"]:near(:text("Transit"))');
    
    // Uncheck all
    if (await walkCheckbox.isChecked()) await walkCheckbox.uncheck();
    if (await bikeCheckbox.isChecked()) await bikeCheckbox.uncheck();
    if (await driveCheckbox.isChecked()) await driveCheckbox.uncheck();
    if (await transitCheckbox.isChecked()) await transitCheckbox.uncheck();
    
    // Submit button should be disabled or show error
    const submitButton = page.locator('button:has-text("Analyze Travel Modes")');
    await expect(submitButton).toBeDisabled();
  });

  test('should export comparison results', async ({ page }) => {
    // Complete an analysis first (simplified)
    await page.fill('input[placeholder*="location"]', 'Boston, MA');
    await page.check('text=Walking');
    await page.check('text=Transit');
    
    // Mock quick completion
    await page.route('**/api/v1/**', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ 
          job_id: 'test-123',
          status: 'completed',
          results: { accessibility_score: 0.75 }
        })
      });
    });
    
    await page.click('button:has-text("Analyze Travel Modes")');
    
    // Wait for export button
    await expect(page.locator('button:has-text("Export Results")')).toBeVisible({ timeout: 10000 });
    
    // Test export functionality
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('button:has-text("Export Results")')
    ]);
    
    // Verify download
    expect(download.suggestedFilename()).toContain('travel-modes-comparison');
  });
});