import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Input, Space, message, Card } from 'antd';
import { DownloadOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

interface LogEntry {
  id: number;
  timestamp: string;
  status: 'GRANTED' | 'DENIED_QR' | 'DENIED_FACE';
  reason: string;
  employee_name: string;
  employee_email: string;
}

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      // NOTE: Make sure the JWT token is stored in localStorage under the key 'access_token'
      // If the key name is different (e.g. 'token'), update this line accordingly
      const token = localStorage.getItem('access_token');

      const response = await fetch('http://localhost:8000/admin/logs', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        message.error('Session expired. Please log in again.');
        return;
      }

      if (!response.ok) {
        throw new Error('Server error');
      }

      const data = await response.json();

      // Add a required "key" field for Ant Design Table
      const formattedData = data.map((item: LogEntry) => ({
        ...item,
        key: item.id.toString(),
      }));

      setLogs(formattedData);
      message.success('Log list updated successfully');
    } catch (error) {
      console.error(error);
      message.error('Failed to fetch logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const exportLogs = async () => {
    try {
      const token = localStorage.getItem('access_token');
      message.loading({ content: 'Generating report...', key: 'exportMsg' });

      const response = await fetch('http://localhost:8000/admin/logs/export', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Export error');
      }

      // Support binary file download (CSV stream)
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // File name with timestamp
      link.download = `access_report_${dayjs().format('YYYY-MM-DD_HH-mm')}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      message.success({ content: 'CSV file downloaded', key: 'exportMsg' });
    } catch (error) {
      message.error({ content: 'Failed to download export file', key: 'exportMsg' });
    }
  };

  const columns: ColumnsType<LogEntry> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Date & Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      sorter: (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      filters: [
        { text: 'GRANTED', value: 'GRANTED' },
        { text: 'DENIED_QR', value: 'DENIED_QR' },
        { text: 'DENIED_FACE', value: 'DENIED_FACE' },
      ],
      onFilter: (value, record) => record.status === value,
      render: (status) => {
        let color: 'default' | 'success' | 'warning' | 'error' = 'default';
        let label = status;

        if (status === 'GRANTED') {
          color = 'success';
          label = 'ACCESS GRANTED';
        } else if (status === 'DENIED_QR') {
          color = 'warning';
          label = 'QR CODE ERROR';
        } else if (status === 'DENIED_FACE') {
          color = 'error';
          label = 'BIOMETRIC ERROR';
        }

        return <Tag color={color}>{label}</Tag>;
      },
    },
    {
      title: 'Employee',
      key: 'employee',
      width: 250,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{record.employee_name}</div>
          <div style={{ fontSize: '12px', color: '#888' }}>
            {record.employee_email}
          </div>
        </div>
      ),
    },
    {
      title: 'Reason / Details',
      dataIndex: 'reason',
      key: 'reason',
      // Client-side search filter
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => {
        const search = (value as string).toLowerCase();
        return (
          record.reason.toLowerCase().includes(search) ||
          record.employee_name.toLowerCase().includes(search) ||
          record.employee_email.toLowerCase().includes(search)
        );
      },
    },
  ];

  return (
    <div>
      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <Space>
          <Input
            placeholder="Search (reason, name, email)..."
            prefix={<SearchOutlined />}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
          <Button icon={<ReloadOutlined />} onClick={fetchLogs}>
            Refresh
          </Button>
        </Space>

        <Button type="primary" icon={<DownloadOutlined />} onClick={exportLogs}>
          Download CSV report
        </Button>
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <Table<LogEntry>
          columns={columns}
          dataSource={logs}
          loading={loading}
          pagination={{ pageSize: 10, showSizeChanger: true }}
          size="middle"
          rowKey="id"
        />
      </Card>
    </div>
  );
};

export default Logs;
