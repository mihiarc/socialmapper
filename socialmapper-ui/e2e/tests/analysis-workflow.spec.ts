import { test, expect } from '@playwright/test';

test.describe('Analysis Workflow', () => {
  test('should complete a basic location analysis', async ({ page }) => {
    // Start from home page
    await page.goto('/');
    
    // Navigate to Getting Started
    await page.click('text=Getting Started');
    await page.waitForURL('/getting-started');
    
    // Fill in the location
    await page.fill('input[placeholder="Enter a city, county, or address"]', 'Portland, OR');
    
    // Select POI type (assuming there's a dropdown)
    await page.click('text=Select POI Type');
    await page.click('text=Libraries');
    
    // Set travel time
    await page.fill('input[type="number"]', '15');
    
    // Select travel mode
    await page.click('text=Walking');
    
    // Add a census variable
    await page.click('text=Add Census Variables');
    await page.click('text=Total Population');
    
    // Submit the analysis
    await page.click('button:has-text("Analyze Location")');
    
    // Wait for analysis to start (should show loading state)
    await expect(page.locator('text=Analyzing')).toBeVisible();
    
    // Wait for results (with timeout for processing)
    await expect(page.locator('text=Analysis Complete')).toBeVisible({ timeout: 60000 });
    
    // Verify results are displayed
    await expect(page.locator('text=Results')).toBeVisible();
    await expect(page.locator('text=Accessibility Score')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Intercept API calls to simulate error
    await page.route('**/api/v1/analysis/location', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ 
          error: 'Internal Server Error',
          message: 'Failed to process analysis'
        })
      });
    });
    
    await page.goto('/getting-started');
    
    // Fill minimal required fields
    await page.fill('input[placeholder="Enter a city, county, or address"]', 'Test Location');
    
    // Submit
    await page.click('button:has-text("Analyze Location")');
    
    // Should show error message
    await expect(page.locator('text=Failed to process analysis')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/getting-started');
    
    // Try to submit without filling location
    await page.click('button:has-text("Analyze Location")');
    
    // Should show validation error
    await expect(page.locator('text=Location is required')).toBeVisible();
  });
});