import React from 'react';
import { Modal, Typography, Button, Space, message } from 'antd';
import { CopyOutlined, DownloadOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
// @ts-ignore
import SyntaxHighlighter from 'react-syntax-highlighter';
// @ts-ignore
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { Title, Text } = Typography;

interface AgentResultModalProps {
  visible: boolean;
  onClose: () => void;
  agentName: string;
  content: string;
  agentType: 'ui' | 'interaction' | 'midscene' | 'script';
}

const AgentResultModal: React.FC<AgentResultModalProps> = ({
  visible,
  onClose,
  agentName,
  content,
  agentType
}) => {
  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'ui': return '🔍';
      case 'interaction': return '🔄';
      case 'midscene': return '💡';
      case 'script': return '📜';
      default: return '🤖';
    }
  };

  const getAgentColor = (type: string) => {
    switch (type) {
      case 'ui': return '#667eea';
      case 'interaction': return '#11998e';
      case 'midscene': return '#fa709a';
      case 'script': return '#722ed1';
      default: return '#1890ff';
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      message.success('内容已复制到剪贴板');
    } catch (error) {
      message.error('复制失败');
    }
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${agentName}_${Date.now()}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    message.success('文件下载成功');
  };

  // 自定义Markdown组件
  const components = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={tomorrow}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    h1: ({ children }: any) => (
      <Title level={2} style={{ color: getAgentColor(agentType), marginTop: 24 }}>
        {children}
      </Title>
    ),
    h2: ({ children }: any) => (
      <Title level={3} style={{ color: getAgentColor(agentType), marginTop: 20 }}>
        {children}
      </Title>
    ),
    h3: ({ children }: any) => (
      <Title level={4} style={{ color: getAgentColor(agentType), marginTop: 16 }}>
        {children}
      </Title>
    ),
    p: ({ children }: any) => (
      <Text style={{ fontSize: 14, lineHeight: 1.6, display: 'block', marginBottom: 12 }}>
        {children}
      </Text>
    ),
    ul: ({ children }: any) => (
      <ul style={{ paddingLeft: 20, marginBottom: 12 }}>
        {children}
      </ul>
    ),
    ol: ({ children }: any) => (
      <ol style={{ paddingLeft: 20, marginBottom: 12 }}>
        {children}
      </ol>
    ),
    li: ({ children }: any) => (
      <li style={{ marginBottom: 4, fontSize: 14, lineHeight: 1.6 }}>
        {children}
      </li>
    ),
    blockquote: ({ children }: any) => (
      <div style={{
        borderLeft: `4px solid ${getAgentColor(agentType)}`,
        paddingLeft: 16,
        margin: '16px 0',
        background: '#f8f9fa',
        padding: '12px 16px',
        borderRadius: '0 8px 8px 0'
      }}>
        {children}
      </div>
    ),
    table: ({ children }: any) => (
      <div style={{ overflowX: 'auto', margin: '16px 0' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          border: '1px solid #e8e8e8'
        }}>
          {children}
        </table>
      </div>
    ),
    th: ({ children }: any) => (
      <th style={{
        padding: '8px 12px',
        background: getAgentColor(agentType),
        color: 'white',
        border: '1px solid #e8e8e8',
        fontSize: 14,
        fontWeight: 500
      }}>
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td style={{
        padding: '8px 12px',
        border: '1px solid #e8e8e8',
        fontSize: 14
      }}>
        {children}
      </td>
    )
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: getAgentColor(agentType),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18
          }}>
            {getAgentIcon(agentType)}
          </div>
          <div>
            <Title level={4} style={{ margin: 0, color: '#262626' }}>
              {agentName}
            </Title>
            <Text style={{ color: '#8c8c8c', fontSize: 12 }}>
              智能体分析结果详情
            </Text>
          </div>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={1000}
      style={{ top: 20 }}
      footer={
        <Space>
          <Button icon={<CopyOutlined />} onClick={handleCopy}>
            复制内容
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleDownload}>
            下载文件
          </Button>
          <Button type="primary" onClick={onClose}>
            关闭
          </Button>
        </Space>
      }
    >
      <div style={{
        maxHeight: 'calc(100vh - 200px)',
        overflowY: 'auto',
        padding: '16px 0'
      }}>
        {content ? (
          <ReactMarkdown components={components}>
            {content}
          </ReactMarkdown>
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '40px 0',
            color: '#8c8c8c'
          }}>
            <Text>暂无分析结果</Text>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default AgentResultModal;
