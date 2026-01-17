import React from 'react';
import { Navigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import {message} from "antd";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const token = Cookies.get('accessToken');

  if (!token) {
    // No token found, redirect to login
    return <Navigate to="/login" replace />;
    message.error("Session expired. Please log in again.");
  }

  // Token exists, render the protected component
  return <>{children}</>;
};

export default ProtectedRoute;
