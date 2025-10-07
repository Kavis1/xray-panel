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
  PasswordInput,
} from '@mantine/core';
import { IconPlus, IconEdit, IconTrash, IconPlugConnected, IconPlugConnectedX } from '@tabler/icons-react';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { nodesApi } from '@/services/api';
import type { Node } from '@/types';
import { handleApiError } from '@/utils/errorFormatter';

export default function NodesPage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [editingNode, setEditingNode] = useState<Node | null>(null);
  const [sslModalOpened, setSSLModalOpened] = useState(false);
  const [createdNodeSSL, setCreatedNodeSSL] = useState<{
    name: string;
    certificate: string;
    key: string;
    ca: string;
  } | null>(null);

  const form = useForm({
    initialValues: {
      name: '',
      address: '',
      api_port: 50051,
      api_protocol: 'grpc',
      api_key: '',
      usage_ratio: 1.0,
      traffic_limit_bytes: 0,
      traffic_notify_percent: 80,
      is_enabled: true,
      add_host_to_inbounds: true,
      view_position: 0,
      country_code: '',
    },
  });

  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await nodesApi.list();
      setNodes(response.data);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to load nodes',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNodes();
  }, []);

  const handleGenerateSSL = async () => {
    const name = form.values.name;
    const address = form.values.address;
    
    if (!name || !address) {
      notifications.show({
        title: 'Error',
        message: 'Please fill in Node Name and Address first',
        color: 'red',
      });
      return;
    }
    
    try {
      const response = await nodesApi.generateSSL(name, address);
      const data = response.data;
      
      setCreatedNodeSSL({
        name: data.name,
        certificate: data.client_certificate,
        key: data.client_key,
        ca: data.ca_certificate,
      });
      setSSLModalOpened(true);
      
      notifications.show({
        title: 'Success',
        message: 'SSL certificates generated',
        color: 'green',
      });
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to generate SSL certificate'),
        color: 'red',
      });
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingNode) {
        await nodesApi.update(editingNode.id, values);
        notifications.show({
          title: 'Success',
          message: 'Node updated successfully',
          color: 'green',
        });
      } else {
        await nodesApi.create(values);
        notifications.show({
          title: 'Success',
          message: 'Node created successfully',
          color: 'green',
        });
      }
      setModalOpened(false);
      form.reset();
      setEditingNode(null);
      setCreatedNodeSSL(null);
      loadNodes();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to save node'),
        color: 'red',
      });
    }
  };

  const handleEdit = (node: Node) => {
    setEditingNode(node);
    form.setValues({
      name: node.name,
      address: node.address,
      api_port: node.api_port,
      api_protocol: node.api_protocol,
      api_key: '', // Don't show existing API key for security
      usage_ratio: node.usage_ratio,
      traffic_limit_bytes: node.traffic_limit_bytes || 0,
      traffic_notify_percent: node.traffic_notify_percent,
      is_enabled: node.is_enabled,
      add_host_to_inbounds: node.add_host_to_inbounds,
      view_position: node.view_position,
      country_code: node.country_code || '',
    });
    setModalOpened(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this node?')) return;
    try {
      await nodesApi.delete(id);
      notifications.show({
        title: 'Success',
        message: 'Node deleted successfully',
        color: 'green',
      });
      loadNodes();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to delete node'),
        color: 'red',
      });
    }
  };

  const handleConnect = async (id: number) => {
    try {
      await nodesApi.connect(id);
      notifications.show({
        title: 'Success',
        message: 'Node connected successfully',
        color: 'green',
      });
      loadNodes();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to connect node'),
        color: 'red',
      });
    }
  };

  const handleDisconnect = async (id: number) => {
    try {
      await nodesApi.disconnect(id);
      notifications.show({
        title: 'Success',
        message: 'Node disconnected successfully',
        color: 'green',
      });
      loadNodes();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to disconnect node'),
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
        <Text size="xl" fw={700}>Nodes Management</Text>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={() => {
            setEditingNode(null);
            form.reset();
            setModalOpened(true);
          }}
        >
          Add Node
        </Button>
      </Group>

      <Paper shadow="xs" p="md">
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>ID</Table.Th>
              <Table.Th>Name</Table.Th>
              <Table.Th>Address</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Xray</Table.Th>
              <Table.Th>Traffic</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {nodes.map((node) => (
              <Table.Tr key={node.id}>
                <Table.Td>{node.id}</Table.Td>
                <Table.Td>
                  {node.name}
                  {node.country_code && (
                    <Badge size="xs" ml="xs">{node.country_code}</Badge>
                  )}
                </Table.Td>
                <Table.Td>{node.address}:{node.api_port}</Table.Td>
                <Table.Td>
                  <Group gap="xs">
                    <Badge color={node.is_enabled ? 'green' : 'gray'}>
                      {node.is_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                    <Badge color={node.is_connected ? 'blue' : 'red'}>
                      {node.is_connected ? 'Connected' : 'Disconnected'}
                    </Badge>
                  </Group>
                </Table.Td>
                <Table.Td>
                  <Badge color={node.xray_running ? 'green' : 'red'}>
                    {node.xray_running ? 'Running' : 'Stopped'}
                  </Badge>
                  {node.xray_version && (
                    <Text size="xs" c="dimmed">{node.xray_version}</Text>
                  )}
                </Table.Td>
                <Table.Td>
                  {formatBytes(node.traffic_used_bytes)}
                  {node.traffic_limit_bytes ? ` / ${formatBytes(node.traffic_limit_bytes)}` : ''}
                </Table.Td>
                <Table.Td>
                  <Group gap="xs">
                    <ActionIcon color="blue" onClick={() => handleEdit(node)}>
                      <IconEdit size={16} />
                    </ActionIcon>
                    {node.is_connected ? (
                      <ActionIcon color="orange" onClick={() => handleDisconnect(node.id)}>
                        <IconPlugConnectedX size={16} />
                      </ActionIcon>
                    ) : (
                      <ActionIcon color="green" onClick={() => handleConnect(node.id)}>
                        <IconPlugConnected size={16} />
                      </ActionIcon>
                    )}
                    <ActionIcon color="red" onClick={() => handleDelete(node.id)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {nodes.length === 0 && (
          <Center py="xl">
            <Text c="dimmed">No nodes found. Add your first node!</Text>
          </Center>
        )}
      </Paper>

      <Modal
        opened={modalOpened}
        onClose={() => {
          setModalOpened(false);
          setEditingNode(null);
          form.reset();
        }}
        title={editingNode ? 'Edit Node' : 'Create Node'}
        size="lg"
      >
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            <TextInput
              label="Name"
              placeholder="Enter node name"
              required
              {...form.getInputProps('name')}
            />
            <TextInput
              label="Address"
              placeholder="Enter node address (IP or domain)"
              required
              {...form.getInputProps('address')}
            />
            
            {!editingNode && (
              <Paper p="sm" withBorder bg="blue.0">
                <Group justify="space-between">
                  <div>
                    <Text size="sm" fw={500}>SSL Certificates</Text>
                    <Text size="xs" c="dimmed">
                      Generate SSL certificates before creating the node
                    </Text>
                  </div>
                  <Button
                    variant="light"
                    size="sm"
                    onClick={handleGenerateSSL}
                    disabled={!form.values.name || !form.values.address}
                  >
                    Generate SSL
                  </Button>
                </Group>
              </Paper>
            )}
            <NumberInput
              label="API Port"
              placeholder="50051"
              required
              min={1}
              max={65535}
              {...form.getInputProps('api_port')}
            />
            <Select
              label="API Protocol"
              data={[
                { value: 'grpc', label: 'gRPC' },
                { value: 'rest', label: 'REST' },
              ]}
              {...form.getInputProps('api_protocol')}
            />
            <PasswordInput
              label="API Key"
              placeholder="Enter API key (min 16 chars)"
              required
              {...form.getInputProps('api_key')}
            />
            <NumberInput
              label="Usage Ratio"
              placeholder="1.0"
              step={0.1}
              min={0.1}
              max={10}
              {...form.getInputProps('usage_ratio')}
            />
            <NumberInput
              label="Traffic Limit (bytes)"
              placeholder="0 for unlimited"
              min={0}
              {...form.getInputProps('traffic_limit_bytes')}
            />
            <NumberInput
              label="Traffic Notify Percent"
              placeholder="80"
              min={0}
              max={100}
              {...form.getInputProps('traffic_notify_percent')}
            />
            <TextInput
              label="Country Code"
              placeholder="US, UK, etc."
              {...form.getInputProps('country_code')}
            />
            <NumberInput
              label="View Position"
              placeholder="0"
              min={0}
              {...form.getInputProps('view_position')}
            />
            <Switch
              label="Enabled"
              {...form.getInputProps('is_enabled', { type: 'checkbox' })}
            />
            <Switch
              label="Add Host to Inbounds"
              {...form.getInputProps('add_host_to_inbounds', { type: 'checkbox' })}
            />
            <Group justify="flex-end" mt="md">
              <Button type="submit">
                {editingNode ? 'Update' : 'Create'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* SSL Certificate Modal */}
      <Modal
        opened={sslModalOpened}
        onClose={() => setSSLModalOpened(false)}
        title={`SSL Certificate for ${createdNodeSSL?.name || 'Node'}`}
        size="lg"
      >
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            Copy this certificate and paste it during node installation. This single certificate contains everything needed for secure connection.
          </Text>
          
          <div>
            <Group justify="space-between" mb={5}>
              <Text size="sm" fw={500}>Client Certificate:</Text>
              <Button
                size="xs"
                variant="light"
                onClick={() => {
                  const fullCert = `${createdNodeSSL?.certificate || ''}\n${createdNodeSSL?.key || ''}`;
                  navigator.clipboard.writeText(fullCert);
                  notifications.show({
                    message: 'Certificate copied to clipboard',
                    color: 'green',
                  });
                }}
              >
                📋 Copy Certificate
              </Button>
            </Group>
            <textarea
              readOnly
              value={`${createdNodeSSL?.certificate || ''}\n${createdNodeSSL?.key || ''}`}
              style={{
                width: '100%',
                height: '200px',
                fontFamily: 'monospace',
                fontSize: '11px',
                padding: '8px',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                resize: 'vertical',
              }}
            />
          </div>

          <Paper p="sm" withBorder bg="blue.0">
            <Text size="sm" fw={500} mb={5}>📋 Quick Setup:</Text>
            <Text size="xs" c="dimmed" style={{ whiteSpace: 'pre-line' }}>
{`1. Copy the certificate above
2. SSH to your node: ssh root@${createdNodeSSL?.name || 'your-server'}
3. Save to file: nano /root/node-cert.pem
4. Paste the certificate and save (Ctrl+X, Y, Enter)
5. Use this certificate for your node setup`}
            </Text>
          </Paper>

          <Group justify="flex-end">
            <Button onClick={() => setSSLModalOpened(false)}>
              Close
            </Button>
          </Group>
        </Stack>
      </Modal>
    </div>
  );
}
