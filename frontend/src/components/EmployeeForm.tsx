import React, { useEffect } from 'react';
import {
  Button,
  DatePicker,
  Form,
  Input,
  Upload,
  message,
} from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { FormValues, EmployeeDataType } from '../types';
import styles from '../styles/AddEmployee.module.css';



interface EmployeeFormProps {
  initialData?: EmployeeDataType;
  onFinish: (values: FormValues) => Promise<void>;
  isLoading?: boolean;
  submitButtonText?: string;
  formRules?: {
    name?: any[];
    email?: any[];
    expirationTime?: any[];
    photo?: any[];
  };
}

const formItemLayout = {
  labelCol: {
    xs: { span: 24 },
    sm: { span: 10 },
  },
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 8 },
  },
};

const EmployeeForm: React.FC<EmployeeFormProps> = ({
  initialData,
  onFinish,
  isLoading = false,
  submitButtonText = 'Submit',
  formRules = {
    name: [{ required: false}],
    email: [{ required: false}],
    expirationTime: [{ required: false}],
    photo: [{ required: false}],
  },
}) => {
  const [form] = Form.useForm<FormValues>();

  // Populate form with initial data if editing
  useEffect(() => {
    if (initialData) {
      form.setFieldsValue({
        name: initialData.name,
        email: initialData.email,
      });
    }
  }, [initialData, form]);

  const handleFinish = async (values: FormValues) => {
    try {
      await onFinish(values);
      // Reset form only if creating new (no initial data)
      if (!initialData) {
        form.resetFields();
      }
    //   message.success('Operation completed successfully');
    } catch (error) {
      console.error('Error:', error);
      message.error('Failed to complete operation');
    }
  };

  return (
    <Form
      {...formItemLayout}
      form={form}
      variant="outlined"
      className={styles.form}
      onFinish={handleFinish}
    >
      <Form.Item
        label="Name and Surname"
        name="name"
        rules={formRules.name}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Email"
        name="email"
        rules={formRules.email}
      >
        <Input />
      </Form.Item>
      <Form.Item
        label="Expiration Date"
        name="expirationTime"
        rules={formRules.expirationTime}
      >
        <DatePicker showTime/>
      </Form.Item>
      <Form.Item
          name="photo"
          label="Upload Photo"
          valuePropName="fileList"
          getValueFromEvent={(e) => {
            if (Array.isArray(e)) return e;
            return e?.fileList ?? [];
          }}
          rules={formRules.photo}
        >
          <Upload beforeUpload={() => false} maxCount={1} listType="picture">
            <Button icon={<UploadOutlined />}>Click to Upload</Button>
          </Upload>
        </Form.Item>


      <Form.Item label={null}>
        <Button
          type="primary"
          htmlType="submit"
          className={styles.submitButton}
          loading={isLoading}
        >
          {submitButtonText}
        </Button>
      </Form.Item>
    </Form>
  );
};

export default EmployeeForm;
