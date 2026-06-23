// Kiểu cho Pipeline/Workflow (SPEC 02 §4).

export interface StepDef {
  step_key: string;
  adapter: string;
  config: Record<string, unknown>;
}

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  steps: StepDef[];
  builtin: boolean;
  created_at: string;
  updated_at: string;
}

export interface PipelineInput {
  name: string;
  description: string;
  steps: StepDef[];
}
