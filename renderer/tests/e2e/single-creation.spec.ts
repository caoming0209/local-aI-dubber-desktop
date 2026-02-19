/**
 * E2E test: Single video creation flow (T100).
 *
 * Verifies the complete 5-step wizard:
 * 1. Script input with validation
 * 2. Voice selection
 * 3. Digital human selection
 * 4. Video settings
 * 5. Generation with progress
 */
import { test, expect } from '@playwright/test';

test.describe('Single Video Creation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/single-create');
  });

  test('should display 5-step wizard', async ({ page }) => {
    await expect(page.locator('[data-testid="step-indicator"]')).toBeVisible();
    await expect(page.getByText('文案输入')).toBeVisible();
  });

  test('should validate minimum script length', async ({ page }) => {
    const textarea = page.locator('textarea');
    await textarea.fill('a');
    const nextBtn = page.getByRole('button', { name: /下一步/ });
    await expect(nextBtn).toBeDisabled();
  });

  test('should accept valid script and proceed', async ({ page }) => {
    const textarea = page.locator('textarea');
    await textarea.fill('这是一段有效的测试文案，用于验证单条视频制作流程。');
    const nextBtn = page.getByRole('button', { name: /下一步/ });
    await expect(nextBtn).toBeEnabled();
  });

  test('should navigate through all 5 steps', async ({ page }) => {
    // Step 1: Script
    const textarea = page.locator('textarea');
    await textarea.fill('这是一段有效的测试文案，用于验证完整的五步向导流程。');
    await page.getByRole('button', { name: /下一步/ }).click();

    // Step 2: Voice selection
    await expect(page.getByText('语音选择')).toBeVisible();
    await page.getByRole('button', { name: /下一步/ }).click();

    // Step 3: Digital human
    await expect(page.getByText('数字人选择')).toBeVisible();
    await page.getByRole('button', { name: /下一步/ }).click();

    // Step 4: Video settings
    await expect(page.getByText('视频设置')).toBeVisible();
    await page.getByRole('button', { name: /下一步/ }).click();

    // Step 5: Generate
    await expect(page.getByText('生成视频')).toBeVisible();
  });

  test('should allow going back to previous steps', async ({ page }) => {
    const textarea = page.locator('textarea');
    await textarea.fill('测试返回上一步功能的文案内容。');
    await page.getByRole('button', { name: /下一步/ }).click();

    // Go back
    await page.getByRole('button', { name: /上一步/ }).click();
    await expect(textarea).toHaveValue('测试返回上一步功能的文案内容。');
  });
});
