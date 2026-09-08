import { test, expect } from '@playwright/test';

test.describe('Platform Chat E2E', () => {
  test('should login and navigate to chat onboarding', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Login
    await page.fill('input[type="text"], input[name="username"]', 'admin');
    await page.fill('input[type="password"]', 'admin123456');
    await page.click('button:has-text("Log in")');
    await page.waitForURL('**/workspace**', { timeout: 10000 });
    
    await page.goto('/workspace/chat');
    
    // 验证首次进入引导页面显示正常 (Empty State)
    await expect(page.getByText('首次进入引导')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('去选 Agent')).toBeVisible();
    await expect(page.getByText('去选 Graph')).toBeVisible();
    
    // 注意：真正的聊天界面 (包含搜索会话和输入框) 需要在选定 Agent 后才会渲染。
    // 这部分的 E2E 可以通过 API 预先绑定 Target 来进行扩展。
  });
});
