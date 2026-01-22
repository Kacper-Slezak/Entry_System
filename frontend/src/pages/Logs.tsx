import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, message, Card } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import Cookies from 'js-cookie';

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

  const fetchLogs = async (showSuccessMessage = false) => {
    setLoading(true);
    try {
      const token = Cookies.get('access_token');

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

      const formattedData = data.map((item: LogEntry) => ({
        ...item,
        key: item.id.toString(),
      }));

      setLogs(formattedData);
      if (showSuccessMessage) {
        message.success('Log list updated successfully');
      }
    } catch (error) {
      console.error(error);
      message.error('Failed to fetch logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(false);
  }, []);

  const exportLogs = async () => {
    try {
      const token = Cookies.get('access_token');
      if (!token) {
        message.error('Authorization token missing. Please log in again.');
        return;
      }

      message.loading({ content: 'Generating report...', key: 'exportMsg' });

      const response = await fetch('http://localhost:8000/admin/logs/export', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        message.error({ content: 'Session expired', key: 'exportMsg' });
        return;
      }

      if (!response.ok) {
        throw new Error('Export error');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      const now = new Date();
      const dateStr = now.toISOString().slice(0, 10);
      const timeStr = now.toTimeString().slice(0, 5).replace(':', '-');

      link.download = `access_report_${dateStr}_${timeStr}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      message.success({ content: 'CSV file downloaded', key: 'exportMsg' });
    } catch (error) {
      console.error(error);
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
      render: (text) => {
        if (!text) return '-';
        return new Date(text).toLocaleString('pl-PL', {
             year: 'numeric',
             month: '2-digit',
             day: '2-digit',
             hour: '2-digit',
             minute: '2-digit',
             second: '2-digit'
        });
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      filters: [
        { text: 'ACCESS_GRANTED', value: 'GRANTED' },
        { text: 'QR_CODE_ERROR', value: 'DENIED_QR' },
        { text: 'BIOMETRIC ERROR', value: 'DENIED_FACE' },
      ],
      onFilter: (value, record) => record.status === value,
      render: (status) => {
        let color: 'default' | 'success' | 'warning' | 'error' = 'default';
        let label = status;

        if (status === 'GRANTED') {
          color = 'success';
          label = 'ACCESS_GRANTED';
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
            <Button icon={<ReloadOutlined />} onClick={() => fetchLogs(true)}>
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
          pagination={{
            pageSize: 6,
          }}
          size="middle"
          rowKey="id"
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
};

export default Logs;
