import React from 'react';
import { useAuth } from '../context/AuthContext';
import AuthNavigator from './AuthNavigator';
import MainNavigator from './MainNavigator';

const AppNavigator = () => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <MainNavigator /> : <AuthNavigator />;
};

export default AppNavigator;