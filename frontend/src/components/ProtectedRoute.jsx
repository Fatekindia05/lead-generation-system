import React from 'react';
import { Navigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const ProtectedRoute = ({ children }) => {
  const isAuthenticated = localStorage.getItem('auth_token') !== null;
  
  if (!isAuthenticated) {
    toast.error('Please login to access the dashboard');
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

export default ProtectedRoute;