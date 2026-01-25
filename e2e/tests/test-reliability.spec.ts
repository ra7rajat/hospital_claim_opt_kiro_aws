import { test, expect } from '@playwright/test';

/**
 * Property 46: E2E Test Reliability
 * Requirements: 7.1
 * Tests: Consistency, No flaky tests, Data isolation, Cleanup
 */

test.describe('E2E Test Reliability Properties', () => {
  test('Property 46.1: Tests pass consistently', async ({ page }) => {
    // Run same test multiple times to verify consistency
    for (let i = 0; i < 5; i++) {
      await page.goto('/login');
      await page.fill('[name="email"]', 'test@test.com');
      await page.fill('[name="password"]', 'Test123!@#');
      await page.click('button[type="submit"]');
      
      await expect(page).toHaveURL(/\/dashboard/);
      
      await page.click('text=Logout');
      await expect(page).toHaveURL('/login');
    }
  });

  test('Property 46.2: No flaky tests - timing independent', async ({ page }) => {
    // Test should pass regardless of timing variations
    await page.goto('/login');
    
    // Slow down to simulate network latency
    await page.route('**/*', route => {
      setTimeout(() => route.continue(), Math.random() * 1000);
    });
    
    await page.fill('[name="email"]', 'test@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    
    // Should still work with proper waits
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
  });

  test('Property 46.3: Data properly isolated between tests', async ({ page, context }) => {
    // Test 1: Create data
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    
    await page.goto('/admin/policy-management');
    const initialCount = await page.locator('tr.policy-row').count();
    
    // Clear context
    await context.clearCookies();
    await page.goto('/login');
    
    // Test 2: Verify isolation
    await page.fill('[name="email"]', 'test2@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    
    await page.goto('/admin/policy-management');
    const newCount = await page.locator('tr.policy-row').count();
    
    // Different users should see different data
    expect(newCount).not.toBe(initialCount);
  });

  test('Property 46.4: Cleanup after test completion', async ({ page }) => {
    // Create test data
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    
    await page.goto('/admin/policy-management');
    await page.click('button:has-text("Upload Policy")');
    await page.setInputFiles('input[type="file"]', 'test-fixtures/test-policy.pdf');
    await page.fill('[name="policyName"]', 'Cleanup Test Policy');
    await page.click('button:has-text("Upload")');
    
    await expect(page.locator('text=Upload successful')).toBeVisible({ timeout: 30000 });
    
    // Cleanup: Delete test data
    await page.click('tr:has-text("Cleanup Test Policy") button[aria-label="Delete"]');
    await page.click('button:has-text("Confirm Delete")');
    
    await expect(page.locator('text=Policy deleted')).toBeVisible();
    await expect(page.locator('text=Cleanup Test Policy')).not.toBeVisible();
  });
});
