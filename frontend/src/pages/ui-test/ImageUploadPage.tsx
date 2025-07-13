/**
 * UI测试图片上传页面
 * 专门用于UI界面图片的批量上传和分析
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
} from 'antd';
import {
  CloudUploadOutlined,
  FileImageOutlined,
  RocketOutlined,
  HomeOutlined,
  BarChartOutlined,
} from '@ant-design/icons';

import {
  ProjectSelector,
  ImageUploadPanel,
} from '../../components/ui-test';

import type { TaskSummary } from '../../types/ui-test';

const { Content } = Layout;
const { Title, Text } = Typography;

const ImageUploadPage: React.FC = () => {
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

  // 处理上传完成事件
  const handleUploadComplete = () => {
    setRefreshKey(prev => prev + 1);
  };

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
            <CloudUploadOutlined />
            <span>图片上传</span>
          </Breadcrumb.Item>
        </Breadcrumb>

        {/* 页面头部 */}
        <div style={{ marginBottom: '24px' }}>
          <Row align="middle" justify="space-between">
            <Col>
              <Space align="center">
                <Avatar
                  size={48}
                  icon={<CloudUploadOutlined />}
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
                    UI界面图片上传
                  </Title>
                  <Text type="secondary">
                    批量上传UI界面截图，AI智能分析界面元素和交互流程
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
                <Tooltip title="查看任务管理">
                  <Button
                    icon={<BarChartOutlined />}
                    onClick={() => window.location.href = '/ui-test/tasks'}
                  >
                    任务管理
                  </Button>
                </Tooltip>
              </Space>
            </Col>
          </Row>
        </div>

        {/* 项目统计卡片 */}
        {selectedProject && (
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={24} sm={12} md={6}>
              <Card style={{
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(10px)',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
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
              }}>
                <Statistic
                  title="已完成"
                  value={taskSummary.completed_tasks}
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
              }}>
                <Statistic
                  title="处理中"
                  value={taskSummary.processing_tasks}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card style={{
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(10px)',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}>
                <Statistic
                  title="失败"
                  value={taskSummary.failed_tasks}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* 主要功能区域 */}
        <Card style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
        }}>
          <ImageUploadPanel
            selectedProject={selectedProject}
            onUploadComplete={handleUploadComplete}
          />
        </Card>

        {/* 功能说明 */}
        <Card
          title="功能说明"
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
                <Text strong>📷 支持的图片格式</Text>
                <Text type="secondary">
                  .jpg, .jpeg, .png, .gif, .bmp, .webp
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>📏 文件大小限制</Text>
                <Text type="secondary">
                  单个文件不超过 10MB
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>🔄 处理流程</Text>
                <Text type="secondary">
                  上传 → 验证 → AI分析 → 生成报告
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>🎯 分析内容</Text>
                <Text type="secondary">
                  UI元素识别、交互流程、测试脚本生成
                </Text>
              </Space>
            </Col>
          </Row>
        </Card>
      </Content>
    </Layout>
  );
};

export default ImageUploadPage;
