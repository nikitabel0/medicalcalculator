import React, { useState } from 'react';
import { View, Text, TextInput, Button, Alert, ScrollView } from 'react-native';
import { useAuth } from '../../context/AuthContext';

const RegisterScreen = ({ navigation }) => {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);

const handleRegister = async () => {
  if (!formData.email || !formData.username || !formData.password) {
    Alert.alert('Ошибка', 'Заполните обязательные поля');
    return;
  }

  if (formData.password !== formData.confirmPassword) {
    Alert.alert('Ошибка', 'Пароли не совпадают');
    return;
  }

  if (formData.password.length < 6) {
    Alert.alert('Ошибка', 'Пароль должен быть не менее 6 символов');
    return;
  }

  const userData = {
    email: formData.email.trim(),
    username: formData.username.trim(),
    full_name: formData.full_name.trim() || null,
    password: formData.password
  };
  
  console.log('Отправляемые данные:', userData);
  
  setLoading(true);
  const result = await register(userData);
  setLoading(false);
  
  if (result.success) {
    Alert.alert('Успешно', 'Регистрация прошла успешно!');
    navigation.navigate('Login');
  } else {
    console.log('Полная ошибка:', result.error);
    Alert.alert('Ошибка', result.error);
  }
};

  return (
    <ScrollView style={{ flex: 1, padding: 20 }}>
      <Text>Регистрация</Text>
      
      <Text>Email:</Text>
      <TextInput
        value={formData.email}
        onChangeText={(text) => setFormData({ ...formData, email: text })}
        placeholder="example@mail.com"
        style={{ borderWidth: 1, padding: 10, marginBottom: 10 }}
        autoCapitalize="none"
      />
      
      <Text>Имя пользователя:</Text>
      <TextInput
        value={formData.username}
        onChangeText={(text) => setFormData({ ...formData, username: text })}
        placeholder="username"
        style={{ borderWidth: 1, padding: 10, marginBottom: 10 }}
        autoCapitalize="none"
      />
      
      <Text>Полное имя (необязательно):</Text>
      <TextInput
        value={formData.full_name}
        onChangeText={(text) => setFormData({ ...formData, full_name: text })}
        placeholder="Иван Иванов"
        style={{ borderWidth: 1, padding: 10, marginBottom: 10 }}
      />
      
      <Text>Пароль:</Text>
      <TextInput
        value={formData.password}
        onChangeText={(text) => setFormData({ ...formData, password: text })}
        secureTextEntry
        placeholder="Пароль"
        style={{ borderWidth: 1, padding: 10, marginBottom: 10 }}
      />
      
      <Text>Подтвердите пароль:</Text>
      <TextInput
        value={formData.confirmPassword}
        onChangeText={(text) => setFormData({ ...formData, confirmPassword: text })}
        secureTextEntry
        placeholder="Подтвердите пароль"
        style={{ borderWidth: 1, padding: 10, marginBottom: 20 }}
      />
      
      <Button
        title={loading ? "Регистрация..." : "Зарегистрироваться"}
        onPress={handleRegister}
        disabled={loading}
      />
      
      <View style={{ marginTop: 20 }}>
        <Button
          title="Уже есть аккаунт? Войти"
          onPress={() => navigation.navigate('Login')}
        />
      </View>
    </ScrollView>
  );
};

export default RegisterScreen;