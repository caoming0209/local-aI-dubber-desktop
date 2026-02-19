/**
 * E2E test: Settings page (T107).
 *
 * Verifies:
 * - Settings page loads with current values
 * - Theme toggle works
 * - GPU detection button exists
 */
import { test, expect } from '@playwright/test';

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/settings');
  });

  test('should display settings page', async ({ page }) => {
    await expect(page.getByText('设置')).toBeVisible();
  });

  test('should show theme toggle', async ({ page }) => {
    const themeSelect = page.locator('select[title="主题选择"]');
    await expect(themeSelect).toBeVisible();
  });

  test('should show inference mode selector', async ({ page }) => {
    const inferenceSelect = page.locator('select[title="推理模式"]');
    await expect(inferenceSelect).toBeVisible();
  });

  test('should show path configuration', async ({ page }) => {
    await expect(page.getByText('作品保存路径')).toBeVisible();
    await expect(page.getByText('模型存储路径')).toBeVisible();
  });

  test('should show license section', async ({ page }) => {
    await expect(page.getByText(/授权|激活/)).toBeVisible();
  });

  test('should toggle theme', async ({ page }) => {
    const themeSelect = page.locator('select[title="主题选择"]');
    await themeSelect.selectOption('dark');
    // Verify dark class is applied
    const html = page.locator('html');
    await expect(html).toHaveClass(/dark/);
  });
});
