import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
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
  SettingOutlined,
} from '@ant-design/icons';
import { SystemAPI, Role, RoleCreateRequest, RoleUpdateRequest, Api } from '@/api/system';

// const { Search } = Input; // 暂未使用
const { TextArea } = Input;

const RoleManagePage: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [apis, setApis] = useState<Api[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [permissionModalVisible, setPermissionModalVisible] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [form] = Form.useForm();
  const [permissionForm] = Form.useForm();

  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [searchParams, setSearchParams] = useState({
    name: '',
  });

  // 加载角色列表
  const loadRoles = async () => {
    setLoading(true);
    try {
      const response = await SystemAPI.getRoleList({
        page: pagination.current,
        page_size: pagination.pageSize,
        ...searchParams,
      });
      setRoles(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
      }));
    } catch (error) {
      message.error('加载角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载API列表
  const loadApis = async () => {
    try {
      const response = await SystemAPI.getApiList({ page_size: 1000 });
      setApis(response.data);
    } catch (error) {
      message.error('加载API列表失败');
    }
  };

  useEffect(() => {
    loadRoles();
  }, [pagination.current, pagination.pageSize]);

  useEffect(() => {
    loadApis();
  }, []);

  // 搜索处理
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }));
    loadRoles();
  };

  // 重置搜索
  const handleReset = () => {
    setSearchParams({ name: '' });
    setPagination(prev => ({ ...prev, current: 1 }));
    setTimeout(loadRoles, 0);
  };

  // 新增角色
  const handleAdd = () => {
    setEditingRole(null);
    setModalVisible(true);
    form.resetFields();
  };

  // 编辑角色
  const handleEdit = (role: Role) => {
    setEditingRole(role);
    setModalVisible(true);
    form.setFieldsValue({
      name: role.name,
      description: role.description,
      is_active: role.is_active,
    });
  };

  // 删除角色
  const handleDelete = async (id: number) => {
    try {
      await SystemAPI.deleteRole(id);
      message.success('删除成功');
      loadRoles();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 设置权限
  const handleSetPermissions = async (role: Role) => {
    setEditingRole(role);
    setPermissionModalVisible(true);

    // 获取角色详情
    try {
      const response = await SystemAPI.getRole(role.id);
      permissionForm.setFieldsValue({
        api_ids: response.data.api_ids || [],
      });
    } catch (error) {
      message.error('加载角色权限失败');
    }
  };

  // 保存角色
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setModalLoading(true);

      if (editingRole) {
        // 更新角色
        await SystemAPI.updateRole(editingRole.id, values as RoleUpdateRequest);
        message.success('更新成功');
      } else {
        // 创建角色
        await SystemAPI.createRole(values as RoleCreateRequest);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadRoles();
    } catch (error: any) {
      if (error?.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(editingRole ? '更新失败' : '创建失败');
    } finally {
      setModalLoading(false);
    }
  };

  // 保存权限
  const handleSavePermissions = async () => {
    if (!editingRole) return;

    try {
      const values = await permissionForm.validateFields();
      setModalLoading(true);

      await SystemAPI.updateRoleApis(editingRole.id, values.api_ids || []);
      message.success('权限设置成功');
      setPermissionModalVisible(false);
      loadRoles();
    } catch (error) {
      message.error('权限设置失败');
    } finally {
      setModalLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '角色名',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Tag color="blue">{name}</Tag>
      ),
    },
    {
      title: '角色描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '创建日期',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => new Date(created_at).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right' as const,
      width: 250,
      render: (_: any, record: Role) => (
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
            title="确定删除该角色吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="primary" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
          <Button
            type="default"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => handleSetPermissions(record)}
          >
            设置权限
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Input
                placeholder="请输入角色名"
                value={searchParams.name}
                onChange={(e) => setSearchParams(prev => ({ ...prev, name: e.target.value }))}
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
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新建角色
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={roles}
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
        />
      </Card>

      {/* 新增/编辑角色弹窗 */}
      <Modal
        title={editingRole ? '编辑角色' : '新建角色'}
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
          }}
        >
          <Form.Item
            label="角色名称"
            name="name"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="请输入角色名称" />
          </Form.Item>

          <Form.Item label="角色描述" name="description">
            <TextArea rows={4} placeholder="请输入角色描述" />
          </Form.Item>

          <Form.Item label="状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 设置权限弹窗 */}
      <Modal
        title={`设置权限 - ${editingRole?.name}`}
        open={permissionModalVisible}
        onOk={handleSavePermissions}
        onCancel={() => setPermissionModalVisible(false)}
        confirmLoading={modalLoading}
        width={800}
      >
        <Form form={permissionForm} layout="vertical">
          <Form.Item label="API权限" name="api_ids">
            <div style={{ maxHeight: 400, overflow: 'auto' }}>
              {apis?.map(api => (
                <div key={api.id} style={{ marginBottom: 8 }}>
                  <Tag color={api.method === 'GET' ? 'green' : api.method === 'POST' ? 'blue' : 'orange'}>
                    {api.method}
                  </Tag>
                  <span style={{ marginLeft: 8 }}>{api.path}</span>
                  {api.summary && <span style={{ marginLeft: 8, color: '#666' }}>- {api.summary}</span>}
                </div>
              ))}
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RoleManagePage;
