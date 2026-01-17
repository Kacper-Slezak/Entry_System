import React, { useRef, useState, useEffect } from 'react';
import { SearchOutlined } from '@ant-design/icons';
import type { InputRef, TableColumnsType, TableColumnType } from 'antd';
import { Button, Input, Space, Table, message, Spin} from 'antd';
import type { FilterDropdownProps } from 'antd/es/table/interface';
import Highlighter from 'react-highlight-words';
import type  { EmployeeDataType } from '../types';
import {fetchEmployees} from "../services/api";
import dayjs from 'dayjs';
import EmployeeActions from '../components/EmployeePageActions';
import { useNavigate } from 'react-router-dom';

type DataIndex = keyof EmployeeDataType;

const mockEmployees: EmployeeDataType[] = [
  {
    uuid: '1',
    name: 'John Doe',
    email: '<EMAIL>',
    is_active: true,
    expires_at: '2024-12-31T23:59:59Z',

  },
  {
    uuid: '2',
    name: '<NAME>',
    email: '<EMAIL>',
    is_active: false,
    expires_at: '2024-12-31T23:59:59Z',
  },
];

const EmployeesPage: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');
  const [employees, setEmployees] = useState<EmployeeDataType[]>([]);
  const [loading, setLoading] = useState(true);
  const searchInput = useRef<InputRef>(null);
  const navigate = useNavigate();


  // ---------Fething Employees List on Component Mount---------
  useEffect(() => {
  const token = localStorage.getItem('access_token'); // Get token from storage
  
  if (!token) {
    message.error('No authentication token found');
    setLoading(false);
    return;
  }

  fetchEmployees(token)
    .then(data => {
      setEmployees(data);
      setLoading(false);
    })
    .catch(error => {
      console.error('Error fetching employees:', error);
      message.error('Failed to load employees');
      setLoading(false);
    });
}, []);

  const handleEdit = (record: EmployeeDataType) => {
    navigate(`/edit-employee/${record.uuid}`, { state: { employee: record } });
  };

  const handleSearch = (
    selectedKeys: string[],
    confirm: FilterDropdownProps['confirm'],
    dataIndex: DataIndex,
  ) => {
    confirm();
    setSearchText(selectedKeys[0]);
    setSearchedColumn(dataIndex);
  };

  const handleReset = (clearFilters: () => void) => {
    clearFilters();
    setSearchText('');
  };

  const getColumnSearchProps = (dataIndex: DataIndex): TableColumnType<EmployeeDataType> => ({
    filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters, close }) => (
      <div style={{ padding: 8 }} onKeyDown={(e) => e.stopPropagation()}>
        <Input
          ref={searchInput}
          placeholder={`Search ${dataIndex}`}
          value={selectedKeys[0]}
          onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
          onPressEnter={() => handleSearch(selectedKeys as string[], confirm, dataIndex)}
          style={{ marginBottom: 8, display: 'block' }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys as string[], confirm, dataIndex)}
            icon={<SearchOutlined />}
            size="small"
            style={{ width: 90 }}
          >
            Search
          </Button>
          <Button
            onClick={() => clearFilters && handleReset(clearFilters)}
            size="small"
            style={{ width: 90 }}
          >
            Reset
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              confirm({ closeDropdown: false });
              setSearchText((selectedKeys as string[])[0]);
              setSearchedColumn(dataIndex);
            }}
          >
            Filter
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              close();
            }}
          >
            close
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <SearchOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
    ),
    onFilter: (value, record) =>
      record[dataIndex]
        .toString()
        .toLowerCase()
        .includes((value as string).toLowerCase()),
    filterDropdownProps: {
      onOpenChange(open) {
        if (open) {
          setTimeout(() => searchInput.current?.select(), 100);
        }
      },
    },
    render: (text) =>
      searchedColumn === dataIndex ? (
        <Highlighter
          highlightStyle={{ backgroundColor: '#ffc069', padding: 0 }}
          searchWords={[searchText]}
          autoEscape
          textToHighlight={text ? text.toString() : ''}
        />
      ) : (
        text
      ),
  });

  const columns: TableColumnsType<EmployeeDataType> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: '25%',
      ...getColumnSearchProps('name'),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: '25%',
      ...getColumnSearchProps('email'),
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: '5%',
      ...getColumnSearchProps('is_active'),
      render: (text: string) => text === 'true' ? 'Yes' : 'No',
    },
    {
      title: 'Expiration Date',
      dataIndex: 'expires_at',
      key: 'expires_at',
      width: '15%',
      ...getColumnSearchProps('expires_at'),
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : 'N/A',
      sorter: (a: EmployeeDataType, b: EmployeeDataType) => {
        if (!a.expires_at || !b.expires_at) return 0;
        return new Date(a.expires_at).getTime() - new Date(b.expires_at).getTime();
      },
      sortDirections: ['descend', 'ascend'],
    },
    {
    title: 'Action',
    key: 'action',
    width: '30%',
    render: (_: any, record: EmployeeDataType) => (
      <EmployeeActions
        record={record}
        onEdit={handleEdit}
        onDeleteSuccess={() => {
          // Refresh list
          // fetchEmployeesList();
        }}
      />
    ),
  },

  ];

  return( 
    <Spin spinning={loading}>
      <Table<EmployeeDataType> columns={columns} dataSource={mockEmployees} />
    </Spin>
  );
};

export default EmployeesPage;
