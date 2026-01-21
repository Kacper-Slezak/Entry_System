import React, { useRef, useState, useEffect } from 'react';
import { SearchOutlined } from '@ant-design/icons';
import type { InputRef, TableColumnsType, TableColumnType } from 'antd';
import { Button, Input, Space, Table, message, Spin} from 'antd';
import type { FilterDropdownProps } from 'antd/es/table/interface';
import Highlighter from 'react-highlight-words';
import type  { EmployeeDataType } from '../types';
import {fetchEmployees,updateEmployeeStatus} from "../services/api";
import dayjs from 'dayjs';
import EmployeeActions from '../components/EmployeePageActions';
import { data, useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';


type DataIndex = keyof EmployeeDataType;


const EmployeesPage: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');
  const [employees, setEmployees] = useState<EmployeeDataType[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const searchInput = useRef<InputRef>(null);
  const navigate = useNavigate();




  // ---------Fething Employees List on Component Mount---------
  useEffect(() => {
    const getData = async () => {
    try {
      const token = Cookies.get('access_token');
      if (!token) {
        message.error('No authentication token found');
        return;
      }
      const data = await fetchEmployees(token);
      setEmployees(data);
      console.log(data); 
    } catch (error) {
      console.error("Failed to fetch employees:", error);
    } finally {
      setLoading(false);
      
    }
  }
    getData();

    
  }, [refreshKey]);

  const handleEdit = (record: EmployeeDataType) => {
    navigate(`/edit-employee/${record.uuid}`, { state: { employee: record } });
  };
  const handleAccess = (record: EmployeeDataType) => {
    const updateStatus = async (status: boolean) => {
      try {
        const token = Cookies.get('access_token');
        if (!token) {
          message.error('No authentication token found');
          return;
        }
        await updateEmployeeStatus(record.uuid, status, token);
        message.success('Employee access granted');
        setRefreshKey((prev) => prev + 1);
      } catch (error) {
        console.error('Error updating employee status:', error);
        message.error('Failed to update employee status');
      }
    };
    
    if (record.is_active===true) {
      updateStatus(false);
    }else{
      updateStatus(true);
    }
  }

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
      render: (is_active: boolean) => is_active ? 'Yes' : 'No',
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
    width: '15%',
    render: (_: any, record: EmployeeDataType) => (
      <EmployeeActions
        record={record}
        onEdit={handleEdit}
        onAccess={handleAccess}
        onDeleteSuccess={() => setRefreshKey((prev) => prev + 1)}
      />
    ),
  },

  ];

  return(
    <Spin spinning={loading}>
      <Table<EmployeeDataType> columns={columns} dataSource={employees} />
    </Spin>
  );
};

export default EmployeesPage;
