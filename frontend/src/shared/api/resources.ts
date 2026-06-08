import { clearCsrfTokenForNewSession, requestApi } from "./client";
import type {
  LlmText,
  MatchResult,
  MatchState,
  ProfileSummary,
  StoryCaseBriefing,
  StoryCaseSummary,
  TurnResult,
  User,
} from "../types/api";

export type LoginRequest = {
  email: string;
  password: string;
};

export type SignupRequest = {
  email: string;
  nickname: string;
  password: string;
};

export type TurnSubmitRequest = {
  action_code: string;
  info_target_key?: string | null;
  client_nonce: string;
};

export async function signup(body: SignupRequest): Promise<{ user: User }> {
  return requestApi<{ user: User }>("/api/v1/auth/signup", {
    method: "POST",
    body,
    csrf: true,
  });
}

export async function login(body: LoginRequest): Promise<{
  user: User;
  profile: ProfileSummary;
  session: {
    authenticated: true;
    access_expires_in_seconds: number;
  };
}> {
  return requestApi("/api/v1/auth/login", {
    method: "POST",
    body,
    csrf: true,
  });
}

export async function logout(): Promise<{ logged_out: true }> {
  try {
    return await requestApi<{ logged_out: true }>("/api/v1/auth/logout", {
      method: "POST",
      body: {},
      csrf: true,
    });
  } finally {
    clearCsrfTokenForNewSession();
  }
}

export async function getCurrentSession(): Promise<{
  authenticated: true;
  user: User;
  profile: ProfileSummary;
}> {
  return requestApi("/api/v1/auth/me");
}

export async function listStoryCases(): Promise<{ cases: StoryCaseSummary[] }> {
  return requestApi("/api/v1/story/cases");
}

export async function getStoryCaseBriefing(caseId: string): Promise<{ case: StoryCaseBriefing }> {
  return requestApi(`/api/v1/story/cases/${encodeURIComponent(caseId)}/briefing`);
}

export async function startStoryMatch(
  caseId: string,
  body: {
    client_request_id: string;
    player_display_name: string | null;
  },
): Promise<{ match: MatchState }> {
  return requestApi(`/api/v1/story/cases/${encodeURIComponent(caseId)}/matches`, {
    method: "POST",
    body,
    csrf: true,
  });
}

export async function getMatchDetail(matchId: string): Promise<{ match: MatchState }> {
  return requestApi(`/api/v1/matches/${encodeURIComponent(matchId)}`);
}

export async function submitTurn(
  matchId: string,
  body: TurnSubmitRequest,
): Promise<{
  turn_result: TurnResult;
  match: MatchState;
}> {
  return requestApi(`/api/v1/matches/${encodeURIComponent(matchId)}/turns`, {
    method: "POST",
    body,
    csrf: true,
  });
}

export async function generateTurnLlmText(
  matchId: string,
  turnId: string,
  displaySlot: string | null,
): Promise<{ llm_text: LlmText }> {
  return requestApi(
    `/api/v1/matches/${encodeURIComponent(matchId)}/turns/${encodeURIComponent(turnId)}/llm-text`,
    {
      method: "POST",
      body: { display_slot: displaySlot },
      csrf: true,
    },
  );
}

export async function getMatchResult(matchId: string): Promise<{ result: MatchResult }> {
  return requestApi(`/api/v1/matches/${encodeURIComponent(matchId)}/result`);
}

export async function getProfileMe(): Promise<{
  user: User;
  profile: ProfileSummary;
}> {
  return requestApi("/api/v1/profile/me");
}
