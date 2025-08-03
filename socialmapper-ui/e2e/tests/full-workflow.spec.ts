import { test, expect } from '@playwright/test';
import { 
  mockAPIEndpoints, 
  fillLocationAnalysisForm, 
  mockAnalysisWorkflow,
  loginWithAPIKey 
} from '../helpers/test-utils';

test.describe('Full Application Workflow', () => {
  test('should complete full analysis workflow with authentication', async ({ page }) => {
    // Set up API mocks
    await mockAPIEndpoints(page);
    
    // 1. Start at home page
    await page.goto('/');
    await expect(page.locator('h1:has-text("Welcome to SocialMapper")')).toBeVisible();
    
    // 2. Go to settings and configure API key
    await page.click('text=Settings');
    await loginWithAPIKey(page, 'test-api-key-full-workflow');
    
    // 3. Navigate to Getting Started
    await page.click('a:has-text("SocialMapper")'); // Go back home
    await page.click('text=Getting Started');
    
    // 4. Set up analysis mocks
    await mockAnalysisWorkflow(page, 'workflow-test-123');
    
    // 5. Fill and submit analysis form
    await fillLocationAnalysisForm(page, 'San Francisco, CA', 'Hospitals', 20, 'Driving');
    
    // Add census variables
    await page.click('text=Add Census Variables');
    await page.click('text=Total Population');
    await page.click('text=Median Household Income');
    
    // 6. Submit analysis
    await page.click('button:has-text("Analyze Location")');
    
    // 7. Wait for completion
    await expect(page.locator('text=Analysis Complete')).toBeVisible({ timeout: 10000 });
    
    // 8. Verify results are displayed
    await expect(page.locator('text=Results')).toBeVisible();
    await expect(page.locator('text=Accessibility Score: 0.75')).toBeVisible();
    await expect(page.locator('text=Total POIs: 23')).toBeVisible();
    await expect(page.locator('text=Total Population: 45,000')).toBeVisible();
    
    // 9. Test export functionality
    await page.route('**/api/v1/results/workflow-test-123/export', route => {
      route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': 'attachment; filename="analysis-results.csv"'
        },
        body: 'location,accessibility_score,total_pois\nSan Francisco,0.75,23'
      });
    });
    
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('button:has-text("Export CSV")')
    ]);
    
    expect(download.suggestedFilename()).toBe('analysis-results.csv');
  });

  test('should handle multi-tab workflow', async ({ browser }) => {
    // Create two contexts (tabs)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // Set up mocks for both pages
    await mockAPIEndpoints(page1);
    await mockAPIEndpoints(page2);
    
    // Tab 1: Start an analysis
    await page1.goto('/getting-started');
    await mockAnalysisWorkflow(page1, 'tab1-job');
    await fillLocationAnalysisForm(page1, 'Austin, TX');
    await page1.click('button:has-text("Analyze Location")');
    
    // Tab 2: Start a different analysis
    await page2.goto('/travel-modes');
    await page2.fill('input[placeholder*="location"]', 'Denver, CO');
    await page2.check('text=Walking');
    await page2.check('text=Transit');
    
    // Mock travel modes analysis
    await page2.route('**/api/v1/analysis/location', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ job_id: 'tab2-job' })
      });
    });
    
    await page2.click('button:has-text("Analyze Travel Modes")');
    
    // Both should complete independently
    await expect(page1.locator('text=Analysis Complete')).toBeVisible({ timeout: 10000 });
    await expect(page2.locator('text=Analyzing')).toBeVisible();
    
    // Clean up
    await context1.close();
    await context2.close();
  });

  test('should maintain state across page navigation', async ({ page }) => {
    await mockAPIEndpoints(page);
    
    // Configure settings
    await page.goto('/settings');
    await page.fill('input[placeholder*="localhost:8000"]', 'http://api.test.com');
    await page.fill('input[placeholder*="API key"]', 'persistent-key-123');
    await page.click('button:has-text("Save Settings")');
    
    // Navigate away and back
    await page.goto('/');
    await page.goto('/getting-started');
    await page.goto('/settings');
    
    // Settings should persist
    await expect(page.locator('input[placeholder*="localhost:8000"]')).toHaveValue('http://api.test.com');
    await expect(page.locator('input[placeholder*="API key"]')).toHaveValue('persistent-key-123');
  });

  test('should handle browser refresh during analysis', async ({ page }) => {
    await mockAPIEndpoints(page);
    await page.goto('/getting-started');
    
    // Start analysis
    await mockAnalysisWorkflow(page, 'refresh-test-job');
    await fillLocationAnalysisForm(page, 'Chicago, IL');
    await page.click('button:has-text("Analyze Location")');
    
    // Refresh page during analysis
    await page.reload();
    
    // Should either show results or allow restarting
    // (depending on implementation - results might be lost or persisted)
    await expect(
      page.locator('text=Getting Started').or(page.locator('text=Results'))
    ).toBeVisible();
  });
});