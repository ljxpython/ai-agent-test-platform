/**
 * UI测试模块的类型定义
 */

// 基础响应类型
export interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

// 项目相关类型
export interface Project {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  departments?: string[];
  members?: string[];
}

export interface ProjectCreate {
  name: string;
  display_name: string;
  description?: string;
  is_active?: boolean;
}

// 任务相关类型
export type TaskStatus =
  | 'pending'
  | 'uploading'
  | 'validating'
  | 'duplicate'
  | 'processing'
  | 'analyzing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type TaskType =
  | 'image_upload'
  | 'image_analysis'
  | 'ui_element'
  | 'interaction'
  | 'midscene'
  | 'script';

export interface Task {
  id: number;
  task_id: string;
  conversation_id: string;
  project_name: string;
  task_type: TaskType;
  status: TaskStatus;
  filename: string;
  file_path: string;
  file_size: number;
  file_md5: string;
  user_requirement?: string;
  progress: number;
  current_step?: string;
  result_data: TaskResultData;
  error_message?: string;
  parent_task_id?: string;
  collection_name?: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  metadata: Record<string, any>;
}

export interface TaskResultData {
  ui_analysis?: string;
  interaction_analysis?: string;
  midscene_json?: string;
  yaml_script?: string;
  playwright_script?: string;
  [key: string]: any;
}

export interface TaskSummary {
  total_tasks: number;
  completed_tasks: number;
  processing_tasks: number;
  failed_tasks: number;
}

export interface TaskListResponse {
  conversation_id?: string;
  project_name?: string;
  summary: TaskSummary;
  tasks: Task[];
}

// 上传相关类型
export interface UploadFile {
  uid: string;
  name: string;
  status: 'uploading' | 'done' | 'error' | 'removed';
  url?: string;
  thumbUrl?: string;
  size: number;
  type: string;
  originFileObj?: File;
  progress?: number;
  taskId?: string;
  errorMessage?: string;
}

export interface UploadProgress {
  type: string;
  source: string;
  content: string;
  task_id?: string;
  conversation_id: string;
  timestamp: string;
  message_type?: string;
  step?: string;
}

export interface UploadRequest {
  project: string;
  conversation_id?: string;
  user_requirement?: string;
  images: File[];
}

export interface UploadResponse {
  conversation_id: string;
  project: string;
  image_count: number;
  message: string;
}

// 支持格式相关类型
export interface SupportedFormats {
  supported_formats: string[];
  description: string;
}

// Collection相关类型
export interface Collection {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  business_type: string;
  dimension: number;
  metric_type: string;
  index_params: Record<string, any>;
  created_at: string;
  updated_at: string;
  document_count: number;
  is_active: boolean;
}

// 文件相关类型
export interface FileRecord {
  id: number;
  filename: string;
  file_md5: string;
  file_size: number;
  collection_name: string;
  user_id: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// 组件Props类型
export interface ProjectSelectorProps {
  value?: string;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
  placeholder?: string;
  disabled?: boolean;
}

export interface ImageUploadPanelProps {
  selectedProject: string;
  onUploadComplete?: () => void;
  disabled?: boolean;
}

export interface TaskManagementPanelProps {
  selectedProject: string;
  refreshKey: number;
  onTaskUpdate?: () => void;
}

export interface ResultViewPanelProps {
  selectedProject: string;
  refreshKey: number;
}

// 表格列类型
export interface TaskTableColumn {
  title: string;
  dataIndex: string;
  key: string;
  width?: number;
  ellipsis?: boolean;
  render?: (value: any, record: Task, index: number) => React.ReactNode;
  sorter?: boolean | ((a: Task, b: Task) => number);
  filters?: Array<{ text: string; value: string }>;
  onFilter?: (value: string, record: Task) => boolean;
}

// 筛选和搜索类型
export interface TaskFilter {
  status: TaskStatus | 'all';
  taskType: TaskType | 'all';
  dateRange: [string, string] | null;
  searchText: string;
}

export interface TaskSort {
  field: keyof Task;
  order: 'ascend' | 'descend';
}

// 统计数据类型
export interface ProjectStats {
  totalTasks: number;
  completedTasks: number;
  processingTasks: number;
  failedTasks: number;
  completionRate: number;
  averageProcessingTime: number;
  totalFileSize: number;
  uniqueFiles: number;
}

// 错误类型
export interface ApiError {
  code: number;
  message: string;
  details?: any;
}

// 事件类型
export interface UploadEvent {
  type: 'start' | 'progress' | 'complete' | 'error';
  data: any;
}

export interface TaskEvent {
  type: 'created' | 'updated' | 'completed' | 'failed' | 'deleted';
  task: Task;
}

// 配置类型
export interface UITestConfig {
  maxFileSize: number; // MB
  maxFileCount: number;
  supportedFormats: string[];
  autoRefreshInterval: number; // 秒
  sseTimeout: number; // 秒
}

// 主题类型
export interface Theme {
  primaryColor: string;
  successColor: string;
  warningColor: string;
  errorColor: string;
  backgroundColor: string;
  cardBackground: string;
  borderRadius: number;
  boxShadow: string;
}

// 用户偏好类型
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-CN' | 'en-US';
  autoRefresh: boolean;
  refreshInterval: number;
  defaultProject?: string;
  tablePageSize: number;
  showAdvancedFeatures: boolean;
}

// 导出所有类型
export type {
  // 重新导出常用类型
  Task as UITask,
  TaskStatus as UITaskStatus,
  TaskType as UITaskType,
  Project as UIProject,
  UploadFile as UIUploadFile,
  UploadProgress as UIUploadProgress,
};
