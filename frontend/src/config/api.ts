/**
 * API配置文件
 * 统一管理API相关配置
 */

import { getEnvironment, getApiBaseUrl, isDevelopment } from '../utils/env';

// API配置接口
export interface ApiConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

// 获取动态API基础URL
const apiBaseUrl = getApiBaseUrl();

// 默认配置
const defaultConfig: ApiConfig = {
  baseURL: apiBaseUrl,
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// 开发环境配置
const developmentConfig: ApiConfig = {
  ...defaultConfig,
  timeout: 60000,
};

// 生产环境配置
const productionConfig: ApiConfig = {
  ...defaultConfig,
  timeout: 30000,
};

// 测试环境配置
const testConfig: ApiConfig = {
  ...defaultConfig,
  timeout: 10000,
};

/**
 * 获取API配置
 */
export function getApiConfig(): ApiConfig {
  const env = getEnvironment();

  switch (env) {
    case 'development':
      return developmentConfig;
    case 'production':
      return productionConfig;
    case 'test':
      return testConfig;
    default:
      return defaultConfig;
  }
}

/**
 * 设置自定义API配置
 */
export function setApiConfig(config: Partial<ApiConfig>): void {
  Object.assign(getApiConfig(), config);
}

/**
 * API端点配置 - 适配新的版本化API结构
 */
export const API_ENDPOINTS = {
  // 认证相关 - v1版本
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    PROFILE: '/api/v1/auth/me',
    UPDATE_PROFILE: '/api/v1/auth/me',
    CHANGE_PASSWORD: '/api/v1/auth/change-password',
  },

  // 聊天相关 - v1版本
  CHAT: {
    SEND: '/api/v1/chat/',
    STREAM: '/api/v1/chat/stream',
    HISTORY: '/api/v1/chat/history',
    CONVERSATIONS: '/api/v1/chat/conversations',
    DELETE_CONVERSATION: '/api/v1/chat/conversation/{id}',
    STATS: '/api/v1/chat/stats',
    CLEANUP: '/api/v1/chat/cleanup',
  },

  // 测试用例相关 - v1版本
  TESTCASE: {
    UPLOAD: '/api/v1/testcase/upload',
    GENERATE_STREAMING: '/api/v1/testcase/generate/streaming',
    FEEDBACK: '/api/v1/testcase/feedback',
    FEEDBACK_STREAMING: '/api/v1/testcase/feedback/streaming',
    HISTORY: '/api/v1/testcase/history/{id}',
    DELETE_CONVERSATION: '/api/v1/testcase/conversation/{id}',
    TEST: '/api/v1/testcase/test',
    EXPORT: '/api/v1/testcase/export',
  },

  // Midscene相关 - v1版本
  MIDSCENE: {
    UPLOAD: '/api/v1/midscene/upload',
    GENERATE_STREAMING: '/api/v1/midscene/generate/streaming',
    ANALYZE: '/api/v1/midscene/analyze',
    STREAM: '/api/v1/midscene/stream/{id}',
    DELETE_SESSION: '/api/v1/midscene/session/{id}',
    UPLOAD_AND_ANALYZE: '/api/v1/midscene/upload_and_analyze',
    TEST: '/api/v1/midscene/test',
  },

  // 文件相关（保持原有路径，如果有的话）
  FILE: {
    UPLOAD: '/api/v1/file/upload',
    DOWNLOAD: '/api/v1/file/download/{id}',
    DELETE: '/api/v1/file/delete/{id}',
  },
} as const;

/**
 * HTTP状态码
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
} as const;

/**
 * 业务状态码
 */
export const BUSINESS_CODE = {
  SUCCESS: 0,
  INVALID_PARAMS: 1001,
  UNAUTHORIZED: 1002,
  FORBIDDEN: 1003,
  NOT_FOUND: 1004,
  INTERNAL_ERROR: 1005,
  RATE_LIMIT: 1006,
} as const;

// 导出当前配置
export const apiConfig = getApiConfig();

// 打印当前配置（仅在开发环境）
if (isDevelopment()) {
  console.log('API配置:', apiConfig);
}
