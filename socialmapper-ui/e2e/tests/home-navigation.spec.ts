import { test, expect } from '@playwright/test';

test.describe('Home Page Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display welcome message and navigation cards', async ({ page }) => {
    // Check welcome message
    await expect(page.locator('h1')).toContainText('Welcome to SocialMapper');
    await expect(page.locator('text=Analyze accessibility to essential services')).toBeVisible();

    // Check all tutorial cards are visible
    await expect(page.locator('text=Getting Started')).toBeVisible();
    await expect(page.locator('text=Custom POIs')).toBeVisible();
    await expect(page.locator('text=Travel Modes')).toBeVisible();
    await expect(page.locator('text=ZCTA Analysis')).toBeVisible();
    await expect(page.locator('text=Address Geocoding')).toBeVisible();
    await expect(page.locator('text=Batch Analysis')).toBeVisible();
  });

  test('should navigate to Getting Started page', async ({ page }) => {
    await page.click('text=Getting Started');
    await page.waitForURL('/getting-started');
    
    // Verify we're on the right page
    await expect(page.locator('h1')).toContainText('Getting Started');
    await expect(page.locator('text=Basic Location Analysis')).toBeVisible();
  });

  test('should navigate to Travel Modes page', async ({ page }) => {
    await page.click('text=Travel Modes');
    await page.waitForURL('/travel-modes');
    
    // Verify we're on the right page
    await expect(page.locator('h1')).toContainText('Travel Modes Comparison');
    await expect(page.locator('text=Compare accessibility across different modes')).toBeVisible();
  });

  test('should navigate to Settings page', async ({ page }) => {
    await page.click('text=Settings');
    await page.waitForURL('/settings');
    
    // Verify we're on the right page
    await expect(page.locator('h1')).toContainText('Settings');
    await expect(page.locator('text=API Configuration')).toBeVisible();
  });
});