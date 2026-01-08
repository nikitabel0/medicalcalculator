import React, { useState, useEffect } from 'react';
import { View, Text, Button, FlatList, Alert } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

const AdminScreen = () => {
  const { user, token } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.is_superuser) {
      fetchUsers();
    }
  }, []);

  const fetchUsers = async () => {
    try {
      // Здесь будет запрос к API для получения списка пользователей
      // const response = await api.get('/admin/users', {
      //   headers: { Authorization: `Bearer ${token}` }
      // });
      // setUsers(response.data);
      
      // Заглушка
      setUsers([
        { id: 1, username: 'admin', email: 'admin@example.com', is_superuser: true },
        { id: 2, username: 'user1', email: 'user1@example.com', is_superuser: false },
      ]);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось загрузить пользователей');
    } finally {
      setLoading(false);
    }
  };

  if (!user?.is_superuser) {
    return (
      <View style={{ flex: 1, padding: 20 }}>
        <Text>Доступ запрещен. Только для администраторов.</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text>Панель администратора</Text>
      
      <Text>Список пользователей:</Text>
      
      {loading ? (
        <Text>Загрузка...</Text>
      ) : (
        <FlatList
          data={users}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <View style={{ padding: 10, borderBottomWidth: 1 }}>
              <Text>Имя: {item.username}</Text>
              <Text>Email: {item.email}</Text>
              <Text>Админ: {item.is_superuser ? 'Да' : 'Нет'}</Text>
            </View>
          )}
        />
      )}

      <Button title="Обновить список" onPress={fetchUsers} />
    </View>
  );
};

export default AdminScreen;