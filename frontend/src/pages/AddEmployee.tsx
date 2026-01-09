import React from 'react';
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
} from 'antd';
import {props} from '../components/UploadComponent';
import { UploadOutlined } from '@ant-design/icons';
import {  Upload } from 'antd';

const formItemLayout = {
  labelCol: {
    xs: { span: 24 },
    sm: { span: 10 },
  },
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 14 },
  },
};

const AddEmployee: React.FC = () => {
  const [form] = Form.useForm();
  return (
    <Card style={{ margin: 'auto', padding: '20px', minWidth: 400 }} >
        <Form
        {...formItemLayout}
        form={form}
        variant={'outlined'}
        style={{ maxWidth: 600, justifyItems: 'center', padding:'20px' }}
        initialValues={{ variant: 'filled' }}
        >

            <Form.Item label="Name" name="Name" rules={[{ required: true, message: 'Please input!' }]}>
            <Input />
            </Form.Item>

            <Form.Item label="Surname" name="Surname" rules={[{ required: true, message: 'Please input!' }]}>
            <Input />
            </Form.Item>

            <Form.Item label="Expiration Time" name="DatePicker" rules={[{ required: true, message: 'Please input!' }]}>
                <DatePicker showTime />
            </Form.Item>

            <Form.Item label="Upload Photo" name="Upload" rules={[{required:true}]}>
                <Upload {...props}>
                    <Button icon={<UploadOutlined />}>Click to Upload</Button>
                </Upload>
            </Form.Item>

            <Form.Item label={null}>
            <Button type="primary" htmlType="submit">
                Submit
            </Button>
            </Form.Item>
        </Form>
    </Card>
    )
};

export default AddEmployee;
