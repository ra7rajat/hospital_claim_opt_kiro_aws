import { test, expect } from '@playwright/test';

/**
 * Policy Management E2E Tests
 * Requirements: 7.2.1
 * Tests: Upload, View, Compare, Rollback
 */

test.describe('Policy Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should upload policy successfully', async ({ page }) => {
    await page.goto('/admin/policy-management');
    
    await page.click('text=Upload Policy');
    await page.setInputFiles('input[type="file"]', 'test-fixtures/sample-policy.pdf');
    await page.fill('[name="policyName"]', 'Test Policy');
    await page.fill('[name="policyNumber"]', 'POL-001');
    await page.click('button:has-text("Upload")');
    
    await expect(page.locator('text=Processing')).toBeVisible();
    await expect(page.locator('text=Upload successful')).toBeVisible({ timeout: 30000 });
  });

  test('should view policy details', async ({ page }) => {
    await page.goto('/admin/policy-management');
    
    await page.click('tr:has-text("Test Policy")');
    
    await expect(page.locator('text=Policy Details')).toBeVisible();
    await expect(page.locator('text=POL-001')).toBeVisible();
    await expect(page.locator('text=Confidence:')).toBeVisible();
  });

  test('should compare two policy versions', async ({ page }) => {
    await page.goto('/admin/policy-management');
    
    await page.click('tr:has-text("Test Policy")');
    await page.click('button:has-text("Compare Versions")');
    
    await page.selectOption('[name="version1"]', 'v1.0');
    await page.selectOption('[name="version2"]', 'v2.0');
    await page.click('button:has-text("Compare")');
    
    await expect(page.locator('text=Version Comparison')).toBeVisible();
    await expect(page.locator('.added-rule')).toBeVisible();
    await expect(page.locator('.removed-rule')).toBeVisible();
  });

  test('should rollback policy version', async ({ page }) => {
    await page.goto('/admin/policy-management');
    
    await page.click('tr:has-text("Test Policy")');
    await page.click('button:has-text("Compare Versions")');
    
    await page.selectOption('[name="version1"]', 'v2.0');
    await page.selectOption('[name="version2"]', 'v1.0');
    await page.click('button:has-text("Compare")');
    
    await page.click('button:has-text("Rollback to v1.0")');
    
    await expect(page.locator('text=Confirm Rollback')).toBeVisible();
    await page.fill('[name="reason"]', 'Testing rollback functionality');
    await page.click('button:has-text("Confirm")');
    
    await expect(page.locator('text=Rollback successful')).toBeVisible();
  });
});
