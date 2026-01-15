import React from 'react';
import { Space, Button, Popconfirm, message } from 'antd';
import { EditOutlined, DeleteOutlined, FieldTimeOutlined } from '@ant-design/icons';
import type { EmployeeDataType } from '../types';
import { deleteEmployee } from '../services/api';

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
      const token = localStorage.getItem('access_token');
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
      <Button 
          size="small" 
          icon={<FieldTimeOutlined />}
        >
          Expiration Time
      </Button>
    </Space>
  );
};

export default EmployeeActions;