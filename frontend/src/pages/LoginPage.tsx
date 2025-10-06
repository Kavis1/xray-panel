import { useState, useEffect } from 'react';
import { Container, Paper, TextInput, PasswordInput, Button, Title, Stack } from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import { notifications } from '@mantine/notifications';
import { useAuthStore } from '@/stores/authStore';
import { handleApiError } from '@/utils/errorFormatter';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(username, password);
      notifications.show({
        title: 'Success',
        message: 'Logged in successfully',
        color: 'green',
      });
      navigate('/');
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Login failed'),
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size={420} my={100}>
      <Title ta="center">Xray Control Panel</Title>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={handleSubmit}>
          <Stack>
            <TextInput
              label="Username"
              placeholder="admin"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />

            <PasswordInput
              label="Password"
              placeholder="Your password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <Button type="submit" fullWidth loading={loading}>
              Sign in
            </Button>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}
