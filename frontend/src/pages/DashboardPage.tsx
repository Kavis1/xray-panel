import { useState, useEffect } from 'react';
import { Grid, Card, Text, Group, Stack, Loader } from '@mantine/core';
import { IconUsers, IconServer, IconNetwork, IconArrowUp } from '@tabler/icons-react';
import { usersApi, nodesApi, inboundsApi } from '@/services/api';

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeNodes: 0,
    totalInbounds: 0,
    totalTraffic: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [usersRes, nodesRes, inboundsRes] = await Promise.all([
        usersApi.list(),
        nodesApi.list(),
        inboundsApi.list(),
      ]);

      const totalUsers = usersRes.data.total || usersRes.data.items?.length || 0;
      const activeNodes = Array.isArray(nodesRes.data) 
        ? nodesRes.data.filter((n: any) => n.is_enabled).length 
        : 0;
      const totalInbounds = Array.isArray(inboundsRes.data) 
        ? inboundsRes.data.length 
        : (inboundsRes.data as any).items?.length || 0;
      
      // Calculate total traffic from users
      const totalTraffic = usersRes.data.items?.reduce((sum: number, user: any) => 
        sum + (user.traffic_used_bytes || 0), 0) || 0;

      setStats({
        totalUsers,
        activeNodes,
        totalInbounds,
        totalTraffic: Math.round(totalTraffic / 1024 / 1024 / 1024 * 100) / 100, // GB
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader size="lg" />
      </Stack>
    );
  }

  return (
    <Stack>
      <Text size="xl" fw={700}>Dashboard</Text>

      <Grid>
        <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">Total Users</Text>
                <Text size="xl" fw={700}>{stats.totalUsers}</Text>
              </div>
              <IconUsers size={40} opacity={0.5} />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">Active Nodes</Text>
                <Text size="xl" fw={700}>{stats.activeNodes}</Text>
              </div>
              <IconServer size={40} opacity={0.5} />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">Inbounds</Text>
                <Text size="xl" fw={700}>{stats.totalInbounds}</Text>
              </div>
              <IconNetwork size={40} opacity={0.5} />
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group justify="space-between">
              <div>
                <Text c="dimmed" size="sm">Total Traffic</Text>
                <Text size="xl" fw={700}>{stats.totalTraffic} GB</Text>
              </div>
              <IconArrowUp size={40} opacity={0.5} />
            </Group>
          </Card>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
