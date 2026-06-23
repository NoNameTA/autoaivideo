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

export function useJobsAll(status?: string, search?: string) {
  return useQuery({
    queryKey: ["jobs-all", status ?? "all", search ?? ""],
    queryFn: () => endpoints.listJobs({ status, search }),
  });
}

export function useRetryJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.retryJob(id),
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: qk.job(job.id) });
      qc.invalidateQueries({ queryKey: ["jobs-all"] });
    },
  });
}

export function useCancelJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.cancelJob(id),
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: qk.job(job.id) });
      qc.invalidateQueries({ queryKey: ["jobs-all"] });
    },
  });
}

export function useAgents() {
  return useQuery({ queryKey: qk.agents, queryFn: endpoints.listAgents });
}

export function usePlugins() {
  return useQuery({ queryKey: qk.plugins, queryFn: endpoints.listPlugins });
}

export function usePipelines() {
  return useQuery({ queryKey: ["pipelines"], queryFn: endpoints.listPipelines });
}

export function useSavePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: {
      editing: boolean;
      name: string;
      data: { description: string; steps: { step_key: string; adapter: string; config: Record<string, unknown> }[] };
    }) =>
      args.editing
        ? endpoints.updatePipeline(args.name, args.data)
        : endpoints.createPipeline({ name: args.name, ...args.data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}

export function useDeletePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => endpoints.deletePipeline(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pipelines"] }),
  });
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
