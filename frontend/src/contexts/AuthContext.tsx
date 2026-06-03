import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import { api } from '../lib/api';
import { setAccessToken, setRefreshToken, getAccessToken } from '../lib/auth';
import { events } from '../lib/events';

interface User {
  id: string;
  email: string;
  name: string;
  onboarding_completed: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(getAccessToken());

  const fetchUser = useCallback(async (authToken: string) => {
    try {
      const response = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setUser(response.data);
    } catch {
      setUser(null);
      setAccessToken(null);
      setRefreshToken(null);
      setToken(null);
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      setLoading(true);
      const storedToken = getAccessToken();
      if (storedToken) {
        setToken(storedToken);
        await fetchUser(storedToken);
      }
      setLoading(false);
    };
    initAuth();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await api.post('/auth/login', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      const { access_token, refresh_token } = response.data;
      setToken(access_token);
      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      await fetchUser(access_token);
      
      events.emit('toast', {
        type: 'success',
        title: 'Login Successful',
        message: 'Welcome back! You have been successfully logged in.',
        duration: 3000,
      });
    } catch (error) {
      events.emit('toast', {
        type: 'error',
        title: 'Login Failed',
        message: 'Invalid email or password. Please try again.',
        duration: 5000,
      });
      throw error;
    }
  };

  const register = async (name: string, email: string, password: string) => {
    try {
      const response = await api.post('/auth/register', { name, email, password });
      const { access_token, refresh_token } = response.data;
      setToken(access_token);
      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      await fetchUser(access_token);
      
      events.emit('toast', {
        type: 'success',
        title: 'Registration Successful',
        message: 'Your account has been created. You are now logged in.',
        duration: 3000,
      });
    } catch (error) {
      events.emit('toast', {
        type: 'error',
        title: 'Registration Failed',
        message: 'An account with this email already exists. Please try again.',
        duration: 5000,
      });
      throw error;
    }
  };

  const logout = () => {
    events.emit('toast', {
      type: 'success',
      title: 'Logout Successful',
      message: 'You have been successfully logged out.',
      duration: 3000,
    });
    
    setUser(null);
    setToken(null);
    setAccessToken(null);
    setRefreshToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
