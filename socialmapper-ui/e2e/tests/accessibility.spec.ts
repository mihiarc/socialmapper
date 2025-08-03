import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility Tests', () => {
  test('home page should have no accessibility violations', async ({ page }) => {
    await page.goto('/');
    await injectAxe(page);
    await checkA11y(page);
  });

  test('settings page should have no accessibility violations', async ({ page }) => {
    await page.goto('/settings');
    await injectAxe(page);
    await checkA11y(page);
  });

  test('all interactive elements should be keyboard accessible', async ({ page }) => {
    await page.goto('/');
    
    // Tab through all interactive elements
    await page.keyboard.press('Tab');
    let activeElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(activeElement).toBeTruthy();
    
    // Continue tabbing and ensure we can reach all cards
    const cardLinks = await page.locator('a[href^="/"]').count();
    for (let i = 0; i < cardLinks; i++) {
      await page.keyboard.press('Tab');
    }
    
    // Press Enter on focused link
    await page.keyboard.press('Enter');
    
    // Should navigate to new page
    await expect(page).not.toHaveURL('/');
  });

  test('forms should have proper labels', async ({ page }) => {
    await page.goto('/getting-started');
    
    // All inputs should have associated labels
    const inputs = page.locator('input');
    const inputCount = await inputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const label = await input.evaluate((el: HTMLInputElement) => {
        // Check for aria-label, aria-labelledby, or associated label
        return el.getAttribute('aria-label') || 
               el.getAttribute('aria-labelledby') ||
               el.labels?.[0]?.textContent ||
               el.placeholder;
      });
      expect(label).toBeTruthy();
    }
  });

  test('color contrast should meet WCAG standards', async ({ page }) => {
    await page.goto('/');
    await injectAxe(page);
    
    // Check specifically for color contrast
    await checkA11y(page, undefined, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
  });
});

test.describe('Responsive Design Tests', () => {
  test('should be usable on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Check that content is visible and not cut off
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('text=Getting Started')).toBeVisible();
    
    // Navigation should work on mobile
    await page.click('text=Getting Started');
    await expect(page).toHaveURL('/getting-started');
  });

  test('should adapt layout for tablet devices', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    // Check grid layout adapts
    const cards = page.locator('[data-testid="card"]');
    const firstCard = cards.first();
    const cardBox = await firstCard.boundingBox();
    
    // Cards should not be too narrow on tablet
    expect(cardBox?.width).toBeGreaterThan(300);
  });

  test('should handle landscape orientation', async ({ page }) => {
    // Set landscape mobile viewport
    await page.setViewportSize({ width: 667, height: 375 });
    await page.goto('/travel-modes');
    
    // Content should still be accessible
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('button:has-text("Analyze")')).toBeVisible();
  });

  test('touch interactions should work on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/settings');
    
    // Tap instead of click
    await page.tap('input[placeholder*="API key"]');
    await page.type('input[placeholder*="API key"]', 'mobile-test-key');
    
    // Verify input received text
    await expect(page.locator('input[placeholder*="API key"]')).toHaveValue('mobile-test-key');
  });
});