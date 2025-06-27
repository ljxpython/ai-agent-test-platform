import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Typography, Card, Row, Col, Button, Space, Steps, Alert, Tag } from 'antd';
import {
  SearchOutlined,
  SyncOutlined,
  BulbOutlined,
  RocketOutlined,
  FileImageOutlined,
  CodeOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;
// const { Step } = Steps; // 暂未使用

const UITestIntroPage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <SearchOutlined style={{ fontSize: 48, color: '#667eea' }} />,
      title: '智能UI分析',
      description: '自动识别界面中的按钮、输入框、链接等UI元素，提供精确的元素描述',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    {
      icon: <SyncOutlined style={{ fontSize: 48, color: '#11998e' }} />,
      title: '交互流程设计',
      description: '基于用户需求分析用户操作流程，设计完整的交互路径',
      gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)'
    },
    {
      icon: <BulbOutlined style={{ fontSize: 48, color: '#fa709a' }} />,
      title: '脚本自动生成',
      description: '整合分析结果，生成符合Midscene.js规范的可执行测试脚本',
      gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
    }
  ];

  const steps = [
    {
      title: '上传UI截图',
      description: '选择或拖拽UI截图到上传区域，支持多张图片同时上传',
      icon: <FileImageOutlined />
    },
    {
      title: '描述测试需求',
      description: '详细描述您希望测试的功能和用户交互流程',
      icon: <CodeOutlined />
    },
    {
      title: '实时查看分析',
      description: '观察四个智能体的实时工作进度和生成的分析内容',
      icon: <SyncOutlined />
    },
    {
      title: '获取测试脚本',
      description: '分析完成后下载结果文件或复制生成的Midscene.js测试脚本',
      icon: <CheckCircleOutlined />
    }
  ];

  const techStack = [
    { icon: '🐍', name: 'Python + FastAPI', color: '#3776ab' },
    { icon: '🤖', name: 'Microsoft AutoGen', color: '#00bcf2' },
    { icon: '🧠', name: '豆包大模型', color: '#ff6b6b' },
    { icon: '⚛️', name: 'React + TypeScript', color: '#61dafb' },
    { icon: '🎨', name: 'Ant Design', color: '#1890ff' },
    { icon: '📡', name: 'Server-Sent Events', color: '#52c41a' }
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* 页面标题 */}
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <Title level={1} style={{
              fontSize: 48,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: 16
            }}>
              🤖 Midscene 智能体系统
            </Title>
            <Paragraph style={{ fontSize: 18, color: '#666', maxWidth: 600, margin: '0 auto' }}>
              基于AI的UI自动化测试脚本生成平台，通过上传UI截图即可自动生成Midscene.js测试脚本
            </Paragraph>
          </div>

          {/* 欢迎提示 */}
          <Alert
            message="📢 欢迎体验！"
            description="这是一个基于AI的UI自动化测试脚本生成平台，通过上传UI截图即可自动生成Midscene.js测试脚本。"
            type="info"
            showIcon
            style={{ marginBottom: 32, borderRadius: 12 }}
          />

          {/* 核心功能 */}
          <Title level={2} style={{ textAlign: 'center', marginBottom: 32 }}>
            🚀 核心功能
          </Title>
          <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
            {features.map((feature, index) => (
              <Col xs={24} md={8} key={index}>
                <Card
                  style={{
                    height: '100%',
                    borderRadius: 16,
                    border: 'none',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    overflow: 'hidden'
                  }}
                  styles={{ body: { padding: 0 } }}
                >
                  <div
                    style={{
                      background: feature.gradient,
                      padding: '32px 24px',
                      textAlign: 'center',
                      color: 'white'
                    }}
                  >
                    {feature.icon}
                    <Title level={3} style={{ color: 'white', marginTop: 16, marginBottom: 8 }}>
                      {feature.title}
                    </Title>
                  </div>
                  <div style={{ padding: 24 }}>
                    <Paragraph style={{ margin: 0, color: '#666' }}>
                      {feature.description}
                    </Paragraph>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>

          {/* 使用步骤 */}
          <Title level={2} style={{ textAlign: 'center', marginBottom: 32 }}>
            📋 使用步骤
          </Title>
          <Card style={{ marginBottom: 32, borderRadius: 16 }}>
            <Steps
              direction="vertical"
              size="small"
              current={-1}
              items={steps.map((step) => ({
                title: step.title,
                description: step.description,
                icon: step.icon
              }))}
            />
          </Card>

          {/* 注意事项 */}
          <Alert
            message="⚠️ 注意事项"
            description={
              <ul style={{ margin: '8px 0 0 16px', paddingLeft: 0 }}>
                <li>确保后端服务正在运行</li>
                <li>支持的图片格式：JPG、PNG、GIF、WebP</li>
                <li>单个文件大小不超过10MB</li>
                <li>建议使用Chrome、Firefox、Safari等现代浏览器</li>
              </ul>
            }
            type="warning"
            showIcon
            style={{ marginBottom: 32, borderRadius: 12 }}
          />

          {/* 操作按钮 */}
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <Space size="large">
              <Button
                type="primary"
                size="large"
                icon={<RocketOutlined />}
                onClick={() => navigate('/ui-test-script')}
                style={{
                  height: 48,
                  fontSize: 16,
                  borderRadius: 12,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none'
                }}
              >
                开始使用
              </Button>
              <Button
                size="large"
                icon={<ApiOutlined />}
                onClick={() => window.open('https://github.com/web-infra-dev/midscene', '_blank')}
                style={{
                  height: 48,
                  fontSize: 16,
                  borderRadius: 12
                }}
              >
                了解Midscene.js
              </Button>
            </Space>
          </div>

          {/* 技术栈 */}
          <Title level={2} style={{ textAlign: 'center', marginBottom: 32 }}>
            🛠️ 技术栈
          </Title>
          <Row gutter={[16, 16]} style={{ marginBottom: 48 }}>
            {techStack.map((tech, index) => (
              <Col xs={12} sm={8} md={4} key={index}>
                <Card
                  style={{
                    textAlign: 'center',
                    borderRadius: 12,
                    transition: 'all 0.3s ease',
                    cursor: 'pointer'
                  }}
                  hoverable
                  styles={{ body: { padding: 16 } }}
                >
                  <div style={{ fontSize: 32, marginBottom: 8 }}>{tech.icon}</div>
                  <Text style={{ fontSize: 12, fontWeight: 500, color: tech.color }}>
                    {tech.name}
                  </Text>
                </Card>
              </Col>
            ))}
          </Row>

          {/* 系统架构 */}
          <Card style={{ marginBottom: 32, borderRadius: 16 }}>
            <Title level={2} style={{ marginBottom: 24 }}>
              📊 系统架构
            </Title>
            <Paragraph style={{ fontSize: 16, marginBottom: 24 }}>
              系统采用四智能体协作架构，通过流式通信实现实时分析：
            </Paragraph>

            <div style={{
              background: '#f8f9fa',
              padding: 24,
              borderRadius: 12,
              marginBottom: 24,
              fontFamily: 'Monaco, monospace',
              fontSize: 14,
              lineHeight: 1.6
            }}>
              <pre style={{ margin: 0 }}>
{`用户上传图片 → FastAPI接口 → 四智能体并行工作
                                    ↓
UI分析智能体 ←→ 交互分析智能体 ←→ Midscene生成智能体 ←→ 脚本生成智能体
                                    ↓
                            流式结果推送 → 前端实时显示`}
              </pre>
            </div>

            <Title level={3} style={{ marginBottom: 16 }}>
              🔄 工作流程
            </Title>
            <ol style={{ paddingLeft: 20 }}>
              <li><Text strong>UI分析智能体</Text>：分析上传的UI截图，识别界面元素</li>
              <li><Text strong>交互分析智能体</Text>：基于用户需求设计交互流程</li>
              <li><Text strong>Midscene生成智能体</Text>：生成Midscene.js测试用例</li>
              <li><Text strong>脚本生成智能体</Text>：生成YAML和Playwright脚本</li>
            </ol>

            <Title level={3} style={{ marginBottom: 16, marginTop: 24 }}>
              📡 实时通信
            </Title>
            <Paragraph>采用Server-Sent Events (SSE) 技术实现：</Paragraph>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Tag icon={<ThunderboltOutlined />} color="blue">实时进度推送</Tag>
              </Col>
              <Col span={12}>
                <Tag icon={<SyncOutlined />} color="green">流式内容显示</Tag>
              </Col>
              <Col span={12}>
                <Tag icon={<ExclamationCircleOutlined />} color="red">错误状态通知</Tag>
              </Col>
              <Col span={12}>
                <Tag icon={<CheckCircleOutlined />} color="purple">完成状态确认</Tag>
              </Col>
            </Row>
          </Card>

          {/* 页脚 */}
          <div style={{ textAlign: 'center', color: '#999', fontSize: 14 }}>
            <Paragraph style={{ margin: 0 }}>
              © 2025 Midscene 智能体系统 | 基于 AutoGen 和 豆包大模型构建
            </Paragraph>
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default UITestIntroPage;
