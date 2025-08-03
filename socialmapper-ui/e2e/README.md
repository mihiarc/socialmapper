# E2E Tests for SocialMapper UI

This directory contains end-to-end tests for the SocialMapper React application using Playwright.

## Structure

```
e2e/
├── tests/               # Test files
│   ├── home-navigation.spec.ts      # Navigation tests
│   ├── analysis-workflow.spec.ts    # Analysis workflow tests
│   ├── settings.spec.ts             # Settings page tests
│   ├── travel-modes.spec.ts         # Travel modes comparison tests
│   ├── full-workflow.spec.ts        # Complete application workflow
│   └── accessibility.spec.ts        # Accessibility and responsive tests
├── helpers/             # Test utilities
│   └── test-utils.ts   # Common test helpers and mocks
└── README.md           # This file
```

## Running Tests

### Prerequisites

1. Install dependencies:
   ```bash
   npm install
   ```

2. Install Playwright browsers (first time only):
   ```bash
   npx playwright install
   ```

### Run all tests
```bash
npm run test:e2e
```

### Run tests with UI mode (recommended for development)
```bash
npm run test:e2e:ui
```

### Debug tests
```bash
npm run test:e2e:debug
```

### Run specific test file
```bash
npx playwright test e2e/tests/settings.spec.ts
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

### Run tests in specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Generate test report
```bash
npm run test:e2e:report
```

## Test Coverage

The E2E tests cover:

1. **Navigation**: Verifying all page routes and navigation links work correctly
2. **Analysis Workflow**: Complete location analysis from start to finish
3. **Settings Management**: API configuration, validation, and persistence
4. **Travel Modes**: Multi-mode comparison functionality
5. **Full Workflow**: End-to-end user journey with authentication
6. **Accessibility**: WCAG compliance and keyboard navigation
7. **Responsive Design**: Mobile, tablet, and desktop viewports

## Writing New Tests

### Basic Test Structure
```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Welcome');
  });
});
```

### Using Test Helpers
```typescript
import { mockAPIEndpoints, fillLocationAnalysisForm } from '../helpers/test-utils';

test('analysis test', async ({ page }) => {
  await mockAPIEndpoints(page);
  await page.goto('/getting-started');
  await fillLocationAnalysisForm(page, 'Portland, OR');
});
```

## Best Practices

1. **Use data-testid attributes**: For reliable element selection
2. **Mock API responses**: Tests should not depend on real backend
3. **Test user journeys**: Focus on complete workflows, not just individual pages
4. **Include error cases**: Test both success and failure scenarios
5. **Keep tests independent**: Each test should be able to run in isolation
6. **Use Page Object Model**: For complex pages, create page objects

## Debugging

### Take screenshots on failure
Tests automatically capture screenshots on failure. Find them in `test-results/`.

### Use page.pause()
```typescript
await page.pause(); // Opens Playwright Inspector
```

### Slow down execution
```typescript
test.use({ video: 'on', slowMo: 500 });
```

### View test report
After running tests:
```bash
npx playwright show-report
```

## CI/CD Integration

The Playwright config includes CI-specific settings:
- Retries on failure (2 attempts on CI)
- Parallel execution disabled on CI
- Fail on `test.only` in CI

## Troubleshooting

### Tests fail with "No tests found"
- Ensure test files end with `.spec.ts`
- Check that tests are in the `e2e/tests` directory

### Browser not installed
```bash
npx playwright install
```

### Port already in use
- The dev server runs on port 5173
- The API server runs on port 8000
- Ensure these ports are free or update `playwright.config.ts`

### Timeout errors
- Increase timeout in specific tests: `test.setTimeout(120000)`
- Or globally in `playwright.config.ts`