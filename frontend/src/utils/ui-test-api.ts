/**
 * UI测试相关的API工具函数
 */

import type {
  Project,
  Task,
  TaskSummary,
  ApiResponse,
  TaskListResponse,
  UploadResponse,
  SupportedFormats,
} from '../types/ui-test';

// 基础请求函数
const request = async <T>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// 项目相关API
export const projectApi = {
  // 获取项目列表
  getProjects: async (): Promise<Project[]> => {
    const response = await request<Project[]>('/api/projects');
    return response.data;
  },

  // 创建项目
  createProject: async (project: {
    name: string;
    display_name: string;
    description?: string;
    is_active?: boolean;
  }): Promise<Project> => {
    const response = await request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(project),
    });
    return response.data;
  },

  // 获取项目详情
  getProject: async (projectName: string): Promise<Project> => {
    const response = await request<Project>(`/api/projects/${projectName}`);
    return response.data;
  },
};

// 任务相关API
export const taskApi = {
  // 获取对话的所有任务
  getTasksByConversation: async (conversationId: string): Promise<TaskListResponse> => {
    const response = await request<TaskListResponse>(`/api/ui-test/tasks/status/${conversationId}`);
    return response.data;
  },

  // 获取单个任务状态
  getTask: async (taskId: string): Promise<Task> => {
    const response = await request<Task>(`/api/ui-test/task/status/${taskId}`);
    return response.data;
  },

  // 获取项目的所有任务
  getTasksByProject: async (projectName: string): Promise<TaskListResponse> => {
    const response = await request<TaskListResponse>(`/api/ui-test/tasks/project/${projectName}`);
    return response.data;
  },

  // 删除任务
  deleteTask: async (taskId: string): Promise<void> => {
    await request(`/api/ui-test/task/${taskId}`, {
      method: 'DELETE',
    });
  },
};

// 上传相关API
export const uploadApi = {
  // 获取支持的图片格式
  getSupportedFormats: async (): Promise<SupportedFormats> => {
    const response = await request<SupportedFormats>('/api/ui-test/supported-formats');
    return response.data;
  },

  // 批量上传图片（同步模式）
  uploadImages: async (
    project: string,
    images: File[],
    userRequirement?: string,
    conversationId?: string
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('project', project);
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }
    if (userRequirement) {
      formData.append('user_requirement', userRequirement);
    }

    images.forEach(image => {
      formData.append('images', image);
    });

    const response = await fetch('/api/ui-test/upload/images/batch', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result.data;
  },


};

// 文件工具函数
export const fileUtils = {
  // 验证图片文件
  validateImageFile: (file: File, supportedFormats: string[]): boolean => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    return supportedFormats.includes(fileExtension);
  },

  // 验证文件大小
  validateFileSize: (file: File, maxSizeMB: number = 10): boolean => {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return file.size <= maxSizeBytes;
  },

  // 格式化文件大小
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  // 生成文件预览URL
  createFilePreviewUrl: (file: File): string => {
    return URL.createObjectURL(file);
  },

  // 释放文件预览URL
  revokeFilePreviewUrl: (url: string): void => {
    URL.revokeObjectURL(url);
  },
};

// 状态工具函数
export const statusUtils = {
  // 获取状态显示文本
  getStatusText: (status: string): string => {
    const statusMap: Record<string, string> = {
      pending: '等待中',
      uploading: '上传中',
      validating: '验证中',
      duplicate: '重复文件',
      processing: '处理中',
      analyzing: '分析中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消',
    };
    return statusMap[status] || status;
  },

  // 获取状态颜色
  getStatusColor: (status: string): string => {
    const colorMap: Record<string, string> = {
      pending: 'default',
      uploading: 'processing',
      validating: 'processing',
      duplicate: 'warning',
      processing: 'processing',
      analyzing: 'processing',
      completed: 'success',
      failed: 'error',
      cancelled: 'default',
    };
    return colorMap[status] || 'default';
  },

  // 判断是否为处理中状态
  isProcessingStatus: (status: string): boolean => {
    return ['uploading', 'validating', 'processing', 'analyzing'].includes(status);
  },

  // 判断是否为完成状态
  isCompletedStatus: (status: string): boolean => {
    return ['completed', 'failed', 'cancelled'].includes(status);
  },
};

// 时间工具函数
export const timeUtils = {
  // 格式化持续时间
  formatDuration: (seconds: number): string => {
    if (!seconds || seconds < 0) return '-';

    if (seconds < 60) {
      return `${seconds.toFixed(1)}秒`;
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    if (minutes < 60) {
      return `${minutes}分${remainingSeconds.toFixed(0)}秒`;
    }

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}小时${remainingMinutes}分`;
  },

  // 格式化相对时间
  formatRelativeTime: (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 1) return '刚刚';
    if (diffMinutes < 60) return `${diffMinutes}分钟前`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}小时前`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}天前`;

    return date.toLocaleDateString();
  },
};
