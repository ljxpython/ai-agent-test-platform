import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  Switch,
  Popconfirm,
  message,
  Card,
  Row,
  Col,
  InputNumber,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { SystemAPI, Department, DepartmentCreateRequest, DepartmentUpdateRequest } from '@/api/system';

// const { Search } = Input; // 暂未使用
const { TextArea } = Input;

const DepartmentManagePage: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);
  const [form] = Form.useForm();

  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [searchParams, setSearchParams] = useState({
    name: '',
  });

  // 加载部门列表
  const loadDepartments = async () => {
    setLoading(true);
    try {
      const response = await SystemAPI.getDepartmentList({
        page: pagination.current,
        page_size: pagination.pageSize,
        ...searchParams,
      });
      setDepartments(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
      }));
    } catch (error) {
      message.error('加载部门列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDepartments();
  }, [pagination.current, pagination.pageSize]);

  // 搜索处理
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }));
    loadDepartments();
  };

  // 重置搜索
  const handleReset = () => {
    setSearchParams({ name: '' });
    setPagination(prev => ({ ...prev, current: 1 }));
    setTimeout(loadDepartments, 0);
  };

  // 新增部门
  const handleAdd = () => {
    setEditingDepartment(null);
    setModalVisible(true);
    form.resetFields();
  };

  // 编辑部门
  const handleEdit = (department: Department) => {
    setEditingDepartment(department);
    setModalVisible(true);
    form.setFieldsValue({
      name: department.name,
      description: department.description,
      parent_id: department.parent_id,
      sort_order: department.sort_order,
      is_active: department.is_active,
    });
  };

  // 删除部门
  const handleDelete = async (id: number) => {
    try {
      await SystemAPI.deleteDepartment(id);
      message.success('删除成功');
      loadDepartments();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 保存部门
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setModalLoading(true);

      if (editingDepartment) {
        // 更新部门
        await SystemAPI.updateDepartment(editingDepartment.id, values as DepartmentUpdateRequest);
        message.success('更新成功');
      } else {
        // 创建部门
        await SystemAPI.createDepartment(values as DepartmentCreateRequest);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadDepartments();
    } catch (error: any) {
      if (error?.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(editingDepartment ? '更新失败' : '创建失败');
    } finally {
      setModalLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '部门名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '备注',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (description: string) => description || '-',
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, record: Department) => (
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
            title="确定删除该部门吗？"
            description="删除部门前请确保该部门下没有子部门和用户"
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
            <Col span={8}>
              <Input
                placeholder="请输入部门名称"
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
            新建部门
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={departments}
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

      {/* 新增/编辑部门弹窗 */}
      <Modal
        title={editingDepartment ? '编辑部门' : '新建部门'}
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
            sort_order: 0,
          }}
        >
          <Form.Item
            label="部门名称"
            name="name"
            rules={[{ required: true, message: '请输入部门名称' }]}
          >
            <Input placeholder="请输入部门名称" />
          </Form.Item>

          <Form.Item label="部门描述" name="description">
            <TextArea rows={4} placeholder="请输入部门描述" />
          </Form.Item>

          <Form.Item label="排序" name="sort_order">
            <InputNumber
              min={0}
              placeholder="请输入排序值"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item label="状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DepartmentManagePage;
