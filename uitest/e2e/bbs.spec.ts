import { expect } from "@playwright/test";
import { test } from "./fixture";


test.beforeEach(async ({ page }) => {
  page.setViewportSize({ width: 1280, height: 768 });
  await page.goto("http://bbs.huice.com/admin.php");
  await page.waitForLoadState("networkidle");
});

// 更新npm init playwright@latest
// url: http://bbs.huice.com/admin.php
// discuz论坛后台--》论坛--》新分区、新板块的维护
test("在论坛上发帖", async ({
  ai,
  aiQuery,
  aiAssert,
  aiInput,
  aiTap,
  aiScroll,
  aiWaitFor,
    aiAsk
}) => {
    // 使用 aiInput 输入搜索关键词
    await aiInput('admin', '用户名输入框');
    await aiInput('admin', '密码输入框');

    // 使用 aiTap 点击搜索按钮
    await aiTap('提交');
    // 等待搜索结果加载
    await aiAssert('页面右上角有"您好,admin"字样出现');
    await aiTap('点击导航栏中的论坛');
    await aiTap('在正文:点击大模型应用测试这一栏下的添加新板块');
    const data = await aiAssert('根据一级标题,给新版块取一个适合的名字');
    console.log("data:", data);
    await aiInput(data.text, '删除框中的数据,填入新的数据');
    // await aiInput('版块描述', '版块描述');
    // await aiTap('提交');
});
