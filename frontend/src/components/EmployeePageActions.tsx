import React from 'react';
import { Space, Button, Popconfirm, message } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { EmployeeDataType } from '../types';
import { deleteEmployee } from '../services/api';
import Cookies from 'js-cookie';

    interface EmployeeActionsProps {
    record: EmployeeDataType;
    onEdit: (record: EmployeeDataType) => void;
    onDeleteSuccess: () => void;
    }

const EmployeeActions: React.FC<EmployeeActionsProps> = ({
  record,
  onEdit,
  onDeleteSuccess
}) => {
  const handleDelete = async () => {
    try {
      const token = Cookies.get('access_token');
      if (!token) {
        message.error('No authentication token');
        return;
      }
      await deleteEmployee(record.uuid, token);
      message.success('Employee deleted');
      onDeleteSuccess();
    } catch (error) {
      message.error('Failed to delete employee');
      console.error(error);
    }
  };

  return (
    <Space size="small">
      <Button
        type="primary"
        size="small"
        icon={<EditOutlined />}
        onClick={() => onEdit(record)}
      >
        Edit
      </Button>
      <Popconfirm
        title="Delete employee"
        description="Are you sure to delete this employee?"
        onConfirm={handleDelete}
        okText="Yes"
        cancelText="No"
      >
        <Button
          danger
          size="small"
          icon={<DeleteOutlined />}
        >
          Delete
        </Button>
      </Popconfirm>
    </Space>
  );
};

export default EmployeeActions;
