/**
 * 文档管理页面
 */
import { PlusOutlined, DeleteOutlined, CloudUploadOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { ProTable, ModalForm, ProFormText, ProFormTextArea } from '@ant-design/pro-components';
import { Button, message, Upload, Tag, Popconfirm, Space } from 'antd';
import React, { useRef, useState } from 'react';
import type { UploadFile } from 'antd/es/upload/interface';
import {
  getDocumentList,
  uploadDocument,
  processDocument,
  deleteDocument,
  type Document,
} from '@/services/knowledge-base';

const DocumentManagement: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [createModalOpen, setCreateModalOpen] = useState<boolean>(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // 状态标签颜色映射
  const statusColorMap: Record<string, string> = {
    uploaded: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error',
  };

  // 状态文本映射
  const statusTextMap: Record<string, string> = {
    uploaded: '已上传',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  };

  // 文件大小格式化
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // 处理文档
  const handleProcess = async (record: Document) => {
    try {
      await processDocument(record.id);
      message.success('文档处理成功');
      actionRef.current?.reload();
    } catch (error) {
      message.error('文档处理失败');
    }
  };

  // 删除文档
  const handleDelete = async (record: Document) => {
    try {
      await deleteDocument(record.id);
      message.success('删除成功');
      actionRef.current?.reload();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 上传文档
  const handleUpload = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择文件');
      return false;
    }

    const formData = new FormData();
    formData.append('file', fileList[0] as any);
    if (values.description) {
      formData.append('description', values.description);
    }
    if (values.tags) {
      formData.append('tags', values.tags);
    }

    try {
      await uploadDocument(formData);
      message.success('上传成功');
      setFileList([]);
      setCreateModalOpen(false);
      actionRef.current?.reload();
      return true;
    } catch (error) {
      message.error('上传失败');
      return false;
    }
  };

  const columns: ProColumns<Document>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
      search: false,
    },
    {
      title: '文件名',
      dataIndex: 'original_filename',
      ellipsis: true,
      copyable: true,
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      width: 100,
      search: false,
      render: (text) => <Tag>{text}</Tag>,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      width: 120,
      search: false,
      render: (_, record) => formatFileSize(record.file_size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      valueType: 'select',
      valueEnum: {
        uploaded: { text: '已上传', status: 'Default' },
        processing: { text: '处理中', status: 'Processing' },
        completed: { text: '已完成', status: 'Success' },
        failed: { text: '失败', status: 'Error' },
      },
      render: (_, record) => (
        <Tag color={statusColorMap[record.status]}>
          {statusTextMap[record.status] || record.status}
        </Tag>
      ),
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      width: 100,
      search: false,
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      valueType: 'dateTime',
      width: 180,
      search: false,
    },
    {
      title: '操作',
      valueType: 'option',
      width: 200,
      render: (_, record) => [
        record.status === 'uploaded' && (
          <a key="process" onClick={() => handleProcess(record)}>
            处理
          </a>
        ),
        <Popconfirm
          key="delete"
          title="确定要删除吗?"
          onConfirm={() => handleDelete(record)}
        >
          <a style={{ color: 'red' }}>删除</a>
        </Popconfirm>,
      ],
    },
  ];

  return (
    <>
      <ProTable<Document>
        headerTitle="文档管理"
        actionRef={actionRef}
        rowKey="id"
        search={{
          labelWidth: 120,
        }}
        toolBarRender={() => [
          <Button
            type="primary"
            key="primary"
            onClick={() => setCreateModalOpen(true)}
          >
            <PlusOutlined /> 上传文档
          </Button>,
        ]}
        request={async (params) => {
          const response = await getDocumentList({
            page: params.current,
            page_size: params.pageSize,
            status: params.status,
          });
          return {
            data: response.data.list,
            success: response.success,
            total: response.data.total,
          };
        }}
        columns={columns}
      />

      <ModalForm
        title="上传文档"
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onFinish={handleUpload}
      >
        <Upload
          beforeUpload={(file) => {
            setFileList([file]);
            return false;
          }}
          onRemove={() => setFileList([])}
          fileList={fileList}
          maxCount={1}
        >
          <Button icon={<CloudUploadOutlined />}>选择文件</Button>
        </Upload>
        <ProFormTextArea
          name="description"
          label="描述"
          placeholder="请输入文档描述"
        />
        <ProFormText
          name="tags"
          label="标签"
          placeholder="请输入标签,多个标签用逗号分隔"
        />
      </ModalForm>
    </>
  );
};

export default DocumentManagement;
