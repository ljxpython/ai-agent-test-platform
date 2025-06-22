# 前端架构详细文档

## 概述

本项目前端采用现代化的React技术栈，基于React 18和TypeScript构建，使用Ant Design Pro风格的企业级UI组件库，采用组件化架构设计，支持SSE流式数据处理和响应式布局。

## 技术栈

### 核心框架
- **React 18**: 现代化前端框架，支持并发特性和自动批处理
- **TypeScript**: 类型安全的JavaScript超集，提供更好的开发体验
- **Vite**: 下一代前端构建工具，快速的开发服务器和构建
- **React Router DOM 6**: 声明式路由管理

### UI组件库
- **Ant Design 5.12+**: 企业级UI设计语言和组件库
- **Ant Design Pro Components**: 高级业务组件
- **Ant Design Pro Layout**: 专业的布局组件
- **Ant Design Icons**: 丰富的图标库

### 数据处理
- **Axios**: HTTP客户端，支持请求拦截和响应处理
- **SWR**: 数据获取库，支持缓存、重新验证和错误处理
- **Day.js**: 轻量级日期处理库

### 内容渲染
- **React Markdown**: Markdown内容渲染
- **React Syntax Highlighter**: 代码语法高亮
- **Rehype/Remark**: Markdown处理插件生态
- **Highlight.js**: 代码高亮库

### 开发工具
- **ESLint**: 代码质量检查
- **TypeScript Compiler**: 类型检查
- **Vite Plugin React**: React支持插件

## 项目结构

```
frontend/
├── public/                     # 静态资源
│   └── vite.svg               # 应用图标
├── src/                       # 源代码目录
│   ├── main.tsx               # 应用入口文件
│   ├── App.tsx                # 根组件
│   ├── index.css              # 全局样式
│   ├── components/            # 通用组件
│   │   ├── SideNavigation.tsx     # 侧边导航组件
│   │   ├── TopNavigation.tsx      # 顶部导航组件
│   │   ├── PageLayout.tsx         # 页面布局组件
│   │   ├── ChatMessage.tsx        # 聊天消息组件
│   │   ├── ChatInput.tsx          # 聊天输入组件
│   │   ├── MarkdownRenderer.tsx   # Markdown渲染组件
│   │   ├── FileUpload.tsx         # 文件上传组件
│   │   ├── AgentMessage.tsx       # 智能体消息组件
│   │   ├── StreamingContent.tsx   # 流式内容组件
│   │   └── LoadingSpinner.tsx     # 加载动画组件
│   ├── pages/                 # 页面组件
│   │   ├── HomePage.tsx           # 首页
│   │   ├── LoginPage.tsx          # 登录页面
│   │   ├── ChatPage.tsx           # AI对话页面
│   │   ├── TestCasePage.tsx       # 测试用例生成页面
│   │   ├── MidscenePage.tsx       # Midscene智能体页面
│   │   ├── UITestScriptPage.tsx   # UI测试脚本页面
│   │   ├── ScrollTestPage.tsx     # 滚动测试页面
│   │   ├── UserProfilePage.tsx    # 用户资料页面
│   │   └── system/                # 系统管理页面
│   │       ├── UserManagePage.tsx     # 用户管理
│   │       ├── RoleManagePage.tsx     # 角色管理
│   │       ├── DepartmentManagePage.tsx # 部门管理
│   │       └── ApiManagePage.tsx      # API管理
│   ├── services/              # API服务层
│   │   ├── api.ts                 # 通用API配置
│   │   ├── auth.ts                # 认证服务
│   │   ├── chat.ts                # 对话服务
│   │   ├── testcase.ts            # 测试用例服务
│   │   ├── midscene.ts            # Midscene服务
│   │   └── system.ts              # 系统管理服务
│   ├── types/                 # 类型定义
│   │   ├── auth.ts                # 认证相关类型
│   │   ├── chat.ts                # 对话相关类型
│   │   ├── testcase.ts            # 测试用例相关类型
│   │   ├── midscene.ts            # Midscene相关类型
│   │   └── common.ts              # 通用类型
│   ├── hooks/                 # 自定义Hooks
│   │   ├── useAuth.ts             # 认证Hook
│   │   ├── useSSE.ts              # SSE流式数据Hook
│   │   ├── useLocalStorage.ts     # 本地存储Hook
│   │   └── useDebounce.ts         # 防抖Hook
│   ├── utils/                 # 工具函数
│   │   ├── request.ts             # 请求工具
│   │   ├── storage.ts             # 存储工具
│   │   ├── format.ts              # 格式化工具
│   │   └── constants.ts           # 常量定义
│   ├── config/                # 配置文件
│   │   └── api.ts                 # API配置
│   ├── docs/                  # 文档组件
│   └── examples/              # 示例组件
├── package.json               # 项目依赖配置
├── package-lock.json          # 依赖锁定文件
├── tsconfig.json              # TypeScript配置
├── tsconfig.node.json         # Node.js TypeScript配置
├── vite.config.ts             # Vite构建配置
└── index.html                 # HTML模板
```

## 架构设计模式

### 1. 组件化架构

**组件分层**:
- **页面组件** (Pages): 路由级别的顶层组件
- **布局组件** (Layouts): 页面结构和导航组件
- **业务组件** (Business): 特定业务逻辑的组件
- **通用组件** (Common): 可复用的基础组件

**组件设计原则**:
```typescript
// 单一职责原则
const ChatMessage: React.FC<ChatMessageProps> = ({ message, onCopy }) => {
  // 只负责消息显示和基本交互
}

// 组合优于继承
const ChatPage: React.FC = () => {
  return (
    <PageLayout>
      <ChatInput onSend={handleSend} />
      <ChatMessageList messages={messages} />
    </PageLayout>
  )
}
```

### 2. 状态管理模式

**本地状态** (useState):
```typescript
// 组件内部状态
const [messages, setMessages] = useState<ChatMessage[]>([])
const [loading, setLoading] = useState(false)
```

**全局状态** (Context + localStorage):
```typescript
// 用户认证状态
const AuthContext = createContext<AuthContextType | null>(null)

// 主题配置状态
const ThemeContext = createContext<ThemeContextType | null>(null)
```

**服务端状态** (SWR):
```typescript
// 数据获取和缓存
const { data, error, mutate } = useSWR('/api/users', fetcher)
```

### 3. 路由管理模式

**路由配置** (`src/App.tsx`):
```typescript
const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* 公开路由 */}
        <Route path="/login" element={<LoginPage />} />

        {/* 受保护的路由 */}
        <Route path="/" element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        } />

        {/* 带侧边栏的路由 */}
        <Route path="/chat" element={
          <ProtectedRoute>
            <SideNavigation>
              <ChatPage />
            </SideNavigation>
          </ProtectedRoute>
        } />
      </Routes>
    </Router>
  )
}
```

**路由保护**:
```typescript
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />
}
```

## 核心组件详解

### 1. 应用入口 (main.tsx)

**功能**: 应用初始化和全局配置

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
```

**特性**:
- React 18严格模式
- Ant Design中文本地化
- 全局样式导入

### 2. 侧边导航 (SideNavigation.tsx)

**功能**: 可折叠的侧边导航栏

**特性**:
- 层级菜单结构
- 折叠/展开状态管理
- 路由高亮显示
- 响应式设计

**使用示例**:
```typescript
const menuItems = [
  {
    key: 'ai-assist',
    label: 'AI助力',
    icon: <RobotOutlined />,
    children: [
      { key: '/chat', label: 'AI对话' },
      { key: '/testcase', label: '测试用例生成' }
    ]
  },
  {
    key: 'ui-test',
    label: 'UI测试',
    icon: <AppstoreOutlined />,
    children: [
      { key: '/midscene', label: 'Midscene智能体' }
    ]
  }
]
```

### 3. 流式内容组件 (StreamingContent.tsx)

**功能**: 处理SSE流式数据显示

**特性**:
- 实时内容更新
- 打字机效果
- Markdown渲染
- 错误处理

**使用示例**:
```typescript
const StreamingContent: React.FC<StreamingContentProps> = ({
  content,
  isStreaming,
  onComplete
}) => {
  return (
    <div className="streaming-content">
      <MarkdownRenderer content={content} />
      {isStreaming && <LoadingSpinner />}
    </div>
  )
}
```

## API服务层设计

### 1. 通用API配置 (services/api.ts)

**功能**: 统一的HTTP客户端配置

```typescript
import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 清除token并跳转登录
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### 2. SSE流式服务 (services/sse.ts)

**功能**: 处理Server-Sent Events流式数据

```typescript
export class SSEService {
  private eventSource: EventSource | null = null

  connect(url: string, options: SSEOptions): Promise<void> {
    return new Promise((resolve, reject) => {
      this.eventSource = new EventSource(url)

      this.eventSource.onopen = () => resolve()
      this.eventSource.onerror = (error) => reject(error)

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          options.onMessage?.(data)
        } catch (error) {
          options.onError?.(error)
        }
      }
    })
  }

  disconnect() {
    this.eventSource?.close()
    this.eventSource = null
  }
}
```

### 3. 认证服务 (services/auth.ts)

**功能**: 用户认证和权限管理

```typescript
export const authService = {
  // 用户登录
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await api.post('/v1/auth/login', credentials)
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('user_info', JSON.stringify(response.user))
    }
    return response
  },

  // 获取当前用户信息
  async getCurrentUser(): Promise<User> {
    return api.get('/v1/auth/me')
  },

  // 用户登出
  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    window.location.href = '/login'
  },

  // 检查是否已认证
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }
}
```

## 自定义Hooks

### 1. 认证Hook (hooks/useAuth.ts)

**功能**: 管理用户认证状态

```typescript
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const userInfo = await authService.getCurrentUser()
          setUser(userInfo)
        }
      } catch (error) {
        console.error('Auth initialization failed:', error)
        authService.logout()
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    const response = await authService.login(credentials)
    setUser(response.user)
    return response
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  return { user, loading, login, logout, isAuthenticated: !!user }
}
```

### 2. SSE流式数据Hook (hooks/useSSE.ts)

**功能**: 处理流式数据接收

```typescript
export const useSSE = () => {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const sseServiceRef = useRef<SSEService | null>(null)

  const connect = useCallback(async (url: string, onMessage: (data: any) => void) => {
    try {
      sseServiceRef.current = new SSEService()
      await sseServiceRef.current.connect(url, {
        onMessage,
        onError: (err) => setError(err.message)
      })
      setIsConnected(true)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
    }
  }, [])

  const disconnect = useCallback(() => {
    sseServiceRef.current?.disconnect()
    setIsConnected(false)
  }, [])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return { isConnected, error, connect, disconnect }
}
```

### 3. 本地存储Hook (hooks/useLocalStorage.ts)

**功能**: 管理本地存储状态

```typescript
export const useLocalStorage = <T>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }

  return [storedValue, setValue] as const
}
```

## 页面组件设计

### 1. AI对话页面 (pages/ChatPage.tsx)

**功能**: AI智能对话界面

**核心特性**:
- 实时流式对话
- 消息历史管理
- Markdown渲染
- 代码高亮

**组件结构**:
```typescript
const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const { connect, disconnect } = useSSE()

  const handleSendMessage = async (content: string) => {
    // 1. 添加用户消息
    const userMessage = { role: 'user', content, timestamp: Date.now() }
    setMessages(prev => [...prev, userMessage])

    // 2. 建立SSE连接
    setIsStreaming(true)
    await connect('/v1/chat/stream', (data) => {
      if (data.type === 'streaming_chunk') {
        // 更新流式内容
        updateStreamingMessage(data.content)
      } else if (data.type === 'task_result') {
        // 完成流式传输
        setIsStreaming(false)
        disconnect()
      }
    })
  }

  return (
    <div className="chat-page">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {isStreaming && <StreamingContent />}
      </div>
      <ChatInput onSend={handleSendMessage} disabled={isStreaming} />
    </div>
  )
}
```

### 2. 测试用例生成页面 (pages/TestCasePage.tsx)

**功能**: AI驱动的测试用例生成

**核心特性**:
- 文件上传支持
- 多智能体协作显示
- 用户反馈机制
- 结果导出功能

**布局设计**:
```typescript
const TestCasePage: React.FC = () => {
  return (
    <div className="testcase-page">
      {/* 左侧面板 - 输入区域 */}
      <div className="input-panel">
        <Card title="需求输入">
          <FileUpload onUpload={handleFileUpload} />
          <TextArea
            placeholder="请描述测试需求..."
            value={requirements}
            onChange={setRequirements}
          />
          <Button
            type="primary"
            onClick={handleGenerate}
            loading={isGenerating}
          >
            开始生成
          </Button>
        </Card>
      </div>

      {/* 右侧面板 - 结果显示 */}
      <div className="result-panel">
        <Card title="生成结果">
          <AgentMessage
            agentType="requirement_analyst"
            content={analysisResult}
          />
          <AgentMessage
            agentType="testcase_expert"
            content={testcaseResult}
          />
          <FeedbackSection onFeedback={handleFeedback} />
        </Card>
      </div>
    </div>
  )
}
```

## 样式和主题

### 1. 全局样式 (index.css)

**功能**: 基础样式重置和全局样式

```css
/* 样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 全局字体 */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
               'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue',
               Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #333;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

/* 响应式断点 */
@media (max-width: 768px) {
  .desktop-only {
    display: none;
  }
}

@media (min-width: 769px) {
  .mobile-only {
    display: none;
  }
}
```

### 2. Ant Design主题定制

**配置**: 通过ConfigProvider自定义主题

```typescript
const themeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      siderBg: '#001529',
      headerBg: '#fff',
    },
    Menu: {
      darkItemBg: '#001529',
      darkItemSelectedBg: '#1890ff',
    },
  },
}

<ConfigProvider theme={themeConfig}>
  <App />
</ConfigProvider>
```

## 构建和部署

### 1. Vite配置 (vite.config.ts)

**功能**: 开发服务器和构建配置

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd', '@ant-design/icons'],
        }
      }
    }
  }
})
```

### 2. TypeScript配置 (tsconfig.json)

**功能**: TypeScript编译配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 3. 部署脚本

**开发环境**:
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 类型检查
npm run type-check
```

**生产环境**:
```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 部署到静态服务器
npm run deploy
```

## 性能优化

### 1. 代码分割

**路由级别分割**:
```typescript
import { lazy, Suspense } from 'react'

const ChatPage = lazy(() => import('./pages/ChatPage'))
const TestCasePage = lazy(() => import('./pages/TestCasePage'))

const App = () => (
  <Suspense fallback={<LoadingSpinner />}>
    <Routes>
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/testcase" element={<TestCasePage />} />
    </Routes>
  </Suspense>
)
```

**组件级别分割**:
```typescript
const HeavyComponent = lazy(() => import('./HeavyComponent'))

const ParentComponent = () => {
  const [showHeavy, setShowHeavy] = useState(false)

  return (
    <div>
      {showHeavy && (
        <Suspense fallback={<Spin />}>
          <HeavyComponent />
        </Suspense>
      )}
    </div>
  )
}
```

### 2. 内存优化

**防止内存泄漏**:
```typescript
const useCleanup = () => {
  useEffect(() => {
    const timer = setInterval(() => {
      // 定时任务
    }, 1000)

    return () => {
      clearInterval(timer)
    }
  }, [])
}
```

**大列表虚拟化**:
```typescript
import { FixedSizeList as List } from 'react-window'

const VirtualizedList = ({ items }) => (
  <List
    height={600}
    itemCount={items.length}
    itemSize={50}
    itemData={items}
  >
    {({ index, style, data }) => (
      <div style={style}>
        {data[index].content}
      </div>
    )}
  </List>
)
```

### 3. 网络优化

**请求缓存**:
```typescript
// 使用SWR进行数据缓存
const { data, error } = useSWR('/api/users', fetcher, {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  refreshInterval: 60000, // 1分钟刷新
})
```

**请求去重**:
```typescript
const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}
```

## 测试策略

### 1. 单元测试

**组件测试**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import ChatInput from '../ChatInput'

describe('ChatInput', () => {
  it('should call onSend when submit button is clicked', () => {
    const mockOnSend = jest.fn()
    render(<ChatInput onSend={mockOnSend} />)

    const input = screen.getByPlaceholderText('请输入消息...')
    const button = screen.getByText('发送')

    fireEvent.change(input, { target: { value: 'test message' } })
    fireEvent.click(button)

    expect(mockOnSend).toHaveBeenCalledWith('test message')
  })
})
```

### 2. 集成测试

**API集成测试**:
```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useAuth } from '../hooks/useAuth'

describe('useAuth', () => {
  it('should login successfully', async () => {
    const { result } = renderHook(() => useAuth())

    await act(async () => {
      await result.current.login({
        username: 'test',
        password: 'password'
      })
    })

    await waitFor(() => {
      expect(result.current.user).toBeTruthy()
      expect(result.current.isAuthenticated).toBe(true)
    })
  })
})
```

### 3. E2E测试

**端到端测试**:
```typescript
// cypress/e2e/chat.cy.ts
describe('Chat Flow', () => {
  it('should complete a chat conversation', () => {
    cy.visit('/login')
    cy.get('[data-testid=username]').type('test')
    cy.get('[data-testid=password]').type('test')
    cy.get('[data-testid=login-button]').click()

    cy.url().should('include', '/')
    cy.get('[data-testid=chat-link]').click()

    cy.get('[data-testid=chat-input]').type('Hello AI')
    cy.get('[data-testid=send-button]').click()

    cy.get('[data-testid=chat-messages]').should('contain', 'Hello AI')
    cy.get('[data-testid=ai-response]').should('be.visible')
  })
})
```

## 扩展指南

### 1. 添加新页面

1. **创建页面组件** (`src/pages/NewPage.tsx`)
2. **添加路由配置** (`src/App.tsx`)
3. **更新导航菜单** (`src/components/SideNavigation.tsx`)
4. **添加API服务** (`src/services/newService.ts`)
5. **定义类型** (`src/types/newTypes.ts`)

### 2. 集成新的UI组件

1. **安装组件库** (`npm install new-component-lib`)
2. **创建封装组件** (`src/components/NewComponent.tsx`)
3. **添加类型定义** (`src/types/components.ts`)
4. **编写使用文档** (`src/docs/NewComponent.md`)

### 3. 添加新的数据流

1. **定义数据类型** (`src/types/`)
2. **创建API服务** (`src/services/`)
3. **实现自定义Hook** (`src/hooks/`)
4. **更新页面组件** (`src/pages/`)

这个前端架构文档为开发者提供了完整的技术指南，涵盖了组件设计、状态管理、API集成、性能优化和测试策略等各个方面。
