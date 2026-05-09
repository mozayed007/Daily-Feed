import { test, expect } from '@playwright/test';

test.describe('Daily Feed Smoke Tests', () => {
  test('homepage loads without errors', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Welcome back').or(page.locator('text=Sign in'))).toBeVisible();
  });

  test('login page loads', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('text=Welcome back')).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('register page loads', async ({ page }) => {
    await page.goto('/register');
    await expect(page.locator('text=Create an account')).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('forgot password page loads', async ({ page }) => {
    await page.goto('/forgot-password');
    await expect(page.locator('text=Forgot Password')).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('404 page works', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await expect(page.locator('text=404')).toBeVisible();
    await expect(page.locator('text=Page Not Found')).toBeVisible();
  });
});
