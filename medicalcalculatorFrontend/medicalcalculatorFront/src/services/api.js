import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавим обработчик для сериализации данных
api.interceptors.request.use(
  (config) => {
    // Для регистрации убедимся, что отправляем правильный формат
    if (config.data && config.data.password) {
      // Убедимся, что пароль - строка и обрезаем если больше 72 символов (на всякий случай)
      if (config.data.password.length > 72) {
        config.data.password = config.data.password.substring(0, 72);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 400) {
      console.log('Ошибка 400:', error.response.data);
    }
    if (error.response?.status === 401) {
      console.log('Ошибка авторизации, токен истек или неверный');
    }
    return Promise.reject(error);
  }
);

export default api;