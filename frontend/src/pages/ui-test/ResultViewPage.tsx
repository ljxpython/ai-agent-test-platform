/**
 * UI测试结果查看页面
 * 专门用于查看和管理UI测试分析结果
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
  Tag,
  Tooltip,
} from 'antd';
import {
  EyeOutlined,
  FileImageOutlined,
  RocketOutlined,
  HomeOutlined,
  CloudUploadOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
  CodeOutlined,

} from '@ant-design/icons';

import {
  ProjectSelector,
  ResultViewPanel,
} from '../../components/ui-test';

import type { TaskSummary } from '../../types/ui-test';

const { Content } = Layout;
const { Title, Text } = Typography;

const ResultViewPage: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [taskSummary, setTaskSummary] = useState<TaskSummary>({
    total_tasks: 0,
    completed_tasks: 0,
    processing_tasks: 0,
    failed_tasks: 0,
  });
  const [refreshKey] = useState(0);

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
            <EyeOutlined />
            <span>结果查看</span>
          </Breadcrumb.Item>
        </Breadcrumb>

        {/* 页面头部 */}
        <div style={{ marginBottom: '24px' }}>
          <Row align="middle" justify="space-between">
            <Col>
              <Space align="center">
                <Avatar
                  size={48}
                  icon={<EyeOutlined />}
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
                    分析结果查看
                  </Title>
                  <Text type="secondary">
                    查看AI分析结果，下载测试脚本和分析报告
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
                    icon={<CloudUploadOutlined />}
                    onClick={() => window.location.href = '/ui-test/upload'}
                  >
                    上传图片
                  </Button>
                </Tooltip>
                <Tooltip title="任务管理">
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

        {/* 结果统计 */}
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
                title="已完成分析"
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
                title="UI分析报告"
                value={taskSummary.completed_tasks}
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
                title="YAML脚本"
                value={taskSummary.completed_tasks}
                prefix={<FileTextOutlined style={{ color: '#faad14' }} />}
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
              transition: 'all 0.3s ease',
            }}>
              <Statistic
                title="Playwright脚本"
                value={taskSummary.completed_tasks}
                prefix={<CodeOutlined style={{ color: '#722ed1' }} />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 结果类型说明 */}
        <Card
          title="结果类型说明"
          style={{
            marginBottom: '24px',
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(10px)',
            borderRadius: '12px',
          }}
        >
          <Row gutter={[24, 16]}>
            <Col xs={24} md={12}>
              <Space>
                <Tag color="blue" icon={<FileImageOutlined />}>UI分析</Tag>
                <Text type="secondary">界面元素识别和结构分析</Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space>
                <Tag color="green" icon={<EyeOutlined />}>交互分析</Tag>
                <Text type="secondary">用户交互流程和操作路径</Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space>
                <Tag color="orange" icon={<FileTextOutlined />}>YAML脚本</Tag>
                <Text type="secondary">Midscene测试配置文件</Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space>
                <Tag color="purple" icon={<CodeOutlined />}>Playwright脚本</Tag>
                <Text type="secondary">自动化测试执行脚本</Text>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 结果查看面板 */}
        <Card style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
        }}>
          <ResultViewPanel
            selectedProject={selectedProject}
            refreshKey={refreshKey}
          />
        </Card>

        {/* 操作指南 */}
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
                <Text strong>👁️ 查看详情</Text>
                <Text type="secondary">
                  点击结果卡片查看完整的分析内容和生成的脚本
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>📋 复制内容</Text>
                <Text type="secondary">
                  使用复制按钮将分析结果或脚本复制到剪贴板
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>💾 下载文件</Text>
                <Text type="secondary">
                  下载分析报告和测试脚本到本地文件
                </Text>
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" size="small">
                <Text strong>🔄 实时更新</Text>
                <Text type="secondary">
                  新完成的分析结果会自动显示在列表中
                </Text>
              </Space>
            </Col>
          </Row>
        </Card>
      </Content>
    </Layout>
  );
};

export default ResultViewPage;
