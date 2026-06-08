import { useCallback } from "react";
import { useLocation, useParams } from "react-router-dom";
import { RitualDuelScreen, PrototypeTurnRequest } from "../../features/match/RitualDuelScreen";
import { ApiClientError } from "../../shared/api/client";
import { generateTurnLlmText, getMatchDetail, submitTurn } from "../../shared/api/resources";
import type { LlmText, MatchState, TurnResult } from "../../shared/types/api";

type MatchRouteState = {
  fromLobbyTransition?: boolean;
  fromPrologueTransition?: boolean;
};

export function MatchRoute() {
  const location = useLocation();
  const { matchId = "prototype-mirror-guest" } = useParams();
  const state = location.state as MatchRouteState | null;
  const turnResultProvider = useCallback(
    async (request: PrototypeTurnRequest) => {
      if (!request.turnSubmitPayload) {
        throw new Error("turnSubmitPayload is required for backend turn submission.");
      }

      let data: {
        turn_result: TurnResult;
        match: MatchState;
      };
      try {
        data = await submitTurn(matchId, request.turnSubmitPayload);
      } catch (error) {
        if (error instanceof ApiClientError && error.code === "TURN_DEADLINE_EXPIRED") {
          const latest = await getMatchDetail(matchId);
          return toPrototypeDeadlineExpiredResult(latest.match);
        }
        throw error;
      }

      let llmText: LlmText | null = null;
      try {
        const llmResponse = await generateTurnLlmText(
          matchId,
          data.turn_result.turn_id,
          "right_apparition_message",
        );
        llmText = llmResponse.llm_text;
      } catch {
        llmText = null;
      }

      return toPrototypeTurnResult(data.turn_result, data.match, llmText);
    },
    [matchId],
  );

  return (
    <RitualDuelScreen
      matchId={matchId}
      fadeIn={Boolean(state?.fromLobbyTransition || state?.fromPrologueTransition)}
      turnResultProvider={turnResultProvider}
    />
  );
}

function toPrototypeTurnResult(turnResult: TurnResult, match: MatchState, llmText: LlmText | null) {
  const enemyKey = toPrototypeActionKey(turnResult.opponent_action.code);
  const stateChanges = toPrototypeStateChanges(turnResult, match);
  const sealSuccess = turnResult.match_outcome === "player_win";

  return {
    playerLabel: turnResult.player_action.display_name,
    enemy: {
      key: enemyKey,
      label: turnResult.opponent_action.display_name,
      action: `괴이 행동: ${turnResult.opponent_action.display_name}`,
      line: turnResult.public_log.text,
    },
    briefing: turnResult.public_log.text,
    delta: formatStateDelta(turnResult),
    publicLog: turnResult.public_log.text,
    stateChanges,
    patternHint: llmText?.text || "",
    seal: turnResult.player_action.code === "seal"
      ? {
          interference: sealSuccess ? 0 : 2,
          success: sealSuccess,
        }
      : null,
    llm_text: llmText,
    llm_ui_texts: llmText?.enabled && llmText.text ? [llmText] : [],
  };
}

function toPrototypeActionKey(actionCode: string): string {
  return actionCode === "trick" ? "deceive" : actionCode;
}

function toPrototypeStateChanges(turnResult: TurnResult, match: MatchState) {
  const stateDelta = turnResult.state_delta;
  const resources = match.player.resources;

  return {
    sanity: mapResourceDelta(stateDelta.sanity, resources.sanity_max),
    soulfire: mapResourceDelta(stateDelta.ritual_power, resources.ritual_power_max),
    curse: mapResourceDelta(stateDelta.curse_marks, resources.curse_marks_max),
    shield: resources.shield,
    partialTrueName: resources.incomplete_true_name_fragments ?? 0,
    trueNamePieces: resources.true_name_fragments,
    suspicion: resources.suspicion,
    clues: turnResult.clue_delta.added
      .filter((clue) => clue.truth_state === "true_revealed")
      .map(toPrototypeClue),
    suspectClues: turnResult.clue_delta.added
      .filter((clue) => clue.truth_state === "false_revealed")
      .map(toPrototypeClue),
    revealedFalseClues: turnResult.clue_delta.revealed.map(toPrototypeClue),
    turnEvents: [turnResult.public_log.text],
  };
}

function toPrototypeDeadlineExpiredResult(match: MatchState) {
  const latestLog = match.recent_public_logs.at(-1)?.text
    || "서버 기준 제한 시간이 지나 침묵으로 처리되었습니다.";
  const resources = match.player.resources;

  return {
    playerLabel: "침묵",
    enemy: {
      key: "silence",
      label: "침묵",
      action: "괴이 행동: 침묵",
      line: latestLog,
    },
    briefing: latestLog,
    delta: "시간초과로 서버 최신 상태를 다시 불러왔습니다.",
    publicLog: latestLog,
    stateChanges: {
      sanity: {
        before: resources.sanity,
        after: resources.sanity,
        delta: 0,
        max: resources.sanity_max,
      },
      curse: {
        before: resources.curse_marks,
        after: resources.curse_marks,
        delta: 0,
        max: resources.curse_marks_max,
      },
      shield: resources.shield,
      partialTrueName: resources.incomplete_true_name_fragments ?? 0,
      trueNamePieces: resources.true_name_fragments,
      suspicion: resources.suspicion,
      clues: [],
      suspectClues: [],
      revealedFalseClues: [],
      turnEvents: [latestLog],
    },
    patternHint: "",
    seal: null,
    llm_text: null,
    llm_ui_texts: [],
  };
}

function mapResourceDelta(value: unknown, max: number) {
  if (!isDelta(value)) return undefined;
  return {
    before: value.before,
    after: value.after,
    delta: value.delta,
    max,
  };
}

function isDelta(value: unknown): value is { before: number; after: number; delta: number } {
  return typeof value === "object"
    && value !== null
    && typeof (value as { before?: unknown }).before === "number"
    && typeof (value as { after?: unknown }).after === "number"
    && typeof (value as { delta?: unknown }).delta === "number";
}

function toPrototypeClue(clue: { clue_id: string; text: string }) {
  return {
    id: clue.clue_id,
    text: clue.text,
    source: clue.clue_id,
  };
}

function formatStateDelta(turnResult: TurnResult): string {
  const entries = Object.entries(turnResult.state_delta);
  if (entries.length === 0) {
    return "상태 변화 없음";
  }

  return entries
    .map(([key, value]) => {
      if (!isDelta(value)) return key;
      const sign = value.delta > 0 ? "+" : "";
      return `${key} ${value.before}->${value.after} (${sign}${value.delta})`;
    })
    .join(" / ");
}
