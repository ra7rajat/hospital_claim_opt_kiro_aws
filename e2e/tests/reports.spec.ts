import { test, expect } from '@playwright/test';

/**
 * Reports E2E Tests
 * Requirements: 7.2.5
 * Tests: Report generation, Export, Scheduling
 */

test.describe('Reports', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should generate claims report', async ({ page }) => {
    await page.goto('/admin/reports');
    
    await page.click('button:has-text("Generate Report")');
    
    await page.selectOption('[name="reportType"]', 'claims');
    await page.fill('[name="startDate"]', '2026-01-01');
    await page.fill('[name="endDate"]', '2026-01-31');
    await page.click('button:has-text("Generate")');
    
    await expect(page.locator('text=Generating report')).toBeVisible();
    await expect(page.locator('text=Report ready')).toBeVisible({ timeout: 30000 });
    
    await expect(page.locator('text=Total Claims:')).toBeVisible();
    await expect(page.locator('text=Settlement Ratio:')).toBeVisible();
  });

  test('should export report as PDF', async ({ page }) => {
    await page.goto('/admin/reports/RPT-001');
    
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export PDF")');
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toContain('.pdf');
    expect(download.suggestedFilename()).toContain('claims-report');
  });

  test('should export report as CSV', async ({ page }) => {
    await page.goto('/admin/reports/RPT-001');
    
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export CSV")');
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toContain('.csv');
  });

  test('should schedule recurring report', async ({ page }) => {
    await page.goto('/admin/reports');
    
    await page.click('button:has-text("Schedule Report")');
    
    await page.selectOption('[name="reportType"]', 'weekly-summary');
    await page.selectOption('[name="frequency"]', 'weekly');
    await page.selectOption('[name="day"]', 'monday');
    await page.fill('[name="recipients"]', 'admin@test.com, manager@test.com');
    await page.click('button:has-text("Schedule")');
    
    await expect(page.locator('text=Report scheduled')).toBeVisible();
    await expect(page.locator('text=Weekly Summary - Every Monday')).toBeVisible();
  });

  test('should view scheduled reports', async ({ page }) => {
    await page.goto('/admin/reports');
    
    await page.click('text=Scheduled Reports');
    
    await expect(page.locator('.scheduled-report')).toHaveCount(3);
    await expect(page.locator('text=Weekly Summary')).toBeVisible();
    await expect(page.locator('text=Monthly Analytics')).toBeVisible();
  });
});
