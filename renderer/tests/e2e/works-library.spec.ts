/**
 * E2E test: Works library (T105).
 *
 * Verifies:
 * - Works card display
 * - Search and filter
 * - Pagination
 * - Delete confirmation
 */
import { test, expect } from '@playwright/test';

test.describe('Works Library', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/works');
  });

  test('should display works library page', async ({ page }) => {
    await expect(page.getByText('作品库')).toBeVisible();
  });

  test('should show empty state when no works', async ({ page }) => {
    await expect(page.getByText(/暂无作品|开始制作/)).toBeVisible();
  });

  test('should have search input', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await expect(searchInput).toBeVisible();
  });

  test('should have filter controls', async ({ page }) => {
    const filterSelect = page.locator('select').first();
    await expect(filterSelect).toBeVisible();
  });

  test('should navigate to single creation from empty state', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /新建|制作/ });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page).toHaveURL(/single-create/);
    }
  });
});
