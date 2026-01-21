import React, { useState, useEffect } from 'react';
import { Card, message, Spin } from 'antd';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import type { FormValues, EmployeeDataType } from '../types';
import { updateEmployee } from '../services/api';
import EmployeeForm from '../components/EmployeeForm';
import styles from '../styles/AddEmployee.module.css';
import Cookies from 'js-cookie';
import dayjs from 'dayjs';

const EditEmployee: React.FC = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [employee, setEmployee] = useState<EmployeeDataType | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Get employee from navigation state first
    const passedEmployee = (location.state as any)?.employee;

    if (passedEmployee) {
      setEmployee(passedEmployee);
      setLoading(false);
    } [uuid, navigate, location]});


  const handleFormSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      const token = Cookies.get('access_token');

      if (!token || !uuid) {
        message.error('Missing required token or employee ID');
        return;
      }

      const formData = new FormData();
      if (values.name) formData.append('name', values.name);
      if (values.email) formData.append('email', values.email);
      if (values.expirationTime) formData.append('expiration_date', values.expirationTime.toISOString());

      if (values.photo && values.photo.length > 0) {
        const file = (values.photo[0] as any).originFileObj;
        if (file) {
          formData.append('photo', file);
        }
      }

      await updateEmployee(uuid, formData, token);
      message.success('Employee updated successfully');
      navigate('/employees');

    } catch (error) {
      console.error('Error:', error);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };


  if (loading) return <Spin />;

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <h1 className={styles.title}>Edit Employee</h1>
        {employee && (
          <EmployeeForm
            initialData={employee}
            onFinish={handleFormSubmit}
            isLoading={isSubmitting}
            submitButtonText="Submit"
            formRules={{ expirationTime: [{
                  validator: (_: any, value: dayjs.Dayjs | null) => {
                    if (!value) {
                      return Promise.resolve();
                    }
                    if (value.isAfter(dayjs())) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('Date must be later than right now!'));
                  }
                }] }}
          />
        )}
      </Card>
    </div>
  );
};

export default EditEmployee;
