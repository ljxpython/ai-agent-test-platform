import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  Select,
  Switch,
  Tag,
  Popconfirm,
  message,
  Card,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { SystemAPI, Api, ApiCreateRequest, ApiUpdateRequest } from '@/api/system';

// const { Search } = Input; // 暂未使用
const { TextArea } = Input;
const { Option } = Select;

const ApiManagePage: React.FC = () => {
  const [apis, setApis] = useState<Api[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [editingApi, setEditingApi] = useState<Api | null>(null);
  const [form] = Form.useForm();

  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [searchParams, setSearchParams] = useState({
    path: '',
    method: '',
    tags: '',
  });

  // HTTP方法选项
  const methodOptions = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

  // 加载API列表
  const loadApis = async () => {
    setLoading(true);
    try {
      const response = await SystemAPI.getApiList({
        page: pagination.current,
        page_size: pagination.pageSize,
        ...searchParams,
      });
      setApis(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
      }));
    } catch (error) {
      message.error('加载API列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApis();
  }, [pagination.current, pagination.pageSize]);

  // 搜索处理
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }));
    loadApis();
  };

  // 重置搜索
  const handleReset = () => {
    setSearchParams({
      path: '',
      method: '',
      tags: '',
    });
    setPagination(prev => ({ ...prev, current: 1 }));
    setTimeout(loadApis, 0);
  };

  // 同步API
  const handleSync = async () => {
    try {
      setLoading(true);
      await SystemAPI.syncApis();
      message.success('API同步成功');
      loadApis();
    } catch (error) {
      message.error('API同步失败');
    } finally {
      setLoading(false);
    }
  };

  // 新增API
  const handleAdd = () => {
    setEditingApi(null);
    setModalVisible(true);
    form.resetFields();
  };

  // 编辑API
  const handleEdit = (api: Api) => {
    setEditingApi(api);
    setModalVisible(true);
    form.setFieldsValue({
      path: api.path,
      method: api.method,
      summary: api.summary,
      description: api.description,
      tags: api.tags,
      is_active: api.is_active,
    });
  };

  // 删除API
  const handleDelete = async (id: number) => {
    try {
      await SystemAPI.deleteApi(id);
      message.success('删除成功');
      loadApis();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 保存API
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setModalLoading(true);

      if (editingApi) {
        // 更新API
        await SystemAPI.updateApi(editingApi.id, values as ApiUpdateRequest);
        message.success('更新成功');
      } else {
        // 创建API
        await SystemAPI.createApi(values as ApiCreateRequest);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadApis();
    } catch (error: any) {
      if (error?.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(editingApi ? '更新失败' : '创建失败');
    } finally {
      setModalLoading(false);
    }
  };

  // 获取方法标签颜色
  const getMethodColor = (method: string) => {
    const colors: Record<string, string> = {
      GET: 'green',
      POST: 'blue',
      PUT: 'orange',
      DELETE: 'red',
      PATCH: 'purple',
    };
    return colors[method] || 'default';
  };

  // 表格列定义
  const columns = [
    {
      title: 'API路径',
      dataIndex: 'path',
      key: 'path',
      ellipsis: true,
    },
    {
      title: '请求方式',
      dataIndex: 'method',
      key: 'method',
      width: 100,
      render: (method: string) => (
        <Tag color={getMethodColor(method)}>{method}</Tag>
      ),
    },
    {
      title: 'API简介',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
      render: (summary: string) => summary || '-',
    },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      width: 120,
      render: (tags: string) => (
        tags ? <Tag color="blue">{tags}</Tag> : '-'
      ),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, record: Api) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除该API吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="primary" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Input
                placeholder="请输入API路径"
                value={searchParams.path}
                onChange={(e) => setSearchParams(prev => ({ ...prev, path: e.target.value }))}
                onPressEnter={handleSearch}
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="请求方法"
                value={searchParams.method}
                onChange={(value) => setSearchParams(prev => ({ ...prev, method: value }))}
                allowClear
                style={{ width: '100%' }}
              >
                {methodOptions.map(method => (
                  <Option key={method} value={method}>
                    {method}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Input
                placeholder="请输入API标签"
                value={searchParams.tags}
                onChange={(e) => setSearchParams(prev => ({ ...prev, tags: e.target.value }))}
                onPressEnter={handleSearch}
              />
            </Col>
            <Col span={8}>
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                  搜索
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleReset}>
                  重置
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button type="primary" icon={<SyncOutlined />} onClick={handleSync}>
              同步API
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新建API
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={apis}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({
                ...prev,
                current: page,
                pageSize: pageSize || 10,
              }));
            },
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 新增/编辑API弹窗 */}
      <Modal
        title={editingApi ? '编辑API' : '新建API'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        confirmLoading={modalLoading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_active: true,
            method: 'GET',
          }}
        >
          <Form.Item
            label="API路径"
            name="path"
            rules={[{ required: true, message: '请输入API路径' }]}
          >
            <Input placeholder="请输入API路径，如：/api/v1/users" />
          </Form.Item>

          <Form.Item
            label="请求方法"
            name="method"
            rules={[{ required: true, message: '请选择请求方法' }]}
          >
            <Select placeholder="请选择请求方法">
              {methodOptions.map(method => (
                <Option key={method} value={method}>
                  {method}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="API简介" name="summary">
            <Input placeholder="请输入API简介" />
          </Form.Item>

          <Form.Item label="API描述" name="description">
            <TextArea rows={4} placeholder="请输入API描述" />
          </Form.Item>

          <Form.Item label="API标签" name="tags">
            <Input placeholder="请输入API标签" />
          </Form.Item>

          <Form.Item label="状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiManagePage;
