import message from 'antd/es/message';
import type { EmployeeDataType } from '../types';
import Cookies from 'js-cookie';

const API_BASE_URL = 'http://localhost:8000'; // or your backend URL

export const fetchEmployees = async (token: string): Promise<EmployeeDataType[]> => {
  const response = await fetch(`${API_BASE_URL}/admin/employees`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch employees');
  }

  return response.json();
};

export const createEmployee = async (
  formData: FormData,
  token: string
): Promise<{ message: string }> => {
  const response = await fetch(`${API_BASE_URL}/admin/create_employee`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to create employee');
  }

  return response.json();
};

export const deleteEmployee = async (
  uuid: string,
  token: string,
): Promise<{ message: string }> => {
  const response = await fetch(`${API_BASE_URL}/admin/employees/${uuid}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    });

  if (!response.ok) {
    throw new Error('Failed to delete employee');
  }

  return response.json();
};

export const updateEmployee = async (
  uuid: string,
  formData: FormData,
  token: string,
): Promise<{ message: string }> => {
  const response = await fetch(`${API_BASE_URL}/admin/employees/${uuid}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });
    if (!response.ok) {
    throw new Error('Failed to update employee');
    }
    return response.json();
};

export const fetchEmployeesList = async () => {
  const token = Cookies.get('access_token');

  if (!token) {
    message.error('No authentication token found');
    return [];
  }

  try {
    const data = await fetchEmployees(token);

    return data;
  } catch (error) {
    console.error('Error fetching employees:', error);
    message.error('Failed to load employees');
    return [];
  }
};
