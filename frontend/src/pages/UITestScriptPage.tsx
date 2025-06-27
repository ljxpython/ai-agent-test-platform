import React, { useState, useRef, useEffect } from 'react';
import { Upload, Input, Typography, message } from 'antd';
// import {
//   UploadOutlined, PlayCircleOutlined, StopOutlined, ReloadOutlined,
//   DownloadOutlined, CopyOutlined, EyeOutlined, RobotOutlined,
//   BulbOutlined, CodeOutlined, FileImageOutlined, DeleteOutlined
// } from '@ant-design/icons'; // 暂未使用
import type { UploadFile, UploadProps } from 'antd';
import AgentResultModal from '../components/AgentResultModal';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface AgentStatus {
  status: 'waiting' | 'working' | 'complete' | 'error';
  content: string;
  progress: number;
}

interface SystemLog {
  id: string;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning';
  timestamp: string;
}

const UITestScriptPage: React.FC = () => {
  // 基础状态
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [userRequirement, setUserRequirement] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showResult, setShowResult] = useState(false);

  // 智能体状态
  const [agents, setAgents] = useState<Record<string, AgentStatus>>({
    'UI分析智能体': { status: 'waiting', content: '', progress: 0 },
    '交互分析智能体': { status: 'waiting', content: '', progress: 0 },
    'Midscene生成智能体': { status: 'waiting', content: '', progress: 0 },
    '脚本生成智能体': { status: 'waiting', content: '', progress: 0 }
  });

  // 系统日志
  const [systemLogs, setSystemLogs] = useState<SystemLog[]>([]);
  const [analysisResults, setAnalysisResults] = useState<Record<string, string>>({});
  const [, setCurrentUserId] = useState('');

  // 智能体结果弹窗状态
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<{
    name: string;
    content: string;
    type: 'ui' | 'interaction' | 'midscene' | 'script';
  } | null>(null);

  // 脚本生成结果
  const [scriptResults, setScriptResults] = useState<{
    yaml_script?: string;
    playwright_script?: string;
    script_info?: {
      test_name: string;
      steps_count: number;
      estimated_duration: string;
      description?: string;
    };
  }>({});

  // 引用
  const logContainerRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // 智能体配置
  const agentConfigs = [
    {
      key: 'UI分析智能体',
      name: 'UI分析智能体',
      icon: '🔍',
      color: '#667eea',
      description: '分析UI元素和布局结构'
    },
    {
      key: '交互分析智能体',
      name: '交互分析智能体',
      icon: '🔄',
      color: '#11998e',
      description: '设计用户交互流程'
    },
    {
      key: 'Midscene用例生成智能体',
      name: 'Midscene智能体',
      icon: '💡',
      color: '#fa709a',
      description: '生成Midscene测试用例'
    },
    {
      key: '脚本生成智能体',
      name: '脚本生成智能体',
      icon: '📜',
      color: '#722ed1',
      description: '生成可执行测试脚本'
    }
  ];

  // 添加系统日志
  const addSystemLog = (message: string, type: SystemLog['type'] = 'info') => {
    const newLog: SystemLog = {
      id: Date.now().toString(),
      message,
      type,
      timestamp: new Date().toLocaleTimeString()
    };
    setSystemLogs(prev => [...prev, newLog]);

    // 自动滚动到底部
    setTimeout(() => {
      if (logContainerRef.current) {
        logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
      }
    }, 100);
  };

  // 更新智能体状态
  const updateAgentStatus = (agentName: string, status: AgentStatus['status'], content: string = '', progress: number = 0) => {
    setAgents(prev => ({
      ...prev,
      [agentName]: { status, content, progress }
    }));
  };

  // 处理SSE消息
  const handleSSEMessage = (data: any) => {
    const { type, agent, content, step, message } = data;

    switch (type) {
      case 'system_start':
        addSystemLog(message || '系统开始处理', 'info');
        setProgress(10);
        break;

      case 'agent_start':
        if (agent) {
          updateAgentStatus(agent, 'working', step || '开始处理', 25);
          addSystemLog(`${agent} 开始工作: ${step || '处理中'}`, 'info');
        }
        break;

      case 'stream_chunk':
        if (agent && content) {
          setAgents(prev => ({
            ...prev,
            [agent]: {
              ...prev[agent],
              content: (prev[agent]?.content || '') + content
            }
          }));
        }
        break;

      case 'agent_complete':
        if (agent) {
          updateAgentStatus(agent, 'complete', content || '处理完成', 100);
          setAnalysisResults(prev => ({
            ...prev,
            [agent]: content || ''
          }));
          addSystemLog(`${agent} 完成: ${step || '处理完成'}`, 'success');
          setProgress(prev => Math.min(prev + 20, 90));
        }
        break;

      case 'script_generated':
        if (content) {
          try {
            const scriptData = JSON.parse(content);
            console.log('📜 收到脚本数据:', scriptData);
            setScriptResults(scriptData);
            addSystemLog('📜 测试脚本生成完成', 'success');
          } catch (error) {
            console.error('解析脚本数据失败:', error);
            addSystemLog(`❌ 脚本数据解析失败: ${error}`, 'error');
          }
        }
        break;

      case 'system_complete':
        addSystemLog('🎉 所有智能体协作分析完成！', 'success');
        console.log('📊 当前脚本结果状态:', scriptResults);
        console.log('📊 showResult状态:', showResult);
        setProgress(100);
        setIsAnalyzing(false);
        setShowResult(true);
        break;

      case 'agent_error':
      case 'system_error':
        if (agent) {
          updateAgentStatus(agent, 'error', content || '处理失败', 0);
        }
        addSystemLog(`❌ ${message || '处理失败'}: ${content || ''}`, 'error');
        setIsAnalyzing(false);
        break;

      default:
        console.log('未知消息类型:', type, data);
    }
  };

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    fileList,
    beforeUpload: () => false, // 阻止自动上传
    onChange: ({ fileList: newFileList }) => {
      setFileList(newFileList);
    },
    onRemove: (file) => {
      setFileList(prev => prev.filter(item => item.uid !== file.uid));
    },
    accept: '.jpg,.jpeg,.png,.gif,.bmp,.webp',
    showUploadList: {
      showPreviewIcon: true,
      showRemoveIcon: true,
      showDownloadIcon: false,
    }
  };

  // 开始分析
  const handleStartAnalysis = async () => {
    if (fileList.length === 0) {
      message.error('请先上传UI截图');
      return;
    }

    if (!userRequirement.trim()) {
      message.error('请输入测试需求描述');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setShowResult(false);
    setSystemLogs([]);

    // 重置智能体状态
    Object.keys(agents).forEach(agentName => {
      updateAgentStatus(agentName, 'waiting', '', 0);
    });

    const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setCurrentUserId(userId);

    try {
      const formData = new FormData();
      fileList.forEach(file => {
        if (file.originFileObj) {
          formData.append('files', file.originFileObj);
        }
      });
      formData.append('user_id', userId);
      formData.append('user_requirement', userRequirement);

      const response = await fetch('/api/v1/midscene/upload_and_analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // 处理SSE流
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                handleSSEMessage(data);
              } catch (error) {
                console.error('解析SSE数据失败:', error);
              }
            }
          }
        }
      }

    } catch (error) {
      console.error('上传分析失败:', error);
      message.error(`上传分析失败: ${error}`);
      setIsAnalyzing(false);
      addSystemLog(`上传分析失败: ${error}`, 'error');
    }
  };

  // 停止分析
  const handleStopAnalysis = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsAnalyzing(false);
    addSystemLog('用户手动停止分析', 'warning');
  };

  // 重置所有状态
  const handleReset = () => {
    setFileList([]);
    setUserRequirement('');
    setIsAnalyzing(false);
    setProgress(0);
    setShowResult(false);
    setSystemLogs([]);
    setAnalysisResults({});
    setScriptResults({});
    setCurrentUserId('');

    // 重置智能体状态
    Object.keys(agents).forEach(agentName => {
      updateAgentStatus(agentName, 'waiting', '', 0);
    });

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  // 获取状态颜色 (暂未使用)
  // const getStatusColor = (status: AgentStatus['status']) => {
  //   switch (status) {
  //     case 'waiting': return '#d9d9d9';
  //     case 'working': return '#1890ff';
  //     case 'complete': return '#52c41a';
  //     case 'error': return '#ff4d4f';
  //     default: return '#d9d9d9';
  //   }
  // };

  // 获取状态文本
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

  // 清理资源
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      padding: '20px'
    }}>
      <div style={{ maxWidth: 1400, margin: '0 auto' }}>
        {/* 页面标题 */}
        <header style={{ textAlign: 'center', marginBottom: 40 }}>
          <Title level={1} style={{
            fontSize: '3rem',
            margin: 0,
            marginBottom: 10,
            background: 'linear-gradient(135deg, #4a5568 0%, #2d3748 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            textShadow: 'none'
          }}>
            🤖 Midscene 智能体系统
          </Title>
          <Text style={{
            fontSize: '1.2rem',
            color: '#4a5568',
            opacity: 0.8
          }}>
            基于AI的UI自动化测试脚本生成平台
          </Text>
        </header>

        {/* 上传区域 */}
        <section style={{
          background: 'white',
          borderRadius: 20,
          padding: 30,
          boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
          marginBottom: 30
        }}>
          <div style={{ textAlign: 'center', marginBottom: 30 }}>
            <Title level={2} style={{ color: '#2c3e50', marginBottom: 10 }}>
              📤 上传UI截图
            </Title>
            <Text style={{ color: '#7f8c8d' }}>
              支持多张图片，系统将自动分析并生成Midscene.js测试脚本
            </Text>
          </div>

          <div style={{ marginBottom: 25 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 10,
              fontWeight: 600,
              color: '#2c3e50'
            }}>
              <span style={{ marginRight: 8, fontSize: '1.2rem' }}>🖼️</span>
              选择UI截图
            </div>
            <Upload.Dragger {...uploadProps} style={{
              border: '3px dashed #cbd5e0',
              borderRadius: 15,
              background: '#f7fafc',
              padding: '40px 20px'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>📁</div>
              <p style={{ margin: '5px 0', fontSize: 16 }}>点击选择文件或拖拽到此处</p>
              <p style={{ margin: '5px 0', fontSize: '0.9rem', color: '#718096' }}>
                支持 JPG、PNG、GIF 格式，可选择多张图片
              </p>
            </Upload.Dragger>
            {fileList.length > 0 && (
              <div style={{ marginTop: 15 }}>
                <Text style={{ color: '#48bb78', fontWeight: 500 }}>
                  ✅ 已选择 {fileList.length} 个文件
                </Text>
              </div>
            )}
          </div>

          <div style={{ marginBottom: 25 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 10,
              fontWeight: 600,
              color: '#2c3e50'
            }}>
              <span style={{ marginRight: 8, fontSize: '1.2rem' }}>📝</span>
              测试需求描述
            </div>
            <TextArea
              value={userRequirement}
              onChange={(e) => setUserRequirement(e.target.value)}
              placeholder="请详细描述您的测试需求..."
              rows={4}
              style={{
                width: '100%',
                padding: 15,
                border: '2px solid #e0e6ed',
                borderRadius: 10,
                fontSize: 16,
                background: '#f8f9fa',
                fontFamily: 'inherit',
                resize: 'vertical'
              }}
            />
          </div>

          <button
            onClick={isAnalyzing ? handleStopAnalysis : handleStartAnalysis}
            disabled={!isAnalyzing && (fileList.length === 0 || !userRequirement.trim())}
            style={{
              width: '100%',
              padding: 18,
              background: isAnalyzing
                ? 'linear-gradient(135deg, #fed7d7 0%, #fbb6ce 100%)'
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: 12,
              fontSize: 18,
              fontWeight: 600,
              cursor: fileList.length === 0 || !userRequirement.trim() ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: (!isAnalyzing && (fileList.length === 0 || !userRequirement.trim())) ? 0.6 : 1,
              position: 'relative'
            }}
          >
            {isAnalyzing ? (
              <>
                <div style={{
                  width: 20,
                  height: 20,
                  border: '3px solid rgba(74,85,104,0.3)',
                  borderTop: '3px solid #4a5568',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  marginRight: 10
                }} />
                <span style={{ color: '#4a5568' }}>停止分析</span>
              </>
            ) : (
              <>
                <span style={{ marginRight: 10, fontSize: '1.2rem' }}>🚀</span>
                开始分析
              </>
            )}
          </button>
        </section>

        {/* 分析区域 */}
        {(isAnalyzing || showResult) && (
          <section style={{
            background: 'white',
            borderRadius: 20,
            padding: 30,
            boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
            marginBottom: 30
          }}>
            <div style={{ marginBottom: 30 }}>
              <Title level={2} style={{ color: '#2c3e50', marginBottom: 20 }}>
                📊 实时分析进度
              </Title>
              <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                <div style={{
                  flex: 1,
                  height: 8,
                  background: '#e2e8f0',
                  borderRadius: 4,
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    background: 'linear-gradient(90deg, #667eea, #764ba2)',
                    width: `${progress}%`,
                    transition: 'width 0.5s ease',
                    borderRadius: 4
                  }} />
                </div>
                <span style={{
                  fontWeight: 600,
                  color: '#4a5568',
                  minWidth: 40
                }}>
                  {Math.round(progress)}%
                </span>
              </div>
            </div>

            {/* 系统日志 */}
            {systemLogs.length > 0 && (
              <div style={{
                marginBottom: 30,
                border: '1px solid #e2e8f0',
                borderRadius: 12,
                overflow: 'hidden'
              }}>
                <div style={{
                  background: '#f7fafc',
                  padding: '15px 20px',
                  margin: 0,
                  color: '#2d3748',
                  borderBottom: '1px solid #e2e8f0',
                  fontWeight: 600
                }}>
                  📋 系统日志
                </div>
                <div style={{
                  maxHeight: 200,
                  overflowY: 'auto',
                  padding: '15px 20px',
                  background: '#fafafa'
                }}>
                  {systemLogs.map((log) => (
                    <div
                      key={log.id}
                      style={{
                        padding: '8px 12px',
                        margin: '5px 0',
                        borderRadius: 6,
                        fontSize: 14,
                        fontFamily: 'Monaco, Menlo, Ubuntu Mono, monospace',
                        background: log.type === 'error' ? '#fed7d7' :
                                   log.type === 'success' ? '#f0fff4' :
                                   log.type === 'warning' ? '#fefcbf' : '#e6fffa',
                        color: log.type === 'error' ? '#742a2a' :
                               log.type === 'success' ? '#22543d' :
                               log.type === 'warning' ? '#744210' : '#234e52',
                        borderLeft: `4px solid ${
                          log.type === 'error' ? '#f56565' :
                          log.type === 'success' ? '#48bb78' :
                          log.type === 'warning' ? '#ed8936' : '#38b2ac'
                        }`
                      }}
                    >
                      [{log.timestamp}] {log.message}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 智能体工作区域 */}
            <div style={{
              display: 'grid',
              gap: 20,
              marginBottom: 30,
              gridTemplateColumns: window.innerWidth >= 1400 ? 'repeat(4, 1fr)' :
                                   window.innerWidth >= 1000 ? 'repeat(2, 1fr)' : '1fr'
            }}>
              {agentConfigs.map((config) => {
                const agent = agents[config.key] || { status: 'waiting', content: '', progress: 0 };
                const agentContent = analysisResults[config.key] || agent.content || '';

                return (
                  <div
                    key={config.key}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: 12,
                      overflow: 'hidden',
                      background: 'white',
                      transition: 'all 0.3s ease',
                      boxShadow: agent.status === 'working' ? '0 8px 25px rgba(0,0,0,0.1)' : 'none',
                      transform: agent.status === 'working' ? 'translateY(-2px)' : 'none'
                    }}
                  >
                    {/* 智能体头部 */}
                    <div style={{
                      background: 'linear-gradient(135deg, #4a5568 0%, #2d3748 100%)',
                      color: 'white',
                      padding: '15px 20px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      minHeight: 60
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        fontWeight: 600,
                        flex: 1,
                        minWidth: 0
                      }}>
                        <span style={{
                          marginRight: 10,
                          fontSize: '1.3rem',
                          flexShrink: 0
                        }}>
                          {config.icon}
                        </span>
                        <span style={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {config.name}
                        </span>
                      </div>
                      <div style={{
                        padding: '4px 12px',
                        borderRadius: 20,
                        fontSize: '0.85rem',
                        fontWeight: 500,
                        background: agent.status === 'waiting' ? '#718096' :
                                   agent.status === 'working' ? '#ed8936' :
                                   agent.status === 'complete' ? '#48bb78' : '#f56565',
                        color: 'white',
                        animation: agent.status === 'working' ? 'pulse 2s infinite' : 'none',
                        flexShrink: 0,
                        marginLeft: 10
                      }}>
                        {getStatusText(agent.status)}
                      </div>
                    </div>

                    {/* 智能体内容 */}
                    <div style={{
                      padding: 20,
                      minHeight: 200,
                      maxHeight: 350,
                      overflowY: 'auto',
                      background: '#f8f9fa',
                      fontFamily: 'Monaco, Menlo, Ubuntu Mono, monospace',
                      fontSize: 14,
                      lineHeight: 1.5,
                      whiteSpace: 'pre-wrap',
                      wordWrap: 'break-word'
                    }}>
                      {agentContent ? (
                        <div>{agentContent}</div>
                      ) : (
                        <div style={{
                          color: '#718096',
                          fontStyle: 'italic',
                          textAlign: 'center',
                          padding: '40px 20px',
                          fontFamily: 'inherit'
                        }}>
                          {agent.status === 'waiting' ? '等待开始分析...' :
                           agent.status === 'working' ? '正在分析中...' : '等待前序步骤完成...'}
                        </div>
                      )}
                    </div>

                    {/* 查看详细结果按钮 - 放在内容区域外部 */}
                    {(agent.status === 'complete' || analysisResults[config.key]) && (
                      <div style={{
                        padding: '15px 20px',
                        borderTop: '1px solid #e2e8f0',
                        textAlign: 'center',
                        background: '#ffffff'
                      }}>
                        <button
                          onClick={() => handleViewAgentResult(config.key)}
                          style={{
                            padding: '10px 20px',
                            background: config.color,
                            color: 'white',
                            border: 'none',
                            borderRadius: 8,
                            cursor: 'pointer',
                            fontSize: 13,
                            fontWeight: 500,
                            transition: 'all 0.3s ease',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                          }}
                        >
                          👁️ 查看详细结果
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* 最终结果 */}
            {showResult && (scriptResults.yaml_script || scriptResults.playwright_script) && (
              <div style={{ marginTop: 30 }}>
                <div style={{
                  background: 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
                  color: 'white',
                  padding: 25,
                  borderRadius: 15,
                  textAlign: 'center'
                }}>
                  <Title level={3} style={{
                    marginBottom: 20,
                    fontSize: '1.5rem',
                    color: 'white'
                  }}>
                    🎉 分析完成
                  </Title>
                  <div style={{
                    display: 'flex',
                    gap: 15,
                    justifyContent: 'center',
                    flexWrap: 'wrap'
                  }}>
                    {scriptResults.yaml_script && (
                      <button
                        onClick={() => {
                          const blob = new Blob([scriptResults.yaml_script!], { type: 'text/yaml' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `midscene_test_${Date.now()}.yaml`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          URL.revokeObjectURL(url);
                          message.success('YAML脚本已下载');
                        }}
                        style={{
                          padding: '12px 24px',
                          border: '2px solid white',
                          background: 'transparent',
                          color: 'white',
                          borderRadius: 8,
                          cursor: 'pointer',
                          fontWeight: 500,
                          transition: 'all 0.3s ease',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8
                        }}
                      >
                        <span>📄</span>
                        下载YAML脚本
                      </button>
                    )}

                    {scriptResults.playwright_script && (
                      <button
                        onClick={() => {
                          const blob = new Blob([scriptResults.playwright_script!], { type: 'text/typescript' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `midscene_test_${Date.now()}.spec.ts`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          URL.revokeObjectURL(url);
                          message.success('Playwright脚本已下载');
                        }}
                        style={{
                          padding: '12px 24px',
                          border: '2px solid white',
                          background: 'transparent',
                          color: 'white',
                          borderRadius: 8,
                          cursor: 'pointer',
                          fontWeight: 500,
                          transition: 'all 0.3s ease',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8
                        }}
                      >
                        <span>🎭</span>
                        下载Playwright脚本
                      </button>
                    )}

                    <button
                      onClick={handleReset}
                      style={{
                        padding: '12px 24px',
                        border: '2px solid white',
                        background: 'white',
                        color: '#48bb78',
                        borderRadius: 8,
                        cursor: 'pointer',
                        fontWeight: 500,
                        transition: 'all 0.3s ease',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8
                      }}
                    >
                      <span>🔄</span>
                      新建分析
                    </button>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        {/* 智能体结果详情弹窗 */}
        <AgentResultModal
          visible={modalVisible}
          onClose={() => setModalVisible(false)}
          agentName={selectedAgent?.name || ''}
          content={selectedAgent?.content || ''}
          agentType={selectedAgent?.type || 'ui'}
        />
      </div>

      {/* 添加CSS动画 */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        button:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }

        .upload-dragger:hover {
          border-color: #667eea !important;
          background: #f0f4ff !important;
        }
      `}</style>
    </div>
  );
};

export default UITestScriptPage;
