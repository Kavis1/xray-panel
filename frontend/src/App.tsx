import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';

import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';

import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import UsersPage from '@/pages/UsersPage';
import NodesPage from '@/pages/NodesPage';
import InboundsPage from '@/pages/InboundsPage';
import SettingsPage from '@/pages/SettingsPage';
import Layout from '@/components/Layout';

function App() {
  const { fetchMe, isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <MantineProvider defaultColorScheme="dark">
      <Notifications position="top-right" />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          {isAuthenticated ? (
            <Route path="/" element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="nodes" element={<NodesPage />} />
              <Route path="inbounds" element={<InboundsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          ) : (
            <Route path="*" element={<Navigate to="/login" replace />} />
          )}
        </Routes>
      </BrowserRouter>
    </MantineProvider>
  );
}

export default App;
