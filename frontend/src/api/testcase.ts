/**
 * 测试用例相关API - 重新设计版本
 * 适配新的POST流式接口
 */

import { useState } from 'react';
import { request, ApiResponse } from '../utils/request';
import { API_ENDPOINTS } from '../config/api';
import type {
  TestCaseRequest,
  FeedbackRequest,
  StreamResponse,
  // BaseResponse, // 暂未使用
} from './types';

/**
 * 测试用例API服务 - 重新设计版本
 */
export class TestCaseAPI {
  /**
   * 流式生成测试用例（POST + SSE）
   */
  static async generateStreaming(data: TestCaseRequest): Promise<ReadableStreamDefaultReader<Uint8Array>> {
    const response = await fetch(API_ENDPOINTS.TESTCASE.GENERATE_STREAMING, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id: data.conversation_id,
        text_content: data.text_content || '',
        files: data.files || [],
        round_number: data.round_number || 1,
        enable_streaming: data.enable_streaming !== false,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    return response.body.getReader();
  }

  /**
   * 流式处理用户反馈（POST + SSE）
   */
  static async feedbackStreaming(data: FeedbackRequest): Promise<ReadableStreamDefaultReader<Uint8Array>> {
    const response = await fetch(API_ENDPOINTS.TESTCASE.FEEDBACK_STREAMING, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    return response.body.getReader();
  }

  /**
   * 获取对话历史
   */
  static async getHistory(conversationId: string): Promise<ApiResponse<any>> {
    return request.get(`${API_ENDPOINTS.TESTCASE.HISTORY}/${conversationId}`);
  }

  /**
   * 测试服务状态
   */
  static async test(): Promise<ApiResponse<any>> {
    return request.get(API_ENDPOINTS.TESTCASE.TEST);
  }

  /**
   * 导出测试用例
   */
  static async export(data: {
    conversation_id: string;
    format: 'excel' | 'pdf' | 'word';
  }): Promise<ApiResponse<{ download_url: string }>> {
    return request.post(API_ENDPOINTS.TESTCASE.EXPORT, data);
  }
}

/**
 * 流式数据处理工具函数
 */
export const parseStreamData = (chunk: string): StreamResponse[] => {
  const messages: StreamResponse[] = [];
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const data = JSON.parse(line.slice(6));
        messages.push(data);
      } catch (error) {
        console.error('解析SSE数据失败:', error, line);
      }
    }
  }

  return messages;
};

/**
 * 安全的SSE数据解析函数
 */
export const parseSSELine = (line: string): StreamResponse | null => {
  // 跳过空行
  if (!line.trim()) {
    return null;
  }

  // 处理SSE数据行
  let jsonStr = line.trim();

  // 检查是否是SSE数据行
  if (!jsonStr.startsWith('data: ')) {
    // 如果不是以 data: 开头，可能是其他SSE事件类型，跳过
    return null;
  }

  // 移除 "data: " 前缀
  jsonStr = jsonStr.slice(6).trim();

  // 处理可能的重复前缀（这种情况不应该发生，但作为容错处理）
  while (jsonStr.startsWith('data: ')) {
    console.warn('⚠️ 检测到重复的data前缀:', line);
    jsonStr = jsonStr.slice(6).trim();
  }

  // 如果不是以 { 开头，说明不是JSON数据
  if (!jsonStr.startsWith('{')) {
    console.debug('🔍 跳过非JSON数据:', jsonStr);
    return null;
  }

  // 跳过空的JSON数据
  if (!jsonStr) {
    return null;
  }

  try {
    const data = JSON.parse(jsonStr);
    return data as StreamResponse;
  } catch (error) {
    console.error('❌ 解析SSE数据失败:', error);
    console.error('   原始行:', line);
    console.error('   处理后JSON字符串:', jsonStr);
    console.error('   JSON字符串长度:', jsonStr.length);
    console.error('   JSON字符串前50字符:', jsonStr.substring(0, 50));
    return null;
  }
};

/**
 * 处理SSE数据流的通用函数
 */
export const processSSEStream = async (
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onMessage: (message: StreamResponse) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void
): Promise<void> => {
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log('✅ SSE流处理完成');
        onComplete?.();
        break;
      }

      // 解码数据块
      const chunk = decoder.decode(value, { stream: true });
      console.debug('🔍 收到数据块:', chunk.length, '字符');
      buffer += chunk;

      // 使用双换行符分割SSE消息（标准SSE格式）
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || ''; // 保留不完整的消息

      for (const messageBlock of messages) {
        if (!messageBlock.trim()) {
          continue;
        }

        // 处理消息块中的每一行
        const lines = messageBlock.split('\n');
        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }

          console.debug('🔍 处理SSE行:', line);

          const message = parseSSELine(line);
          if (message) {
            console.log('📤 收到SSE消息:', message.type, message.source, '内容长度:', message.content?.length || 0);
            onMessage(message);

            // 检查是否完成
            if (message.type === 'task_result' || message.type === 'error') {
              console.log('🏁 检测到完成信号:', message.type);
              onComplete?.();
              return;
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('❌ SSE流处理错误:', error);
    onError?.(error instanceof Error ? error : new Error(String(error)));
  }
};

/**
 * 流式测试用例生成Hook - 重新设计版本
 */
export const useTestCaseStreaming = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentReader, setCurrentReader] = useState<ReadableStreamDefaultReader<Uint8Array> | null>(null);

  /**
   * 开始流式生成测试用例
   */
  const startGeneration = async (
    data: TestCaseRequest,
    onMessage: (message: StreamResponse) => void
  ): Promise<void> => {
    setIsStreaming(true);
    setError(null);

    try {
      console.log('🚀 开始流式生成测试用例:', data);

      const reader = await TestCaseAPI.generateStreaming(data);
      setCurrentReader(reader);

      // 使用通用SSE处理函数
      await processSSEStream(
        reader,
        onMessage,
        () => {
          console.log('✅ 流式生成完成');
        },
        (error) => {
          throw error;
        }
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '流式生成失败';
      console.error('❌ 流式生成错误:', errorMessage);
      setError(errorMessage);
      throw err;
    } finally {
      setIsStreaming(false);
      setCurrentReader(null);
    }
  };

  /**
   * 开始流式反馈处理
   */
  const startFeedback = async (
    data: FeedbackRequest,
    onMessage: (message: StreamResponse) => void
  ): Promise<void> => {
    setIsStreaming(true);
    setError(null);

    try {
      console.log('🔄 开始流式反馈处理:', data);

      const reader = await TestCaseAPI.feedbackStreaming(data);
      setCurrentReader(reader);

      // 使用通用SSE处理函数
      await processSSEStream(
        reader,
        onMessage,
        () => {
          console.log('✅ 流式反馈处理完成');
        },
        (error) => {
          throw error;
        }
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '流式反馈处理失败';
      console.error('❌ 流式反馈错误:', errorMessage);
      setError(errorMessage);
      throw err;
    } finally {
      setIsStreaming(false);
      setCurrentReader(null);
    }
  };

  /**
   * 停止流式处理
   */
  const stopStreaming = () => {
    if (currentReader) {
      currentReader.cancel();
      setCurrentReader(null);
    }
    setIsStreaming(false);
  };

  return {
    isStreaming,
    error,
    startGeneration,
    startFeedback,
    stopStreaming,
  };
};

/**
 * 简化的测试用例生成Hook - 重新设计版本
 */
export const useTestCaseGeneration = () => {
  const [messages, setMessages] = useState<StreamResponse[]>([]);
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [currentAgent, setCurrentAgent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string>('');

  const { isStreaming, startGeneration, startFeedback, stopStreaming } = useTestCaseStreaming();

  /**
   * 生成测试用例
   */
  const generate = async (data: TestCaseRequest) => {
    setMessages([]);
    setStreamingContent('');
    setCurrentAgent('');
    setLoading(true);
    setError(null);

    try {
      await startGeneration(data, (message) => {
        console.log('📨 处理消息:', message.type, message.source);

        // 更新对话ID
        if (message.conversation_id && !conversationId) {
          setConversationId(message.conversation_id);
        }

        // 处理不同类型的消息
        switch (message.type) {
          case 'streaming_chunk':
            // 流式输出块 - 实时显示
            console.log('🔥 处理streaming_chunk:', message.source, message.content);
            setCurrentAgent(message.source);
            setStreamingContent(prev => {
              const newContent = prev + message.content;
              console.log('🔥 更新streamingContent:', newContent);
              return newContent;
            });
            break;

          case 'text_message':
            // 智能体完整消息
            console.log('📝 处理text_message:', message.source, message.content.length);
            setMessages(prev => [...prev, message]);
            setStreamingContent(''); // 清空流式内容
            setCurrentAgent('');
            break;

          case 'task_result':
            // 任务完成
            console.log('🏁 处理task_result');
            setMessages(prev => [...prev, message]);
            setStreamingContent('');
            setCurrentAgent('');
            break;

          case 'error':
            // 错误消息
            console.log('❌ 处理error:', message.content);
            setError(message.content);
            break;
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 提交反馈
   */
  const submitFeedback = async (feedback: string, previousTestcases: string = '') => {
    if (!conversationId) {
      setError('没有有效的对话ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const feedbackData: FeedbackRequest = {
        conversation_id: conversationId,
        feedback,
        round_number: messages.length + 1,
        previous_testcases: previousTestcases,
      };

      await startFeedback(feedbackData, (message) => {
        console.log('📨 处理反馈消息:', message.type, message.source);

        // 处理不同类型的消息
        switch (message.type) {
          case 'streaming_chunk':
            // 流式输出块 - 实时显示
            setCurrentAgent(message.source);
            setStreamingContent(prev => prev + message.content);
            break;

          case 'text_message':
            // 智能体完整消息
            setMessages(prev => [...prev, message]);
            setStreamingContent(''); // 清空流式内容
            setCurrentAgent('');
            break;

          case 'task_result':
            // 任务完成
            setMessages(prev => [...prev, message]);
            setStreamingContent('');
            setCurrentAgent('');
            break;

          case 'error':
            // 错误消息
            setError(message.content);
            break;
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '反馈处理失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 停止生成
   */
  const stop = () => {
    stopStreaming();
    setLoading(false);
  };

  /**
   * 清空消息
   */
  const clear = () => {
    setMessages([]);
    setStreamingContent('');
    setCurrentAgent('');
    setError(null);
    setConversationId('');
  };

  return {
    messages,
    streamingContent,
    currentAgent,
    loading: loading || isStreaming,
    error,
    conversationId,
    generate,
    submitFeedback,
    stop,
    clear,
  };
};

export default TestCaseAPI;
