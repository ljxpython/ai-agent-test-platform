/**
 * UI测试概览页面
 * 提供UI测试功能的总体概览和快速入口
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
  Avatar,
  Breadcrumb,
  Progress,
  List,
  Tag,
} from 'antd';
import {
  RocketOutlined,
  HomeOutlined,
  CloudUploadOutlined,
  BarChartOutlined,
  EyeOutlined,
  FileImageOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,

  ArrowRightOutlined,
  TrophyOutlined,
  FireOutlined,
} from '@ant-design/icons';

import { ProjectSelector } from '../../components/ui-test';
import type { TaskSummary } from '../../types/ui-test';

const { Content } = Layout;
const { Title, Text } = Typography;

const OverviewPage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [taskSummary, setTaskSummary] = useState<TaskSummary>({
    total_tasks: 0,
    completed_tasks: 0,
    processing_tasks: 0,
    failed_tasks: 0,
  });
  const [recentTasks, setRecentTasks] = useState<any[]>([]);

  // 刷新数据
  const refreshData = async () => {
    if (!selectedProject) return;

    try {
      const response = await fetch(`/api/ui-test/tasks/project/${selectedProject}`);
      if (response.ok) {
        const data = await response.json();
        setTaskSummary(data.data.summary);
        // 获取最近的5个任务
        setRecentTasks(data.data.tasks.slice(0, 5));
      }
    } catch (error) {
      console.error('获取数据失败:', error);
    }
  };

  useEffect(() => {
    refreshData();
  }, [selectedProject]);

  // 计算完成率
  const completionRate = taskSummary.total_tasks > 0
    ? Math.round((taskSummary.completed_tasks / taskSummary.total_tasks) * 100)
    : 0;

  // 功能卡片数据
  const featureCards = [
    {
      title: '图片上传',
      description: '批量上传UI界面截图，开始AI智能分析',
      icon: <CloudUploadOutlined />,
      color: '#1890ff',
      path: '/ui-test/upload',
      action: '立即上传',
    },
    {
      title: '任务管理',
      description: '监控分析进度，管理任务状态',
      icon: <BarChartOutlined />,
      color: '#52c41a',
      path: '/ui-test/tasks',
      action: '查看任务',
    },
    {
      title: '结果查看',
      description: '查看分析结果，下载测试脚本',
      icon: <EyeOutlined />,
      color: '#faad14',
      path: '/ui-test/results',
      action: '查看结果',
    },
  ];

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
          <Breadcrumb.Item>概览</Breadcrumb.Item>
        </Breadcrumb>

        {/* 页面头部 */}
        <div style={{ marginBottom: '32px' }}>
          <Row align="middle" justify="space-between">
            <Col>
              <Space align="center">
                <Avatar
                  size={64}
                  icon={<RocketOutlined />}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
                  }}
                />
                <div>
                  <Title
                    level={1}
                    style={{
                      margin: 0,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}
                  >
                    UI智能测试平台
                  </Title>
                  <Text type="secondary" style={{ fontSize: '16px' }}>
                    基于AI的UI界面分析与自动化测试用例生成
                  </Text>
                </div>
              </Space>
            </Col>
            <Col>
              <ProjectSelector
                value={selectedProject}
                onChange={setSelectedProject}
                style={{ minWidth: 200 }}
              />
            </Col>
          </Row>
        </div>

        {/* 统计概览 */}
        <Row gutter={[24, 24]} style={{ marginBottom: '32px' }}>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="总任务数"
                value={taskSummary.total_tasks}
                prefix={<FileImageOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ color: '#1890ff', fontSize: '28px' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="已完成"
                value={taskSummary.completed_tasks}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a', fontSize: '28px' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="处理中"
                value={taskSummary.processing_tasks}
                prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: '#faad14', fontSize: '28px' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="完成率"
                value={completionRate}
                suffix="%"
                prefix={<TrophyOutlined style={{ color: '#722ed1' }} />}
                valueStyle={{ color: '#722ed1', fontSize: '28px' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 功能入口 */}
        <Row gutter={[24, 24]} style={{ marginBottom: '32px' }}>
          {featureCards.map((card, index) => (
            <Col xs={24} md={8} key={index}>
              <Card
                hoverable
                style={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '16px',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  height: '200px',
                  transition: 'all 0.3s ease',
                }}
                bodyStyle={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                onClick={() => window.location.href = card.path}
              >
                <div style={{ flex: 1 }}>
                  <Space align="start" style={{ marginBottom: '16px' }}>
                    <Avatar
                      size={48}
                      icon={card.icon}
                      style={{ backgroundColor: card.color }}
                    />
                    <div>
                      <Title level={4} style={{ margin: 0, color: card.color }}>
                        {card.title}
                      </Title>
                      <Text type="secondary">{card.description}</Text>
                    </div>
                  </Space>
                </div>
                <Button
                  type="primary"
                  icon={<ArrowRightOutlined />}
                  style={{
                    backgroundColor: card.color,
                    borderColor: card.color,
                    borderRadius: '8px',
                  }}
                >
                  {card.action}
                </Button>
              </Card>
            </Col>
          ))}
        </Row>

        {/* 项目进度和最近任务 */}
        <Row gutter={[24, 24]}>
          {/* 项目进度 */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <FireOutlined style={{ color: '#ff4d4f' }} />
                  项目进度
                </Space>
              }
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                height: '300px',
              }}
            >
              {selectedProject ? (
                <div>
                  <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                    <Progress
                      type="circle"
                      percent={completionRate}
                      size={120}
                      strokeColor={{
                        '0%': '#667eea',
                        '100%': '#764ba2',
                      }}
                    />
                  </div>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic
                        title="已完成"
                        value={taskSummary.completed_tasks}
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="总任务"
                        value={taskSummary.total_tasks}
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </Col>
                  </Row>
                </div>
              ) : (
                <div style={{
                  height: '200px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column',
                }}>
                  <Text type="secondary">请先选择项目</Text>
                </div>
              )}
            </Card>
          </Col>

          {/* 最近任务 */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <ClockCircleOutlined style={{ color: '#1890ff' }} />
                  最近任务
                </Space>
              }
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                height: '300px',
              }}
              extra={
                <Button
                  type="link"
                  onClick={() => window.location.href = '/ui-test/tasks'}
                >
                  查看全部
                </Button>
              }
            >
              <List
                dataSource={recentTasks}
                renderItem={(task) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text ellipsis style={{ maxWidth: 150 }}>
                            {task.filename}
                          </Text>
                          <Tag color={
                            task.status === 'completed' ? 'success' :
                            task.status === 'failed' ? 'error' : 'processing'
                          }>
                            {task.status === 'completed' ? '已完成' :
                             task.status === 'failed' ? '失败' : '处理中'}
                          </Tag>
                        </Space>
                      }
                      description={
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {new Date(task.created_at).toLocaleString()}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
                locale={{ emptyText: '暂无任务' }}
              />
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default OverviewPage;
