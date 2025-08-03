import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('application loads and shows home page', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check that we have a title
    const title = await page.title();
    expect(title).toContain('SocialMapper');
    
    // Check for main heading
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('Welcome to SocialMapper');
  });

  test('can navigate between pages', async ({ page }) => {
    await page.goto('/');
    
    // Check we can see navigation links
    const settingsLink = page.locator('text=Settings').first();
    await expect(settingsLink).toBeVisible();
    
    // Navigate to settings
    await settingsLink.click();
    await page.waitForURL('/settings');
    
    // Verify we're on settings page
    await expect(page.locator('h1')).toContainText('Settings');
  });

  test('renders without JavaScript errors', async ({ page }) => {
    const errors: string[] = [];
    
    // Listen for console errors
    page.on('pageerror', (error) => {
      errors.push(error.message);
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Should have no JavaScript errors
    expect(errors).toHaveLength(0);
  });
});