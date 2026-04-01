import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Configure axios interceptor for auth header
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function formatApiErrorDetail(detail) {
  if (detail == null) return "Une erreur est survenue. Veuillez réessayer.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = checking, false = not auth, object = auth
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setUser(false);
      setLoading(false);
      return;
    }
    
    try {
      const { data } = await axios.get(`${API}/auth/me`);
      setUser(data);
    } catch (e) {
      // Token invalid, clear storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const { data } = await axios.post(`${API}/auth/login`, { email, password });
    // Store tokens in localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setUser({
      id: data.id,
      email: data.email,
      name: data.name,
      role: data.role
    });
    return data;
  };

  const register = async (email, password, name, role = 'commercial') => {
    const { data } = await axios.post(`${API}/auth/register`, { email, password, name, role });
    // Store tokens in localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setUser({
      id: data.id,
      email: data.email,
      name: data.name,
      role: data.role
    });
    return data;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (e) {
      console.error('Logout error:', e);
    }
    // Clear localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
