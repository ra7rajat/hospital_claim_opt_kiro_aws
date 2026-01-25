import { test, expect } from '@playwright/test';

/**
 * Bill Audit E2E Tests
 * Requirements: 7.2.3
 * Tests: Bill creation, Audit submission, Results display
 */

test.describe('Bill Audit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'billing@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should create and submit bill for audit', async ({ page }) => {
    await page.goto('/billing/bill-audit');
    
    await page.click('button:has-text("New Bill")');
    
    await page.fill('[name="patientId"]', 'PAT-001');
    await page.fill('[name="claimId"]', 'CLM-001');
    await page.fill('[name="totalAmount"]', '5000');
    
    // Add line items
    await page.click('button:has-text("Add Item")');
    await page.fill('[name="items[0].code"]', 'CPT-12345');
    await page.fill('[name="items[0].amount"]', '2500');
    
    await page.click('button:has-text("Submit for Audit")');
    
    await expect(page.locator('text=Bill submitted')).toBeVisible();
    await expect(page.locator('text=Audit in progress')).toBeVisible();
  });

  test('should display audit results', async ({ page }) => {
    await page.goto('/billing/bill-audit/BILL-001');
    
    await expect(page.locator('text=Audit Results')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Risk Score:')).toBeVisible();
    await expect(page.locator('text=Settlement Ratio:')).toBeVisible();
    await expect(page.locator('text=Optimization Suggestions')).toBeVisible();
  });

  test('should approve bill after audit', async ({ page }) => {
    await page.goto('/billing/bill-audit/BILL-001');
    
    await expect(page.locator('text=Audit Results')).toBeVisible();
    
    await page.click('button:has-text("Approve")');
    
    await expect(page.locator('text=Confirm Approval')).toBeVisible();
    await page.click('button:has-text("Confirm")');
    
    await expect(page.locator('text=Bill approved')).toBeVisible();
    await expect(page.locator('.status-approved')).toBeVisible();
  });

  test('should reject bill with reason', async ({ page }) => {
    await page.goto('/billing/bill-audit/BILL-002');
    
    await expect(page.locator('text=Audit Results')).toBeVisible();
    
    await page.click('button:has-text("Reject")');
    
    await expect(page.locator('text=Rejection Reason')).toBeVisible();
    await page.fill('[name="reason"]', 'Incorrect procedure codes');
    await page.click('button:has-text("Confirm Rejection")');
    
    await expect(page.locator('text=Bill rejected')).toBeVisible();
  });
});
