/**
 * 知识库管理API服务
 */
import { request } from '@umijs/max';

// 直接访问后端API (后端运行在8002端口,避免与Umi代理的8001端口冲突)
const API_BASE_URL = 'http://localhost:8002/api';

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  upload_time: string;
  status: string;
  chunk_count: number;
  description?: string;
  tags?: string;
}

export interface SearchResult {
  content: string;
  metadata: Record<string, any>;
  score: number;
}

export interface QuestionAnswer {
  question: string;
  answer: string;
  messages: Array<{
    type: string;
    content: string;
  }>;
}

/**
 * 上传文档
 */
export async function uploadDocument(formData: FormData) {
  return request(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    data: formData,
    requestType: 'form',
  });
}

/**
 * 处理文档
 */
export async function processDocument(docId: number) {
  return request(`${API_BASE_URL}/documents/${docId}/process`, {
    method: 'POST',
  });
}

/**
 * 获取文档列表
 */
export async function getDocumentList(params: {
  page?: number;
  page_size?: number;
  status?: string;
}) {
  return request(`${API_BASE_URL}/documents`, {
    method: 'GET',
    params,
  });
}

/**
 * 获取文档详情
 */
export async function getDocument(docId: number) {
  return request(`${API_BASE_URL}/documents/${docId}`, {
    method: 'GET',
  });
}

/**
 * 删除文档
 */
export async function deleteDocument(docId: number) {
  return request(`${API_BASE_URL}/documents/${docId}`, {
    method: 'DELETE',
  });
}

/**
 * 搜索文档
 */
export async function searchDocuments(params: {
  query: string;
  k?: number;
  search_type?: string;
}) {
  return request(`${API_BASE_URL}/search`, {
    method: 'POST',
    data: params,
  });
}

/**
 * 问答
 */
export async function askQuestion(question: string) {
  return request(`${API_BASE_URL}/question`, {
    method: 'POST',
    data: { question },
  });
}

/**
 * 健康检查
 */
export async function healthCheck() {
  return request(`${API_BASE_URL}/health`, {
    method: 'GET',
  });
}
