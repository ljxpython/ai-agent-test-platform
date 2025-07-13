/**
 * 图片上传面板组件
 * 支持多图片上传、实时进度显示、SSE流式输出
 */

import React, { useState } from 'react';
import {
  Card,
  Upload,
  Button,
  Input,
  Form,
  message,
  List,
  Tag,
  Space,
  Typography,
  Row,
  Col,
  Alert,
  Spin,
  Empty,
  Badge,
} from 'antd';
import {
  InboxOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  FileImageOutlined,
  SendOutlined,
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';

const { TextArea } = Input;
const { Text } = Typography;
const { Dragger } = Upload;

interface ImageUploadPanelProps {
  selectedProject: string;
  onUploadComplete?: () => void;
}

interface UploadProgress {
  type: string;
  source: string;
  content: string;
  task_id?: string;
  timestamp: string;
}

interface FileWithStatus extends UploadFile {
  status: 'uploading' | 'done' | 'error' | 'removed';
  progress?: number;
  taskId?: string;
  errorMessage?: string;
}

const ImageUploadPanel: React.FC<ImageUploadPanelProps> = ({
  selectedProject,
  onUploadComplete,
}) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<FileWithStatus[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [conversationId, setConversationId] = useState<string>('');

  // 支持的图片格式
  const supportedFormats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];

  // 文件上传前的验证
  const beforeUpload = (file: File) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error(`${file.name} 不是图片文件`);
      return false;
    }

    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error(`${file.name} 文件大小不能超过 10MB`);
      return false;
    }

    return false; // 阻止自动上传，手动控制
  };

  // 处理文件列表变化
  const handleChange: UploadProps['onChange'] = (info) => {
    let newFileList = [...info.fileList];

    // 过滤重复文件
    newFileList = newFileList.filter((file, index, self) =>
      index === self.findIndex(f => f.name === file.name && f.size === file.size)
    );

    setFileList(newFileList as FileWithStatus[]);
  };

  // 移除文件
  const handleRemove = (file: UploadFile) => {
    setFileList(prev => prev.filter(f => f.uid !== file.uid));
  };

  // 开始上传
  const handleUpload = async () => {
    if (!selectedProject) {
      message.error('请先选择项目');
      return;
    }

    if (fileList.length === 0) {
      message.error('请先选择要上传的图片');
      return;
    }

    try {
      const values = await form.validateFields();
      setUploading(true);
      setUploadProgress([]);

      // 生成对话ID
      const newConversationId = `ui_upload_${Date.now()}`;
      setConversationId(newConversationId);

      // 准备FormData
      const formData = new FormData();
      formData.append('project', selectedProject);
      formData.append('conversation_id', newConversationId);
      formData.append('user_requirement', values.user_requirement || '');

      // 添加图片文件
      fileList.forEach((file) => {
        if (file.originFileObj) {
          formData.append('images', file.originFileObj);
        }
      });

      // 发送上传请求（同步模式）
      const response = await fetch('/api/ui-test/upload/images/batch', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('上传失败');
      }

      const result = await response.json();

      // 处理上传结果
      if (result.code === 200) {
        const data = result.data;

        // 更新进度显示
        setUploadProgress([
          {
            type: 'upload_start',
            source: '图片上传',
            content: `开始处理 ${data.image_count} 张图片`,
            conversation_id: newConversationId,
            timestamp: new Date().toISOString(),
          },
          {
            type: 'upload_complete',
            source: '图片上传',
            content: `处理完成：成功 ${data.processed_count} 张，失败 ${data.failed_count} 张，重复 ${data.duplicate_count} 张`,
            conversation_id: newConversationId,
            timestamp: new Date().toISOString(),
          }
        ]);

        // 更新文件状态
        setFileList(prev => prev.map(file => ({
          ...file,
          status: 'done' as const,
        })));

        setUploading(false);
        message.success(`图片上传完成！成功处理 ${data.processed_count} 张图片`);
        onUploadComplete?.();
      } else {
        throw new Error(result.msg || '上传失败');
      }

    } catch (error) {
      console.error('上传失败:', error);
      message.error('上传失败，请重试');
      setUploading(false);
    }
  };

  // 清空文件列表
  const handleClear = () => {
    setFileList([]);
    setUploadProgress([]);
    form.resetFields();
  };

  // 获取进度状态图标
  const getProgressIcon = (type: string) => {
    switch (type) {
      case 'task_created':
      case 'project_create':
      case 'collection_create':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'task_complete':
      case 'upload_complete':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'task_failed':
      case 'upload_error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <LoadingOutlined style={{ color: '#faad14' }} />;
    }
  };

  return (
    <Row gutter={[24, 24]}>
      {/* 左侧：上传区域 */}
      <Col xs={24} lg={12}>
        <Card title="图片上传" extra={
          <Space>
            <Badge count={fileList.length} showZero>
              <FileImageOutlined />
            </Badge>
            <Button size="small" onClick={handleClear} disabled={uploading}>
              清空
            </Button>
          </Space>
        }>
          <Form form={form} layout="vertical">
            <Form.Item
              name="user_requirement"
              label="分析需求"
              tooltip="描述您希望AI如何分析这些UI界面"
            >
              <TextArea
                rows={3}
                placeholder="例如：分析登录页面的UI元素，识别所有可交互的组件..."
                disabled={uploading}
              />
            </Form.Item>
          </Form>

          <Dragger
            multiple
            fileList={fileList}
            beforeUpload={beforeUpload}
            onChange={handleChange}
            onRemove={handleRemove}
            disabled={uploading}
            style={{ marginBottom: 16 }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽图片到此区域上传</p>
            <p className="ant-upload-hint">
              支持多张图片同时上传，支持格式：{supportedFormats.join(', ')}
            </p>
          </Dragger>

          <Space style={{ width: '100%', justifyContent: 'center' }}>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleUpload}
              loading={uploading}
              disabled={fileList.length === 0 || !selectedProject}
              size="large"
            >
              开始分析
            </Button>
          </Space>

          {!selectedProject && (
            <Alert
              message="请先选择项目"
              type="warning"
              style={{ marginTop: 16 }}
            />
          )}
        </Card>
      </Col>

      {/* 右侧：进度显示 */}
      <Col xs={24} lg={12}>
        <Card
          title="处理进度"
          extra={uploading && <Spin size="small" />}
        >
          {uploadProgress.length === 0 ? (
            <Empty
              description="等待上传..."
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <List
              size="small"
              dataSource={uploadProgress}
              renderItem={(item, index) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={getProgressIcon(item.type)}
                    title={
                      <Space>
                        <Text strong>{item.source}</Text>
                        <Tag color={
                          item.type.includes('complete') ? 'success' :
                          item.type.includes('failed') || item.type.includes('error') ? 'error' :
                          'processing'
                        }>
                          {item.type}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Text>{item.content}</Text>
                        {item.task_id && (
                          <div>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              任务ID: {item.task_id}
                            </Text>
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
              style={{ maxHeight: 400, overflow: 'auto' }}
            />
          )}
        </Card>
      </Col>
    </Row>
  );
};

export default ImageUploadPanel;
