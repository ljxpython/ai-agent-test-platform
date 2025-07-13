/**
 * 项目选择器组件
 * 支持项目选择、创建新项目等功能
 */

import React, { useState, useEffect } from 'react';
import {
  Select,
  Button,
  Modal,
  Form,
  Input,
  message,
  Space,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  FolderOutlined,
  ReloadOutlined,
} from '@ant-design/icons';

const { Option } = Select;

interface Project {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  is_active: boolean;
}

interface ProjectSelectorProps {
  value?: string;
  onChange?: (value: string) => void;
  style?: React.CSSProperties;
  placeholder?: string;
}

const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  value,
  onChange,
  style,
  placeholder = "选择项目",
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [createForm] = Form.useForm();

  // 获取项目列表
  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/projects');
      if (response.ok) {
        const data = await response.json();
        setProjects(data.data || []);

        // 如果没有选中项目且有项目列表，自动选择第一个
        if (!value && data.data && data.data.length > 0) {
          onChange?.(data.data[0].name);
        }
      } else {
        message.error('获取项目列表失败');
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
      message.error('获取项目列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建新项目
  const handleCreateProject = async (values: any) => {
    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: values.name,
          display_name: values.display_name || values.name,
          description: values.description || `UI测试项目 - ${values.name}`,
          is_active: true,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        message.success('项目创建成功');
        setCreateModalVisible(false);
        createForm.resetFields();

        // 刷新项目列表
        await fetchProjects();

        // 自动选择新创建的项目
        onChange?.(values.name);
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || '项目创建失败');
      }
    } catch (error) {
      console.error('创建项目失败:', error);
      message.error('创建项目失败');
    }
  };

  // 组件挂载时获取项目列表
  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <Space.Compact style={style}>
      <Select
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        loading={loading}
        style={{ flex: 1, minWidth: 150 }}
        showSearch
        filterOption={(input, option) =>
          (option?.children as unknown as string)
            ?.toLowerCase()
            ?.includes(input.toLowerCase())
        }
        dropdownRender={(menu) => (
          <>
            {menu}
            <div style={{ padding: '8px', borderTop: '1px solid #f0f0f0' }}>
              <Button
                type="link"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
                style={{ width: '100%', textAlign: 'left' }}
              >
                创建新项目
              </Button>
            </div>
          </>
        )}
      >
        {projects.map((project) => (
          <Option key={project.name} value={project.name}>
            <Space>
              <FolderOutlined />
              {project.display_name || project.name}
            </Space>
          </Option>
        ))}
      </Select>

      <Tooltip title="刷新项目列表">
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchProjects}
          loading={loading}
        />
      </Tooltip>

      {/* 创建项目模态框 */}
      <Modal
        title="创建新项目"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        onOk={() => createForm.submit()}
        okText="创建"
        cancelText="取消"
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateProject}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[
              { required: true, message: '请输入项目名称' },
              { pattern: /^[a-zA-Z0-9_-]+$/, message: '项目名称只能包含字母、数字、下划线和横线' },
            ]}
          >
            <Input placeholder="例如: my_ui_project" />
          </Form.Item>

          <Form.Item
            name="display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="例如: 我的UI项目" />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入项目描述（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space.Compact>
  );
};

export default ProjectSelector;
