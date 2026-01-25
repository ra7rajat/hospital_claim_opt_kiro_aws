import { test, expect } from '@playwright/test';

/**
 * Eligibility Check E2E Tests
 * Requirements: 7.2.2
 * Tests: Single check, Batch check, Results display
 */

test.describe('Eligibility Check', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'doctor@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should perform single eligibility check', async ({ page }) => {
    await page.goto('/doctor/eligibility-check');
    
    await page.fill('[name="patientId"]', 'PAT-001');
    await page.fill('[name="procedureCode"]', 'CPT-12345');
    await page.fill('[name="policyNumber"]', 'POL-001');
    await page.click('button:has-text("Check Eligibility")');
    
    await expect(page.locator('text=Checking eligibility')).toBeVisible();
    await expect(page.locator('text=Coverage Result')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Coverage Percentage:')).toBeVisible();
  });

  test('should perform batch eligibility check', async ({ page }) => {
    await page.goto('/doctor/eligibility-check');
    
    await page.click('text=Batch Mode');
    
    await page.setInputFiles('input[type="file"]', 'test-fixtures/patients.csv');
    
    await expect(page.locator('text=100 rows detected')).toBeVisible();
    
    await page.click('button:has-text("Next")');
    
    // Column mapping
    await page.selectOption('[name="patientId"]', 'Patient ID');
    await page.selectOption('[name="procedureCode"]', 'Procedure');
    await page.click('button:has-text("Process Batch")');
    
    await expect(page.locator('text=Processing')).toBeVisible();
    await expect(page.locator('text=Completed: 100/100')).toBeVisible({ timeout: 60000 });
  });

  test('should display and export batch results', async ({ page }) => {
    await page.goto('/doctor/eligibility-check');
    await page.click('text=Batch Mode');
    
    // Assume batch already processed
    await page.goto('/doctor/eligibility-check/batch/BATCH-001');
    
    await expect(page.locator('text=Batch Results')).toBeVisible();
    await expect(page.locator('text=Summary Statistics')).toBeVisible();
    
    // Filter results
    await page.selectOption('[name="filter"]', 'not_covered');
    await expect(page.locator('tr.not-covered')).toHaveCount(10);
    
    // Export
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export CSV")');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.csv');
  });
});
