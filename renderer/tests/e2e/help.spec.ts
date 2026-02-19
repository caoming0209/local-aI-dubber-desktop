/**
 * E2E test: Help page (T109).
 *
 * Verifies:
 * - Guide sections displayed
 * - FAQ section with expandable items
 * - Feedback section visible
 */
import { test, expect } from '@playwright/test';

test.describe('Help Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/help');
  });

  test('should display help page title', async ({ page }) => {
    await expect(page.getByText('帮助与指南')).toBeVisible();
  });

  test('should show guide sections', async ({ page }) => {
    await expect(page.getByText('单条视频制作')).toBeVisible();
    await expect(page.getByText('批量制作')).toBeVisible();
    await expect(page.getByText('设置与优化')).toBeVisible();
  });

  test('should show FAQ section', async ({ page }) => {
    await expect(page.getByText('常见问题')).toBeVisible();
    await expect(page.getByText('生成视频需要联网吗？')).toBeVisible();
  });

  test('should show feedback section', async ({ page }) => {
    await expect(page.getByText('遇到问题或有建议？')).toBeVisible();
    await expect(page.getByRole('button', { name: '反馈问题' })).toBeVisible();
  });

  test('should display numbered steps in guides', async ({ page }) => {
    // Check that step numbers are rendered
    const steps = page.locator('ol li');
    expect(await steps.count()).toBeGreaterThan(0);
  });
});
