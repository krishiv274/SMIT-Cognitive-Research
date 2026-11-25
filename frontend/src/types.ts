export type Condition = "A" | "B" | "C";
export type Answer = "same" | "different";
export type TF = "true" | "false";

export interface SecondaryStimulus {
  text: string;
  correct: TF;
  pattern?: number[];
  question?: "symmetry" | "centre";
  a?: number;
  b?: number;
  shown?: number;
}

export interface PlanTrial {
  trial_number: number;
  block_number: number;
  condition: Condition;
  practice: boolean;
  original_pattern: number[];
  recognition_pattern: number[];
  trial_type: Answer;
  correct_answer: Answer;
  interference_type: "none" | "numerical" | "visual";
  interference: SecondaryStimulus | null;
  planned_iti_ms: number;
  planned_fixation_ms: number;
  planned_memory_stimulus_ms: number;
  planned_post_stimulus_blank_ms: number;
  planned_interference_ms: number;
  planned_retention_ms: number;
  planned_recognition_deadline_ms: number;
}

export interface PlanBlock {
  block_number: number;
  condition: Condition;
  trials: PlanTrial[];
}

export interface TrialPlan {
  seed: number;
  condition_order: string;
  grid_size: number;
  highlight_count: number;
  practice: PlanTrial[];
  blocks: PlanBlock[];
  n_practice: number;
  n_main: number;
}

export interface ExperimentConfig {
  name: string;
  grid: {
    size: number;
    highlight_count: number;
    cell_size_px: number;
    cell_gap_px: number;
    background_color: string;
    cell_color: string;
    memory_highlight_color: string;
    visual_interference_highlight_color: string;
    grid_border_color: string;
  };
  timing: {
    fixation_ms: number;
    memory_stimulus_ms: number;
    post_stimulus_blank_ms: number;
    interference_ms: number;
    retention_ms: number;
    recognition_deadline_ms: number;
    iti_min_ms: number;
    iti_max_ms: number;
    practice_feedback_ms: number;
    break_min_s: number;
  };
  trials: {
    practice_per_condition: number;
    trials_per_condition: number;
    same_proportion: number;
    max_same_answer_run: number;
    change_type: string;
    max_practice_repeats: number;
  };
  secondary_tasks: {
    numerical: Record<string, unknown>;
    visual: { probe: "symmetry" | "centre"; highlight_count: number; true_proportion: number };
  };
  keys: { same: string; different: string; secondary_true: string; secondary_false: string; continue: string };
  analysis: Record<string, number>;
}

/** Data recorded for one trial and uploaded to the server. */
export interface TrialResult {
  trial_number: number;
  practice_trial: boolean;
  practice_attempt: number;
  participant_response: Answer | null;
  reaction_time_ms: number | null;
  response_timeout: boolean;
  premature_keypresses: number;
  interference_response: TF | null;
  interference_reaction_time_ms: number | null;
  actual_fixation_duration_ms: number | null;
  measured_stimulus_duration_ms: number | null;
  measured_post_stimulus_blank_ms: number | null;
  measured_interference_duration_ms: number | null;
  measured_retention_duration_ms: number | null;
  inter_trial_interval_ms: number | null;
  refresh_rate_hz: number | null;
  dropped_frames: number;
  focus_loss: boolean;
  event_timestamps: Record<string, number>;
}

export interface SessionStart {
  participant_id: string;
  session_id: string;
  session_token: string;
  session_type: "main" | "pilot";
  condition_order: string;
  experiment_version: string;
  config: ExperimentConfig;
  plan: TrialPlan;
}
