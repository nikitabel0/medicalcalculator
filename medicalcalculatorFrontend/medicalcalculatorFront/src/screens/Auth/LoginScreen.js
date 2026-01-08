import React, { useState } from 'react';
import { View, Text, TextInput, Button, Alert } from 'react-native';
import { useAuth } from '../../context/AuthContext';

const LoginScreen = ({ navigation }) => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Ошибка', 'Введите имя пользователя и пароль');
      return;
    }

    setLoading(true);
    const result = await login(username, password);
    setLoading(false);

    if (!result.success) {
      Alert.alert('Ошибка', result.error);
    }
  };

  return (
    <View style={{ flex: 1, padding: 20, justifyContent: 'center' }}>
      <Text>Вход в систему</Text>
      
      <Text>Имя пользователя или email:</Text>
      <TextInput
        value={username}
        onChangeText={setUsername}
        placeholder="Введите email или имя пользователя"
        style={{ borderWidth: 1, padding: 10, marginBottom: 10 }}
        autoCapitalize="none"
      />
      
      <Text>Пароль:</Text>
      <TextInput
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        placeholder="Введите пароль"
        style={{ borderWidth: 1, padding: 10, marginBottom: 20 }}
      />
      
      <Button
        title={loading ? "Вход..." : "Войти"}
        onPress={handleLogin}
        disabled={loading}
      />
      
      <View style={{ marginTop: 20 }}>
        <Button
          title="Регистрация"
          onPress={() => navigation.navigate('Register')}
        />
      </View>
    </View>
  );
};

export default LoginScreen;