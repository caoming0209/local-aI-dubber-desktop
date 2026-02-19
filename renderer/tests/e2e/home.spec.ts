/**
 * E2E test: Home page (T108).
 *
 * Verifies:
 * - Three quick action buttons visible and clickable
 * - Recent works section displayed
 * - Tutorial hint visible
 */
import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/');
  });

  test('should display welcome section', async ({ page }) => {
    await expect(page.getByText('欢迎回来')).toBeVisible();
  });

  test('should show three quick action buttons', async ({ page }) => {
    await expect(page.getByText('新建单条视频')).toBeVisible();
    await expect(page.getByText('批量制作')).toBeVisible();
    await expect(page.getByText('查看作品库')).toBeVisible();
  });

  test('should navigate to single creation', async ({ page }) => {
    await page.getByText('新建单条视频').click();
    await expect(page).toHaveURL(/single-create/);
  });

  test('should navigate to batch creation', async ({ page }) => {
    await page.getByText('批量制作').click();
    await expect(page).toHaveURL(/batch-create/);
  });

  test('should navigate to works library', async ({ page }) => {
    await page.getByText('查看作品库').click();
    await expect(page).toHaveURL(/works/);
  });

  test('should show recent works section', async ({ page }) => {
    await expect(page.getByText('最近使用记录')).toBeVisible();
  });

  test('should show tutorial hint', async ({ page }) => {
    await expect(page.getByText('新手教程')).toBeVisible();
    await page.getByText('查看教程').click();
    await expect(page).toHaveURL(/help/);
  });
});
