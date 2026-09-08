import { test, expect } from '@playwright/test';
import fs from 'node:fs';

test('reproduce edit and resend: send gpt -> stop -> edit message -> submit edit', async ({ page }) => {
  const consoleMessages: string[] = [];
  const networkLogs: { url: string; method: string; status: number; body?: string }[] = [];

  page.on('console', (msg) => {
    consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
  });

  page.on('request', (request) => {
    consoleMessages.push(`[REQUEST] ${request.method()} ${request.url()} | postData: ${request.postData()?.slice(0, 300)}`);
  });

  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('/runs') || url.includes('/commands') || url.includes('/cancel') || url.includes('/threads') || url.includes('/state')) {
      let bodyText = '';
      try {
        bodyText = await response.text();
      } catch (e) {
        bodyText = '<stream>';
      }
      networkLogs.push({
        url,
        method: response.request().method(),
        status: response.status(),
        body: bodyText.slice(0, 500)
      });
    }
  });

  // 1. Login
  await page.goto('/auth/login');
  await page.fill('input[type="text"], input[name="username"]', 'admin');
  await page.fill('input[type="password"]', 'admin123456');
  await page.click('button:has-text("Log in")');
  await page.waitForURL('**/workspace**', { timeout: 15000 });

  // 2. Open chat page
  await page.goto('/workspace/chat?targetType=assistant&assistantId=workflow_demo&assistantName=Workflow+Demo+HITL&startNew=1');
  await page.waitForTimeout(3000);

  // 3. Select GPT model (gpt-5.6-terra) using search
  const modelSelectorBtn = page.locator('button[aria-label="选择模型"]');
  if (await modelSelectorBtn.isVisible()) {
    await modelSelectorBtn.click();
    await page.waitForTimeout(600);
    const searchInput = page.locator('input[placeholder*="快速搜索模型"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('gpt-5.6-terra');
      await page.waitForTimeout(500);
    }
    const gptModelOption = page.locator('text=gpt-5.6-terra').first();
    if (await gptModelOption.isVisible()) {
      await gptModelOption.click();
      await page.waitForTimeout(600);
    }
  }

  // 4. Send message
  const textarea = page.locator('textarea');
  await textarea.fill('请写一首关于春天的五言绝句。');
  const sendBtn = page.locator('button:has-text("发送消息")');
  await sendBtn.click();

  // 5. Wait for "停止生成" and click it
  const stopBtn = page.locator('button:has-text("停止生成")');
  await expect(stopBtn).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(500);
  await stopBtn.click();

  // Wait for stop
  await expect(sendBtn).toBeVisible({ timeout: 10000 });
  console.log('Stopped successfully.');
  await page.waitForTimeout(1500);

  // 6. Look for "编辑" button on the message
  const editBtn = page.locator('button:has-text("编辑")').first();
  await expect(editBtn).toBeVisible({ timeout: 5000 });
  console.log('Edit button is visible, clicking edit...');
  await editBtn.click();
  await page.waitForTimeout(1000);

  // 7. Find editing textarea inside message turn
  const editTextarea = page.locator('article.pw-chat-turn textarea');
  await expect(editTextarea).toBeVisible({ timeout: 3000 });
  await editTextarea.fill('请写一首关于秋天的七言绝句（已编辑）。');
  await page.waitForTimeout(500);

  // 8. Click "提交重发"
  const submitEditBtn = page.locator('button:has-text("提交重发")');
  await expect(submitEditBtn).toBeVisible({ timeout: 3000 });
  console.log('Clicking 提交重发...');
  await submitEditBtn.click();

  // 9. 核心断言：编辑框必须立即收起，绝不卡在页面上！
  await expect(page.locator('article.pw-chat-turn textarea')).not.toBeVisible({ timeout: 5000 });
  await expect(submitEditBtn).not.toBeVisible({ timeout: 5000 });
  console.log('Verified: Edit textarea and submit button are closed immediately!');

  // 10. 检查新编辑的消息文本已呈现
  await expect(page.locator('text=请写一首关于秋天的七言绝句（已编辑）').first()).toBeVisible({ timeout: 5000 });
  console.log('Verified: Edited message is rendered in the message list!');

  // 等待流式反馈（正常生成或错误提示展示）
  await page.waitForTimeout(6000);

  // Take screenshot
  await page.screenshot({
    path: '/Users/lijiaxin/.gemini/antigravity/brain/fe469ce2-acdc-4fa1-892f-364e4a5b20ca/edit_resend_verified.png',
    fullPage: true
  });

  fs.writeFileSync(
    '/Users/lijiaxin/.gemini/antigravity/brain/fe469ce2-acdc-4fa1-892f-364e4a5b20ca/edit_resend_verified.log',
    `=== CONSOLE ===\n${consoleMessages.join('\n')}\n\n=== NETWORK ===\n${JSON.stringify(networkLogs, null, 2)}`
  );
});
