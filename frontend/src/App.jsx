import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';
import MainLayout from './components/MainLayout';
import Dashboard from './pages/Dashboard';
import UserManagement from './pages/UserManagement';
import AccessLogs from './pages/AccessLogs';
import DeviceManagement from './pages/DeviceManagement';
import LoginPage from './pages/LoginPage';
import NotFound from './pages/NotFound';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="users" element={<UserManagement />} />
              <Route path="devices" element={<DeviceManagement />} />
              <Route path="logs" element={<AccessLogs />} />
              
              <Route path="*" element={<NotFound />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;