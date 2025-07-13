/**
 * 结果查看面板组件
 * 显示AI分析结果、生成的测试脚本等
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Space,
  Typography,
  Modal,
  Tabs,
  Alert,
  Empty,
  Tag,
  Tooltip,
  message,
  Spin,
} from 'antd';
import {
  EyeOutlined,
  DownloadOutlined,
  CopyOutlined,
  FileTextOutlined,
  CodeOutlined,
  PictureOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;
const { TabPane } = Tabs;

interface ResultViewPanelProps {
  selectedProject: string;
  refreshKey: number;
}

interface TaskResult {
  task_id: string;
  filename: string;
  status: string;
  result_data: {
    ui_analysis?: string;
    interaction_analysis?: string;
    midscene_json?: string;
    yaml_script?: string;
    playwright_script?: string;
  };
  file_path: string;
  created_at: string;
}

const ResultViewPanel: React.FC<ResultViewPanelProps> = ({
  selectedProject,
  refreshKey,
}) => {
  const [results, setResults] = useState<TaskResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState<TaskResult | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // 获取完成的任务结果
  const fetchResults = async () => {
    if (!selectedProject) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/ui-test/tasks/project/${selectedProject}`);
      if (response.ok) {
        const data = await response.json();
        // 只显示已完成且有结果数据的任务
        const completedTasks = (data.data.tasks || []).filter(
          (task: any) => task.status === 'completed' &&
                        task.result_data &&
                        Object.keys(task.result_data).length > 0
        );
        setResults(completedTasks);
      } else {
        message.error('获取结果数据失败');
      }
    } catch (error) {
      console.error('获取结果数据失败:', error);
      message.error('获取结果数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 查看详细结果
  const handleViewDetail = (result: TaskResult) => {
    setSelectedResult(result);
    setDetailModalVisible(true);
  };

  // 复制内容到剪贴板
  const handleCopy = (content: string, type: string) => {
    navigator.clipboard.writeText(content).then(() => {
      message.success(`${type}已复制到剪贴板`);
    }).catch(() => {
      message.error('复制失败');
    });
  };

  // 下载内容为文件
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
    message.success('文件下载成功');
  };

  // 渲染结果内容
  const renderResultContent = (result: TaskResult) => {
    const { result_data } = result;

    return (
      <Tabs defaultActiveKey="ui_analysis">
        {result_data.ui_analysis && (
          <TabPane
            tab={
              <Space>
                <PictureOutlined />
                UI分析
              </Space>
            }
            key="ui_analysis"
          >
            <Card
              size="small"
              extra={
                <Space>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopy(result_data.ui_analysis!, 'UI分析结果')}
                  >
                    复制
                  </Button>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(
                      result_data.ui_analysis!,
                      `${result.filename}_ui_analysis.txt`
                    )}
                  >
                    下载
                  </Button>
                </Space>
              }
            >
              <pre style={{
                whiteSpace: 'pre-wrap',
                background: '#f5f5f5',
                padding: 16,
                borderRadius: 6,
                maxHeight: 400,
                overflow: 'auto'
              }}>
                {result_data.ui_analysis}
              </pre>
            </Card>
          </TabPane>
        )}

        {result_data.interaction_analysis && (
          <TabPane
            tab={
              <Space>
                <PlayCircleOutlined />
                交互分析
              </Space>
            }
            key="interaction_analysis"
          >
            <Card
              size="small"
              extra={
                <Space>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopy(result_data.interaction_analysis!, '交互分析结果')}
                  >
                    复制
                  </Button>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(
                      result_data.interaction_analysis!,
                      `${result.filename}_interaction_analysis.txt`
                    )}
                  >
                    下载
                  </Button>
                </Space>
              }
            >
              <pre style={{
                whiteSpace: 'pre-wrap',
                background: '#f5f5f5',
                padding: 16,
                borderRadius: 6,
                maxHeight: 400,
                overflow: 'auto'
              }}>
                {result_data.interaction_analysis}
              </pre>
            </Card>
          </TabPane>
        )}

        {result_data.yaml_script && (
          <TabPane
            tab={
              <Space>
                <FileTextOutlined />
                YAML脚本
              </Space>
            }
            key="yaml_script"
          >
            <Card
              size="small"
              extra={
                <Space>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopy(result_data.yaml_script!, 'YAML脚本')}
                  >
                    复制
                  </Button>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(
                      result_data.yaml_script!,
                      `${result.filename}_test.yaml`
                    )}
                  >
                    下载
                  </Button>
                </Space>
              }
            >
              <pre style={{
                whiteSpace: 'pre-wrap',
                background: '#f5f5f5',
                padding: 16,
                borderRadius: 6,
                maxHeight: 400,
                overflow: 'auto',
                fontFamily: 'Monaco, Consolas, monospace'
              }}>
                {result_data.yaml_script}
              </pre>
            </Card>
          </TabPane>
        )}

        {result_data.playwright_script && (
          <TabPane
            tab={
              <Space>
                <CodeOutlined />
                Playwright脚本
              </Space>
            }
            key="playwright_script"
          >
            <Card
              size="small"
              extra={
                <Space>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopy(result_data.playwright_script!, 'Playwright脚本')}
                  >
                    复制
                  </Button>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(
                      result_data.playwright_script!,
                      `${result.filename}_test.js`
                    )}
                  >
                    下载
                  </Button>
                </Space>
              }
            >
              <pre style={{
                whiteSpace: 'pre-wrap',
                background: '#f5f5f5',
                padding: 16,
                borderRadius: 6,
                maxHeight: 400,
                overflow: 'auto',
                fontFamily: 'Monaco, Consolas, monospace'
              }}>
                {result_data.playwright_script}
              </pre>
            </Card>
          </TabPane>
        )}
      </Tabs>
    );
  };

  // 监听刷新
  useEffect(() => {
    fetchResults();
  }, [selectedProject, refreshKey]);

  if (!selectedProject) {
    return (
      <Alert
        message="请先选择项目"
        description="选择一个项目后即可查看该项目的分析结果"
        type="info"
        showIcon
      />
    );
  }

  return (
    <div>
      <Spin spinning={loading}>
        {results.length === 0 ? (
          <Empty
            description="暂无分析结果"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Text type="secondary">
              上传图片并完成分析后，结果将显示在这里
            </Text>
          </Empty>
        ) : (
          <List
            grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3 }}
            dataSource={results}
            renderItem={(result) => (
              <List.Item>
                <Card
                  hoverable
                  actions={[
                    <Tooltip title="查看详情">
                      <Button
                        type="text"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewDetail(result)}
                      >
                        查看详情
                      </Button>
                    </Tooltip>,
                  ]}
                >
                  <Card.Meta
                    avatar={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24 }} />}
                    title={
                      <Tooltip title={result.filename}>
                        <Text ellipsis style={{ maxWidth: 200 }}>
                          {result.filename}
                        </Text>
                      </Tooltip>
                    }
                    description={
                      <div>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {new Date(result.created_at).toLocaleString()}
                          </Text>
                        </div>
                        <Space wrap>
                          {result.result_data.ui_analysis && (
                            <Tag color="blue">UI分析</Tag>
                          )}
                          {result.result_data.interaction_analysis && (
                            <Tag color="green">交互分析</Tag>
                          )}
                          {result.result_data.yaml_script && (
                            <Tag color="orange">YAML脚本</Tag>
                          )}
                          {result.result_data.playwright_script && (
                            <Tag color="purple">Playwright脚本</Tag>
                          )}
                        </Space>
                      </div>
                    }
                  />
                </Card>
              </List.Item>
            )}
          />
        )}
      </Spin>

      {/* 详情模态框 */}
      <Modal
        title={`分析结果 - ${selectedResult?.filename}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width="90%"
        style={{ top: 20 }}
      >
        {selectedResult && (
          <div>
            <Alert
              message={`任务ID: ${selectedResult.task_id}`}
              type="info"
              style={{ marginBottom: 16 }}
            />
            {renderResultContent(selectedResult)}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ResultViewPanel;
