import { useState } from 'react';
import {
  Text,
  Button,
  TextInput,
  Switch,
  Group,
  Stack,
  Paper,
  Title,
  Divider,
  PasswordInput,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';

export default function SettingsPage() {
  const [loading, setLoading] = useState(false);

  const profileForm = useForm({
    initialValues: {
      username: 'admin',
      email: '',
      telegram_id: '',
    },
  });

  const passwordForm = useForm({
    initialValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
    validate: {
      new_password: (value) => (value.length < 8 ? 'Password must be at least 8 characters' : null),
      confirm_password: (value, values) =>
        value !== values.new_password ? 'Passwords do not match' : null,
    },
  });

  const systemForm = useForm({
    initialValues: {
      panel_name: 'Xray Management Panel',
      subscription_url: 'https://jdsshrerwwte.dmevent.de/sub',
      username_tag: '@mybot',
      session_timeout: 3600,
      enable_registration: false,
      enable_telegram_bot: false,
      telegram_bot_token: '',
    },
  });

  const handleProfileUpdate = async (_values: any) => {
    try {
      setLoading(true);
      notifications.show({
        title: 'Success',
        message: 'Profile updated successfully',
        color: 'green',
      });
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to update profile',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (_values: any) => {
    try {
      setLoading(true);
      notifications.show({
        title: 'Success',
        message: 'Password changed successfully',
        color: 'green',
      });
      passwordForm.reset();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to change password',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSystemUpdate = async (_values: any) => {
    try {
      setLoading(true);
      notifications.show({
        title: 'Success',
        message: 'System settings updated successfully',
        color: 'green',
      });
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to update settings',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Text size="xl" fw={700} mb="md">Panel Settings</Text>

      {/* Profile Settings */}
      <Paper shadow="xs" p="md" mb="md">
        <Title order={3} mb="md">Profile Settings</Title>
        <form onSubmit={profileForm.onSubmit(handleProfileUpdate)}>
          <Stack gap="md">
            <TextInput
              label="Username"
              placeholder="Enter username"
              required
              {...profileForm.getInputProps('username')}
            />
            <TextInput
              label="Email"
              placeholder="Enter email"
              type="email"
              {...profileForm.getInputProps('email')}
            />
            <TextInput
              label="Telegram ID"
              placeholder="Enter Telegram ID"
              {...profileForm.getInputProps('telegram_id')}
            />
            <Group justify="flex-end">
              <Button type="submit" loading={loading}>
                Save Profile
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>

      {/* Password Change */}
      <Paper shadow="xs" p="md" mb="md">
        <Title order={3} mb="md">Change Password</Title>
        <form onSubmit={passwordForm.onSubmit(handlePasswordChange)}>
          <Stack gap="md">
            <PasswordInput
              label="Current Password"
              placeholder="Enter current password"
              required
              {...passwordForm.getInputProps('current_password')}
            />
            <PasswordInput
              label="New Password"
              placeholder="Enter new password"
              required
              {...passwordForm.getInputProps('new_password')}
            />
            <PasswordInput
              label="Confirm Password"
              placeholder="Confirm new password"
              required
              {...passwordForm.getInputProps('confirm_password')}
            />
            <Group justify="flex-end">
              <Button type="submit" loading={loading}>
                Change Password
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>

      {/* System Settings */}
      <Paper shadow="xs" p="md" mb="md">
        <Title order={3} mb="md">System Settings</Title>
        <form onSubmit={systemForm.onSubmit(handleSystemUpdate)}>
          <Stack gap="md">
            <TextInput
              label="Panel Name"
              placeholder="Panel name"
              required
              {...systemForm.getInputProps('panel_name')}
            />
            <TextInput
              label="Subscription URL"
              placeholder="https://example.com/sub"
              required
              {...systemForm.getInputProps('subscription_url')}
            />
            <TextInput
              label="Username Tag"
              description="Tag to append to all VPN connection names (e.g., @mybot, | MyVPN)"
              placeholder="@mybot"
              {...systemForm.getInputProps('username_tag')}
            />
            <TextInput
              label="Session Timeout (seconds)"
              placeholder="3600"
              type="number"
              {...systemForm.getInputProps('session_timeout')}
            />
            
            <Divider my="sm" />
            
            <Switch
              label="Enable User Registration"
              description="Allow users to self-register"
              {...systemForm.getInputProps('enable_registration', { type: 'checkbox' })}
            />
            
            <Divider my="sm" />
            
            <Switch
              label="Enable Telegram Bot"
              description="Enable Telegram bot notifications"
              {...systemForm.getInputProps('enable_telegram_bot', { type: 'checkbox' })}
            />
            
            {systemForm.values.enable_telegram_bot && (
              <TextInput
                label="Telegram Bot Token"
                placeholder="Enter bot token"
                {...systemForm.getInputProps('telegram_bot_token')}
              />
            )}
            
            <Group justify="flex-end">
              <Button type="submit" loading={loading}>
                Save Settings
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>

      {/* API Information */}
      <Paper shadow="xs" p="md">
        <Title order={3} mb="md">API Information</Title>
        <Stack gap="sm">
          <Group>
            <Text fw={600}>API Base URL:</Text>
            <Text c="dimmed">https://jdsshrerwwte.dmevent.de/api/v1</Text>
          </Group>
          <Group>
            <Text fw={600}>Subscription URL:</Text>
            <Text c="dimmed">https://jdsshrerwwte.dmevent.de/sub</Text>
          </Group>
          <Group>
            <Text fw={600}>WebSocket URL:</Text>
            <Text c="dimmed">wss://jdsshrerwwte.dmevent.de/ws</Text>
          </Group>
        </Stack>
      </Paper>
    </div>
  );
}
