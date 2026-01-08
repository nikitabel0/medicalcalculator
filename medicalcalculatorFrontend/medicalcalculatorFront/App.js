import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { View, ActivityIndicator } from 'react-native';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import AppNavigator from './src/navigation/AppNavigator';

const AppContent = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return <AppNavigator />;
};

export default function App() {
  return (
    <AuthProvider>
      <NavigationContainer>
        <AppContent />
      </NavigationContainer>
    </AuthProvider>
  );
}