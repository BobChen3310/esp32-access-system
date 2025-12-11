import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

export const AuthContext = createContext(null);

// 設定閒置逾時 (15分鐘)
const IDLE_TIMEOUT = 15 * 60 * 1000; 

const parseJwt = (token) => {
  try {
    if (!token) return null;
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      window.atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  // 初始化：直接讀取 localStorage
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);
  
  const [user, setUser] = useState(() => {
    if (token) {
      const decoded = parseJwt(token);
      return decoded?.sub || null;
    }
    return null;
  });

  // 監聽 Token 變化
  useEffect(() => {
    if (token) {
      setIsAuthenticated(true);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      const decoded = parseJwt(token);
      if (decoded && decoded.sub) {
        setUser(decoded.sub);
      }
    } else {
      setIsAuthenticated(false);
      setUser(null);
      delete apiClient.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    
    const newToken = response.data.access_token;
    localStorage.setItem('access_token', newToken);
    setToken(newToken);
    return true;
  };

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  // 閒置逾時偵測
  useEffect(() => {
    let timeoutId;
    
    const resetTimer = () => {
      if (timeoutId) clearTimeout(timeoutId);
      if (isAuthenticated) {
        timeoutId = setTimeout(() => {
          console.log("閒置逾時，自動登出");
          logout();
        }, IDLE_TIMEOUT);
      }
    };

    if (isAuthenticated) {
      const events = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'];
      
      events.forEach(event => {
        window.addEventListener(event, resetTimer);
      });
      
      resetTimer();

      return () => {
        if (timeoutId) clearTimeout(timeoutId);
        events.forEach(event => {
          window.removeEventListener(event, resetTimer);
        });
      };
    }
  }, [isAuthenticated, logout]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);