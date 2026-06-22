// Hàm gọi API thuần theo tài nguyên (SPEC 04 §2). React Query bọc ở hooks.ts.
import type {
  Agent,
  Batch,
  BatchCreate,
  Info,
  Job,
  JobDetail,
  Page,
  Plugin,
  PluginRegister,
  Project,
  ProjectCreate,
  ProjectUpdate,
} from "../types/api";
import { http } from "./client";

export const endpoints = {
  info: () => http.get<Info>("/api/v1/info"),

  listProjects: () => http.get<Page<Project>>("/api/v1/projects"),
  getProject: (id: string) => http.get<Project>(`/api/v1/projects/${id}`),
  createProject: (data: ProjectCreate) => http.post<Project>("/api/v1/projects", data),
  updateProject: (id: string, data: ProjectUpdate) =>
    http.patch<Project>(`/api/v1/projects/${id}`, data),
  deleteProject: (id: string) => http.del(`/api/v1/projects/${id}`),

  createBatch: (projectId: string, data: BatchCreate) =>
    http.post<Batch>(`/api/v1/projects/${projectId}/batches`, data),
  getBatch: (id: string) => http.get<Batch>(`/api/v1/batches/${id}`),
  listBatchJobs: (id: string, status?: string) =>
    http.get<Page<Job>>(
      `/api/v1/batches/${id}/jobs${status ? `?status=${status}` : ""}`,
    ),

  getJob: (id: string) => http.get<JobDetail>(`/api/v1/jobs/${id}`),
  retryJob: (id: string) => http.post<Job>(`/api/v1/jobs/${id}/retry`),
  cancelJob: (id: string) => http.post<Job>(`/api/v1/jobs/${id}/cancel`),

  listAgents: () => http.get<Agent[]>("/api/v1/agents"),

  listPlugins: () => http.get<Plugin[]>("/api/v1/plugins"),
  registerPlugin: (data: PluginRegister) => http.post<Plugin>("/api/v1/plugins", data),
  getPluginSchema: (name: string) =>
    http.get<{ name: string; schema: Record<string, unknown> }>(
      `/api/v1/plugins/${name}/schema`,
    ),
  updatePlugin: (name: string, data: { enabled?: boolean; config?: Record<string, unknown> }) =>
    http.patch<Plugin>(`/api/v1/plugins/${name}`, data),
  removePlugin: (name: string) => http.del(`/api/v1/plugins/${name}`),
};
