import { test } from '@playwright/test';

test('capture luxury chat model selector in chat workspace', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 960 });

  // Login
  await page.goto('/auth/login');
  await page.fill('input[type="text"], input[name="username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123456');
  await page.click('button:has-text("Log in")');
  await page.waitForURL('**/workspace**', { timeout: 15000 });

  // Navigate to Chat page
  await page.goto('/workspace/chat?targetType=assistant&assistantId=workflow_demo&assistantName=Workflow+Demo+HITL&startNew=1');
  await page.waitForTimeout(3000);

  // 1. Capture closed state of trigger button
  const triggerBtn = page.locator('button[title="选择对话运行模型"]');
  await triggerBtn.waitFor({ state: 'visible', timeout: 10000 });
  await page.screenshot({
    path: '/Users/lijiaxin/.gemini/antigravity/brain/fe469ce2-acdc-4fa1-892f-364e4a5b20ca/chat_model_selector_trigger_screenshot.png',
    fullPage: false
  });

  // 2. Click to open the luxury popover panel
  await triggerBtn.click();
  await page.waitForTimeout(600);

  await page.screenshot({
    path: '/Users/lijiaxin/.gemini/antigravity/brain/fe469ce2-acdc-4fa1-892f-364e4a5b20ca/chat_model_selector_open_screenshot.png',
    fullPage: false
  });

  // 3. Type in the search box to test live filter
  const searchInput = page.locator('input[placeholder="快速搜索模型名称、ID 或渠道..."]');
  if (await searchInput.isVisible()) {
    await searchInput.fill('gpt');
    await page.waitForTimeout(400);

    await page.screenshot({
      path: '/Users/lijiaxin/.gemini/antigravity/brain/fe469ce2-acdc-4fa1-892f-364e4a5b20ca/chat_model_selector_search_screenshot.png',
      fullPage: false
    });

    // Select the filtered GPT model
    const gptCard = page.locator('.cursor-pointer:has-text("GPT 5.6 Terra")');
    if (await gptCard.isVisible()) {
      await gptCard.click();
      await page.waitForTimeout(500);

      // Screenshot after selecting GPT model
      await page.screenshot({
        path: '/Users/lijiaxin/.gemini/antigravity/brain/fe469ce2-acdc-4fa1-892f-364e4a5b20ca/chat_model_selector_selected_screenshot.png',
        fullPage: false
      });
    }
  }
});
