import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should save API configuration', async ({ page }) => {
    // Clear existing values
    await page.fill('input[placeholder*="localhost:8000"]', '');
    await page.fill('input[placeholder*="API key"]', '');
    
    // Enter new values
    await page.fill('input[placeholder*="localhost:8000"]', 'http://api.example.com');
    await page.fill('input[placeholder*="API key"]', 'test-api-key-123');
    
    // Save settings
    await page.click('button:has-text("Save Settings")');
    
    // Should show success message
    await expect(page.locator('text=Settings saved successfully')).toBeVisible();
    
    // Reload page to verify persistence
    await page.reload();
    
    // Values should be retained
    await expect(page.locator('input[placeholder*="localhost:8000"]')).toHaveValue('http://api.example.com');
    await expect(page.locator('input[placeholder*="API key"]')).toHaveValue('test-api-key-123');
  });

  test('should test API connection', async ({ page }) => {
    // Mock successful API response
    await page.route('**/api/v1/health', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ status: 'healthy', version: '0.1.0' })
      });
    });
    
    await page.click('button:has-text("Test Connection")');
    
    // Should show success
    await expect(page.locator('text=Connection successful')).toBeVisible();
  });

  test('should handle connection test failure', async ({ page }) => {
    // Mock failed API response
    await page.route('**/api/v1/health', route => {
      route.abort('failed');
    });
    
    await page.click('button:has-text("Test Connection")');
    
    // Should show error
    await expect(page.locator('text=Connection failed')).toBeVisible();
  });

  test('should reset to default values', async ({ page }) => {
    // Change values
    await page.fill('input[placeholder*="localhost:8000"]', 'http://custom.api.com');
    await page.fill('input[placeholder*="API key"]', 'custom-key');
    
    // Reset
    await page.click('button:has-text("Reset to Defaults")');
    
    // Should restore defaults
    await expect(page.locator('input[placeholder*="localhost:8000"]')).toHaveValue('http://localhost:8000');
    await expect(page.locator('input[placeholder*="API key"]')).toHaveValue('');
  });

  test('should validate URL format', async ({ page }) => {
    // Enter invalid URL
    await page.fill('input[placeholder*="localhost:8000"]', 'not-a-url');
    
    // Try to save
    await page.click('button:has-text("Save Settings")');
    
    // Should show validation error
    await expect(page.locator('text=Please enter a valid URL')).toBeVisible();
  });
});