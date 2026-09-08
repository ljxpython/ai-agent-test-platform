# 修复 usePlatformChatStream 初始化的两个关键响应式 Bug

## 改动时间
2026-09-08

## 相关任务
- Task 1.2: 修复 `usePlatformChatStream` 两个关键 Bug

## 改动文件
- `apps/platform-web/src/modules/chat/composables/usePlatformChatStream.ts`

## 具体改动

### 1. 动态获取 projectId
**位置：** `usePlatformChatStream.ts:72-76` (scopedFetch 内部)

**改动前：**
```typescript
const projectId = options.projectId.value.trim() // 在 composable 最外层被静态求值

const scopedFetch: typeof fetch = (input, init) => {
  const headers = new Headers(init?.headers)
  if (projectId) {
    headers.set('x-project-id', projectId)
  }
  // ...
}
```

**改动后：**
```typescript
// 移除了外层的 const projectId
const scopedFetch: typeof fetch = (input, init) => {
  const headers = new Headers(init?.headers)
  const currentProjectId = options.projectId.value.trim() // 每次 fetch 时动态获取
  if (currentProjectId) {
    headers.set('x-project-id', currentProjectId)
  }
  // ...
}
```

**理由：** 
原有的 `projectId` 在 `usePlatformChatStream` 初始化时被求值。如果是通过 URL `/projects/123/chat` 直接访问，往往初始化时 router 还没完全解析到 ID，导致 `projectId` 为空字符串。后续 `scopedFetch` 在发请求时闭包捕获的始终是最初始的空字符串，导致 platform-api 拦截器报错。

### 2. 修复 assistantId 的响应式丢失
**位置：** `usePlatformChatStream.ts:83`

**改动前：**
```typescript
const stream = useStream<ChatState>({
  // ...
  assistantId: options.target.value?.resolvedTargetId || '',
  // ...
})
```

**改动后：**
```typescript
const stream = useStream<ChatState>({
  // ...
  assistantId: () => options.target.value?.resolvedTargetId || '',
  // ...
})
```

**理由：** 
同理，`options.target` 是一个 `ComputedRef`。改为 getter `() => ...` 后，`useStream` 能动态获取到。

## 影响评估
- ✅ 向后兼容：解决了首次加载 Chat 页面直接失效的严重问题。

## 验证
- [x] 代码已修改
- [ ] 后续通过 Task 1.3 冒烟测试验证流式对话能否跑通（待执行）
