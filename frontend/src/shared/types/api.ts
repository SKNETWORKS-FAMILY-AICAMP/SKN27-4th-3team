export type ApiMeta = {
  request_id: string;
  server_time: string;
};

export type ApiError = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};

export type ApiSuccessEnvelope<T> = {
  data: T;
  meta: ApiMeta;
};

export type ApiErrorEnvelope = {
  error: ApiError;
  meta: ApiMeta;
};

export type User = {
  id: string;
  email: string;
  created_at?: string;
};

export type StyleMetrics = {
  aggression: number;
  defense: number;
  insight_focus: number;
  deception: number;
  risk_preference: number;
  silence_reliance: number;
  crisis_guard_rate: number;
  crisis_contract_rate: number;
  late_choice_rate: number;
};

export type StyleSummary = {
  label: string | null;
  display_text: string | null;
  metrics: StyleMetrics;
  updated_at: string | null;
};

export type ProfileSummary = {
  nickname: string;
  public_record: {
    ai_story_matches: number;
    ai_story_wins: number;
    ai_story_losses: number;
  };
  style_summary: StyleSummary;
};

export type StoryCaseSummary = {
  case_id: string;
  title: string;
  summary?: string;
  difficulty?: string;
  mvp_available: boolean;
  estimated_turns?: number;
};

export type StoryCaseBriefing = {
  case_id: string;
  title: string;
  apparition_alias: string;
  briefing_text: string[];
  taboo: {
    title: string;
    description: string;
  };
  info_targets: Array<{
    key: string;
    display_name: string;
  }>;
  max_turns: number;
};

export type ResourceState = {
  sanity: number;
  sanity_max: number;
  ritual_power: number;
  ritual_power_max: number;
  curse_marks: number;
  curse_marks_max: number;
  true_name_fragments: number;
  true_name_fragments_required: number;
  incomplete_true_name_fragments?: number;
  false_clues: number;
  false_clues_max: number;
  suspicion: number;
  suspicion_max: number;
  shield: number;
  shield_max: number;
  timeout_count: number;
};

export type PublicLog = {
  turn_number: number;
  text: string;
  log_key?: string | null;
};

export type Clue = {
  clue_id: string;
  text: string;
  truth_state: string;
  source_turn_number: number;
};

export type MatchState = {
  match_id: string;
  mode: string;
  status: string;
  case: {
    case_id: string;
    title: string;
  };
  turn: {
    turn_id: string;
    turn_number: number;
    max_turns: number;
    status: string;
    deadline_at: string;
    remaining_seconds: number;
    resolved_at?: string | null;
  };
  player: {
    participant_id: string;
    participant_type: "human";
    display_name: string;
    resources: ResourceState;
  };
  opponent: {
    participant_id: string;
    participant_type: "apparition";
    display_name: string;
    public_state: {
      true_name_fragments_revealed: number;
      true_name_fragments_required: number;
      seal_available: boolean;
    };
  };
  available_actions: Array<{
    code: string;
    display_name: string;
    ritual_power_cost: number;
    enabled: boolean;
    disabled_reason?: string | null;
    requires_info_target?: boolean;
  }>;
  clues: Clue[];
  recent_public_logs: PublicLog[];
};

export type TurnResult = {
  turn_id: string;
  turn_number: number;
  player_action: {
    code: string;
    display_name: string;
    info_target_key?: string | null;
    timeout_applied?: boolean;
  };
  opponent_action: {
    code: string;
    display_name: string;
    info_target_key?: string | null;
    timeout_applied?: boolean;
  };
  public_log: PublicLog;
  state_delta: Record<string, unknown>;
  clue_delta: {
    added: Clue[];
    removed_clue_ids: string[];
    revealed: Clue[];
  };
  match_outcome?: string;
};

export type LlmText = {
  enabled: boolean;
  purpose: string;
  text: string | null;
  display_slot: string | null;
  fallback_used: boolean;
  generation_id: string | null;
  context_refs: unknown[];
  metadata: Record<string, unknown>;
};

export type MatchResult = {
  match_id: string;
  result: string;
  result_reason: string;
  case: {
    case_id: string;
    title: string;
  };
  final_resources: ResourceState;
  turn_logs: PublicLog[];
  story_result_text: string[];
  style_summary: StyleSummary;
  llm_summary: {
    enabled: boolean;
    text: string | null;
    generation_id: string | null;
  };
};
