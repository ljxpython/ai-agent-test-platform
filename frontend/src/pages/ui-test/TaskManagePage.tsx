/**
 * UI测试任务管理页面
 * 专门用于管理UI测试任务的状态、进度和详情
 */

import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Row,
  Col,
  Typography,
  Space,
  Statistic,
  Button,
  Tooltip,
  Avatar,
  Breadcrumb,
  Badge,
} from 'antd';
import {
  BarChartOutlined,
  FileImageOutlined,
  RocketOutlined,
  HomeOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
} from '@ant-design/icons';

import {
  ProjectSelector,
  TaskManagementPanel,
} from '../../components/ui-test';

import type { TaskSummary } from '../../types/ui-test';

const { Content } = Layout;
const { Title, Text } = Typography;

const TaskManagePage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [taskSummary, setTaskSummary] = useState<TaskSummary>({
    total_tasks: 0,
    completed_tasks: 0,
    processing_tasks: 0,
    failed_tasks: 0,
  });
  const [refreshKey, setRefreshKey] = useState(0);

  // 刷新任务统计
  const refreshTaskSummary = async () => {
    if (!selectedProject) return;

    try {
      const response = await fetch(`/api/ui-test/tasks/project/${selectedProject}`);
      if (response.ok) {
        const data = await response.json();
        setTaskSummary(data.data.summary);
      }
    } catch (error) {
      console.error('获取任务统计失败:', error);
    }
  };

  // 项目变更时刷新数据
  useEffect(() => {
    refreshTaskSummary();
  }, [selectedProject, refreshKey]);

  // 处理任务更新事件
  const handleTaskUpdate = () => {
    setRefreshKey(prev => prev + 1);
  };

  // 计算完成率
  const completionRate = taskSummary.total_tasks > 0
    ? Math.round((taskSummary.completed_tasks / taskSummary.total_tasks) * 100)
    : 0;

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '24px' }}>
        {/* 面包屑导航 */}
        <Breadcrumb style={{ marginBottom: '24px' }}>
          <Breadcrumb.Item>
            <HomeOutlined />
            <span>首页</span>
          </Breadcrumb.Item>
          <Breadcrumb.Item>
            <RocketOutlined />
            <span>UI测试</span>
          </Breadcrumb.Item>
          <Breadcrumb.Item>
            <BarChartOutlined />
            <span>任务管理</span>
          </Breadcrumb.Item>
        </Breadcrumb>

        {/* 页面头部 */}
        <div style={{ marginBottom: '24px' }}>
          <Row align="middle" justify="space-between">
            <Col>
              <Space align="center">
                <Avatar
                  size={48}
                  icon={<BarChartOutlined />}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  }}
                />
                <div>
                  <Title
                    level={2}
                    style={{
                      margin: 0,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}
                  >
                    任务管理中心
                  </Title>
                  <Text type="secondary">
                    实时监控UI测试任务状态，管理分析进度和结果
                  </Text>
                </div>
              </Space>
            </Col>
            <Col>
              <Space>
                <ProjectSelector
                  value={selectedProject}
                  onChange={setSelectedProject}
                  style={{ minWidth: 200 }}
                />
                <Tooltip title="上传新图片">
                  <Button
                    type="primary"
                    icon={<CloudUploadOutlined />}
                    onClick={() => window.location.href = '/ui-test/upload'}
                  >
                    上传图片
                  </Button>
                </Tooltip>
                <Tooltip title="查看结果">
                  <Button
                    icon={<EyeOutlined />}
                    onClick={() => window.location.href = '/ui-test/results'}
                  >
                    查看结果
                  </Button>
                </Tooltip>
              </Space>
            </Col>
          </Row>
        </div>

        {/* 统计概览 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="总任务数"
                value={taskSummary.total_tasks}
                prefix={<FileImageOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="已完成"
                value={taskSummary.completed_tasks}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="处理中"
                value={taskSummary.processing_tasks}
                prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: '#faad14' }}
                suffix={
                  taskSummary.processing_tasks > 0 && (
                    <Badge status="processing" />
                  )
                }
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="失败"
                value={taskSummary.failed_tasks}
                prefix={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 完成率进度条 */}
        {taskSummary.total_tasks > 0 && (
          <Card style={{
            marginBottom: '24px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            borderRadius: '12px',
            border: 'none',
          }}>
            <Row align="middle">
              <Col flex="auto">
                <Text strong style={{ color: 'white', fontSize: '16px' }}>
                  项目完成进度
                </Text>
                <div style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  borderRadius: '10px',
                  height: '20px',
                  marginTop: '8px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    background: 'rgba(255, 255, 255, 0.8)',
                    height: '100%',
                    width: `${completionRate}%`,
                    borderRadius: '10px',
                    transition: 'width 0.3s ease',
                  }} />
                </div>
              </Col>
              <Col style={{ marginLeft: '24px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'white' }}>
                    {completionRate}%
                  </div>
                  <Text style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px' }}>
                    {taskSummary.completed_tasks} / {taskSummary.total_tasks}
                  </Text>
                </div>
              </Col>
            </Row>
          </Card>
        )}

        {/* 任务管理面板 */}
        <Card style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
        }}>
          <TaskManagementPanel
            selectedProject={selectedProject}
            refreshKey={refreshKey}
            onTaskUpdate={handleTaskUpdate}
          />
        </Card>

        {/* 操作提示 */}
        <Card
          title="操作指南"
          style={{
            marginTop: '24px',
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(10px)',
            borderRadius: '12px',
          }}
        >
          <Row gutter={[24, 16]}>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>🔍 任务筛选</Text>
                <Text type="secondary">
                  使用搜索框和状态筛选器快速找到特定任务
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>📊 实时监控</Text>
                <Text type="secondary">
                  处理中的任务会自动刷新状态和进度
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>👁️ 详情查看</Text>
                <Text type="secondary">
                  点击"查看详情"按钮查看任务完整信息
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>🗑️ 任务管理</Text>
                <Text type="secondary">
                  支持删除失败或不需要的任务
                </Text>
              </Space>
            </Col>
          </Row>
        </Card>
      </Content>
    </Layout>
  );
};

export default TaskManagePage;
