import { test, expect } from '@playwright/test';

/**
 * Dashboard E2E Tests
 * Requirements: 7.2.4
 * Tests: Metrics display, Filtering, Alerts
 */

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should display key metrics', async ({ page }) => {
    await expect(page.locator('text=Total Claims')).toBeVisible();
    await expect(page.locator('text=Settlement Ratio')).toBeVisible();
    await expect(page.locator('text=High Risk Claims')).toBeVisible();
    await expect(page.locator('text=Active Policies')).toBeVisible();
    
    // Check metric values are displayed
    await expect(page.locator('[data-testid="total-claims-value"]')).toHaveText(/\d+/);
    await expect(page.locator('[data-testid="settlement-ratio-value"]')).toHaveText(/\d+%/);
  });

  test('should filter claims by status', async ({ page }) => {
    await page.selectOption('[name="statusFilter"]', 'pending');
    
    await expect(page.locator('tr.claim-row')).toHaveCount(15);
    await expect(page.locator('tr.claim-row .status-pending')).toHaveCount(15);
  });

  test('should filter claims by date range', async ({ page }) => {
    await page.fill('[name="startDate"]', '2026-01-01');
    await page.fill('[name="endDate"]', '2026-01-31');
    await page.click('button:has-text("Apply Filter")');
    
    await expect(page.locator('text=Showing claims from')).toBeVisible();
    await expect(page.locator('tr.claim-row')).toHaveCount(25);
  });

  test('should handle alert notifications', async ({ page }) => {
    await expect(page.locator('.alert-badge')).toHaveText('3');
    
    await page.click('.alert-badge');
    
    await expect(page.locator('text=Alerts')).toBeVisible();
    await expect(page.locator('.alert-item')).toHaveCount(3);
    
    await page.click('.alert-item:first-child');
    
    await expect(page.locator('text=Alert Details')).toBeVisible();
    await expect(page.locator('text=High risk claim detected')).toBeVisible();
  });

  test('should display analytics charts', async ({ page }) => {
    await page.click('text=Analytics');
    
    await expect(page.locator('canvas#claims-chart')).toBeVisible();
    await expect(page.locator('canvas#settlement-chart')).toBeVisible();
    await expect(page.locator('canvas#risk-chart')).toBeVisible();
    
    // Check chart has data
    const chartData = await page.locator('canvas#claims-chart').getAttribute('data-points');
    expect(chartData).toBeTruthy();
  });
});
