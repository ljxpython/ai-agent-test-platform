/**
 * 知识检索页面
 */
import { SearchOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { Card, Input, Button, List, Tag, Space, Spin, Empty, Tabs, message } from 'antd';
import React, { useState } from 'react';
import { searchDocuments, askQuestion, type SearchResult, type QuestionAnswer } from '@/services/knowledge-base';

const { TextArea } = Input;
const { TabPane } = Tabs;

const KnowledgeSearch: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState<boolean>(false);

  const [question, setQuestion] = useState<string>('');
  const [answer, setAnswer] = useState<QuestionAnswer | null>(null);
  const [questionLoading, setQuestionLoading] = useState<boolean>(false);

  // 搜索文档
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索内容');
      return;
    }

    setSearchLoading(true);
    try {
      const response = await searchDocuments({
        query: searchQuery,
        k: 10,
      });
      setSearchResults(response.data.results || []);
    } catch (error) {
      message.error('搜索失败');
    } finally {
      setSearchLoading(false);
    }
  };

  // 问答
  const handleAskQuestion = async () => {
    if (!question.trim()) {
      message.warning('请输入问题');
      return;
    }

    setQuestionLoading(true);
    try {
      const response = await askQuestion(question);
      setAnswer(response.data);
    } catch (error) {
      message.error('问答失败');
    } finally {
      setQuestionLoading(false);
    }
  };

  return (
    <PageContainer>
      <Tabs defaultActiveKey="search">
        <TabPane tab="文档搜索" key="search">
          <Card>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Input.Search
                placeholder="请输入搜索关键词"
                enterButton={
                  <Button type="primary" icon={<SearchOutlined />}>
                    搜索
                  </Button>
                }
                size="large"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onSearch={handleSearch}
                loading={searchLoading}
              />

              <Spin spinning={searchLoading}>
                {searchResults.length > 0 ? (
                  <List
                    itemLayout="vertical"
                    dataSource={searchResults}
                    renderItem={(item, index) => (
                      <List.Item
                        key={index}
                        extra={
                          <Tag color="blue">
                            相似度: {(1 / (1 + item.score)).toFixed(4)}
                          </Tag>
                        }
                      >
                        <List.Item.Meta
                          title={`结果 ${index + 1}`}
                          description={
                            <Space direction="vertical" style={{ width: '100%' }}>
                              {item.metadata && Object.keys(item.metadata).length > 0 && (
                                <div>
                                  {Object.entries(item.metadata).map(([key, value]) => (
                                    <Tag key={key}>
                                      {key}: {String(value)}
                                    </Tag>
                                  ))}
                                </div>
                              )}
                            </Space>
                          }
                        />
                        <div
                          style={{
                            padding: '12px',
                            background: '#f5f5f5',
                            borderRadius: '4px',
                            whiteSpace: 'pre-wrap',
                          }}
                        >
                          {item.content}
                        </div>
                      </List.Item>
                    )}
                  />
                ) : (
                  !searchLoading && <Empty description="暂无搜索结果" />
                )}
              </Spin>
            </Space>
          </Card>
        </TabPane>

        <TabPane tab="智能问答" key="qa">
          <Card>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <TextArea
                placeholder="请输入您的问题"
                rows={4}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />

              <Button
                type="primary"
                icon={<QuestionCircleOutlined />}
                onClick={handleAskQuestion}
                loading={questionLoading}
                size="large"
              >
                提问
              </Button>

              <Spin spinning={questionLoading}>
                {answer ? (
                  <Card
                    title="回答"
                    bordered={false}
                    style={{ background: '#f9f9f9' }}
                  >
                    <div
                      style={{
                        padding: '16px',
                        background: '#fff',
                        borderRadius: '4px',
                        whiteSpace: 'pre-wrap',
                        minHeight: '100px',
                      }}
                    >
                      {answer.answer}
                    </div>
                  </Card>
                ) : (
                  !questionLoading && <Empty description="请输入问题并提问" />
                )}
              </Spin>
            </Space>
          </Card>
        </TabPane>
      </Tabs>
    </PageContainer>
  );
};

export default KnowledgeSearch;
