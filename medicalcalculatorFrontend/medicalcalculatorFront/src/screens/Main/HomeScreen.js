import React from 'react';
import { View, Text, Button, Alert } from 'react-native';
import { useAuth } from '../../context/AuthContext';

const HomeScreen = () => {
  const { user, logout } = useAuth();

  const getUserRole = () => {
    if (user?.is_superuser) return 'Администратор';
    if (user?.is_medical) return 'Медперсонал';
    return 'Обычный пользователь';
  };

  const handleLogout = () => {
    Alert.alert(
      'Выход',
      'Вы уверены, что хотите выйти?',
      [
        { text: 'Отмена', style: 'cancel' },
        { text: 'Выйти', onPress: logout },
      ]
    );
  };

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text>Главная страница</Text>
      
      <View style={{ marginTop: 20 }}>
        <Text>Добро пожаловать, {user?.username || 'Пользователь'}!</Text>
        <Text>Email: {user?.email}</Text>
        <Text>Полное имя: {user?.full_name || 'Не указано'}</Text>
        <Text>Роль: {getUserRole()}</Text>
        <Text>Статус: {user?.is_active ? 'Активен' : 'Неактивен'}</Text>
        <Text>Дата регистрации: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Неизвестно'}</Text>
      </View>
      
      <View style={{ marginTop: 40 }}>
        <Button title="Выйти из системы" onPress={handleLogout} />
      </View>
    </View>
  );
};

export default HomeScreen;