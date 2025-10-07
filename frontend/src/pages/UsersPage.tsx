import { useState, useEffect } from 'react';
import {
  Text,
  Button,
  Table,
  Modal,
  TextInput,
  Select,
  NumberInput,
  Switch,
  Group,
  Stack,
  Badge,
  ActionIcon,
  Paper,
  Loader,
  Center,
} from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { IconPlus, IconEdit, IconTrash, IconRefresh, IconKey, IconLink } from '@tabler/icons-react';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { usersApi } from '@/services/api';
import type { User } from '@/types';
import { handleApiError } from '@/utils/errorFormatter';

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [keysModalOpened, setKeysModalOpened] = useState(false);
  const [selectedUserKeys, setSelectedUserKeys] = useState<any>(null);
  const [inboundsModalOpened, setInboundsModalOpened] = useState(false);
  const [selectedUserForInbounds, setSelectedUserForInbounds] = useState<User | null>(null);
  const [availableInbounds, setAvailableInbounds] = useState<any[]>([]);
  const [selectedInboundIds, setSelectedInboundIds] = useState<number[]>([]);

  const form = useForm({
    initialValues: {
      username: '',
      email: '',
      password: '',
      status: 'ACTIVE',
      traffic_limit_bytes: 0,
      traffic_limit_strategy: 'MONTH',
      max_connections: 0,
      expire_at: null as Date | null,
      description: '',
    },
  });

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await usersApi.list();
      setUsers(response.data.items);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to load users',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleSubmit = async (values: any) => {
    try {
      // Format date for API
      const formattedValues = {
        ...values,
        expire_at: values.expire_at ? values.expire_at.toISOString() : null,
      };
      
      if (editingUser) {
        await usersApi.update(editingUser.id, formattedValues);
        notifications.show({
          title: 'Success',
          message: 'User updated successfully',
          color: 'green',
        });
      } else {
        await usersApi.create(formattedValues);
        notifications.show({
          title: 'Success',
          message: 'User created successfully',
          color: 'green',
        });
      }
      setModalOpened(false);
      form.reset();
      setEditingUser(null);
      loadUsers();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to save user'),
        color: 'red',
      });
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setValues({
      username: user.username,
      email: user.email || '',
      password: '',
      status: user.status,
      traffic_limit_bytes: user.traffic_limit_bytes || 0,
      traffic_limit_strategy: user.traffic_limit_strategy,
      max_connections: (user as any).max_connections || 0,
      expire_at: user.expire_at ? new Date(user.expire_at) : null,
      description: user.description || '',
    });
    setModalOpened(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await usersApi.delete(id);
      notifications.show({
        title: 'Success',
        message: 'User deleted successfully',
        color: 'green',
      });
      loadUsers();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to delete user'),
        color: 'red',
      });
    }
  };

  const handleResetTraffic = async (id: number) => {
    try {
      await usersApi.resetTraffic(id);
      notifications.show({
        title: 'Success',
        message: 'Traffic reset successfully',
        color: 'green',
      });
      loadUsers();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to reset traffic'),
        color: 'red',
      });
    }
  };

  const handleShowKeys = async (user: User) => {
    try {
      const response = await usersApi.getProxies(user.id);
      setSelectedUserKeys(response.data);
      setKeysModalOpened(true);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to load keys'),
        color: 'red',
      });
    }
  };

  const handleManageInbounds = async (user: User) => {
    try {
      // Load available inbounds
      const inboundsResponse = await fetch(`/api/v1/inbounds/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      const inboundsData = await inboundsResponse.json();
      setAvailableInbounds(inboundsData.items || inboundsData);

      // Load user's current inbounds
      const userInboundsResponse = await usersApi.getInbounds(user.id);
      const currentInboundIds = userInboundsResponse.data.inbounds.map((ib: any) => ib.id);
      setSelectedInboundIds(currentInboundIds);

      setSelectedUserForInbounds(user);
      setInboundsModalOpened(true);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to load inbounds'),
        color: 'red',
      });
    }
  };

  const handleAssignInbounds = async () => {
    if (!selectedUserForInbounds) return;
    
    try {
      await usersApi.assignInbounds(selectedUserForInbounds.id, selectedInboundIds);
      notifications.show({
        title: 'Success',
        message: 'Inbounds assigned successfully',
        color: 'green',
      });
      setInboundsModalOpened(false);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to assign inbounds'),
        color: 'red',
      });
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'green';
      case 'DISABLED': return 'red';
      case 'LIMITED': return 'yellow';
      case 'EXPIRED': return 'gray';
      default: return 'blue';
    }
  };

  if (loading) {
    return (
      <Center h={400}>
        <Loader size="lg" />
      </Center>
    );
  }

  return (
    <div>
      <Group justify="space-between" mb="md">
        <Text size="xl" fw={700}>Users Management</Text>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={() => {
            setEditingUser(null);
            form.reset();
            setModalOpened(true);
          }}
        >
          Add User
        </Button>
      </Group>

      <Paper shadow="xs" p="md">
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>ID</Table.Th>
              <Table.Th>Username</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Traffic</Table.Th>
              <Table.Th>Expire At</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {users.map((user) => (
              <Table.Tr key={user.id}>
                <Table.Td>{user.id}</Table.Td>
                <Table.Td>{user.username}</Table.Td>
                <Table.Td>{user.email || '-'}</Table.Td>
                <Table.Td>
                  <Badge color={getStatusColor(user.status)}>{user.status}</Badge>
                </Table.Td>
                <Table.Td>
                  {formatBytes(user.traffic_used_bytes)}
                  {user.traffic_limit_bytes ? ` / ${formatBytes(user.traffic_limit_bytes)}` : ''}
                </Table.Td>
                <Table.Td>
                  {user.expire_at ? new Date(user.expire_at).toLocaleDateString() : 'Never'}
                </Table.Td>
                <Table.Td>
                  <Group gap="xs">
                    <ActionIcon
                      variant="light"
                      color="green"
                      onClick={() => handleShowKeys(user)}
                      title="Show Keys"
                    >
                      <IconKey size={16} />
                    </ActionIcon>
                    <ActionIcon
                      variant="light"
                      color="violet"
                      onClick={() => handleManageInbounds(user)}
                      title="Manage Inbounds"
                    >
                      <IconLink size={16} />
                    </ActionIcon>
                    <ActionIcon color="blue" onClick={() => handleEdit(user)}>
                      <IconEdit size={16} />
                    </ActionIcon>
                    <ActionIcon color="orange" onClick={() => handleResetTraffic(user.id)}>
                      <IconRefresh size={16} />
                    </ActionIcon>
                    <ActionIcon color="red" onClick={() => handleDelete(user.id)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {users.length === 0 && (
          <Center py="xl">
            <Text c="dimmed">No users found. Create your first user!</Text>
          </Center>
        )}
      </Paper>

      <Modal
        opened={modalOpened}
        onClose={() => {
          setModalOpened(false);
          setEditingUser(null);
          form.reset();
        }}
        title={editingUser ? 'Edit User' : 'Create User'}
        size="lg"
      >
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            <TextInput
              label="Username"
              placeholder="Enter username"
              required
              {...form.getInputProps('username')}
            />
            <TextInput
              label="Email"
              placeholder="Enter email"
              type="email"
              {...form.getInputProps('email')}
            />
            {!editingUser && (
              <TextInput
                label="Password"
                placeholder="Enter password"
                type="password"
                required
                {...form.getInputProps('password')}
              />
            )}
            <Select
              label="Status"
              data={[
                { value: 'ACTIVE', label: 'Active' },
                { value: 'DISABLED', label: 'Disabled' },
                { value: 'LIMITED', label: 'Limited' },
                { value: 'EXPIRED', label: 'Expired' },
              ]}
              {...form.getInputProps('status')}
            />
            <NumberInput
              label="Traffic Limit (bytes)"
              placeholder="0 for unlimited"
              min={0}
              {...form.getInputProps('traffic_limit_bytes')}
            />
            <Select
              label="Traffic Reset Strategy"
              data={[
                { value: 'NO_RESET', label: 'No Reset' },
                { value: 'DAY', label: 'Daily' },
                { value: 'WEEK', label: 'Weekly' },
                { value: 'MONTH', label: 'Monthly' },
              ]}
              {...form.getInputProps('traffic_limit_strategy')}
            />
            <NumberInput
              label="Max Simultaneous Connections"
              description="0 for unlimited"
              placeholder="0"
              min={0}
              {...form.getInputProps('max_connections')}
            />
            <DateTimePicker
              label="Expire At"
              placeholder="Pick date and time"
              clearable
              {...form.getInputProps('expire_at')}
            />
            <TextInput
              label="Description"
              placeholder="Optional description"
              {...form.getInputProps('description')}
            />
            <Group justify="flex-end" mt="md">
              <Button type="submit">
                {editingUser ? 'Update' : 'Create'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Keys Modal */}
      <Modal
        opened={keysModalOpened}
        onClose={() => setKeysModalOpened(false)}
        title={`Keys for ${selectedUserKeys?.username || ''}`}
        size="lg"
      >
        {selectedUserKeys && (
          <Stack gap="md">
            {selectedUserKeys.proxies && selectedUserKeys.proxies.length > 0 ? (
              selectedUserKeys.proxies.map((proxy: any, index: number) => (
                <Paper key={index} p="md" withBorder>
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text fw={500}>{proxy.type}</Text>
                      <Badge color="blue">{proxy.type}</Badge>
                    </Group>
                    <TextInput
                      label="UUID / Key"
                      value={proxy.uuid || proxy.password || 'N/A'}
                      readOnly
                      rightSection={
                        <ActionIcon
                          onClick={() => {
                            navigator.clipboard.writeText(proxy.uuid || proxy.password || '');
                            notifications.show({
                              title: 'Copied!',
                              message: 'Key copied to clipboard',
                              color: 'green',
                            });
                          }}
                        >
                          <IconKey size={16} />
                        </ActionIcon>
                      }
                    />
                    {proxy.flow && <Text size="sm" c="dimmed">Flow: {proxy.flow}</Text>}
                    {proxy.method && <Text size="sm" c="dimmed">Method: {proxy.method}</Text>}
                  </Stack>
                </Paper>
              ))
            ) : (
              <Text c="dimmed">No keys found</Text>
            )}
            
            <Paper p="md" withBorder bg="blue.0">
              <Stack gap="xs">
                <Text fw={500}>Subscription Link</Text>
                <TextInput
                  value={selectedUserKeys.subscription_link}
                  readOnly
                  rightSection={
                    <ActionIcon
                      onClick={() => {
                        navigator.clipboard.writeText(selectedUserKeys.subscription_link);
                        notifications.show({
                          title: 'Copied!',
                          message: 'Subscription link copied',
                          color: 'green',
                        });
                      }}
                    >
                      <IconKey size={16} />
                    </ActionIcon>
                  }
                />
                <Text size="xs" c="dimmed">Use this link in your V2Ray/Xray client</Text>
              </Stack>
            </Paper>
          </Stack>
        )}
      </Modal>

      {/* Inbounds Management Modal */}
      <Modal
        opened={inboundsModalOpened}
        onClose={() => setInboundsModalOpened(false)}
        title={`Manage Inbounds for ${selectedUserForInbounds?.username || ''}`}
        size="md"
      >
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            Select inbounds to assign to this user
          </Text>
          
          {availableInbounds.map((inbound) => (
            <Paper key={inbound.id} p="sm" withBorder>
              <Group justify="space-between">
                <div>
                  <Text fw={500}>{inbound.tag}</Text>
                  <Text size="sm" c="dimmed">
                    {inbound.type} - Port {inbound.port}
                  </Text>
                </div>
                <Switch
                  checked={selectedInboundIds.includes(inbound.id)}
                  onChange={(e) => {
                    if (e.currentTarget.checked) {
                      setSelectedInboundIds([...selectedInboundIds, inbound.id]);
                    } else {
                      setSelectedInboundIds(selectedInboundIds.filter(id => id !== inbound.id));
                    }
                  }}
                />
              </Group>
            </Paper>
          ))}
          
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setInboundsModalOpened(false)}>
              Cancel
            </Button>
            <Button onClick={handleAssignInbounds}>
              Assign Inbounds
            </Button>
          </Group>
        </Stack>
      </Modal>
    </div>
  );
}
