import { AppShell, NavLink, Group, Text, Code, Burger } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  IconDashboard,
  IconUsers,
  IconServer,
  IconNetwork,
  IconSettings,
  IconLogout,
} from '@tabler/icons-react';
import { useAuthStore } from '@/stores/authStore';

export default function Layout() {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, admin } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: IconDashboard },
    { path: '/users', label: 'Users', icon: IconUsers },
    { path: '/nodes', label: 'Nodes', icon: IconServer },
    { path: '/inbounds', label: 'Inbounds', icon: IconNetwork },
    { path: '/settings', label: 'Settings', icon: IconSettings },
  ];

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 250, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Text size="xl" fw={700}>Xray Panel</Text>
          </Group>
          <Group>
            <Code>{admin?.username}</Code>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            label={item.label}
            leftSection={<item.icon size={20} />}
            active={location.pathname === item.path}
            onClick={() => navigate(item.path)}
          />
        ))}
        
        <NavLink
          label="Logout"
          leftSection={<IconLogout size={20} />}
          onClick={handleLogout}
          style={{ marginTop: 'auto' }}
          color="red"
        />
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
