import React from 'react';
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
} from 'antd';
// import {props} from '../components/UploadComponent';
import { UploadOutlined } from '@ant-design/icons';
import { Upload } from 'antd';
import type { UploadFile } from 'antd/es/upload/interface';
import styles from '../styles/AddEmployee.module.css';
import { Dayjs } from 'dayjs';

const formItemLayout = {
  labelCol: {
    xs: { span: 24},
    sm: { span: 10 },
  },
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 8 },
  },
};

const AddEmployee: React.FC = () => {
    const [form] = Form.useForm<FormValues>();

    interface FormValues {
        name: string;
        email: string;
        expirationTime: Dayjs;
        photo: UploadFile[];
    }

    const onFinish = async (values: FormValues) => {
        const formData=new FormData();
        formData.append('name',values.name);
        formData.append('email',values.email);
        formData.append('expirationTime',values.expirationTime.toISOString());

        values.photo?.forEach((fileItem: any) => {
            formData.append('photo', fileItem.originFileObj);
        });

        try {
            const response = await fetch('/admin/create-employee', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(values),
            });
            if (response.ok) {
            console.log('Success:', await response.json());
            form.resetFields(); // Optional: reset form after success
            }
        } catch (error) {
            console.error('Error:', error);
        }
    };

    
    return (
        <div className={styles.container}>
        <Card className={styles.card} >
            <h1 className={styles.title}>Add Employee Form</h1>
            <Form
            {...formItemLayout}
            form={form}
            variant={'outlined'}
            className={styles.form}
            initialValues={{ variant: 'outlined' }}
            onFinish={onFinish}
            >
                <Form.Item label="Name and Surname" name="name" rules={[{ required: true, message: 'Please input!' }]}>
                <Input />
                </Form.Item>

                <Form.Item label="Email" name="email" rules={[{ required: true, message: 'Please input!', type: 'email' }]}>
                <Input />
                </Form.Item>

                <Form.Item label="Expiration Time" name="expirationTime" rules={[{ required: true, message: 'Please input!' }]}>
                    <DatePicker showTime />
                </Form.Item>

                <Form.Item name="photo"
                    label="Upload File"
                    valuePropName="fileList"
                    getValueFromEvent={(e) => {
                        if (Array.isArray(e)) return e;
                        return e?.fileList ?? [];
                    }}
                    rules={[{ required: true, message: 'Please upload a file' }]}>
                    <Upload beforeUpload={() => false}
                        maxCount={1}
                        listType="picture">
                        <Button icon={<UploadOutlined />}>Click to Upload</Button>
                    </Upload>
                </Form.Item>

                <Form.Item label={null}>
                <Button type="primary" htmlType="submit" className={styles.submitButton}>
                    Submit
                </Button>
                </Form.Item>
                
            </Form>
        </Card>
        </div>
        )
};

export default AddEmployee;
