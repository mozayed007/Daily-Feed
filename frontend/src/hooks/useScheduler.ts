import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface ScheduledJob {
  id: string;
  name: string;
  cron?: string;
  interval_seconds?: number;
  enabled: boolean;
  last_run?: string;
  next_run?: string;
  run_count: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error_count: number;
}

export function useSchedulerJobs() {
  return useQuery({
    queryKey: ['scheduler', 'jobs'],
    queryFn: async () => {
      const { data } = await api.get<ScheduledJob[]>('/scheduler/jobs');
      return data;
    },
    refetchInterval: 5000,
  });
}

export function useStartScheduler() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/scheduler/start');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler'] });
    },
  });
}

export function useStopScheduler() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/scheduler/stop');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler'] });
    },
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (job: { name: string; type: 'cron' | 'interval'; cron?: string; interval?: number; enabled?: boolean }) => {
      const { data } = await api.post('/scheduler/jobs', job);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler', 'jobs'] });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      await api.delete(`/scheduler/jobs/${jobId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler', 'jobs'] });
    },
  });
}

export function useToggleJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, enabled }: { jobId: string; enabled: boolean }) => {
      const { data } = await api.patch(`/scheduler/jobs/${jobId}`, { enabled });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduler', 'jobs'] });
    },
  });
}

export function useTriggerJob() {
  return useMutation({
    mutationFn: async (jobId: string) => {
      const { data } = await api.post(`/scheduler/jobs/${jobId}/run`);
      return data;
    },
  });
}

export function useSchedulerStatus() {
  return useQuery({
    queryKey: ['scheduler', 'status'],
    queryFn: async () => {
      const { data } = await api.get<{
        status: string;
        version: string;
        tools_available: string[];
        scheduler_running: boolean;
      }>('/health');
      return { running: data.scheduler_running };
    },
    refetchInterval: 5000,
  });
}
