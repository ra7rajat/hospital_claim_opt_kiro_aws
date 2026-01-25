import { test, expect } from '@playwright/test';

/**
 * Authentication E2E Tests
 * Requirements: 7.2.1
 * Tests: Login, MFA, Password Reset, Session Expiration
 */

test.describe('Authentication Flow', () => {
  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'WrongPassword');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL('/login');
  });

  test('should handle MFA challenge flow', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('[name="email"]', 'mfa-user@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Enter MFA Code')).toBeVisible();
    
    await page.fill('[name="mfaCode"]', '123456');
    await page.click('button:has-text("Verify")');
    
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should complete password reset flow', async ({ page }) => {
    await page.goto('/login');
    
    await page.click('text=Forgot Password');
    await expect(page).toHaveURL('/password-reset');
    
    await page.fill('[name="email"]', 'user@test.com');
    await page.click('button:has-text("Send Reset Link")');
    
    await expect(page.locator('text=Reset link sent')).toBeVisible();
  });

  test('should handle session expiration', async ({ page, context }) => {
    await page.goto('/login');
    
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Clear session cookie
    await context.clearCookies();
    
    // Try to navigate
    await page.goto('/dashboard');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
    await expect(page.locator('text=Session expired')).toBeVisible();
  });
});
