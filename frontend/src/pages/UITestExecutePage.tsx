import React, { useState, useRef, useEffect } from 'react';
import {
  Layout,
  Card,
  Form,
  Input,
  Button,
  Upload,
  Progress,
  Typography,
  Space,
  Row,
  Col,
  message,
  // Divider, // 暂未使用
  Tag,
  // Alert // 暂未使用
} from 'antd';
import {
  UploadOutlined,
  RocketOutlined,
  DownloadOutlined,
  CopyOutlined,
  ReloadOutlined,
  SearchOutlined,
  SyncOutlined,
  BulbOutlined,
  CodeOutlined,
  FileImageOutlined,
  // DeleteOutlined, // 暂未使用
  EyeOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import AgentResultModal from '../components/AgentResultModal';
import ScriptResultPanel from '../components/ScriptResultPanel';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

interface AgentStatus {
  status: 'waiting' | 'working' | 'complete' | 'error';
  content: string;
}

interface StreamMessage {
  type: string;
  agent?: string;
  content?: string;
  message?: string;
  step?: string;
}

const UITestExecutePage: React.FC = () => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [systemLogs, setSystemLogs] = useState<Array<{message: string, type: string, time: string}>>([]);
  const [agents, setAgents] = useState<Record<string, AgentStatus>>({
    'UI分析智能体': { status: 'waiting', content: '等待开始分析...' },
    '交互分析智能体': { status: 'waiting', content: '等待UI分析完成...' },
    'Midscene用例生成智能体': { status: 'waiting', content: '等待交互分析完成...' },
    '脚本生成智能体': { status: 'waiting', content: '等待Midscene生成完成...' }
  });
  const [analysisResults, setAnalysisResults] = useState<Record<string, string>>({});
  const [currentUserId, setCurrentUserId] = useState('');

  // 智能体结果弹窗状态
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<{
    name: string;
    content: string;
    type: 'ui' | 'interaction' | 'midscene' | 'script';
  } | null>(null);

  // 脚本生成结果
  const [scriptResults, setScriptResults] = useState<{
    yamlScript?: string;
    playwrightScript?: string;
    scriptInfo?: {
      testName: string;
      stepsCount: number;
      estimatedDuration: string;
      description?: string;
    };
  }>({});

  const systemLogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    generateUserId();
  }, []);

  useEffect(() => {
    if (systemLogRef.current) {
      systemLogRef.current.scrollTop = systemLogRef.current.scrollHeight;
    }
  }, [systemLogs]);

  const generateUserId = () => {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 5);
    const userId = `user_${timestamp}_${random}`;
    setCurrentUserId(userId);
    form.setFieldsValue({ userId });
  };

  const uploadProps: UploadProps = {
    multiple: true,
    accept: 'image/*',
    beforeUpload: () => false, // 阻止自动上传
    fileList,
    onChange: ({ fileList: newFileList }) => {
      setFileList(newFileList);
    },
    onRemove: (file) => {
      setFileList(prev => prev.filter(item => item.uid !== file.uid));
    }
  };

  const addSystemLog = (message: string, type: string) => {
    const time = new Date().toLocaleTimeString();
    setSystemLogs(prev => [...prev, { message, type, time }]);
  };

  const updateAgentStatus = (agentName: string, status: AgentStatus['status'], content?: string) => {
    setAgents(prev => ({
      ...prev,
      [agentName]: {
        status,
        content: content !== undefined ? content : prev[agentName]?.content || ''
      }
    }));
  };

  const appendAgentContent = (agentName: string, content: string) => {
    setAgents(prev => ({
      ...prev,
      [agentName]: {
        ...prev[agentName],
        content: prev[agentName].content + content
      }
    }));

    // 保存到结果中
    setAnalysisResults(prev => ({
      ...prev,
      [agentName]: (prev[agentName] || '') + content
    }));
  };

  const handleStreamMessage = (data: StreamMessage) => {
    const { type, agent, content, message: msg, step } = data;

    switch (type) {
      case 'system_start':
        addSystemLog(content || msg || '', 'info');
        break;

      case 'agent_start':
        if (agent) {
          updateAgentStatus(agent, 'working', '');
          addSystemLog(`${agent} 开始工作: ${step}`, 'info');
        }
        break;

      case 'step_info':
        if (agent && content) {
          addSystemLog(`${agent}: ${content}`, 'info');
        }
        break;

      case 'stream_chunk':
        if (agent && content) {
          appendAgentContent(agent, content);
        }
        break;

      case 'agent_complete':
        if (agent) {
          updateAgentStatus(agent, 'complete');
          addSystemLog(`${agent} 完成工作`, 'success');

          // 更新进度
          const agentProgress: Record<string, number> = {
            'UI分析智能体': 25,
            '交互分析智能体': 50,
            'Midscene用例生成智能体': 75,
            '脚本生成智能体': 100
          };
          setProgress(agentProgress[agent] || 0);
        }
        break;

      case 'agent_error':
        if (agent && content) {
          updateAgentStatus(agent, 'error', `❌ 错误: ${content}`);
          addSystemLog(`${agent} 发生错误: ${content}`, 'error');
        }
        break;

      case 'script_generated':
        if (content) {
          try {
            const scriptData = JSON.parse(content);
            setScriptResults(scriptData);
            addSystemLog('📜 测试脚本生成完成', 'success');
          } catch (error) {
            console.error('解析脚本数据失败:', error);
          }
        }
        break;

      case 'system_complete':
        addSystemLog('🎉 所有智能体协作分析完成！', 'success');
        setProgress(100);
        setIsAnalyzing(false);
        setShowResult(true);
        break;

      case 'system_error':
        addSystemLog(`❌ 系统错误: ${content}`, 'error');
        message.error('分析过程中发生错误');
        resetAnalysis();
        break;

      default:
        console.log('未知消息类型:', data);
    }
  };

  const handleSubmit = async (values: any) => {
    if (isAnalyzing) return;

    if (fileList.length === 0) {
      message.error('请选择至少一张图片');
      return;
    }

    const formData = new FormData();
    fileList.forEach(file => {
      if (file.originFileObj) {
        formData.append('files', file.originFileObj);
      }
    });
    formData.append('user_id', values.userId);
    formData.append('user_requirement', values.requirement);

    setIsAnalyzing(true);
    setShowAnalysis(true);
    setShowResult(false);
    setProgress(0);
    setSystemLogs([]);

    // 重置智能体状态
    setAgents({
      'UI分析智能体': { status: 'waiting', content: '等待开始分析...' },
      '交互分析智能体': { status: 'waiting', content: '等待UI分析完成...' },
      'Midscene用例生成智能体': { status: 'waiting', content: '等待交互分析完成...' },
      '脚本生成智能体': { status: 'waiting', content: '等待Midscene生成完成...' }
    });

    try {
      const response = await fetch('/api/v1/midscene/upload_and_analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 处理流式响应
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');

          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
              try {
                const data = JSON.parse(line.trim().substring(6));
                handleStreamMessage(data);
              } catch (error) {
                console.error('解析SSE消息失败:', error, line);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('上传分析失败:', error);
      message.error(`上传失败: ${error}`);
      resetAnalysis();
    }
  };

  const resetAnalysis = () => {
    setIsAnalyzing(false);
    setShowAnalysis(false);
    setShowResult(false);
    setProgress(0);
    setSystemLogs([]);
    setAnalysisResults({});
    generateUserId();
  };

  const getStatusColor = (status: AgentStatus['status']) => {
    switch (status) {
      case 'waiting': return '#999';
      case 'working': return '#fa8c16';
      case 'complete': return '#52c41a';
      case 'error': return '#f5222d';
      default: return '#999';
    }
  };

  const getStatusText = (status: AgentStatus['status']) => {
    switch (status) {
      case 'waiting': return '等待中';
      case 'working': return '工作中';
      case 'complete': return '已完成';
      case 'error': return '错误';
      default: return '未知';
    }
  };

  const getAgentType = (agentName: string): 'ui' | 'interaction' | 'midscene' | 'script' => {
    if (agentName.includes('UI分析')) return 'ui';
    if (agentName.includes('交互分析')) return 'interaction';
    if (agentName.includes('Midscene')) return 'midscene';
    if (agentName.includes('脚本生成')) return 'script';
    return 'ui';
  };

  const handleViewAgentResult = (agentName: string) => {
    const content = analysisResults[agentName] || agents[agentName]?.content || '';
    setSelectedAgent({
      name: agentName,
      content,
      type: getAgentType(agentName)
    });
    setModalVisible(true);
  };

  const agentConfigs = [
    { key: 'UI分析智能体', icon: <SearchOutlined />, color: '#667eea' },
    { key: '交互分析智能体', icon: <SyncOutlined />, color: '#11998e' },
    { key: 'Midscene用例生成智能体', icon: <BulbOutlined />, color: '#fa709a' },
    { key: '脚本生成智能体', icon: <CodeOutlined />, color: '#722ed1' }
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          {/* 页面标题 */}
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <Title level={1} style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: 8
            }}>
              🤖 Midscene 智能体系统
            </Title>
            <Paragraph style={{ fontSize: 16, color: '#666' }}>
              基于AI的UI自动化测试脚本生成平台
            </Paragraph>
          </div>

          {/* 上传表单 */}
          <Card
            title={
              <Space>
                <FileImageOutlined />
                <span>📤 上传UI截图</span>
              </Space>
            }
            style={{ marginBottom: 24, borderRadius: 16 }}
          >
            <Paragraph style={{ color: '#666', marginBottom: 24 }}>
              支持多张图片，系统将自动分析并生成Midscene.js测试脚本
            </Paragraph>

            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={{
                requirement: `测试电商网站的用户登录功能，具体包括：
1. 点击登录按钮打开登录表单
2. 输入用户名和密码
3. 点击提交按钮完成登录
4. 验证登录成功状态`
              }}
            >
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    label={
                      <Space>
                        <span>👤</span>
                        <span>用户ID</span>
                      </Space>
                    }
                    name="userId"
                    rules={[{ required: true, message: '请输入用户ID' }]}
                  >
                    <Input placeholder="请输入用户ID" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label={
                      <Space>
                        <span>🖼️</span>
                        <span>选择UI截图</span>
                      </Space>
                    }
                    required
                  >
                    <Upload {...uploadProps}>
                      <Button icon={<UploadOutlined />}>选择文件</Button>
                    </Upload>
                    <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
                      支持 JPG、PNG、GIF 格式，可选择多张图片
                    </Text>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label={
                  <Space>
                    <span>📝</span>
                    <span>测试需求描述</span>
                  </Space>
                }
                name="requirement"
                rules={[{ required: true, message: '请输入测试需求描述' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="请详细描述您的测试需求..."
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  size="large"
                  icon={<RocketOutlined />}
                  loading={isAnalyzing}
                  style={{
                    width: '100%',
                    height: 48,
                    fontSize: 16,
                    borderRadius: 12,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none'
                  }}
                >
                  {isAnalyzing ? '分析中...' : '开始分析'}
                </Button>
              </Form.Item>
            </Form>
          </Card>

          {/* 分析区域 */}
          {showAnalysis && (
            <Card
              title={
                <Space>
                  <SyncOutlined spin={isAnalyzing} />
                  <span>📊 实时分析进度</span>
                </Space>
              }
              style={{ marginBottom: 24, borderRadius: 16 }}
            >
              {/* 进度条 */}
              <div style={{ marginBottom: 24 }}>
                <Progress
                  percent={progress}
                  strokeColor={{
                    '0%': '#667eea',
                    '100%': '#764ba2',
                  }}
                  style={{ marginBottom: 8 }}
                />
                <Text type="secondary">分析进度: {progress}%</Text>
              </div>

              {/* 系统日志 */}
              <Card
                title="📋 系统日志"
                size="small"
                style={{ marginBottom: 24 }}
                styles={{ body: { padding: 0 } }}
              >
                <div
                  ref={systemLogRef}
                  style={{
                    maxHeight: 200,
                    overflowY: 'auto',
                    padding: 16,
                    background: '#fafafa',
                    fontFamily: 'Monaco, monospace',
                    fontSize: 12
                  }}
                >
                  {systemLogs.map((log, index) => (
                    <div
                      key={index}
                      style={{
                        padding: '4px 8px',
                        margin: '2px 0',
                        borderRadius: 4,
                        background: log.type === 'error' ? '#fff2f0' :
                                   log.type === 'success' ? '#f6ffed' : '#e6f7ff',
                        color: log.type === 'error' ? '#a8071a' :
                               log.type === 'success' ? '#389e0d' : '#0958d9',
                        borderLeft: `3px solid ${
                          log.type === 'error' ? '#ff4d4f' :
                          log.type === 'success' ? '#52c41a' : '#1890ff'
                        }`
                      }}
                    >
                      [{log.time}] {log.message}
                    </div>
                  ))}
                </div>
              </Card>

              {/* 智能体工作区域 */}
              <Row gutter={[16, 16]}>
                {agentConfigs.map((config) => {
                  const agent = agents[config.key];
                  return (
                    <Col xs={24} lg={12} xl={6} key={config.key}>
                      <Card
                        size="small"
                        style={{
                          height: 300,
                          borderRadius: 12,
                          border: `2px solid ${agent.status === 'working' ? config.color : '#f0f0f0'}`
                        }}
                        title={
                          <Space>
                            {config.icon}
                            <span style={{ fontSize: 12 }}>{config.key}</span>
                          </Space>
                        }
                        extra={
                          <Space size="small">
                            <Tag
                              color={getStatusColor(agent.status)}
                              style={{ fontSize: 10 }}
                            >
                              {getStatusText(agent.status)}
                            </Tag>
                            {(agent.status === 'complete' || analysisResults[config.key]) && (
                              <Button
                                type="text"
                                size="small"
                                icon={<EyeOutlined />}
                                onClick={() => handleViewAgentResult(config.key)}
                                style={{ fontSize: 10, padding: '0 4px' }}
                                title="查看详细结果"
                              />
                            )}
                          </Space>
                        }
                        styles={{ body: { padding: 8 } }}
                      >
                        <div style={{
                          height: 200,
                          overflowY: 'auto',
                          background: '#f8f9fa',
                          padding: 8,
                          borderRadius: 6,
                          fontFamily: 'Monaco, monospace',
                          fontSize: 11,
                          lineHeight: 1.4,
                          whiteSpace: 'pre-wrap',
                          wordWrap: 'break-word'
                        }}>
                          {agent.content || '等待开始...'}
                        </div>
                      </Card>
                    </Col>
                  );
                })}
              </Row>
            </Card>
          )}

          {/* 结果区域 */}
          {showResult && (
            <Card
              title={
                <Space>
                  <span>🎉</span>
                  <span>分析完成</span>
                </Space>
              }
              style={{ marginBottom: 24, borderRadius: 16 }}
              styles={{ body: { background: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)', color: 'white' } }}
            >
              <div style={{ textAlign: 'center', padding: '16px 0' }}>
                <Title level={3} style={{ color: 'white', marginBottom: 24 }}>
                  🎉 分析完成！
                </Title>
                <Space size="large" wrap>
                  <Button
                    icon={<DownloadOutlined />}
                    size="large"
                    style={{
                      background: 'rgba(255,255,255,0.2)',
                      color: 'white',
                      border: '2px solid white',
                      borderRadius: 8
                    }}
                    onClick={() => {
                      const results = {
                        userId: currentUserId,
                        timestamp: new Date().toISOString(),
                        analysisResults
                      };
                      const blob = new Blob([JSON.stringify(results, null, 2)], {
                        type: 'application/json'
                      });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `midscene_analysis_${currentUserId}_${Date.now()}.json`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      URL.revokeObjectURL(url);
                      message.success('分析结果已下载');
                    }}
                  >
                    💾 下载完整结果
                  </Button>
                  <Button
                    icon={<CopyOutlined />}
                    size="large"
                    style={{
                      background: 'rgba(255,255,255,0.2)',
                      color: 'white',
                      border: '2px solid white',
                      borderRadius: 8
                    }}
                    onClick={async () => {
                      const midsceneScript = analysisResults['Midscene用例生成智能体'] || '';
                      if (!midsceneScript) {
                        message.error('没有可复制的脚本内容');
                        return;
                      }
                      try {
                        await navigator.clipboard.writeText(midsceneScript);
                        message.success('Midscene脚本已复制到剪贴板');
                      } catch (error) {
                        message.error('复制失败，请手动复制');
                      }
                    }}
                  >
                    📋 复制Midscene脚本
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    size="large"
                    style={{
                      background: 'white',
                      color: '#52c41a',
                      border: 'none',
                      borderRadius: 8,
                      fontWeight: 'bold'
                    }}
                    onClick={resetAnalysis}
                  >
                    🔄 新建分析
                  </Button>
                </Space>
              </div>
            </Card>
          )}

          {/* 脚本生成结果面板 */}
          <ScriptResultPanel
            results={scriptResults}
            visible={showResult && (!!scriptResults.yamlScript || !!scriptResults.playwrightScript)}
          />

          {/* 智能体结果详情弹窗 */}
          <AgentResultModal
            visible={modalVisible}
            onClose={() => setModalVisible(false)}
            agentName={selectedAgent?.name || ''}
            content={selectedAgent?.content || ''}
            agentType={selectedAgent?.type || 'ui'}
          />
        </div>
      </Content>
    </Layout>
  );
};

export default UITestExecutePage;
