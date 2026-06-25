// Hàm gọi API thuần theo tài nguyên (SPEC 04 §2). React Query bọc ở hooks.ts.
import type {
  Agent,
  Batch,
  BatchCreate,
  Connection,
  ConnectionCreate,
  ConnectionTestResult,
  CookieConfig,
  CookieTestResult,
  Credential,
  CredentialCreate,
  ExternalApp,
  ExternalAppTestResult,
  Info,
  Job,
  JobDetail,
  LogEntry,
  LogQuery,
  Page,
  Plugin,
  PluginRegister,
  Project,
  ProjectCreate,
  ProjectUpdate,
  RunResult,
  SheetCountResult,
  SheetImportResult,
  SheetPreviewRow,
  SheetReadRequest,
  Stats,
  VideoSource,
  VideoSourceItem,
  VideoSourcesSummary,
} from "../types/api";
import type { AllowedFolder, FsEntry, ReadResult, ScanResult } from "../types/fs";
import type { Pipeline, PipelineInput } from "../types/pipeline";
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

  listJobs: (params: { status?: string; search?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params.status) q.set("status", params.status);
    if (params.search) q.set("search", params.search);
    if (params.limit) q.set("limit", String(params.limit));
    const s = q.toString();
    return http.get<Job[]>(`/api/v1/jobs${s ? `?${s}` : ""}`);
  },
  getJob: (id: string) => http.get<JobDetail>(`/api/v1/jobs/${id}`),
  retryJob: (id: string) => http.post<Job>(`/api/v1/jobs/${id}/retry`),
  cancelJob: (id: string) => http.post<Job>(`/api/v1/jobs/${id}/cancel`),

  listLogs: (q: LogQuery = {}) => {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(q)) {
      if (v !== undefined && v !== "") params.set(k, String(v));
    }
    const s = params.toString();
    return http.get<LogEntry[]>(`/api/v1/logs${s ? `?${s}` : ""}`);
  },

  getStats: () => http.get<Stats>("/api/v1/stats"),

  // Cookie Manager (đa nền tảng) — metadata only, không lưu/đọc nội dung cookie ở web.
  getCookies: () => http.get<CookieConfig>("/api/v1/cookies"),
  saveCookies: (data: {
    enabled: boolean;
    cookie_dir: string;
    platforms: { name: string; hosts: string[]; cookie_file: string }[];
  }) => http.put<CookieConfig>("/api/v1/cookies", data),
  testCookie: (name: string) =>
    http.post<CookieTestResult>(`/api/v1/cookies/${encodeURIComponent(name)}/test`),

  // Video Sources (SPEC 02 §4.1)
  listVideoSources: () => http.get<VideoSource[]>("/api/v1/video-sources"),
  videoSourcesSummary: () => http.get<VideoSourcesSummary>("/api/v1/video-sources/summary"),
  createVideoSource: (data: { name: string; source_type?: string; config?: Record<string, unknown> }) =>
    http.post<VideoSource>("/api/v1/video-sources", data),
  updateVideoSource: (id: string, data: { name?: string; config?: Record<string, unknown> }) =>
    http.patch<VideoSource>(`/api/v1/video-sources/${id}`, data),
  deleteVideoSource: (id: string) => http.del(`/api/v1/video-sources/${id}`),
  readVideoSheet: (id: string, body: SheetReadRequest = {}) =>
    http.post<SheetPreviewRow[]>(`/api/v1/video-sources/${id}/read-sheet`, body),
  countVideoSheet: (id: string, body: SheetReadRequest = {}) =>
    http.post<SheetCountResult>(`/api/v1/video-sources/${id}/count-sheet`, body),
  importVideoSheet: (id: string, body: SheetReadRequest = {}) =>
    http.post<SheetImportResult>(`/api/v1/video-sources/${id}/import-sheet`, body),
  listVideoItems: (id: string) => http.get<VideoSourceItem[]>(`/api/v1/video-sources/${id}/items`),
  addVideoLinks: (id: string, data: { urls?: string[]; text?: string }) =>
    http.post<VideoSource>(`/api/v1/video-sources/${id}/links`, data),
  deleteVideoItem: (id: string, itemId: string) =>
    http.del(`/api/v1/video-sources/${id}/items/${itemId}`),
  runVideoSource: (id: string, data: { item_ids?: string[]; project_id?: string; pipeline?: string }) =>
    http.post<RunResult>(`/api/v1/video-sources/${id}/run`, data),
  createVariations: (
    id: string,
    itemId: string,
    data: {
      count: number;
      spin?: boolean;
      ratio?: boolean;
      ratios?: string[];
      caption?: boolean;
      caption_text?: string;
    },
  ) =>
    http.post<{ batch_id: string; count: number }>(
      `/api/v1/video-sources/${id}/items/${itemId}/variations`,
      data,
    ),
  bvsEdit: (id: string, itemId: string, data: { bulkauto_url?: string; bvs_config?: object }) =>
    http.post<{ batch_id: string }>(
      `/api/v1/video-sources/${id}/items/${itemId}/bvs-edit`,
      data,
    ),

  listExternalApps: () => http.get<ExternalApp[]>("/api/v1/external-apps"),
  testExternalApp: (name: string) =>
    http.post<ExternalAppTestResult>(`/api/v1/external-apps/${name}/test`),

  // Credential Store (SPEC 11 §3) — secret KHÔNG bao giờ trả về.
  listCredentials: () => http.get<Credential[]>("/api/v1/credentials"),
  createCredential: (data: CredentialCreate) =>
    http.post<Credential>("/api/v1/credentials", data),
  deleteCredential: (id: string) => http.del(`/api/v1/credentials/${id}`),

  // Connection Manager (SPEC 06 §10)
  listConnections: () => http.get<Connection[]>("/api/v1/connections"),
  createConnection: (data: ConnectionCreate) =>
    http.post<Connection>("/api/v1/connections", data),
  deleteConnection: (id: string) => http.del(`/api/v1/connections/${id}`),
  testConnection: (id: string) =>
    http.post<ConnectionTestResult>(`/api/v1/connections/${id}/test`),

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

  // File Manager (SPEC 07)
  listAllowed: () => http.get<AllowedFolder[]>("/api/v1/fs/allowed"),
  addAllowed: (path: string, label: string) =>
    http.post<AllowedFolder>("/api/v1/fs/allowed", { path, label }),
  removeAllowed: (id: string) => http.del(`/api/v1/fs/allowed/${id}`),
  fsScan: (path: string) => http.post<ScanResult>("/api/v1/fs/scan", { path }),
  fsRead: (path: string) => http.post<ReadResult>("/api/v1/fs/read", { path }),
  fsMetadata: (path: string) => http.post<FsEntry>("/api/v1/fs/metadata", { path }),
  fsCopy: (src: string, dst: string) => http.post("/api/v1/fs/copy", { src, dst }),
  fsMove: (src: string, dst: string) => http.post("/api/v1/fs/move", { src, dst }),
  fsRename: (path: string, new_name: string) =>
    http.post("/api/v1/fs/rename", { path, new_name }),
  fsDelete: (path: string) => http.post("/api/v1/fs/delete", { path }),
  fsWatch: (path: string, enable: boolean) => http.post("/api/v1/fs/watch", { path, enable }),

  // Pipelines / Workflow (SPEC 02 §4)
  listPipelines: () => http.get<Pipeline[]>("/api/v1/pipelines"),
  createPipeline: (data: PipelineInput) => http.post<Pipeline>("/api/v1/pipelines", data),
  updatePipeline: (name: string, data: { description?: string; steps?: PipelineInput["steps"] }) =>
    http.patch<Pipeline>(`/api/v1/pipelines/${name}`, data),
  deletePipeline: (name: string) => http.del(`/api/v1/pipelines/${name}`),
  runPipeline: (name: string, body: { project_id: string; name: string; inputs: unknown[] }) =>
    http.post<{ id: string }>(`/api/v1/pipelines/${name}/run`, body),
};
