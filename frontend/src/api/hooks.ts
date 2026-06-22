// React Query hooks (SPEC 03 §2). Mutation invalidate cache liên quan.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type {
  BatchCreate,
  PluginRegister,
  ProjectCreate,
  ProjectUpdate,
} from "../types/api";
import { endpoints } from "./endpoints";

export const qk = {
  info: ["info"] as const,
  projects: ["projects"] as const,
  project: (id: string) => ["project", id] as const,
  batch: (id: string) => ["batch", id] as const,
  batchJobs: (id: string, status?: string) => ["batchJobs", id, status ?? "all"] as const,
  job: (id: string) => ["job", id] as const,
  agents: ["agents"] as const,
  plugins: ["plugins"] as const,
};

export function useInfo() {
  return useQuery({ queryKey: qk.info, queryFn: endpoints.info });
}

export function useProjects() {
  return useQuery({ queryKey: qk.projects, queryFn: endpoints.listProjects });
}

export function useProject(id: string) {
  return useQuery({ queryKey: qk.project(id), queryFn: () => endpoints.getProject(id) });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => endpoints.createProject(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.projects }),
  });
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectUpdate) => endpoints.updateProject(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.projects });
      qc.invalidateQueries({ queryKey: qk.project(id) });
    },
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.deleteProject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.projects }),
  });
}

export function useCreateBatch(projectId: string) {
  return useMutation({
    mutationFn: (data: BatchCreate) => endpoints.createBatch(projectId, data),
  });
}

export function useBatch(id: string) {
  return useQuery({ queryKey: qk.batch(id), queryFn: () => endpoints.getBatch(id) });
}

export function useBatchJobs(id: string, status?: string) {
  return useQuery({
    queryKey: qk.batchJobs(id, status),
    queryFn: () => endpoints.listBatchJobs(id, status),
  });
}

export function useJob(id: string) {
  return useQuery({ queryKey: qk.job(id), queryFn: () => endpoints.getJob(id) });
}

export function useRetryJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.retryJob(id),
    onSuccess: (job) => qc.invalidateQueries({ queryKey: qk.job(job.id) }),
  });
}

export function useCancelJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.cancelJob(id),
    onSuccess: (job) => qc.invalidateQueries({ queryKey: qk.job(job.id) }),
  });
}

export function useAgents() {
  return useQuery({ queryKey: qk.agents, queryFn: endpoints.listAgents });
}

export function usePlugins() {
  return useQuery({ queryKey: qk.plugins, queryFn: endpoints.listPlugins });
}

export function useRegisterPlugin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PluginRegister) => endpoints.registerPlugin(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.plugins }),
  });
}

export function useUpdatePlugin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { name: string; enabled?: boolean; config?: Record<string, unknown> }) =>
      endpoints.updatePlugin(args.name, { enabled: args.enabled, config: args.config }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.plugins }),
  });
}

export function useRemovePlugin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => endpoints.removePlugin(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.plugins }),
  });
}
