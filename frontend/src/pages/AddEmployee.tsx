import React from 'react';
import { Card, message } from 'antd';
import type { FormValues } from '../types';
import { createEmployee } from '../services/api';
import EmployeeForm from '../components/EmployeeForm';
import styles from '../styles/AddEmployee.module.css';
import Cookies from 'js-cookie';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

const AddEmployee: React.FC = () => {
  const [isLoading, setIsLoading] = React.useState(false);
  const navigate = useNavigate();

  const handleFormSubmit = async (values: FormValues) => {
    setIsLoading(true);
    try {
      const token = Cookies.get('access_token');

      if (!token) {
        message.error('No authentication token found');
        return;
      }

      const formData = new FormData();
      formData.append('name', values.name);
      formData.append('email', values.email);
      formData.append('expiration_date', dayjs(values.expirationTime).format('YYYY-MM-DD HH:mm:ss'));

      values.photo?.forEach((fileItem: any) => {
        formData.append('photo', fileItem.originFileObj);
      });

      await createEmployee(formData, token);
      message.success('Employee added successfully');
      navigate('/employees');
    } catch (error) {
      console.error('Error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <h1 className={styles.title}>Add Employee Form</h1>
        <EmployeeForm
          onFinish={handleFormSubmit}
          isLoading={isLoading}
          formRules={employeeFormRules}
        />
      </Card>
    </div>
  );
};

const employeeFormRules = {
  name: [
    { required: true, message: 'Please input name!' },
    { min: 2, message: 'Name must be at least 2 characters!' },
  ],
  email: [
    { required: true, message: 'Please input email!' },
    { type: 'email', message: 'Please enter a valid email!' },
  ],
  expirationTime: [
    { required: true, message: 'Please select expiration time!' },
  ],
  photo: [
    { required: true, message: 'Please upload a photo!' },
  ],
};

export default AddEmployee;
