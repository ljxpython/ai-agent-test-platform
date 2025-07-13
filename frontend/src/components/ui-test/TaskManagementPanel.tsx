/**
 * 任务管理面板组件
 * 显示任务列表、状态、进度等信息
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Typography,
  Progress,
  Tooltip,
  Modal,
  Descriptions,
  Alert,
  Input,
  Select,
  Row,
  Col,
  Empty,
  message,
} from 'antd';
import {
  ReloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface Task {
  id: number;
  task_id: string;
  conversation_id: string;
  project_name: string;
  task_type: string;
  status: string;
  filename: string;
  file_path: string;
  file_size: number;
  file_md5: string;
  progress: number;
  current_step: string;
  result_data: any;
  error_message: string;
  created_at: string;
  updated_at: string;
  started_at: string;
  completed_at: string;
  duration: number;
}

interface TaskManagementPanelProps {
  selectedProject: string;
  refreshKey: number;
  onTaskUpdate?: () => void;
}

const TaskManagementPanel: React.FC<TaskManagementPanelProps> = ({
  selectedProject,
  refreshKey,
  onTaskUpdate,
}) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // 获取任务列表
  const fetchTasks = async () => {
    if (!selectedProject) {
      setTasks([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/ui-test/tasks/project/${selectedProject}`);
      if (response.ok) {
        const data = await response.json();
        setTasks(data.data.tasks || []);
      } else {
        message.error('获取任务列表失败');
      }
    } catch (error) {
      console.error('获取任务列表失败:', error);
      message.error('获取任务列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除任务
  const handleDeleteTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/ui-test/task/${taskId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        message.success('任务删除成功');
        fetchTasks();
        onTaskUpdate?.();
      } else {
        message.error('任务删除失败');
      }
    } catch (error) {
      console.error('删除任务失败:', error);
      message.error('任务删除失败');
    }
  };

  // 查看任务详情
  const handleViewDetail = (task: Task) => {
    setSelectedTask(task);
    setDetailModalVisible(true);
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      pending: { color: 'default', text: '等待中' },
      uploading: { color: 'processing', text: '上传中' },
      validating: { color: 'processing', text: '验证中' },
      duplicate: { color: 'warning', text: '重复文件' },
      processing: { color: 'processing', text: '处理中' },
      analyzing: { color: 'processing', text: '分析中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
      cancelled: { color: 'default', text: '已取消' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] ||
                  { color: 'default', text: status };

    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'processing':
      case 'analyzing':
      case 'uploading':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化持续时间
  const formatDuration = (seconds: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(1)}秒`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}分${remainingSeconds.toFixed(0)}秒`;
  };

  // 过滤任务
  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.filename.toLowerCase().includes(searchText.toLowerCase()) ||
                         task.task_id.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // 表格列定义
  const columns: ColumnsType<Task> = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
      render: (text, record) => (
        <Space>
          {getStatusIcon(record.status)}
          <Tooltip title={text}>
            <Text>{text}</Text>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress, record) => (
        <Progress
          percent={progress}
          size="small"
          status={record.status === 'failed' ? 'exception' :
                  record.status === 'completed' ? 'success' : 'active'}
        />
      ),
    },
    {
      title: '当前步骤',
      dataIndex: 'current_step',
      key: 'current_step',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text type="secondary">{text || '-'}</Text>
        </Tooltip>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size) => formatFileSize(size),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="删除任务">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: '确认删除',
                  content: `确定要删除任务 "${record.filename}" 吗？`,
                  onOk: () => handleDeleteTask(record.task_id),
                });
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 监听刷新
  useEffect(() => {
    fetchTasks();
  }, [selectedProject, refreshKey]);

  // 自动刷新处理中的任务
  useEffect(() => {
    const hasProcessingTasks = tasks.some(task =>
      ['uploading', 'processing', 'analyzing'].includes(task.status)
    );

    if (hasProcessingTasks) {
      const timer = setInterval(fetchTasks, 3000);
      return () => clearInterval(timer);
    }
  }, [tasks, selectedProject]);

  if (!selectedProject) {
    return (
      <Alert
        message="请先选择项目"
        description="选择一个项目后即可查看该项目的任务列表"
        type="info"
        showIcon
      />
    );
  }

  return (
    <div>
      {/* 筛选和搜索 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Search
              placeholder="搜索文件名或任务ID"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ maxWidth: 300 }}
            />
          </Col>
          <Col>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 120 }}
            >
              <Option value="all">全部状态</Option>
              <Option value="pending">等待中</Option>
              <Option value="processing">处理中</Option>
              <Option value="analyzing">分析中</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
            </Select>
          </Col>
          <Col>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchTasks}
              loading={loading}
            >
              刷新
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 任务表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredTasks}
          rowKey="task_id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个任务`,
          }}
          locale={{
            emptyText: <Empty description="暂无任务数据" />,
          }}
        />
      </Card>

      {/* 任务详情模态框 */}
      <Modal
        title="任务详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTask && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="任务ID" span={2}>
              {selectedTask.task_id}
            </Descriptions.Item>
            <Descriptions.Item label="文件名">
              {selectedTask.filename}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {getStatusTag(selectedTask.status)}
            </Descriptions.Item>
            <Descriptions.Item label="进度">
              <Progress percent={selectedTask.progress} size="small" />
            </Descriptions.Item>
            <Descriptions.Item label="当前步骤">
              {selectedTask.current_step || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="文件大小">
              {formatFileSize(selectedTask.file_size)}
            </Descriptions.Item>
            <Descriptions.Item label="MD5">
              <Text code>{selectedTask.file_md5}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedTask.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(selectedTask.updated_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="处理时长">
              {formatDuration(selectedTask.duration)}
            </Descriptions.Item>
            {selectedTask.error_message && (
              <Descriptions.Item label="错误信息" span={2}>
                <Text type="danger">{selectedTask.error_message}</Text>
              </Descriptions.Item>
            )}
            {selectedTask.result_data && Object.keys(selectedTask.result_data).length > 0 && (
              <Descriptions.Item label="结果数据" span={2}>
                <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                  {JSON.stringify(selectedTask.result_data, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default TaskManagementPanel;
