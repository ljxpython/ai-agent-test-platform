# UI测试页面模块

基于AI的UI界面分析与自动化测试用例生成平台的前端页面模块。

## 📁 目录结构

```
frontend/src/pages/ui-test/
├── index.ts                          # 页面导出文件
├── OverviewPage.tsx                  # 概览页面
├── ImageUploadPage.tsx               # 图片上传页面
├── TaskManagePage.tsx                # 任务管理页面
├── ResultViewPage.tsx                # 结果查看页面
└── README.md                         # 说明文档
```

## 🎯 页面功能

### 1. 概览页面 (OverviewPage.tsx)
- **路径**: `/ui-test` 或 `/ui-test/overview`
- **功能**:
  - 项目统计概览
  - 功能快速入口
  - 项目进度可视化
  - 最近任务列表
- **特色**: 仪表板风格，提供全局视图

### 2. 图片上传页面 (ImageUploadPage.tsx)
- **路径**: `/ui-test/upload`
- **功能**:
  - 批量图片上传
  - 拖拽上传支持
  - 实时进度显示
  - 格式验证和重复检测
- **特色**: 专注上传体验，SSE流式反馈

### 3. 任务管理页面 (TaskManagePage.tsx)
- **路径**: `/ui-test/tasks`
- **功能**:
  - 任务列表管理
  - 状态实时跟踪
  - 智能筛选搜索
  - 任务详情查看
- **特色**: 表格式管理，支持批量操作

### 4. 结果查看页面 (ResultViewPage.tsx)
- **路径**: `/ui-test/results`
- **功能**:
  - 分析结果展示
  - 测试脚本查看
  - 结果导出下载
  - 多格式支持
- **特色**: 卡片式展示，支持复制和下载

## 🎨 设计特色

### 1. 统一的设计语言
- **Glassmorphism风格**: 毛玻璃效果和半透明设计
- **渐变色彩**: 蓝紫色渐变主题
- **圆角设计**: 统一的16px圆角
- **阴影效果**: 层次分明的阴影系统

### 2. 导航体验
- **面包屑导航**: 清晰的页面层级关系
- **快速跳转**: 页面间便捷的跳转按钮
- **状态保持**: 项目选择状态在页面间保持

### 3. 响应式设计
- **移动端适配**: 完美适配各种屏幕尺寸
- **栅格布局**: 灵活的响应式栅格系统
- **交互优化**: 触摸友好的交互设计

## 🔧 技术实现

### 1. 组件复用
```typescript
// 共享组件
import {
  ProjectSelector,
  ImageUploadPanel,
  TaskManagementPanel,
  ResultViewPanel,
} from '../../components/ui-test';

// 共享类型
import type { TaskSummary } from '../../types/ui-test';
```

### 2. 状态管理
- **本地状态**: 使用React Hooks管理页面状态
- **项目状态**: 跨页面的项目选择状态
- **数据刷新**: 统一的数据刷新机制

### 3. 路由配置
```typescript
// 路由配置示例
const routes = [
  {
    path: '/ui-test',
    redirect: '/ui-test/overview',
  },
  {
    path: '/ui-test/overview',
    component: OverviewPage,
    name: 'UI测试概览',
  },
  {
    path: '/ui-test/upload',
    component: ImageUploadPage,
    name: '图片上传',
  },
  {
    path: '/ui-test/tasks',
    component: TaskManagePage,
    name: '任务管理',
  },
  {
    path: '/ui-test/results',
    component: ResultViewPage,
    name: '结果查看',
  },
];
```

## 📊 页面关系

```
概览页面 (Overview)
    ├── 快速入口 → 图片上传页面 (Upload)
    ├── 快速入口 → 任务管理页面 (Tasks)
    └── 快速入口 → 结果查看页面 (Results)

图片上传页面 (Upload)
    ├── 上传完成 → 任务管理页面 (Tasks)
    └── 导航按钮 → 任务管理页面 (Tasks)

任务管理页面 (Tasks)
    ├── 导航按钮 → 图片上传页面 (Upload)
    └── 导航按钮 → 结果查看页面 (Results)

结果查看页面 (Results)
    ├── 导航按钮 → 图片上传页面 (Upload)
    └── 导航按钮 → 任务管理页面 (Tasks)
```

## 🚀 使用方式

### 1. 导入页面
```typescript
// 导入单个页面
import { OverviewPage } from './pages/ui-test';

// 导入所有页面
import {
  OverviewPage,
  ImageUploadPage,
  TaskManagePage,
  ResultViewPage,
} from './pages/ui-test';
```

### 2. 菜单配置
```typescript
const menuConfig = {
  key: 'ui-test',
  label: 'UI测试',
  icon: <RocketOutlined />,
  children: [
    {
      key: 'ui-test-overview',
      label: '概览',
      path: '/ui-test/overview',
    },
    {
      key: 'ui-test-upload',
      label: '图片上传',
      path: '/ui-test/upload',
    },
    {
      key: 'ui-test-tasks',
      label: '任务管理',
      path: '/ui-test/tasks',
    },
    {
      key: 'ui-test-results',
      label: '结果查看',
      path: '/ui-test/results',
    },
  ],
};
```

## 📱 页面截图

### 概览页面
- 项目统计仪表板
- 功能入口卡片
- 项目进度环形图
- 最近任务列表

### 图片上传页面
- 拖拽上传区域
- 实时进度显示
- 项目统计卡片
- 功能说明面板

### 任务管理页面
- 任务列表表格
- 状态筛选器
- 进度条显示
- 操作按钮组

### 结果查看页面
- 结果卡片网格
- 多标签页内容
- 复制下载按钮
- 结果类型说明

## 🔄 数据流

### 1. 项目选择流
```
用户选择项目 → 更新全局状态 → 刷新页面数据 → 更新UI显示
```

### 2. 上传处理流
```
选择文件 → 验证格式 → 开始上传 → SSE监听 → 状态更新 → 跳转任务页
```

### 3. 任务管理流
```
加载任务列表 → 实时状态更新 → 筛选搜索 → 详情查看 → 批量操作
```

### 4. 结果查看流
```
获取完成任务 → 解析结果数据 → 卡片展示 → 详情模态框 → 复制下载
```

## 🎯 最佳实践

### 1. 页面性能
- 使用React.memo优化组件渲染
- 实现虚拟滚动处理大量数据
- 懒加载非关键组件

### 2. 用户体验
- 提供加载状态反馈
- 实现错误边界处理
- 支持键盘导航

### 3. 代码维护
- 统一的错误处理机制
- 可复用的工具函数
- 清晰的类型定义

## 🔧 开发指南

### 1. 添加新页面
1. 在 `ui-test` 目录下创建新的页面文件
2. 实现页面组件和功能
3. 在 `index.ts` 中导出页面
4. 更新路由配置和菜单

### 2. 修改现有页面
1. 保持设计风格一致性
2. 复用现有组件和工具函数
3. 更新相关类型定义
4. 测试页面间的跳转

### 3. 样式定制
1. 使用统一的设计令牌
2. 保持响应式设计
3. 遵循无障碍设计原则
4. 测试不同设备的显示效果

这个页面模块提供了完整的UI测试功能，每个页面都有明确的职责和优秀的用户体验！
