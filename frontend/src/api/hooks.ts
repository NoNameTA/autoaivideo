// React Query hooks (SPEC 03 §2). Mutation invalidate cache liên quan.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type {
  BatchCreate,
  LogQuery,
  PluginRegister,
  ProjectCreate,
  ProjectUpdate,
  SheetReadRequest,
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

export function useLogs(q: LogQuery) {
  return useQuery({
    queryKey: ["logs", q],
    queryFn: () => endpoints.listLogs(q),
  });
}

export function useStats(refetchMs?: number) {
  return useQuery({
    queryKey: ["stats"],
    queryFn: endpoints.getStats,
    refetchInterval: refetchMs && refetchMs > 0 ? refetchMs : false,
  });
}

export function useVideoSources(refetchMs?: number) {
  return useQuery({
    queryKey: ["video-sources"],
    queryFn: endpoints.listVideoSources,
    refetchInterval: refetchMs && refetchMs > 0 ? refetchMs : false,
  });
}

export function useVideoSourcesSummary(refetchMs?: number) {
  return useQuery({
    queryKey: ["video-sources-summary"],
    queryFn: endpoints.videoSourcesSummary,
    refetchInterval: refetchMs && refetchMs > 0 ? refetchMs : false,
  });
}

export function useVideoItems(id: string | undefined, refetchMs?: number) {
  return useQuery({
    queryKey: ["video-items", id],
    queryFn: () => endpoints.listVideoItems(id as string),
    enabled: !!id,
    refetchInterval: refetchMs && refetchMs > 0 ? refetchMs : false,
  });
}

export function useCreateVideoSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: endpoints.createVideoSource,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["video-sources"] }),
  });
}

export function useDeleteVideoSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.deleteVideoSource(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["video-sources"] }),
  });
}

export function useUpdateVideoSource(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name?: string; config?: Record<string, unknown> }) =>
      endpoints.updateVideoSource(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["video-sources"] }),
  });
}

export function useReadVideoSheet(id: string) {
  return useMutation({
    mutationFn: (body?: SheetReadRequest) => endpoints.readVideoSheet(id, body ?? {}),
  });
}

export function useCountVideoSheet(id: string) {
  return useMutation({
    mutationFn: (body?: SheetReadRequest) => endpoints.countVideoSheet(id, body ?? {}),
  });
}

export function useImportVideoSheet(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body?: SheetReadRequest) => endpoints.importVideoSheet(id, body ?? {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["video-sources"] });
      qc.invalidateQueries({ queryKey: ["video-sources-summary"] });
      qc.invalidateQueries({ queryKey: ["video-items", id] });
    },
  });
}

export function useAddVideoLinks(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { urls?: string[]; text?: string }) => endpoints.addVideoLinks(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["video-sources"] });
      qc.invalidateQueries({ queryKey: ["video-sources-summary"] });
      qc.invalidateQueries({ queryKey: ["video-items", id] });
    },
  });
}

export function useDeleteVideoItem(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => endpoints.deleteVideoItem(id, itemId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["video-items", id] }),
  });
}

export function useCreateVariations(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      itemId: string;
      count: number;
      spin?: boolean;
      ratio?: boolean;
      ratios?: string[];
      caption?: boolean;
      caption_text?: string;
    }) => {
      const { itemId, ...body } = vars;
      return endpoints.createVariations(id, itemId, body);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs-all"] }),
  });
}

export function useRunVideoSource(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { item_ids?: string[]; project_id?: string; pipeline?: string }) =>
      endpoints.runVideoSource(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["video-items", id] });
      qc.invalidateQueries({ queryKey: ["video-sources"] });
      qc.invalidateQueries({ queryKey: ["video-sources-summary"] });
      qc.invalidateQueries({ queryKey: ["jobs-all"] });
    },
  });
}

export function useExternalApps() {
  return useQuery({ queryKey: ["external-apps"], queryFn: endpoints.listExternalApps });
}

export function useTestExternalApp() {
  return useMutation({ mutationFn: (name: string) => endpoints.testExternalApp(name) });
}

export function useCredentials() {
  return useQuery({ queryKey: ["credentials"], queryFn: endpoints.listCredentials });
}

export function useCreateCredential() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: endpoints.createCredential,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["credentials"] }),
  });
}

export function useDeleteCredential() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.deleteCredential(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["credentials"] }),
  });
}

export function useConnections() {
  return useQuery({ queryKey: ["connections"], queryFn: endpoints.listConnections });
}

export function useCreateConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: endpoints.createConnection,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connections"] }),
  });
}

export function useDeleteConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.deleteConnection(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connections"] }),
  });
}

export function useTestConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.testConnection(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connections"] }),
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
