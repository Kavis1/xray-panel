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
import { IconPlus, IconEdit, IconTrash, IconTemplate } from '@tabler/icons-react';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { inboundsApi, templatesApi } from '@/services/api';
import type { Inbound } from '@/types';
import { handleApiError } from '@/utils/errorFormatter';

export default function InboundsPage() {
  const [inbounds, setInbounds] = useState<Inbound[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [templateModalOpened, setTemplateModalOpened] = useState(false);
  const [editingInbound, setEditingInbound] = useState<Inbound | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const form = useForm({
    initialValues: {
      tag: '',
      type: 'vless',
      listen: '0.0.0.0',
      port: 443,
      network: 'tcp',
      security: 'none',
      sniffing_enabled: true,
      is_enabled: true,
      block_torrents: false,
      remark: '',
    },
  });

  const templateForm = useForm({
    initialValues: {
      domain: '',
      port: 443,
    },
  });

  const loadInbounds = async () => {
    try {
      setLoading(true);
      const response = await inboundsApi.list();
      setInbounds(response.data);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to load inbounds',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await templatesApi.list();
      setTemplates(response.data);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to load templates',
        color: 'red',
      });
    }
  };

  useEffect(() => {
    loadInbounds();
    loadTemplates();
  }, []);

  const handleSubmit = async (values: any) => {
    try {
      if (editingInbound) {
        await inboundsApi.update(editingInbound.id, values);
        notifications.show({
          title: 'Success',
          message: 'Inbound updated successfully',
          color: 'green',
        });
      } else {
        await inboundsApi.create(values);
        notifications.show({
          title: 'Success',
          message: 'Inbound created successfully',
          color: 'green',
        });
      }
      setModalOpened(false);
      form.reset();
      setEditingInbound(null);
      loadInbounds();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to save inbound'),
        color: 'red',
      });
    }
  };

  const handleTemplateSubmit = async (values: any) => {
    try {
      const response = await templatesApi.generate(selectedTemplate, values);
      await inboundsApi.create(response.data);
      notifications.show({
        title: 'Success',
        message: 'Inbound created from template successfully',
        color: 'green',
      });
      setTemplateModalOpened(false);
      templateForm.reset();
      setSelectedTemplate('');
      loadInbounds();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to create inbound from template'),
        color: 'red',
      });
    }
  };

  const handleEdit = (inbound: Inbound) => {
    setEditingInbound(inbound);
    form.setValues({
      tag: inbound.tag,
      type: inbound.type,
      listen: inbound.listen,
      port: inbound.port,
      network: inbound.network,
      security: inbound.security || 'none',
      sniffing_enabled: inbound.sniffing_enabled,
      is_enabled: inbound.is_enabled,
      block_torrents: (inbound as any).block_torrents || false,
      remark: inbound.remark || '',
    });
    setModalOpened(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this inbound?')) return;
    try {
      await inboundsApi.delete(id);
      notifications.show({
        title: 'Success',
        message: 'Inbound deleted successfully',
        color: 'green',
      });
      loadInbounds();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: handleApiError(error, 'Failed to delete inbound'),
        color: 'red',
      });
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
        <Text size="xl" fw={700}>Inbounds Management</Text>
        <Group>
          <Button
            leftSection={<IconTemplate size={16} />}
            variant="light"
            onClick={() => setTemplateModalOpened(true)}
          >
            From Template
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => {
              setEditingInbound(null);
              form.reset();
              setModalOpened(true);
            }}
          >
            Add Inbound
          </Button>
        </Group>
      </Group>

      <Paper shadow="xs" p="md">
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>ID</Table.Th>
              <Table.Th>Tag</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>Port</Table.Th>
              <Table.Th>Network</Table.Th>
              <Table.Th>Security</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {inbounds.map((inbound) => (
              <Table.Tr key={inbound.id}>
                <Table.Td>{inbound.id}</Table.Td>
                <Table.Td>
                  {inbound.tag}
                  {inbound.remark && (
                    <Text size="xs" c="dimmed">{inbound.remark}</Text>
                  )}
                </Table.Td>
                <Table.Td>
                  <Badge>{inbound.type.toUpperCase()}</Badge>
                </Table.Td>
                <Table.Td>{inbound.port}</Table.Td>
                <Table.Td>{inbound.network}</Table.Td>
                <Table.Td>
                  {inbound.security ? (
                    <Badge color="green">{inbound.security}</Badge>
                  ) : (
                    <Badge color="gray">none</Badge>
                  )}
                </Table.Td>
                <Table.Td>
                  <Badge color={inbound.is_enabled ? 'green' : 'gray'}>
                    {inbound.is_enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Group gap="xs">
                    <ActionIcon color="blue" onClick={() => handleEdit(inbound)}>
                      <IconEdit size={16} />
                    </ActionIcon>
                    <ActionIcon color="red" onClick={() => handleDelete(inbound.id)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {inbounds.length === 0 && (
          <Center py="xl">
            <Text c="dimmed">No inbounds found. Create your first inbound!</Text>
          </Center>
        )}
      </Paper>

      {/* Create/Edit Modal */}
      <Modal
        opened={modalOpened}
        onClose={() => {
          setModalOpened(false);
          setEditingInbound(null);
          form.reset();
        }}
        title={editingInbound ? 'Edit Inbound' : 'Create Inbound'}
        size="lg"
      >
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            <TextInput
              label="Tag"
              placeholder="inbound-1"
              required
              {...form.getInputProps('tag')}
            />
            <Select
              label="Type"
              data={[
                { value: 'vless', label: 'VLESS' },
                { value: 'vmess', label: 'VMess' },
                { value: 'trojan', label: 'Trojan' },
                { value: 'shadowsocks', label: 'Shadowsocks' },
                { value: 'hysteria', label: 'Hysteria' },
                { value: 'hysteria2', label: 'Hysteria2' },
              ]}
              {...form.getInputProps('type')}
            />
            <TextInput
              label="Listen"
              placeholder="0.0.0.0"
              required
              {...form.getInputProps('listen')}
            />
            <NumberInput
              label="Port"
              placeholder="443"
              required
              min={1}
              max={65535}
              {...form.getInputProps('port')}
            />
            <Select
              label="Network"
              data={[
                { value: 'tcp', label: 'TCP' },
                { value: 'ws', label: 'WebSocket' },
                { value: 'grpc', label: 'gRPC' },
                { value: 'h2', label: 'HTTP/2' },
              ]}
              {...form.getInputProps('network')}
            />
            <Select
              label="Security"
              data={[
                { value: 'none', label: 'None' },
                { value: 'tls', label: 'TLS' },
                { value: 'reality', label: 'Reality' },
              ]}
              {...form.getInputProps('security')}
            />
            <TextInput
              label="Remark"
              placeholder="Optional remark"
              {...form.getInputProps('remark')}
            />
            <Switch
              label="Enable Sniffing"
              {...form.getInputProps('sniffing_enabled', { type: 'checkbox' })}
            />
            <Switch
              label="Block Torrents"
              description="Block BitTorrent protocol traffic"
              {...form.getInputProps('block_torrents', { type: 'checkbox' })}
            />
            <Switch
              label="Enabled"
              {...form.getInputProps('is_enabled', { type: 'checkbox' })}
            />
            <Group justify="flex-end" mt="md">
              <Button type="submit">
                {editingInbound ? 'Update' : 'Create'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Template Modal */}
      <Modal
        opened={templateModalOpened}
        onClose={() => {
          setTemplateModalOpened(false);
          setSelectedTemplate('');
          templateForm.reset();
        }}
        title="Create from Template"
        size="lg"
      >
        <Stack gap="md">
          <Select
            label="Select Template"
            placeholder="Choose a template"
            data={templates.map((t) => ({
              value: t.template || t.id || '',
              label: t.name || '',
            }))}
            value={selectedTemplate}
            onChange={(value) => setSelectedTemplate(value || '')}
          />

          {selectedTemplate && (
            <form onSubmit={templateForm.onSubmit(handleTemplateSubmit)}>
              <Stack gap="md">
                <TextInput
                  label="Domain"
                  placeholder="example.com"
                  required
                  {...templateForm.getInputProps('domain')}
                />
                <NumberInput
                  label="Port"
                  placeholder="443"
                  required
                  min={1}
                  max={65535}
                  {...templateForm.getInputProps('port')}
                />
                <Group justify="flex-end" mt="md">
                  <Button type="submit">Generate</Button>
                </Group>
              </Stack>
            </form>
          )}

          {!selectedTemplate && (
            <Text size="sm" c="dimmed">
              Select a template to see available options
            </Text>
          )}
        </Stack>
      </Modal>
    </div>
  );
}
