import React, { useState } from 'react';
import { Card, Tabs, Button, Space, Typography, message, Collapse } from 'antd';
import { CopyOutlined, DownloadOutlined, FileTextOutlined, CodeOutlined } from '@ant-design/icons';
// @ts-ignore
import SyntaxHighlighter from 'react-syntax-highlighter';
// @ts-ignore
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { Title, Text } = Typography;
// const { TabPane } = Tabs; // 暂未使用
// const { Panel } = Collapse; // 暂未使用

interface ScriptResult {
  yamlScript?: string;
  playwrightScript?: string;
  scriptInfo?: {
    testName: string;
    stepsCount: number;
    estimatedDuration: string;
    description?: string;
  };
}

interface ScriptResultPanelProps {
  results: ScriptResult;
  visible: boolean;
}

const ScriptResultPanel: React.FC<ScriptResultPanelProps> = ({ results, visible }) => {
  const [activeTab, setActiveTab] = useState('yaml');

  if (!visible || (!results.yamlScript && !results.playwrightScript)) {
    return null;
  }

  const handleCopy = async (content: string, type: string) => {
    try {
      await navigator.clipboard.writeText(content);
      message.success(`${type}脚本已复制到剪贴板`);
    } catch (error) {
      message.error('复制失败');
    }
  };

  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    message.success(`${filename} 下载成功`);
  };

  const renderScriptContent = (content: string, language: string) => (
    <div style={{ position: 'relative' }}>
      <SyntaxHighlighter
        language={language}
        style={tomorrow}
        customStyle={{
          margin: 0,
          borderRadius: 8,
          fontSize: 13,
          lineHeight: 1.5
        }}
        showLineNumbers
      >
        {content}
      </SyntaxHighlighter>
    </div>
  );

  return (
    <Card
      title={
        <Space>
          <span>🎉</span>
          <span>生成的测试脚本</span>
        </Space>
      }
      style={{ marginTop: 24, borderRadius: 16 }}
      styles={{ body: { padding: 0 } }}
    >
      {/* 脚本信息 */}
      {results.scriptInfo && (
        <div style={{
          padding: 16,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: '16px 16px 0 0'
        }}>
          <Title level={4} style={{ color: 'white', margin: 0, marginBottom: 8 }}>
            {results.scriptInfo.testName}
          </Title>
          <Space size="large" wrap>
            <Text style={{ color: 'rgba(255,255,255,0.9)' }}>
              📊 步骤数量: {results.scriptInfo.stepsCount}
            </Text>
            <Text style={{ color: 'rgba(255,255,255,0.9)' }}>
              ⏱️ 预估时间: {results.scriptInfo.estimatedDuration}
            </Text>
          </Space>
          {results.scriptInfo.description && (
            <div style={{ marginTop: 8 }}>
              <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 13 }}>
                {results.scriptInfo.description}
              </Text>
            </div>
          )}
        </div>
      )}

      {/* 脚本内容 */}
      <div style={{ padding: 16 }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            ...(results.yamlScript ? [{
              key: 'yaml',
              label: (
                <Space>
                  <FileTextOutlined />
                  YAML 脚本 (Midscene格式)
                </Space>
              ),
              children: (
                <div>
                  <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text style={{ color: '#666', fontSize: 13 }}>
                      适用于 Midscene.js 框架的 YAML 格式测试脚本
                    </Text>
                    <Space>
                      <Button
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => handleCopy(results.yamlScript!, 'YAML')}
                      >
                        复制
                      </Button>
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownload(results.yamlScript!, 'midscene-test.yaml')}
                      >
                        下载
                      </Button>
                    </Space>
                  </div>
                  {renderScriptContent(results.yamlScript, 'yaml')}
                </div>
              )
            }] : []),
            ...(results.playwrightScript ? [{
              key: 'playwright',
              label: (
                <Space>
                  <CodeOutlined />
                  Playwright 脚本 (TypeScript格式)
                </Space>
              ),
              children: (
                <div>
                  <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text style={{ color: '#666', fontSize: 13 }}>
                      基于 Playwright + Midscene 的 TypeScript 测试脚本
                    </Text>
                    <Space>
                      <Button
                        size="small"
                        icon={<CopyOutlined />}
                        onClick={() => handleCopy(results.playwrightScript!, 'Playwright')}
                      >
                        复制
                      </Button>
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownload(results.playwrightScript!, 'midscene-test.spec.ts')}
                      >
                        下载
                      </Button>
                    </Space>
                  </div>
                  {renderScriptContent(results.playwrightScript, 'typescript')}
                </div>
              )
            }] : [])
          ]}
        />

        {/* 使用说明 */}
        <Collapse
          style={{ marginTop: 16 }}
          size="small"
          items={[
            {
              key: 'usage',
              label: '📖 使用说明',
              children: (
                <div style={{ fontSize: 13, lineHeight: 1.6 }}>
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>YAML 脚本使用方法：</Text>
                    <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                      <li>将脚本保存为 <code>.yaml</code> 文件</li>
                      <li>使用 Midscene.js CLI 工具运行：<code>midscene run test.yaml</code></li>
                      <li>确保已安装 Midscene.js 依赖</li>
                    </ul>
                  </div>
                  <div>
                    <Text strong>Playwright 脚本使用方法：</Text>
                    <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                      <li>将脚本保存为 <code>.spec.ts</code> 文件</li>
                      <li>使用 Playwright 运行：<code>npx playwright test</code></li>
                      <li>确保已安装 Playwright 和 Midscene 依赖</li>
                    </ul>
                  </div>
                </div>
              )
            }
          ]}
        />
      </div>
    </Card>
  );
};

export default ScriptResultPanel;
