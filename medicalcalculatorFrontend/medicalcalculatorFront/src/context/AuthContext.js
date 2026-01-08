import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStoredToken();
  }, []);

  const loadStoredToken = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('@auth_token');
      if (storedToken) {
        setToken(storedToken);
        const userInfo = await getCurrentUser(storedToken);
        if (userInfo) {
          setUser(userInfo);
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки токена:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getCurrentUser = async (userToken) => {
    try {
      const response = await api.get('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${userToken}`,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка получения пользователя:', error);
      return null;
    }
  };

  const login = async (username, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;
      await AsyncStorage.setItem('@auth_token', access_token);
      setToken(access_token);
      const userInfo = await getCurrentUser(access_token);
      if (userInfo) {
        setUser(userInfo);
      }
      return { success: true };
    } catch (error) {
      console.error('Ошибка входа:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Неверное имя пользователя или пароль' 
      };
    }
  };

const register = async (userData) => {
  try {
    // Убедимся, что full_name отправляется как строка или null
    const dataToSend = {
      email: userData.email,
      username: userData.username,
      full_name: userData.full_name || null,
      password: userData.password
    };
    
    console.log('Отправляемые данные регистрации:', dataToSend);
    
    const response = await api.post('/api/auth/register', dataToSend, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Ошибка регистрации:', error);
    console.error('Детали ошибки:', error.response?.data);
    
    let errorMessage = 'Ошибка при регистрации. Проверьте данные.';
    
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error.response?.data?.password) {
      errorMessage = error.response.data.password[0];
    }
    
    return { 
      success: false, 
      error: errorMessage 
    };
  }
};
  const logout = async () => {
    try {
      await AsyncStorage.removeItem('@auth_token');
      setToken(null);
      setUser(null);
    } catch (error) {
      console.error('Ошибка выхода:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
        isAuthenticated: !!token,
        isAdmin: user?.is_superuser || false,
        isMedical: user?.is_medical || false,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};