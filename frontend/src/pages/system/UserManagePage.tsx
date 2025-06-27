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
  // Divider, // 暂未使用
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  KeyOutlined,
} from '@ant-design/icons';
import { SystemAPI, User, UserCreateRequest, UserUpdateRequest, Role, Department } from '@/api/system';

// const { Search } = Input; // 暂未使用
const { Option } = Select;

const UserManagePage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form] = Form.useForm();

  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [searchParams, setSearchParams] = useState({
    username: '',
    email: '',
    dept_id: undefined as number | undefined,
  });

  // 加载用户列表
  const loadUsers = async () => {
    console.log('🔄 [UserManagePage] 开始加载用户列表');
    console.log('📋 [UserManagePage] 请求参数:', {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchParams,
    });

    setLoading(true);
    try {
      const response = await SystemAPI.getUserList({
        page: pagination.current,
        page_size: pagination.pageSize,
        ...searchParams,
      });

      console.log('✅ [UserManagePage] API响应成功:', response);
      console.log('📊 [UserManagePage] 响应数据结构:', {
        code: response.code,
        msg: response.msg,
        dataType: typeof response.data,
        dataLength: Array.isArray(response.data) ? response.data.length : 'not array',
        total: response.total,
        page: response.page,
        page_size: response.page_size
      });

      if (Array.isArray(response.data)) {
        console.log('👥 [UserManagePage] 用户数据:', response.data);
        setUsers(response.data);
      } else {
        console.error('❌ [UserManagePage] 响应数据不是数组:', response.data);
        setUsers([]);
      }

      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
      }));

      console.log('📈 [UserManagePage] 分页信息更新:', {
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: response.total || 0
      });

    } catch (error) {
      console.error('❌ [UserManagePage] 加载用户列表失败:', error);
      message.error('加载用户列表失败');
      setUsers([]);
    } finally {
      setLoading(false);
      console.log('🏁 [UserManagePage] 用户列表加载完成');
    }
  };

  // 加载角色和部门数据
  const loadRolesAndDepartments = async () => {
    console.log('🔄 [UserManagePage] 开始加载角色和部门数据');
    try {
      const [rolesResponse, deptsResponse] = await Promise.all([
        SystemAPI.getRoleList({ page_size: 1000 }),
        SystemAPI.getDepartmentTree(),
      ]);

      console.log('✅ [UserManagePage] 角色数据响应:', rolesResponse);
      console.log('✅ [UserManagePage] 部门数据响应:', deptsResponse);

      if (Array.isArray(rolesResponse.data)) {
        console.log('👔 [UserManagePage] 设置角色数据:', rolesResponse.data);
        setRoles(rolesResponse.data);
      } else {
        console.error('❌ [UserManagePage] 角色数据不是数组:', rolesResponse.data);
        setRoles([]);
      }

      if (Array.isArray(deptsResponse.data)) {
        console.log('🏢 [UserManagePage] 设置部门数据:', deptsResponse.data);
        setDepartments(deptsResponse.data);
      } else {
        console.error('❌ [UserManagePage] 部门数据不是数组:', deptsResponse.data);
        setDepartments([]);
      }

    } catch (error) {
      console.error('❌ [UserManagePage] 加载基础数据失败:', error);
      message.error('加载基础数据失败');
      setRoles([]);
      setDepartments([]);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [pagination.current, pagination.pageSize]);

  useEffect(() => {
    loadRolesAndDepartments();
  }, []);

  // 搜索处理
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }));
    loadUsers();
  };

  // 重置搜索
  const handleReset = () => {
    setSearchParams({
      username: '',
      email: '',
      dept_id: undefined,
    });
    setPagination(prev => ({ ...prev, current: 1 }));
    setTimeout(loadUsers, 0);
  };

  // 新增用户
  const handleAdd = () => {
    setEditingUser(null);
    setModalVisible(true);
    form.resetFields();
  };

  // 编辑用户
  const handleEdit = (user: User) => {
    setEditingUser(user);
    setModalVisible(true);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      is_active: user.is_active,
      dept_id: user.dept?.id,
      role_ids: user.roles.map(role => role.id),
    });
  };

  // 删除用户
  const handleDelete = async (id: number) => {
    try {
      await SystemAPI.deleteUser(id);
      message.success('删除成功');
      loadUsers();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 重置密码
  const handleResetPassword = async (id: number) => {
    try {
      await SystemAPI.resetUserPassword(id);
      message.success('密码已重置为123456');
    } catch (error) {
      message.error('重置密码失败');
    }
  };

  // 保存用户
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setModalLoading(true);

      if (editingUser) {
        // 更新用户
        await SystemAPI.updateUser(editingUser.id, values as UserUpdateRequest);
        message.success('更新成功');
      } else {
        // 创建用户
        await SystemAPI.createUser(values as UserCreateRequest);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadUsers();
    } catch (error: any) {
      if (error?.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(editingUser ? '更新失败' : '创建失败');
    } finally {
      setModalLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '名称',
      dataIndex: 'username',
      key: 'username',
      ellipsis: true,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      ellipsis: true,
    },
    {
      title: '用户角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: User['roles']) => (
        <Space wrap>
          {roles.map(role => (
            <Tag key={role.id} color="blue">
              {role.name}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '部门',
      dataIndex: ['dept', 'name'],
      key: 'dept',
      ellipsis: true,
    },
    {
      title: '超级用户',
      dataIndex: 'is_superuser',
      key: 'is_superuser',
      render: (is_superuser: boolean) => (
        <Tag color={is_superuser ? 'red' : 'default'}>
          {is_superuser ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '上次登录时间',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (last_login: string) => last_login || '-',
    },
    {
      title: '禁用',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active: boolean) => (
        <Switch checked={is_active} disabled size="small" />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right' as const,
      width: 200,
      render: (_: any, record: User) => (
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
            title="确定删除该用户吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="primary" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
          {!record.is_superuser && (
            <Popconfirm
              title="确定重置用户密码为123456吗？"
              onConfirm={() => handleResetPassword(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="default" size="small" icon={<KeyOutlined />}>
                重置密码
              </Button>
            </Popconfirm>
          )}
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
                placeholder="请输入用户名称"
                value={searchParams.username}
                onChange={(e) => setSearchParams(prev => ({ ...prev, username: e.target.value }))}
                onPressEnter={handleSearch}
              />
            </Col>
            <Col span={6}>
              <Input
                placeholder="请输入邮箱"
                value={searchParams.email}
                onChange={(e) => setSearchParams(prev => ({ ...prev, email: e.target.value }))}
                onPressEnter={handleSearch}
              />
            </Col>
            <Col span={6}>
              <Select
                placeholder="请选择部门"
                value={searchParams.dept_id}
                onChange={(value) => setSearchParams(prev => ({ ...prev, dept_id: value }))}
                allowClear
                style={{ width: '100%' }}
              >
                {departments?.map(dept => (
                  <Option key={dept.id} value={dept.id}>
                    {dept.name}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
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
            新建用户
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={users}
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
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 新增/编辑用户弹窗 */}
      <Modal
        title={editingUser ? '编辑用户' : '新建用户'}
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
            role_ids: [],
          }}
        >
          <Form.Item
            label="用户名称"
            name="username"
            rules={[{ required: true, message: '请输入用户名称' }]}
          >
            <Input placeholder="请输入用户名称" />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item label="全名" name="full_name">
            <Input placeholder="请输入全名" />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
          )}

          <Form.Item
            label="角色"
            name="role_ids"
            rules={[{ required: true, message: '请至少选择一个角色' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择角色"
              style={{ width: '100%' }}
            >
              {roles?.map(role => (
                <Option key={role.id} value={role.id}>
                  {role.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="部门" name="dept_id">
            <Select placeholder="请选择部门" allowClear>
              {departments?.map(dept => (
                <Option key={dept.id} value={dept.id}>
                  {dept.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagePage;
