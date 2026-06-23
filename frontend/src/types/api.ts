// Kiểu dữ liệu khớp schema backend (SPEC 09, 10). Nguồn chân lý là backend.

export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type StepStatus =
  | "queued"
  | "assigned"
  | "running"
  | "completed"
  | "failed"
  | "retrying"
  | "cancelled";

export type BatchStatus = "created" | "running" | "completed" | "failed" | "cancelled";
export type AgentStatus = "online" | "offline" | "busy";

export interface Page<T> {
  items: T[];
  next_cursor: string | null;
}

export interface Info {
  name: string;
  version: string;
  env: string;
  max_concurrent_steps: number;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  default_pipeline: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
  default_pipeline?: string;
  config?: Record<string, unknown>;
}

export type ProjectUpdate = Partial<ProjectCreate>;

export interface Batch {
  id: string;
  project_id: string;
  name: string;
  status: BatchStatus;
  input_count: number;
  counts: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface BatchCreate {
  name: string;
  inputs: Record<string, unknown>[];
  pipeline?: string | null;
}

export interface Step {
  id: string;
  job_id: string;
  step_key: string;
  order: number;
  adapter: string;
  status: StepStatus;
  attempt: number;
  max_retries: number;
  assigned_agent: string | null;
  inputs: Record<string, unknown>;
  config: Record<string, unknown>;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface Job {
  id: string;
  batch_id: string;
  seq: number;
  status: JobStatus;
  pipeline: string;
  vars: Record<string, unknown>;
  progress: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobDetail extends Job {
  steps: Step[];
}

export interface Agent {
  id: string;
  version: string;
  capabilities: string[];
  capacity: number;
  status: AgentStatus;
  os: string;
  last_heartbeat: string | null;
  registered_at: string;
}

export interface Plugin {
  name: string;
  version: string;
  capability: string;
  type: string;
  enabled: boolean;
  config: Record<string, unknown>;
  manifest: Record<string, unknown>;
  installed_at: string;
}

export interface PluginRegister {
  name: string;
  version?: string;
  capability?: string;
  type?: string;
  manifest?: Record<string, unknown>;
  config?: Record<string, unknown>;
}

// Audit-log cho trang Logs (SPEC 04 §7, 10 §2). `level` suy từ loại event ở backend.
export type LogLevel = "info" | "warn" | "error" | "debug";

export interface LogEntry {
  id: string;
  level: LogLevel;
  category: string;
  entity_id: string;
  type: string;
  trace_id: string | null;
  data: Record<string, unknown>;
  created_at: string;
}

export interface LogQuery {
  level?: LogLevel;
  category?: string;
  project_id?: string;
  batch_id?: string;
  plugin?: string;
  trace_id?: string;
  search?: string;
  limit?: number;
}

// Thống kê vận hành cho trang Statistics (SPEC 02 §7).
export interface ThroughputPoint {
  date: string;
  count: number;
}

export interface AdapterStat {
  adapter: string;
  count: number;
  failed: number;
  avg_seconds: number;
}

export interface Stats {
  jobs_total: number;
  jobs_by_status: Record<string, number>;
  steps_total: number;
  steps_by_status: Record<string, number>;
  completed_total: number;
  failed_total: number;
  fail_rate: number;
  throughput: ThroughputPoint[];
  adapters: AdapterStat[];
  generated_at: string;
}

// External Apps — adapter bọc app ngoài (SPEC 06).
export type ConnectionState = "connected" | "no_agent" | "disabled";

export interface ConnectionStatus {
  status: ConnectionState;
  online_agents: string[];
  capacity_free: boolean;
}

export interface ExternalApp {
  name: string;
  capability: string;
  type: string;
  version: string;
  enabled: boolean;
  free: boolean;
  license: string | null;
  source_url: string | null;
  connection: ConnectionStatus;
}

export interface ExternalAppTestResult {
  ok: boolean;
  reason: string;
  agents: string[];
}
