import { Dayjs } from 'dayjs';
import type { UploadFile } from 'antd/es/upload/interface';

export interface FormValues {
  name: string;
  email: string;
  expirationTime: Dayjs;
  photo: UploadFile[];
}


export interface EmployeeDataType {
  uuid: string;
  name: string;
  email: string;
  is_active: boolean;
  expires_at: string;
}